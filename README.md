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

Answer:
Large Language Models (LLMs) are a type of computational model primarily designed for natural language processing tasks, including language generation. They are very large deep learning models that are pre-trained on extensive datasets to understand and generate human language by learning statistical relationships from text. LLMs utilize a transformer-based architecture to efficiently process large-scale text data and can be fine-tuned for specific tasks or guided by prompt engineering[2][3][4]. They can perform various tasks, such as translation, summarization, sentiment analysis, and generating conversational responses, making them essential in fields like healthcare, customer service, marketing, and beyond[5][6][8]. The operational management of these models in production environments is referred to as LLMOps, which ensures their efficient deployment and maintenance[7][10].

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

Libraries used:

- [Google Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://beta.openai.com/docs/api-reference/completions/create)
- [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [vectordb2](https://github.com/kagisearch/vectordb)
