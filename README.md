# ask.py

A simple Python program to implement the search-extract-summarize-ouput flow, similar to the AI
search engines such as Perplexity.

## The flow

Given a query, the program will

- search Google for the top 10 web pages
- crawl and scape the pages for their text content
- chunk the text content into chunks and save them into a vectordb
- performing a vector search with the query and find the top 10 matched chunks
- use the top 10 chunks as the context to ask an LLM to generate the answer
- output the answer with the references

Of course this flow is a very simplified version of the real AI search engines, but it is a good
starting point to understand the basic concepts.

## How to run the program

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

```text
Answer:
Large Language Models (LLMs) are a type of computational model primarily designed
for natural language processing tasks, including language generation. They are very
large deep learning models that are pre-trained on extensive datasets to understand
and generate human language by learning statistical relationships from text. LLMs
utilize a transformer-based architecture to efficiently process large-scale text
data and can be fine-tuned for specific tasks or guided by prompt engineering [2][3][4].
They can perform various tasks, such as translation, summarization, sentiment analysis,
and generating conversational responses, making them essential in fields like healthcare,
customer service, marketing, and beyond[5][6][8]. The operational management of these
models in production environments is referred to as LLMOps, which ensures their efficient
deployment and maintenance[7][10].

References:

[1] https://www.wiz.io/academy/llm-jacking
[2] https://aws.amazon.com/what-is/large-language-model/
[3] https://en.wikipedia.org/wiki/Large_language_model
[4] https://www.elastic.co/what-is/large-language-models
[5] https://www.elastic.co/what-is/large-language-models
[6] https://www.techtarget.com/whatis/definition/large-language-model-LLM
[7] https://www.databricks.com/glossary/llmops
[8] https://www.techtarget.com/whatis/definition/large-language-model-LLM
[9] https://www.databricks.com/glossary/llmops
[10] https://www.databricks.com/glossary/llmops

```

## Libraries and APIs used

- [Google Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://beta.openai.com/docs/api-reference/completions/create)
- [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [vectordb2](https://github.com/kagisearch/vectordb)
