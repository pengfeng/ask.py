import json
import logging
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

import click
import duckdb
import gradio as gr
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jinja2 import BaseLoader, Environment
from openai import OpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))
default_env_file = os.path.abspath(os.path.join(script_dir, ".env"))


def get_logger(log_level: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class Ask:

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.read_env_variables()

        if logger is not None:
            self.logger = logger
        else:
            self.logger = get_logger("INFO")

        self.table_name = "document_chunks"
        self.db_con = duckdb.connect(":memory:")

        self.db_con.install_extension("vss")
        self.db_con.load_extension("vss")
        self.db_con.install_extension("fts")
        self.db_con.load_extension("fts")
        self.db_con.sql("CREATE SEQUENCE seq_docid START 1000")

        self.db_con.execute(
            f"""
CREATE TABLE {self.table_name} (
    doc_id INTEGER PRIMARY KEY DEFAULT nextval('seq_docid'),
    url TEXT,
    chunk TEXT,
    vec FLOAT[{self.embedding_dimensions}]
);
"""
        )

        self.session = requests.Session()
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        )
        self.session.headers.update({"User-Agent": user_agent})

    def read_env_variables(self) -> None:
        err_msg = ""

        self.search_api_key = os.environ.get("SEARCH_API_KEY")
        if self.search_api_key is None:
            err_msg += "SEARCH_API_KEY env variable not set.\n"
        self.search_project_id = os.environ.get("SEARCH_PROJECT_KEY")
        if self.search_project_id is None:
            err_msg += "SEARCH_PROJECT_KEY env variable not set.\n"
        self.llm_api_key = os.environ.get("LLM_API_KEY")
        if self.llm_api_key is None:
            err_msg += "LLM_API_KEY env variable not set.\n"

        if err_msg != "":
            raise Exception(f"\n{err_msg}\n")

        self.llm_base_url = os.environ.get("LLM_BASE_URL")
        if self.llm_base_url is None:
            self.llm_base_url = "https://api.openai.com/v1"

        self.embedding_model = os.environ.get("EMBEDDING_MODEL")
        self.embedding_dimensions = os.environ.get("EMBEDDING_DIMENSIONS")

        if self.embedding_model is None or self.embedding_dimensions is None:
            self.embedding_model = "text-embedding-3-small"
            self.embedding_dimensions = 1536

    def search_web(self, query: str, date_restrict: int, target_site: str) -> List[str]:
        escaped_query = urllib.parse.quote(query)
        url_base = (
            f"https://www.googleapis.com/customsearch/v1?key={self.search_api_key}"
            f"&cx={self.search_project_id}&q={escaped_query}"
        )
        url_paras = f"&safe=active"
        if date_restrict is not None and date_restrict > 0:
            url_paras += f"&dateRestrict={date_restrict}"
        if target_site is not None and target_site != "":
            url_paras += f"&siteSearch={target_site}&siteSearchFilter=i"
        url = f"{url_base}{url_paras}"

        self.logger.debug(f"Searching for query: {query}")

        resp = requests.get(url)

        if resp is None:
            raise Exception("No response from search API")

        search_results_dict = json.loads(resp.text)
        if "error" in search_results_dict:
            raise Exception(
                f"Error in search API response: {search_results_dict['error']}"
            )

        if "searchInformation" not in search_results_dict:
            raise Exception(
                f"No search information in search API response: {resp.text}"
            )

        total_results = search_results_dict["searchInformation"].get("totalResults", 0)
        if total_results == 0:
            self.logger.warning(f"No results found for query: {query}")
            return []

        results = search_results_dict.get("items", [])
        if results is None or len(results) == 0:
            self.logger.warning(f"No result items in the response for query: {query}")
            return []

        found_links = []
        for result in results:
            link = result.get("link", None)
            if link is None or link == "":
                self.logger.warning(f"Search result link missing: {result}")
                continue
            found_links.append(link)
        return found_links

    def _scape_url(self, url: str) -> Tuple[str, str]:
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")

            body_tag = soup.body
            if body_tag:
                body_text = body_tag.get_text()
                body_text = " ".join(body_text.split()).strip()
                self.logger.debug(f"Scraped {url}: {body_text}...")
                if len(body_text) > 100:
                    return url, body_text
                else:
                    self.logger.warning(
                        f"Body text too short for url: {url}, length: {len(body_text)}"
                    )
                    return url, ""
            else:
                self.logger.warning(f"No body tag found in the response for url: {url}")
                return url, ""
        except Exception as e:
            self.logger.error(f"Scraping error {url}: {e}")
            return url, ""

    def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        # the key is the url and the value is the body text
        scrape_results: Dict[str, str] = {}

        partial_scrape = partial(self._scape_url)
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(partial_scrape, urls)

        for url, body_text in results:
            if body_text != "":
                scrape_results[url] = body_text

        return scrape_results

    def chunk_results(
        self, scrape_results: Dict[str, str], size: int, overlap: int
    ) -> Dict[str, List[str]]:
        chunking_results: Dict[str, List[str]] = {}
        for url, text in scrape_results.items():
            chunks = []
            for pos in range(0, len(text), size - overlap):
                chunks.append(text[pos : pos + size])
            chunking_results[url] = chunks
        return chunking_results

    def get_embedding(self, client: OpenAI, texts: List[str]) -> List[List[float]]:
        if len(texts) == 0:
            return []

        response = client.embeddings.create(input=texts, model=self.embedding_model)
        embeddings = []
        for i in range(len(response.data)):
            embeddings.append(response.data[i].embedding)
        return embeddings

    def batch_get_embedding(
        self, client: OpenAI, chunk_batch: Tuple[str, List[str]]
    ) -> Tuple[Tuple[str, List[str]], List[List[float]]]:
        """
        Return the chunk_batch as well as the embeddings for each chunk so that
        we can aggregate them and save them to the database together.

        Args:
        - client: OpenAI client
        - chunk_batch: Tuple of URL and list of chunks scraped from the URL

        Returns:
        - Tuple of chunk_bach and list of result embeddings
        """
        texts = chunk_batch[1]
        embeddings = self.get_embedding(client, texts)
        return chunk_batch, embeddings

    def save_to_db(self, chunking_results: Dict[str, List[str]]) -> None:
        client = self._get_api_client()
        embed_batch_size = 50
        query_batch_size = 100
        insert_data = []

        batches: List[Tuple[str, List[str]]] = []
        for url, list_chunks in chunking_results.items():
            for i in range(0, len(list_chunks), embed_batch_size):
                list_chunks = list_chunks[i : i + embed_batch_size]
                batches.append((url, list_chunks))

        self.logger.info(f"Embedding {len(batches)} batches of chunks ...")
        partial_get_embedding = partial(self.batch_get_embedding, client)
        with ThreadPoolExecutor(max_workers=10) as executor:
            all_embeddings = executor.map(partial_get_embedding, batches)
        self.logger.info(f"✅ Finished embedding.")

        for chunk_batch, embeddings in all_embeddings:
            url = chunk_batch[0]
            list_chunks = chunk_batch[1]
            insert_data.extend(
                [
                    (url.replace("'", " "), chunk.replace("'", " "), embedding)
                    for chunk, embedding in zip(list_chunks, embeddings)
                ]
            )

        for i in range(0, len(insert_data), query_batch_size):
            # insert the batch into DuckDB
            value_str = ", ".join(
                [
                    f"('{url}', '{chunk}', {embedding})"
                    for url, chunk, embedding in insert_data[i : i + embed_batch_size]
                ]
            )
            query = f"""
            INSERT INTO {self.table_name} (url, chunk, vec) VALUES {value_str};
            """
            self.db_con.execute(query)

        self.db_con.execute(
            f"""
                CREATE INDEX cos_idx ON {self.table_name} USING HNSW (vec)
                WITH (metric = 'cosine');
            """
        )
        self.logger.info(f"✅ Created the vector index ...")
        self.db_con.execute(
            f"""
                PRAGMA create_fts_index(
                {self.table_name}, 'doc_id', 'chunk'
                );    
            """
        )
        self.logger.info(f"✅ Created the full text search index ...")

    def vector_search(self, query: str) -> List[Dict[str, Any]]:
        client = self._get_api_client()
        embeddings = self.get_embedding(client, [query])[0]

        query_result: duckdb.DuckDBPyRelation = self.db_con.sql(
            f"""
            SELECT * FROM {self.table_name} 
            ORDER BY array_distance(vec, {embeddings}::FLOAT[{self.embedding_dimensions}]) 
            LIMIT 10;         
        """
        )

        self.logger.debug(query_result)

        matched_chunks = []
        for record in query_result.fetchall():
            result_record = {
                "url": record[1],
                "chunk": record[2],
            }
            matched_chunks.append(result_record)

        return matched_chunks

    def _get_api_client(self) -> OpenAI:
        return OpenAI(api_key=self.llm_api_key, base_url=self.llm_base_url)

    def _render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        env = Environment(loader=BaseLoader(), autoescape=False)
        template = env.from_string(template_str)
        return template.render(variables)

    def run_inference(
        self,
        query: str,
        model_name: str,
        matched_chunks: List[Dict[str, Any]],
        output_language: str,
        output_length: int,
    ) -> str:
        system_prompt = (
            "You are an expert summarizing the answers based on the provided contents."
        )
        user_promt_template = """
Given the context as a sequence of references with a reference id in the 
format of a leading [x], please answer the following question using {{ language }}:

{{ query }}

In the answer, use format [1], [2], ..., [n] in line where the reference is used. 
For example, "According to the research from Google[3], ...".

Please create the answer strictly related to the context. If the context has no
information about the query, please write "No related information found in the context."
using {{ language }}.

{{ length_instructions }}

Here is the context:
{{ context }}
"""
        context = ""
        for i, chunk in enumerate(matched_chunks):
            context += f"[{i+1}] {chunk['chunk']}\n"

        if output_length is None or output_length == 0:
            length_instructions = ""
        else:
            length_instructions = (
                f"Please provide the answer in { output_length } words."
            )

        user_prompt = self._render_template(
            user_promt_template,
            {
                "query": query,
                "context": context,
                "language": output_language,
                "length_instructions": length_instructions,
            },
        )

        self.logger.debug(f"Running inference with model: {model_name}")
        self.logger.debug(f"Final user prompt: {user_prompt}")

        api_client = self._get_api_client()
        completion = api_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
        if completion is None:
            raise Exception("No completion from the API")

        response_str = completion.choices[0].message.content
        return response_str


