import json
import logging
import os
import urllib.parse

import click
import requests


class Ask:

    def __init__(self):
        self.read_env_variables()
        self.logger = logging.getLogger(__name__)

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

    def search_for_query(self, query: str):
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


@click.command(help="Search web for the query and summarize the results")
@click.option("--query", "-q", required=True, help="Query to search")
def search_extract_summarize(query: str):
    ask = Ask()
    links = ask.search_for_query(query)
    print(f"Found {len(links)} links for query: {query}")
    for i, link in enumerate(links):
        print(f"{i+1}. {link}")


if __name__ == "__main__":
    search_extract_summarize()
