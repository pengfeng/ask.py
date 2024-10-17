# ask.py

A simple Python program to implement the search-extract-summarize-ouput flow.

```Python

# the tensorflow library takes a while to install if running for the first time
pip install -r requirements.txt

# right now we use Google search API
export SEARCH_API_KEY="your-google-search-api-key"
export SEARCH_PROJECT_KEY="your-google-cx-key"

# right now we use OpenAI API
export LLM_API_KEY="your-openai-api-key"

# run the program, the first run will take a while to download the embedding model
python ask.py -q "What is LLM?"
```

Libraries used:

- [Google Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://beta.openai.com/docs/api-reference/completions/create)
- [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [vectordb2](https://github.com/kagisearch/vectordb)