def _read_url_list(url_list_file: str) -> str:
    if url_list_file is None:
        return None

    with open(url_list_file, "r") as f:
        links = f.readlines()
    links = [
        link.strip()
        for link in links
        if link.strip() != "" and not link.startswith("#")
    ]
    return "\n".join(links)


def _run_query(
    query: str,
    date_restrict: int,
    target_site: str,
    output_language: str,
    output_length: int,
    url_list_str: str,
    model_name: str,
    log_level: str,
) -> str:
    logger = get_logger(log_level)

    ask = Ask(logger=logger)

    if url_list_str is None or url_list_str.strip() == "":
        logger.info("Searching the web ...")
        links = ask.search_web(query, date_restrict, target_site)
        logger.info(f"✅ Found {len(links)} links for query: {query}")
        for i, link in enumerate(links):
            logger.debug(f"{i+1}. {link}")
    else:
        links = url_list_str.split("\n")

    logger.info("Scraping the URLs ...")
    scrape_results = ask.scrape_urls(links)
    logger.info(f"✅ Scraped {len(scrape_results)} URLs.")

    logger.info("Chunking the text ...")
    chunking_results = ask.chunk_results(scrape_results, 1000, 100)
    total_chunks = 0
    for url, chunks in chunking_results.items():
        logger.debug(f"URL: {url}")
        total_chunks += len(chunks)
        for i, chunk in enumerate(chunks):
            logger.debug(f"Chunk {i+1}: {chunk}")
    logger.info(f"✅ Generated {total_chunks} chunks ...")

    logger.info(f"Saving {total_chunks} chunks to DB ...")
    ask.save_to_db(chunking_results)
    logger.info(f"✅ Successfully embedded and saved chunks to DB.")

    logger.info("Querying the vector DB to get context ...")
    matched_chunks = ask.vector_search(query)
    for i, result in enumerate(matched_chunks):
        logger.debug(f"{i+1}. {result}")
    logger.info(f"✅ Got {len(matched_chunks)} matched chunks.")

    logger.info("Running inference with context ...")
    answer = ask.run_inference(
        query=query,
        model_name=model_name,
        matched_chunks=matched_chunks,
        output_language=output_language,
        output_length=output_length,
    )
    logger.info("✅ Finished inference API call.")
    logger.info("generateing output ...")

    answer = f"# Answer\n\n{answer}\n"
    references = "\n".join(
        [f"[{i+1}] {result['url']}" for i, result in enumerate(matched_chunks)]
    )
    return f"{answer}\n\n# References\n\n{references}"


