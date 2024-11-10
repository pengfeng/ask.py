import csv
import io
import json
import logging
import os
import queue
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from functools import partial
from queue import Queue
from typing import Any, Dict, Generator, List, Optional, Tuple, TypeVar

import click
import duckdb
import gradio as gr
import requests
from bs4 import BeautifulSoup
from chonkie import Chunk, TokenChunker
from dotenv import load_dotenv
from jinja2 import BaseLoader, Environment
from openai import OpenAI
from pydantic import BaseModel, create_model

TypeVar_BaseModel = TypeVar("TypeVar_BaseModel", bound=BaseModel)


script_dir = os.path.dirname(os.path.abspath(__file__))
default_env_file = os.path.abspath(os.path.join(script_dir, ".env"))


class OutputMode(str, Enum):
    answer = "answer"
    extract = "extract"


class AskSettings(BaseModel):
    date_restrict: int
    target_site: str
    output_language: str
    output_length: int
    url_list: List[str]
    inference_model_name: str
    hybrid_search: bool
    output_mode: OutputMode
    extract_schema_str: str


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


def _read_extract_schema_str(extract_schema_file: str) -> str:
    if not extract_schema_file:
        return ""

    with open(extract_schema_file, "r") as f:
        schema_str = f.read()
    return schema_str


def _output_csv(result_dict: Dict[str, List[BaseModel]], key_name: str) -> str:
    # generate the CSV content from a Dict of URL and list of extracted items
    output = io.StringIO()
    csv_writer = None
    for src_url, items in result_dict.items():
        for item in items:
            value_dict = item.model_dump()
            item_with_url = {**value_dict, key_name: src_url}

            if csv_writer is None:
                headers = list(value_dict.keys()) + [key_name]
                csv_writer = csv.DictWriter(output, fieldnames=headers)
                csv_writer.writeheader()

            csv_writer.writerow(item_with_url)

    csv_content = output.getvalue()
    output.close()
    return csv_content


