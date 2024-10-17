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

One benefit of this simple program is that you can manipulate the search function and output format.
For example:

- You can specify date-restrict to only retrieve the latest information
- You can specify target-site to only create the answer from the contents from a specific site

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
python ask.py -q "What is an LLM agent?"

# we can specify more seach parameters such as date_restrict and target_site
python ask.py --help
Usage: ask.py [OPTIONS]

  Search web for the query and summarize the results

Options:
  -q, --query TEXT                Query to search  [required]
  -d, --date-restrict INTEGER     Restrict search results to a specific date
                                  range, default is no restriction
  -s, --target-site TEXT          Restrict search results to a specific site,
                                  default is no restriction
  -m, --model-name TEXT           Model name to use for inference
  -l, --log-level [DEBUG|INFO|WARNING|ERROR]
                                  Set the logging level  [default: INFO]
  --help                          Show this message and exit.
```

## Libraries and APIs used

- [Google Search API](https://developers.google.com/custom-search/v1/overview)
- [OpenAI API](https://beta.openai.com/docs/api-reference/completions/create)
- [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [vectordb2](https://github.com/kagisearch/vectordb)

## Sample output

### General Search

```
% python ask.py -q "Why do we need agentic RAG even if we have ChatGPT?"

✅ Found 10 links for query: Why do we need agentic RAG even if we have ChatGPT?
✅ Scraping the URLs ...
✅ Scraped 10 URLs ...
✅ Chunking the text ...
✅ Saving to vector DB ...
✅ Querying the vector DB ...
✅ Running inference with context ...

# Answer

Agentic RAG (Retrieval-Augmented Generation) is needed alongside ChatGPT for several reasons:

1. **Precision and Contextual Relevance**: While ChatGPT offers generative responses, it may not
reliably provide precise answers, especially when specific, accurate information is critical[5].
Agentic RAG enhances this by integrating retrieval mechanisms that improve response context and
accuracy, allowing users to access the most relevant and recent data without the need for costly
model fine-tuning[2].

2. **Customizability**: RAG allows businesses to create tailored chatbots that can securely
reference company-specific data[2]. In contrast, ChatGPT’s broader capabilities may not be
directly suited for specialized, domain-specific questions without comprehensive customization[3].

3. **Complex Query Handling**: RAG can be optimized for complex queries and can be adjusted to
work better with specific types of inputs, such as comparing and contrasting information, a task
where ChatGPT may struggle under certain circumstances[9]. This level of customization can lead to
better performance in niche applications where precise retrieval of information is crucial.

4. **Asynchronous Processing Capabilities**: Future agentic systems aim to integrate asynchronous
handling of actions, allowing for parallel processing and reducing wait times for retrieval and
computation, which is a limitation in the current form of ChatGPT[7]. This advancement would enhance
overall efficiency and responsiveness in conversations.

5. **Incorporating Retrieved Information Effectively**: Using RAG can significantly improve how
retrieved information is utilized within a conversation. By effectively managing the context and
relevance of retrieved documents, RAG helps in framing prompts that can guide ChatGPT towards
delivering more accurate responses[10].

In summary, while ChatGPT excels in generating conversational responses, agentic RAG brings
precision, customization, and efficiency that can significantly enhance the overall conversational
AI experience.

# References

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

### Only use the latest information from a specific site

```
% python ask.py -q "OpenAI Swarm Framework" -d 1 -s openai.com
✅ Found 10 links for query: OpenAI Swarm Framework
✅ Scraping the URLs ...
✅ Scraped 10 URLs ...
✅ Chunking the text ...
✅ Saving to vector DB ...
✅ Querying the vector DB to get context ...
✅ Running inference with context ...

# Answer

OpenAI Swarm Framework is an experimental platform designed for building, orchestrating, and
deploying multi-agent systems, enabling multiple AI agents to collaborate on complex tasks. It contrasts
with traditional single-agent models by facilitating agent interaction and coordination, thus enhancing
efficiency[5][9]. The framework provides developers with a way to orchestrate these agent systems in
a lightweight manner, leveraging Node.js for scalable applications[1][4].

One implementation of this framework is Swarm.js, which serves as a Node.js SDK, allowing users to
create and manage agents that perform tasks and hand off conversations. Swarm.js is positioned as
an educational tool, making it accessible for both beginners and experts, although it may still contain
bugs and is currently lightweight[1][3][7]. This new approach emphasizes multi-agent collaboration and is
well-suited for back-end development, requiring some programming expertise for effective implementation[9].

Overall, OpenAI Swarm facilitates a shift in how AI systems can collaborate, differing from existing
OpenAI tools by focusing on backend orchestration rather than user-interactive front-end applications[9].

# References

[1] https://community.openai.com/t/introducing-swarm-js-node-js-implementation-of-openai-swarm/977510
[2] https://community.openai.com/t/introducing-swarm-js-a-node-js-implementation-of-openai-swarm/977510
[3] https://community.openai.com/t/introducing-swarm-js-node-js-implementation-of-openai-swarm/977510
[4] https://community.openai.com/t/introducing-swarm-js-a-node-js-implementation-of-openai-swarm/977510
[5] https://community.openai.com/t/swarm-some-initial-insights/976602
[6] https://community.openai.com/t/swarm-some-initial-insights/976602
[7] https://community.openai.com/t/introducing-swarm-js-node-js-implementation-of-openai-swarm/977510
[8] https://community.openai.com/t/introducing-swarm-js-a-node-js-implementation-of-openai-swarm/977510
[9] https://community.openai.com/t/swarm-some-initial-insights/976602
[10] https://community.openai.com/t/swarm-some-initial-insights/976602
```
