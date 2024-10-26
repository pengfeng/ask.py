import json
import logging
import os
import queue
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from queue import Queue
from typing import Any, Dict, Generator, List, Optional, Tuple

import click
import duckdb
import gradio as gr
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jinja2 import BaseLoader, Environment
from openai import OpenAI
from pydantic import BaseModel

script_dir = os.path.dirname(os.path.abspath(__file__))
default_env_file = os.path.abspath(os.path.join(script_dir, ".env"))


class AskSettings(BaseModel):
    date_restrict: int
    target_site: str
    output_language: str
    output_length: int
    url_list: List[str]
    inference_model_name: str
    hybrid_search: bool


def _get_logger(log_level: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    if len(logger.handlers) > 0:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _read_url_list(url_list_file: str) -> List[str]:
    if not url_list_file:
        return []

    with open(url_list_file, "r") as f:
        links = f.readlines()
    url_list = [
        link.strip()
        for link in links
        if link.strip() != "" and not link.startswith("#")
    ]
    return url_list


class Ask:

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.read_env_variables()

        if logger is not None:
            self.logger = logger
        else:
            self.logger = _get_logger("INFO")

        self.db_con = duckdb.connect(":memory:")

        self.db_con.install_extension("vss")
        self.db_con.load_extension("vss")
        self.db_con.install_extension("fts")
        self.db_con.load_extension("fts")
        self.db_con.sql("CREATE SEQUENCE seq_docid START 1000")

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

    def search_web(self, query: str, settings: AskSettings) -> List[str]:
        escaped_query = urllib.parse.quote(query)
        url_base = (
            f"https://www.googleapis.com/customsearch/v1?key={self.search_api_key}"
            f"&cx={self.search_project_id}&q={escaped_query}"
        )
        url_paras = f"&safe=active"
        if settings.date_restrict > 0:
            url_paras += f"&dateRestrict={settings.date_restrict}"
        if settings.target_site:
            url_paras += f"&siteSearch={settings.target_site}&siteSearchFilter=i"
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
        self.logger.info(f"Scraping {url} ...")
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")

            body_tag = soup.body
            if body_tag:
                body_text = body_tag.get_text()
                body_text = " ".join(body_text.split()).strip()
                self.logger.debug(f"Scraped {url}: {body_text}...")
                if len(body_text) > 100:
                    self.logger.info(
                        f"✅ Successfully scraped {url} with length: {len(body_text)}"
                    )
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

    def _create_table(self) -> str:
        # Simple ways to get a unique table name
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        table_name = f"document_chunks_{timestamp}"

        self.db_con.execute(
            f"""
CREATE TABLE {table_name} (
    doc_id INTEGER PRIMARY KEY DEFAULT nextval('seq_docid'),
    url TEXT,
    chunk TEXT,
    vec FLOAT[{self.embedding_dimensions}]
);
"""
        )
        return table_name

    def save_chunks_to_db(self, chunking_results: Dict[str, List[str]]) -> str:
        """
        The key of chunking_results is the URL and the value is the list of chunks.
        """
        client = self._get_api_client()
        embed_batch_size = 50
        query_batch_size = 100
        insert_data = []

        table_name = self._create_table()

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

        # we batch the insert data to speed up the insertion operation
        # although the DuckDB doc says executeMany is optimized for batch insert
        # but we found that it is faster to batch the insert data and run a single insert
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
            value_str = ", ".join(
                [
                    f"('{url}', '{chunk}', {embedding})"
                    for url, chunk, embedding in insert_data[i : i + embed_batch_size]
                ]
            )
            query = f"""
            INSERT INTO {table_name} (url, chunk, vec) VALUES {value_str};
            """
            self.db_con.execute(query)

        self.db_con.execute(
            f"""
                CREATE INDEX {table_name}_cos_idx ON {table_name} USING HNSW (vec)
                WITH (metric = 'cosine');
            """
        )
        self.logger.info(f"✅ Created the vector index ...")
        self.db_con.execute(
            f"""
                PRAGMA create_fts_index(
                {table_name}, 'doc_id', 'chunk'
                );    
            """
        )
        self.logger.info(f"✅ Created the full text search index ...")
        return table_name

    def vector_search(
        self, table_name: str, query: str, settings: AskSettings
    ) -> List[Dict[str, Any]]:
        """
        The return value is a list of {url: str, chunk: str} records.
        In a real world, we will define a class of Chunk to have more metadata such as offsets.
        """
        client = self._get_api_client()
        embeddings = self.get_embedding(client, [query])[0]

        query_result: duckdb.DuckDBPyRelation = self.db_con.sql(
            f"""
            SELECT * FROM {table_name} 
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

        if settings.hybrid_search:
            self.logger.info("Running full-text search ...")
            pass

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
        matched_chunks: List[Dict[str, Any]],
        settings: AskSettings,
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

        if not settings.output_length:
            length_instructions = ""
        else:
            length_instructions = (
                f"Please provide the answer in { settings.output_length } words."
            )

        user_prompt = self._render_template(
            user_promt_template,
            {
                "query": query,
                "context": context,
                "language": settings.output_language,
                "length_instructions": length_instructions,
            },
        )

        self.logger.debug(
            f"Running inference with model: {settings.inference_model_name}"
        )
        self.logger.debug(f"Final user prompt: {user_prompt}")

        api_client = self._get_api_client()
        completion = api_client.chat.completions.create(
            model=settings.inference_model_name,
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

    def run_query_gradio(
        self,
        query: str,
        date_restrict: int,
        target_site: str,
        output_language: str,
        output_length: int,
        url_list_str: str,
        inference_model_name: str,
        hybrid_search: bool,
    ) -> Generator[Tuple[str, str], None, Tuple[str, str]]:
        logger = self.logger
        log_queue = Queue()

        if url_list_str:
            url_list = url_list_str.split("\n")
        else:
            url_list = []

        settings = AskSettings(
            date_restrict=date_restrict,
            target_site=target_site,
            output_language=output_language,
            output_length=output_length,
            url_list=url_list,
            inference_model_name=inference_model_name,
            hybrid_search=hybrid_search,
        )

        queue_handler = logging.Handler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        queue_handler.emit = lambda record: log_queue.put(formatter.format(record))
        logger.addHandler(queue_handler)

        def update_logs():
            logs = []
            while True:
                try:
                    log = log_queue.get_nowait()
                    logs.append(log)
                except queue.Empty:
                    break
            return "\n".join(logs)

        # wrap the process in a generator to yield the logs to integrate with GradIO
        def process_with_logs():
            if len(settings.url_list) > 0:
                links = settings.url_list
            else:
                logger.info("Searching the web ...")
                yield "", update_logs()
                links = self.search_web(query, settings)
                logger.info(f"✅ Found {len(links)} links for query: {query}")
                for i, link in enumerate(links):
                    logger.debug(f"{i+1}. {link}")
                yield "", update_logs()

            logger.info("Scraping the URLs ...")
            yield "", update_logs()
            scrape_results = self.scrape_urls(links)
            logger.info(f"✅ Scraped {len(scrape_results)} URLs.")
            yield "", update_logs()

            logger.info("Chunking the text ...")
            yield "", update_logs()
            chunking_results = self.chunk_results(scrape_results, 1000, 100)
            total_chunks = 0
            for url, chunks in chunking_results.items():
                logger.debug(f"URL: {url}")
                total_chunks += len(chunks)
                for i, chunk in enumerate(chunks):
                    logger.debug(f"Chunk {i+1}: {chunk}")
            logger.info(f"✅ Generated {total_chunks} chunks ...")
            yield "", update_logs()

            logger.info(f"Saving {total_chunks} chunks to DB ...")
            yield "", update_logs()
            table_name = self.save_chunks_to_db(chunking_results)
            logger.info(f"✅ Successfully embedded and saved chunks to DB.")
            yield "", update_logs()

            logger.info("Querying the vector DB to get context ...")
            matched_chunks = self.vector_search(table_name, query, settings)
            for i, result in enumerate(matched_chunks):
                logger.debug(f"{i+1}. {result}")
            logger.info(f"✅ Got {len(matched_chunks)} matched chunks.")
            yield "", update_logs()

            logger.info("Running inference with context ...")
            yield "", update_logs()
            answer = self.run_inference(
                query=query,
                matched_chunks=matched_chunks,
                settings=settings,
            )
            logger.info("✅ Finished inference API call.")
            logger.info("Generating output ...")
            yield "", update_logs()

            answer = f"# Answer\n\n{answer}\n"
            references = "\n".join(
                [f"[{i+1}] {result['url']}" for i, result in enumerate(matched_chunks)]
            )
            yield f"{answer}\n\n# References\n\n{references}", update_logs()

        logs = ""
        final_result = ""

        try:
            for result, log_update in process_with_logs():
                logs += log_update + "\n"
                final_result = result
                yield final_result, logs
        finally:
            logger.removeHandler(queue_handler)

        return final_result, logs

    def run_query(
        self,
        query: str,
        settings: AskSettings,
    ) -> str:
        url_list_str = "\n".join(settings.url_list)

        for result, logs in self.run_query_gradio(
            query=query,
            date_restrict=settings.date_restrict,
            target_site=settings.target_site,
            output_language=settings.output_language,
            output_length=settings.output_length,
            url_list_str=url_list_str,
            inference_model_name=settings.inference_model_name,
            hybrid_search=settings.hybrid_search,
        ):
            final_result = result
        return final_result


def launch_gradio(
    query: str,
    init_settings: AskSettings,
    share_ui: bool,
    logger: logging.Logger,
) -> None:
    ask = Ask(logger=logger)
    with gr.Blocks() as demo:
        gr.Markdown("# Ask.py - Web Search-Extract-Summarize")
        gr.Markdown(
            "Search the web with the query and summarize the results. Source code: https://github.com/pengfeng/ask.py"
        )

        with gr.Row():
            with gr.Column():

                query_input = gr.Textbox(label="Query", value=query)
                hybrid_search_input = gr.Checkbox(
                    label="Hybrid Search [Use both vector search and full-text search.]",
                    value=init_settings.hybrid_search,
                )
                date_restrict_input = gr.Number(
                    label="Date Restrict (Optional) [0 or empty means no date limit.]",
                    value=init_settings.date_restrict,
                )
                target_site_input = gr.Textbox(
                    label="Target Sites (Optional) [Empty means searching the whole web.]",
                    value=init_settings.target_site,
                )
                output_language_input = gr.Textbox(
                    label="Output Language (Optional) [Default is English.]",
                    value=init_settings.output_language,
                )
                output_length_input = gr.Number(
                    label="Output Length in words (Optional) [Default is automatically decided by LLM.]",
                    value=init_settings.output_length,
                )
                url_list_input = gr.Textbox(
                    label="URL List (Optional) [When specified, scrape the urls instead of searching the web.]",
                    lines=5,
                    max_lines=20,
                    value="\n".join(init_settings.url_list),
                )

                with gr.Accordion("More Options", open=False):
                    inference_model_name_input = gr.Textbox(
                        label="Inference Model Name",
                        value=init_settings.inference_model_name,
                    )

                submit_button = gr.Button("Submit")

            with gr.Column():
                answer_output = gr.Textbox(label="Answer")
                logs_output = gr.Textbox(label="Logs", lines=10)

        submit_button.click(
            fn=ask.run_query_gradio,
            inputs=[
                query_input,
                date_restrict_input,
                target_site_input,
                output_language_input,
                output_length_input,
                url_list_input,
                inference_model_name_input,
                hybrid_search_input,
            ],
            outputs=[answer_output, logs_output],
        )

    demo.queue().launch(share=share_ui)


@click.command(help="Search web for the query and summarize the results.")
@click.option("--query", "-q", required=False, help="Query to search")
@click.option(
    "--date-restrict",
    "-d",
    type=int,
    required=False,
    default=0,
    help="Restrict search results to a specific date range, default is no restriction",
)
@click.option(
    "--target-site",
    "-s",
    required=False,
    default="",
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
    default=0,
    help="Output length for the answer",
)
@click.option(
    "--url-list-file",
    type=str,
    required=False,
    default="",
    show_default=True,
    help="Instead of doing web search, scrape the target URL list and answer the query based on the content",
)
@click.option(
    "--inference-model-name",
    "-m",
    required=False,
    default="gpt-4o-mini",
    help="Model name to use for inference",
)
@click.option(
    "--hybrid-search",
    is_flag=True,
    help="Use hybrid search mode with both vector search and full-text search",
)
@click.option(
    "--web-ui",
    is_flag=True,
    help="Launch the web interface",
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
    query: str,
    date_restrict: int,
    target_site: str,
    output_language: str,
    output_length: int,
    url_list_file: str,
    inference_model_name: str,
    hybrid_search: bool,
    web_ui: bool,
    log_level: str,
):
    load_dotenv(dotenv_path=default_env_file, override=False)
    logger = _get_logger(log_level)

    settings = AskSettings(
        date_restrict=date_restrict,
        target_site=target_site,
        output_language=output_language,
        output_length=output_length,
        url_list=_read_url_list(url_list_file),
        inference_model_name=inference_model_name,
        hybrid_search=hybrid_search,
    )

    if web_ui or os.environ.get("RUN_GRADIO_UI", "false").lower() != "false":
        if os.environ.get("SHARE_GRADIO_UI", "false").lower() == "true":
            share_ui = True
        else:
            share_ui = False
        launch_gradio(
            query=query,
            init_settings=settings,
            share_ui=share_ui,
            logger=logger,
        )
    else:
        if query is None:
            raise Exception("Query is required for the command line mode")
        ask = Ask(logger=logger)

        final_result = ask.run_query(query=query, settings=settings)
        click.echo(final_result)


if __name__ == "__main__":
    search_extract_summarize()