class Ask:

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.read_env_variables()

        if logger is not None:
            self.logger = logger
        else:
            self.logger = _get_logger("INFO")

        self.logger.info("Initializing Chonkie ...")
        self.chunker = TokenChunker(chunk_size=1000, chunk_overlap=100)
        self.logger.info("✅ Successfully initialized Chonkie.")

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

    def chunk_results(self, scrape_results: Dict[str, str]) -> Dict[str, List[Chunk]]:
        chunking_results: Dict[str, List[str]] = {}
        for url, text in scrape_results.items():
            chunking_results[url] = self.chunker.chunk(text)
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

    def save_chunks_to_db(self, all_chunks: Dict[str, List[Chunk]]) -> str:
        """
        The key of chunking_results is the URL and the value is the list of chunks.
        """
        client = self._get_api_client()
        embed_batch_size = 50
        query_batch_size = 100
        insert_data = []

        table_name = self._create_table()

        batches: List[Tuple[str, List[str]]] = []
        for url, list_chunks in all_chunks.items():
            for i in range(0, len(list_chunks), embed_batch_size):
                batch = [chunk.text for chunk in list_chunks[i : i + embed_batch_size]]
                batches.append((url, batch))

        self.logger.info(f"Embedding {len(batches)} batches of chunks ...")
        partial_get_embedding = partial(self.batch_get_embedding, client)
        with ThreadPoolExecutor(max_workers=10) as executor:
            all_embeddings = executor.map(partial_get_embedding, batches)
        self.logger.info(f"✅ Finished embedding.")

        # We batch the insert data to speed up the insertion operation.
        # Although the DuckDB doc says executeMany is optimized for batch insert,
        # we found that it is faster to batch the insert data and run a single insert.
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

        # use a dict to remove duplicates from vector search and full-text search
        matched_chunks_dict = {}
        for vec_result in query_result.fetchall():
            doc_id = vec_result[0]
            result_record = {
                "url": vec_result[1],
                "chunk": vec_result[2],
            }
            matched_chunks_dict[doc_id] = result_record

        if settings.hybrid_search:
            self.logger.info("Running full-text search ...")

            self.db_con.execute(
                f"""
                PREPARE fts_query AS (
                    WITH scored_docs AS (
                        SELECT *, fts_main_{table_name}.match_bm25(
                            doc_id, ?, fields := 'chunk'
                        ) AS score FROM {table_name})
                    SELECT doc_id, url, chunk, score
                    FROM scored_docs
                    WHERE score IS NOT NULL
                    ORDER BY score DESC
                    LIMIT 10)
                """
            )
            self.db_con.execute("PRAGMA threads=4")

            # You can run more complex query rewrite methods here
            # usually: stemming, stop words, etc.
            escaped_query = query.replace("'", " ")
            fts_result: duckdb.DuckDBPyRelation = self.db_con.execute(
                f"EXECUTE fts_query('{escaped_query}')"
            )

            index = 0
            for fts_record in fts_result.fetchall():
                index += 1
                self.logger.debug(f"The full text search record #{index}: {fts_record}")
                doc_id = fts_record[0]
                result_record = {
                    "url": fts_record[1],
                    "chunk": fts_record[2],
                }

                # You can configure the score threashold and top-k
                if fts_record[3] > 1:
                    matched_chunks_dict[doc_id] = result_record
                else:
                    break

                if index >= 10:
                    break

        return matched_chunks_dict.values()

    def _get_api_client(self) -> OpenAI:
        return OpenAI(api_key=self.llm_api_key, base_url=self.llm_base_url)

    def _render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        env = Environment(loader=BaseLoader(), autoescape=False)
        template = env.from_string(template_str)
        return template.render(variables)

    def _get_target_class(self, extract_schema_str: str) -> TypeVar_BaseModel:
        local_namespace = {"BaseModel": BaseModel}
        exec(extract_schema_str, local_namespace, local_namespace)
        for key, value in local_namespace.items():
            if key == "__builtins__":
                continue
            if key == "BaseModel":
                continue
            if isinstance(value, type):
                if issubclass(value, BaseModel):
                    return value
        raise Exception("No Pydantic schema found in the extract schema str.")

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

    def run_extract(
        self,
        query: str,
        extract_schema_str: str,
        target_content: str,
        settings: AskSettings,
    ) -> List[TypeVar_BaseModel]:
        target_class = self._get_target_class(extract_schema_str)
        system_prompt = (
            "You are an expert of extract structual information from the document."
        )
        user_promt_template = """
Given the provided content, if it contains information about {{ query }}, please extract the
list of structured data items as defined in the following Pydantic schema:

{{ extract_schema_str }}

Below is the provided content:
{{ content }}
"""
        user_prompt = self._render_template(
            user_promt_template,
            {
                "query": query,
                "content": target_content,
                "extract_schema_str": extract_schema_str,
            },
        )

        self.logger.debug(
            f"Running extraction with model: {settings.inference_model_name}"
        )
        self.logger.debug(f"Final user prompt: {user_prompt}")

        class_name = target_class.__name__
        list_class_name = f"{class_name}_list"
        response_pydantic_model = create_model(
            list_class_name,
            items=(List[target_class], ...),
        )

        api_client = self._get_api_client()
        completion = api_client.beta.chat.completions.parse(
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
            response_format=response_pydantic_model,
        )
        if completion is None:
            raise Exception("No completion from the API")

        message = completion.choices[0].message
        if message.refusal:
            raise Exception(
                f"Refused to extract information from the document: {message.refusal}."
            )

        extract_result = message.parsed
        return extract_result.items

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
        output_mode_str: str,
        extract_schema_str: str,
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
            output_mode=OutputMode(output_mode_str),
            extract_schema_str=extract_schema_str,
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

            if settings.output_mode == OutputMode.answer:
                logger.info("Chunking the text ...")
                yield "", update_logs()
                all_chunks = self.chunk_results(scrape_results)
                chunk_count = 0
                for url, chunks in all_chunks.items():
                    logger.debug(f"URL: {url}")
                    chunk_count += len(chunks)
                    for i, chunk in enumerate(chunks):
                        logger.debug(f"Chunk {i+1}: {chunk.text}")
                logger.info(f"✅ Generated {chunk_count} chunks ...")
                yield "", update_logs()

                logger.info(f"Saving {chunk_count} chunks to DB ...")
                yield "", update_logs()
                table_name = self.save_chunks_to_db(all_chunks)
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
                    [
                        f"[{i+1}] {result['url']}"
                        for i, result in enumerate(matched_chunks)
                    ]
                )
                yield f"{answer}\n\n# References\n\n{references}", update_logs()
            elif settings.output_mode == OutputMode.extract:
                logger.info("Extracting structured data ...")
                yield "", update_logs()

                aggregated_output = {}
                for url, text in scrape_results.items():
                    items = self.run_extract(
                        query=query,
                        extract_schema_str=extract_schema_str,
                        target_content=text,
                        settings=settings,
                    )
                    self.logger.info(
                        f"✅ Finished inference API call. Extracted {len(items)} items from {url}."
                    )
                    yield "", update_logs()

                    self.logger.debug(items)
                    aggregated_output[url] = items

                logger.info("✅ Finished extraction from all urls.")
                logger.info("Generating output ...")
                yield "", update_logs()
                answer = _output_csv(aggregated_output, "SourceURL")
                yield f"{answer}", update_logs()
            else:
                raise Exception(f"Invalid output mode: {settings.output_mode}")

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
            output_mode_str=settings.output_mode,
            extract_schema_str=settings.extract_schema_str,
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

    def toggle_schema_textbox(option):
        if option == "extract":
            return gr.update(visible=True)
        else:
            return gr.update(visible=False)

    with gr.Blocks() as demo:
        gr.Markdown("# Ask.py - Web Search-Extract-Summarize")
        gr.Markdown(
            "Search the web with the query and summarize the results. Source code: https://github.com/pengfeng/ask.py"
        )

        with gr.Row():
            with gr.Column():

                query_input = gr.Textbox(label="Query", value=query)
                output_mode_input = gr.Radio(
                    label="Output Mode [answer: simple answer, extract: get structured data]",
                    choices=["answer", "extract"],
                    value=init_settings.output_mode,
                )
                extract_schema_input = gr.Textbox(
                    label="Extract Pydantic Schema",
                    visible=(init_settings.output_mode == "extract"),
                    value=init_settings.extract_schema_str,
                    lines=5,
                    max_lines=20,
                )
                output_mode_input.change(
                    fn=toggle_schema_textbox,
                    inputs=output_mode_input,
                    outputs=extract_schema_input,
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
                    hybrid_search_input = gr.Checkbox(
                        label="Hybrid Search [Use both vector search and full-text search.]",
                        value=init_settings.hybrid_search,
                    )
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
                output_mode_input,
                extract_schema_input,
            ],
            outputs=[answer_output, logs_output],
        )

    demo.queue().launch(share=share_ui)