def launch_gradio(
    query: str,
    date_restrict: int,
    target_site: str,
    output_language: str,
    output_length: int,
    url_list_str: str,
    model_name: str,
    log_level: str,
    share_ui: bool,
) -> None:
    iface = gr.Interface(
        fn=_run_query,
        inputs=[
            gr.Textbox(label="Query", value=query),
            gr.Number(
                label="Date Restrict (Optional) [0 or empty means no date limit.]",
                value=date_restrict,
            ),
            gr.Textbox(
                label="Target Sites (Optional) [Empty means seach the whole web.]",
                value=target_site,
            ),
            gr.Textbox(
                label="Output Language (Optional) [Default is English.]",
                value=output_language,
            ),
            gr.Number(
                label="Output Length in words (Optional) [Default is automatically decided by LLM.]",
                value=output_length,
            ),
            gr.Textbox(
                label="URL List (Optional) [When specified, scrape the urls instead of searching the web.]",
                lines=5,
                max_lines=20,
                value=url_list_str,
            ),
        ],
        additional_inputs=[
            gr.Textbox(label="Model Name", value=model_name),
            gr.Textbox(label="Log Level", value=log_level),
        ],
        outputs="text",
        show_progress=True,
        flagging_options=[("Report Error", None)],
        title="Ask.py - Web Search-Extract-Summarize",
        description="Search the web with the query and summarize the results. Source code: https://github.com/pengfeng/ask.py",
    )

    iface.launch(share=share_ui)


