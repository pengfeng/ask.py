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