@click.command(help="Search web for the query and summarize the results.")
@click.option("--query", "-q", required=False, help="Query to search")
@click.option(
    "--output-mode",
    "-o",
    type=click.Choice(["answer", "extract"], case_sensitive=False),
    default="answer",
    required=False,
    help="Output mode for the answer, default is a simple answer",
)
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
    "--extract-schema-file",
    type=str,
    required=False,
    default="",
    show_default=True,
    help="Pydantic schema for the extract mode",
)
@click.option(
    "--inference-model-name",
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
    "--run-cli",
    "-c",
    is_flag=True,
    help="Run as a command line tool instead of launching the Gradio UI",
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
    output_mode: str,
    date_restrict: int,
    target_site: str,
    output_language: str,
    output_length: int,
    url_list_file: str,
    extract_schema_file: str,
    inference_model_name: str,
    hybrid_search: bool,
    run_cli: bool,
    log_level: str,
):
    load_dotenv(dotenv_path=default_env_file, override=False)
    logger = _get_logger(log_level)

    if output_mode == "extract" and not extract_schema_file:
        raise Exception("Extract mode requires the --extract-schema-file argument.")

    settings = AskSettings(
        date_restrict=date_restrict,
        target_site=target_site,
        output_language=output_language,
        output_length=output_length,
        url_list=_read_url_list(url_list_file),
        inference_model_name=inference_model_name,
        hybrid_search=hybrid_search,
        output_mode=OutputMode(output_mode),
        extract_schema_str=_read_extract_schema_str(extract_schema_file),
    )

    if run_cli:
        if query is None:
            raise Exception("Query is required for the command line mode")
        ask = Ask(logger=logger)

        final_result = ask.run_query(query=query, settings=settings)
        click.echo(final_result)
    else:
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


if __name__ == "__main__":
    search_extract_summarize()