@click.command(help="Search web for the query and summarize the results")
@click.option(
    "--web-ui",
    is_flag=True,
    help="Launch the web interface",
)
@click.option("--query", "-q", required=False, help="Query to search")
@click.option(
    "--date-restrict",
    "-d",
    type=int,
    required=False,
    default=None,
    help="Restrict search results to a specific date range, default is no restriction",
)
@click.option(
    "--target-site",
    "-s",
    required=False,
    default=None,
    help="Restrict search results to a specific site, default is no restriction",
)
@click.option(
    "--output-language",
    required=False,
    default="English",
    help="Output language for the answer",
)
@click.option(
    "--output-length",
    type=int,
    required=False,
    default=None,
    help="Output length for the answer",
)
@click.option(
    "--url-list-file",
    type=str,
    required=False,
    default=None,
    show_default=True,
    help="Instead of doing web search, scrape the target URL list and answer the query based on the content",
)
@click.option(
    "--model-name",
    "-m",
    required=False,
    default="gpt-4o-mini",
    help="Model name to use for inference",
)
@click.option(
    "-l",
    "--log-level",
    "log_level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Set the logging level",
    show_default=True,
)
def search_extract_summarize(
    web_ui: bool,
    query: str,
    date_restrict: int,
    target_site: str,
    output_language: str,
    output_length: int,
    url_list_file: str,
    model_name: str,
    log_level: str,
):
    load_dotenv(dotenv_path=default_env_file, override=False)

    if web_ui or os.environ.get("RUN_GRADIO_UI", "false").lower() != "false":
        if os.environ.get("SHARE_GRADIO_UI", "false").lower() == "true":
            share_ui = True
        else:
            share_ui = False
        launch_gradio(
            query=query,
            date_restrict=date_restrict,
            target_site=target_site,
            output_language=output_language,
            output_length=output_length,
            url_list_str=_read_url_list(url_list_file),
            model_name=model_name,
            log_level=log_level,
            share_ui=share_ui,
        )
    else:
        if query is None:
            raise Exception("Query is required for the command line mode")

        result = _run_query(
            query=query,
            date_restrict=date_restrict,
            target_site=target_site,
            output_language=output_language,
            output_length=output_length,
            url_list_str=_read_url_list(url_list_file),
            model_name=model_name,
            log_level=log_level,
        )
        click.echo(result)


if __name__ == "__main__":
    search_extract_summarize()
