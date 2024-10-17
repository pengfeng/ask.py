# ask.py

[![License](https://img.shields.io/github/license/yoheinakajima/ditto)](LICENSE)

A single Python program to implement the search-extract-summarize flow, similar to AI search
engines such as Perplexity.

## The seach-extract-summarize flow

Given a query, the program will

- search Google for the top 10 web pages
- crawl and scape the pages for their text content
- chunk the text content into chunks and save them into a vectordb
- performing a vector search with the query and find the top 10 matched chunks
- use the top 10 chunks as the context to ask an LLM to generate the answer
- output the answer with the references

Of course this flow is a very simplified version of the real AI search engines, but it is a good
starting point to understand the basic concepts.

## Quick start

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
# Answer

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

# References

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

## Sample output

```text
% python ask.py -q "Why do we need agentic RAG even if we have ChatGPT?"

Found 10 links for query: Why do we need agentic RAG even if we have ChatGPT?
Scraping the URLs ...
Chunking the text ...
Saving to vector DB ...
Querying the vector DB ...
Running inference with context ...

Answer:
Agentic RAG (Retrieval-Augmented Generation) is needed alongside ChatGPT for several reasons:

1. **Precision and Contextual Relevance**: While ChatGPT offers generative responses, it may not reliably provide precise answers, especially when specific, accurate information is critical[5]. Agentic RAG enhances this by integrating retrieval mechanisms that improve response context and accuracy, allowing users to access the most relevant and recent data without the need for costly model fine-tuning[2].

2. **Customizability**: RAG allows businesses to create tailored chatbots that can securely reference company-specific data[2]. In contrast, ChatGPT’s broader capabilities may not be directly suited for specialized, domain-specific questions without comprehensive customization[3].

3. **Complex Query Handling**: RAG can be optimized for complex queries and can be adjusted to work better with specific types of inputs, such as comparing and contrasting information, a task where ChatGPT may struggle under certain circumstances[9]. This level of customization can lead to better performance in niche applications where precise retrieval of information is crucial.

4. **Asynchronous Processing Capabilities**: Future agentic systems aim to integrate asynchronous handling of actions, allowing for parallel processing and reducing wait times for retrieval and computation, which is a limitation in the current form of ChatGPT[7]. This advancement would enhance overall efficiency and responsiveness in conversations.

5. **Incorporating Retrieved Information Effectively**: Using RAG can significantly improve how retrieved information is utilized within a conversation. By effectively managing the context and relevance of retrieved documents, RAG helps in framing prompts that can guide ChatGPT towards delivering more accurate responses[10].

In summary, while ChatGPT excels in generating conversational responses, agentic RAG brings precision, customization, and efficiency that can significantly enhance the overall conversational AI experience.

References:

[1] https://community.openai.com/t/how-to-use-rag-properly-and-what-types-of-query-it-is-good-at/658204
[2] https://www.linkedin.com/posts/brianjuliusdc_dax-powerbi-chatgpt-activity-7235953280177041408-wQqq
[3] https://community.openai.com/t/how-to-use-rag-properly-and-what-types-of-query-it-is-good-at/658204
[4] https://community.openai.com/t/prompt-engineering-for-rag/621495
[5] https://www.ben-evans.com/benedictevans/2024/6/8/building-ai-products
[6] https://community.openai.com/t/prompt-engineering-for-rag/621495
[7] https://www.linkedin.com/posts/kurtcagle_agentic-rag-personalizing-and-optimizing-activity-7198097129993613312-z7Sm
[8] https://community.openai.com/t/how-to-use-rag-properly-and-what-types-of-query-it-is-good-at/658204
[9] https://community.openai.com/t/how-to-use-rag-properly-and-what-types-of-query-it-is-good-at/658204
[10] https://community.openai.com/t/prompt-engineering-for-rag/621495
```
