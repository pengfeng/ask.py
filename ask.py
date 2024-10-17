import json
import logging
import os
import urllib.parse
from typing import Dict, List

import click
import requests
from bs4 import BeautifulSoup


class Ask:

    def __init__(self):
        self.read_env_variables()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())

    def read_env_variables(self):
        err_msg = ""

        self.search_api_key = os.environ.get("SEARCH_API_KEY")
        if self.search_api_key is None:
            err_msg += "\nSEARCH_API_KEY env variable not set.\n"
        self.search_project_id = os.environ.get("SEARCH_PROJECT_KEY")
        if self.search_project_id is None:
            err_msg += "SEARCH_PROJECT_KEY env variable not set.\n"

        if err_msg != "":
            raise Exception(err_msg)

    def search_for_query(self, query: str) -> List[str]:
        escaped_query = urllib.parse.quote(query)
        url_base = (
            f"https://www.googleapis.com/customsearch/v1?key={self.search_api_key}"
            f"&cx={self.search_project_id}&q={escaped_query}"
        )
        url_paras = f"&safe=active"
        url = f"{url_base}{url_paras}"

        self.logger.info(f"Searching for query: {query}")

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
            self.logger.info(f"No results found for query: {query}")
            return []

        results = search_results_dict.get("items", [])
        if results is None or len(results) == 0:
            self.logger.info(f"No result items in the response for query: {query}")
            return []

        found_links = []
        for result in results:
            link = result.get("link", None)
            if link is None or link == "":
                self.logger.warning(f"Search result link missing: {result}")
                continue
            found_links.append(link)
        return found_links

    def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        session = requests.Session()
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        )
        session.headers.update({"User-Agent": user_agent})

        # the key is the url and the value is the body text
        scrape_results: Dict[str, str] = {}

        for url in urls:
            try:
                response = session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")

                body_tag = soup.body
                if body_tag:
                    body_text = body_tag.get_text()
                    body_text = " ".join(body_text.split()).strip()
                    scrape_results[url] = body_text
                    self.logger.info(f"Scraped {url}: {body_text}...")
                else:
                    self.logger.warning(
                        f"No body tag found in the response for url: {url}"
                    )
            except Exception as e:
                self.logger.error(f"scraping error {url}: {e}")
                continue
        return scrape_results

    def chunker(
        self, scrape_results: Dict[str, str], size: int, overlap: int
    ) -> Dict[str, List[str]]:
        """
        Chunk the text into smaller parts with overlap.
        """
        chunking_results: Dict[str, List[str]] = {}
        for url, text in scrape_results.items():
            chunks = []
            for pos in range(0, len(text), size - overlap):
                chunks.append(text[pos : pos + size])
            chunking_results[url] = chunks
        return chunking_results


@click.command(help="Search web for the query and summarize the results")
@click.option("--query", "-q", required=True, help="Query to search")
def search_extract_summarize(query: str):
    ask = Ask()
    links = ask.search_for_query(query)
    print(f"Found {len(links)} links for query: {query}")
    for i, link in enumerate(links):
        print(f"{i+1}. {link}")

    print("Scraping the URLs...")
    scrape_results = ask.scrape_urls(links)

    print("Chunking the text...")
    chunking_results = ask.chunker(scrape_results, 1000, 100)
    for url, chunks in chunking_results.items():
        print(f"URL: {url}")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk}")


if __name__ == "__main__":
    search_extract_summarize()
