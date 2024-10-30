# ask.py

[![License](https://img.shields.io/github/license/pengfeng/ask.py)](LICENSE)

A single Python program to implement the search-extract-summarize flow, similar to AI search
engines such as Perplexity.

> [!NOTE]
> Our main goal is to illustrate the basic concepts of AI search engines with the raw constructs.
> Performance or scalability is not in the scope of this program.

> [UPDATE]
>
> - 2024-10-28: add extract function as a new output mode
> - 2024-10-25: add hybrid search demo using DuckDB full-text search
> - 2024-10-22: add GradIO integation
> - 2024-10-21: use DuckDB for the vector search and use API for embedding
> - 2024-10-20: allow to specify a list of input urls
> - 2024-10-18: output-language and output-length parameters for LLM
> - 2024-10-18: date-restrict and target-site parameters for seach

## The search-extract-summarize flow

Given a query, the program will

- search Google for the top 10 web pages
- crawl and scape the pages for their text content
- chunk the text content into chunks and save them into a vectordb
- perform a vector search with the query and find the top 10 matched chunks
- [Optional] search using full-text search and combine the results with the vector search
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

## Quick start

```bash
# recommend to use Python 3.10 or later and use venv or conda to create a virtual environment
pip install -r requirements.txt

# modify .env file to set the API keys or export them as environment variables as below

# right now we use Google search API
export SEARCH_API_KEY="your-google-search-api-key"
export SEARCH_PROJECT_KEY="your-google-cx-key"

# right now we use OpenAI API
export LLM_API_KEY="your-openai-api-key"

# run the program
python ask.py -q "What is an LLM agent?"

# we can specify more parameters to control the behavior such as date_restrict and target_site
python ask.py --help
Usage: ask.py [OPTIONS]

  Search web for the query and summarize the results.

Options:
  -q, --query TEXT                Query to search
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
  -m, --inference-model-name TEXT
                                  Model name to use for inference
  --hybrid-search                 Use hybrid search mode with both vector
                                  search and full-text search
  --web-ui                        Launch the web interface
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
- [GradIO](https://github.com/gradio-app/gradio)

## GradIO Deployment

![image](https://github.com/user-attachments/assets/0483e6a2-75d7-4fbd-813f-bfa13839c836)

> [!NOTE]
> Original GradIO docuemtn [here](https://www.gradio.app/guides/sharing-your-app).

### Quick test and sharing

You can run the program with `--web-ui` option to launch the web interface and check it locally.

```bash
python ask.py --web-ui
* Running on local URL:  http://127.0.0.1:7860

# you can also specify SHARE_GRADIO_UI to run a sharable UI through GradIO
export SHARE_GRADIO_UI=True
python ask.py --web-ui
* Running on local URL:  http://127.0.0.1:7860
* Running on public URL: https://77c277af0330326587.gradio.live
```

### To share a more permanent link using HuggingFace spaces

- First, you need to [create a free Hugging Face account](https://huggingface.co/welcome).
- Then in your [settings/token page](https://huggingface.co/settings/tokens), create a new token with Read permissions.
- In your terminal, run the following commands in you app directory to deploy your program to
  Hugging Face Spaces:

```bash
pip install gradio
gradio deploy
# You will be prompted to enter your HuggingFace token
```

After the deployment, the app should be on https://huggingface.co/spaces/<your_username>/AskPy

Now you need to go to the settings page to add some variables and secrets https://huggingface.co/spaces/<your_username>/AskPy/settings

- variable: RUN_GRADIO_UI=True
- variable: SHARE_GRADIO_UI=True
- secret: SEARCH_API_KEY=<YOUR_SEARCH_API_KEY>
- secret: SEARCH_PROJECT_KEY=<YOUR_SEARCH_PROJECT_KEY>
- sercet: LLM_API_KEY=<YOUR_LLM_API_KEY>

Now you can use the HuggingFace space app to run your queries.

## Use Cases

- [Search like Perplexity](demos/search_and_answer.md)
- [Only use the latest information from a specific site](demos/search_on_site_and_date.md)
- [Extract information from web search results](demos/search_and_extract.md)
