# ask.py

[![License](https://img.shields.io/github/license/pengfeng/ask.py)](LICENSE)

[Update] A full version with db support is open sourced here: [LeetTools](https://github.com/leettools-dev/leettools). Use the web as your knowledge base as you like!

A single Python program to implement the search-extract-summarize flow, similar to AI search
engines such as Perplexity.

- You can run it on command line or with a GradIO UI.
- You can control the output behavior, e.g., extract structured data or change output language,
- You can control the search behavior, e.g., restrict to a specific site or date, or just scrape
  a specified list of URLs.
- You can run it in a cron job or bash script to automate complex search/data extraction tasks.
- You can ask questions against local files.

We have a running UI example [in HuggingFace Spaces](https://huggingface.co/spaces/leettools/AskPy).

![image](https://github.com/user-attachments/assets/0483e6a2-75d7-4fbd-813f-bfa13839c836)

## Demo Use Cases

- [Search like Perplexity](demos/search_and_answer.md)
- [Only use the latest information from a specific site](demos/search_on_site_and_date.md)
- [Extract information from web search results](demos/search_and_extract.md)
- [Ask questions against local files](demos/local_files.md)

> [!NOTE]
>
> - Our main goal is to illustrate the basic concepts of AI search engines with the raw constructs.
>   Performance or scalability is not in the scope of this program.
> - We are planning to open source a real search-enabled AI toolset with real DB setup, real document
>   pipeline, and real query engine soon. Star and watch this repo for updates!

> [UPDATE]
>
> - 2024-12-20: add the full function version link
> - 2024-11-20: add Docling converter and local mode to query against local files
> - 2024-11-10: add Chonkie as the default chunker
> - 2024-10-28: add extract function as a new output mode
> - 2024-10-25: add hybrid search demo using DuckDB full-text search
> - 2024-10-22: add GradIO integation
> - 2024-10-21: use DuckDB for the vector search and use API for embedding
> - 2024-10-20: allow to specify a list of input urls
> - 2024-10-18: output-language and output-length parameters for LLM
> - 2024-10-18: date-restrict and target-site parameters for seach

## The search-extract-summarize flow

Given a query, the program will

- in search mode: search Google for the top 10 web pages
- in local mode: use the local files under the 'data' directory
- crawl and scape the result documents for their text content
- chunk the text content into chunks and save them into a vectordb
- perform a hybrid search (vector and BM25 FTS) with the query and find the top 10 matched chunks
- [Optional] use a reranker to re-rank the top chunks
- use the top chunks as the context to ask an LLM to generate the answer
- output the answer with the references

Of course this flow is a very simplified version of the real AI search engines, but it is a good
starting point to understand the basic concepts.

One benefit is that we can manipulate the search function and output format.

For example, we can:

- search with date-restrict to only retrieve the latest information.
- search within a target-site to only create the answer from the contents from it.
- ask LLM to use a specific language to answer the question.
- ask LLM to answer with a specific length.
- crawl a specific list of urls and answer based on those contents only.

This program can serve as a playground to understand and experiment with different components in
the pipeline.

## Quick start

```bash
# recommend to use Python 3.10 or later and use venv or conda to create a virtual environment
% pip install -r requirements.txt

# modify .env file to set the API keys or export them as environment variables as below

# right now we use Google search API
% export SEARCH_API_KEY="your-google-search-api-key"
% export SEARCH_PROJECT_KEY="your-google-cx-key"

# right now we use OpenAI API
% export LLM_API_KEY="your-openai-api-key"

# By default, the program will start a web UI. See GradIO Deployment section for more info.
# Run the program on command line with -c option
% python ask.py -c -q "What is an LLM agent?"

# You can also query your local files under the 'data' directory using the local mode
% python ask.py -i local -c -q "How does Ask.py work?"

# we can specify more parameters to control the behavior such as date_restrict and target_site
% python ask.py --help
Usage: ask.py [OPTIONS]

  Search web for the query and summarize the results.

Options:
  -q, --query TEXT                Query to search
  -i, --input-mode [search|local]
                                  Input mode for the query, default is search.
                                  When using local, files under 'data' folder
                                  will be used as input.
  -o, --output-mode [answer|extract]
                                  Output mode for the answer, default is a
                                  simple answer
  -d, --date-restrict INTEGER     Restrict search results to a specific date
                                  range, default is no restriction
  -s, --target-site TEXT          Restrict search results to a specific site,
                                  default is no restriction
  --output-language TEXT          Output language for the answer
  --output-length INTEGER         Output length for the answer
  --url-list-file TEXT            Instead of doing web search, scrape the
                                  target URL list and answer the query based
                                  on the content
  --extract-schema-file TEXT      Pydantic schema for the extract mode
  --inference-model-name TEXT     Model name to use for inference
  --vector-search-only            Do not use hybrid search mode, use vector
                                  search only.
  -c, --run-cli                   Run as a command line tool instead of
                                  launching the Gradio UI
  -l, --log-level [DEBUG|INFO|WARNING|ERROR]
                                  Set the logging level  [default: INFO]
  --help                          Show this message and exit.
```

## Libraries and APIs used

- [Google Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://beta.openai.com/docs/api-reference/completions/create)
- [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [DuckDB](https://github.com/duckdb/duckdb)
- [Docling](https://github.com/DS4SD/docling)
- [GradIO](https://github.com/gradio-app/gradio)
- [Chonkie](https://github.com/bhavnicksm/chonkie)

## GradIO Deployment

> [!NOTE]
> Original GradIO app-sharing document [here](https://www.gradio.app/guides/sharing-your-app).

### Quick test and sharing

By default, the program will start a web UI and share through GradIO.

```bash
% python ask.py
* Running on local URL:  http://127.0.0.1:7860
* Running on public URL: https://77c277af0330326587.gradio.live

# you can also specify SHARE_GRADIO_UI to only run locally
% export SHARE_GRADIO_UI=False
% python ask.py
* Running on local URL:  http://127.0.0.1:7860
```

### To share a more permanent link using HuggingFace Spaces

- First, you need to [create a free HuggingFace account](https://huggingface.co/welcome).
- Then in your [settings/token page](https://huggingface.co/settings/tokens), create a new token with Write permissions.
- In your terminal, run the following commands in you app directory to deploy your program to
  HuggingFace Spaces:

```bash
% pip install gradio
% gradio deploy
Creating new Spaces Repo in '/home/you/ask.py'. Collecting metadata, press Enter to accept default value.
Enter Spaces app title [ask.py]: ask.py
Enter Gradio app file [ask.py]:
Enter Spaces hardware (cpu-basic, cpu-upgrade, t4-small, t4-medium, l4x1, l4x4, zero-a10g, a10g-small, a10g-large, a10g-largex2, a10g-largex4, a100-large, v5e-1x1, v5e-2x2, v5e-2x4) [cpu-basic]:
Any Spaces secrets (y/n) [n]: y
Enter secret name (leave blank to end): SEARCH_API_KEY
Enter secret value for SEARCH_API_KEY: YOUR_SEARCH_API_KEY
Enter secret name (leave blank to end): SEARCH_PROJECT_KEY
Enter secret value for SEARCH_API_KEY: YOUR_SEARCH_PROJECT_KEY
Enter secret name (leave blank to end): LLM_API_KEY
Enter secret value for LLM_API_KEY: YOUR_LLM_API_KEY
Enter secret name (leave blank to end):
Create Github Action to automatically update Space on 'git push'? [n]: n
Space available at https://huggingface.co/spaces/your_user_name/ask.py
```

Now you can use the HuggingFace space app to run your queries.
