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

## Screenshot for the GradIO integration

![image](https://github.com/user-attachments/assets/0483e6a2-75d7-4fbd-813f-bfa13839c836)

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

This following query will only use the information from openai.com that are updated in the previous
day. The behavior is similar to the "site:openai.com" and "date-restrict" search parameters in Google
search.

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

### Extract information from web search results

```
% python ask.py -q "LLM Gen-AI Startups" -o extract --extract-schema-file instructions/extract_example.txt
2024-10-29 08:15:24,320 - INFO - Searching the web ...
2024-10-29 08:15:24,684 - INFO - ✅ Found 10 links for query: LLM Gen-AI Startups
2024-10-29 08:15:24,684 - INFO - Scraping the URLs ...
2024-10-29 08:15:24,685 - INFO - Scraping https://www.ycombinator.com/companies/industry/generative-ai ...
2024-10-29 08:15:24,686 - INFO - Scraping https://app.dealroom.co/lists/33530 ...
2024-10-29 08:15:24,687 - INFO - Scraping https://explodingtopics.com/blog/generative-ai-startups ...
2024-10-29 08:15:24,688 - INFO - Scraping https://www.reddit.com/r/learnprogramming/comments/1e0gzbo/are_most_ai_startups_these_days_just_openai/ ...
2024-10-29 08:15:24,689 - INFO - Scraping https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc ...
2024-10-29 08:15:24,690 - INFO - Scraping https://www.reddit.com/r/ycombinator/comments/16xhwz7/is_it_really_impossible_for_genai_startups_to/ ...
2024-10-29 08:15:24,691 - INFO - Scraping https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9 ...
2024-10-29 08:15:24,692 - INFO - Scraping https://a16z.com/ai/ ...
2024-10-29 08:15:24,693 - INFO - Scraping https://www.eweek.com/artificial-intelligence/generative-ai-startups/ ...
2024-10-29 08:15:24,695 - INFO - Scraping https://cohere.com/ ...
2024-10-29 08:15:24,875 - WARNING - Body text too short for url: https://app.dealroom.co/lists/33530, length: 41
2024-10-29 08:15:24,975 - INFO - ✅ Successfully scraped https://explodingtopics.com/blog/generative-ai-startups with length: 17631
2024-10-29 08:15:25,429 - INFO - ✅ Successfully scraped https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9 with length: 3649
2024-10-29 08:15:26,119 - INFO - ✅ Successfully scraped https://a16z.com/ai/ with length: 14828
2024-10-29 08:15:26,144 - INFO - ✅ Successfully scraped https://cohere.com/ with length: 2696
2024-10-29 08:15:26,220 - INFO - ✅ Successfully scraped https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc with length: 13858
2024-10-29 08:15:26,520 - INFO - ✅ Successfully scraped https://www.reddit.com/r/learnprogramming/comments/1e0gzbo/are_most_ai_startups_these_days_just_openai/ with length: 2029
2024-10-29 08:15:26,541 - INFO - ✅ Successfully scraped https://www.reddit.com/r/ycombinator/comments/16xhwz7/is_it_really_impossible_for_genai_startups_to/ with length: 3445
2024-10-29 08:15:26,947 - WARNING - Body text too short for url: https://www.ycombinator.com/companies/industry/generative-ai, length: 0
2024-10-29 08:15:26,989 - INFO - ✅ Successfully scraped https://www.eweek.com/artificial-intelligence/generative-ai-startups/ with length: 69104
2024-10-29 08:15:26,990 - INFO - ✅ Scraped 8 URLs.
2024-10-29 08:15:26,990 - INFO - Extracting structured data ...
2024-10-29 08:15:34,019 - INFO - ✅ Finished inference API call. Extracted 33 items from https://explodingtopics.com/blog/generative-ai-startups.
2024-10-29 08:15:34,490 - INFO - ✅ Finished inference API call. Extracted 0 items from https://www.reddit.com/r/learnprogramming/comments/1e0gzbo/are_most_ai_startups_these_days_just_openai/.
2024-10-29 08:15:38,135 - INFO - ✅ Finished inference API call. Extracted 20 items from https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc.
2024-10-29 08:15:39,165 - INFO - ✅ Finished inference API call. Extracted 2 items from https://www.reddit.com/r/ycombinator/comments/16xhwz7/is_it_really_impossible_for_genai_startups_to/.
2024-10-29 08:15:40,463 - INFO - ✅ Finished inference API call. Extracted 7 items from https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9.
2024-10-29 08:15:44,150 - INFO - ✅ Finished inference API call. Extracted 23 items from https://a16z.com/ai/.
2024-10-29 08:16:02,785 - INFO - ✅ Finished inference API call. Extracted 73 items from https://www.eweek.com/artificial-intelligence/generative-ai-startups/.
2024-10-29 08:16:04,423 - INFO - ✅ Finished inference API call. Extracted 3 items from https://cohere.com/.
2024-10-29 08:16:04,423 - INFO - ✅ Finished extraction from all urls.
2024-10-29 08:16:04,423 - INFO - Generating output ...
name,description,SourceURL
Cohere,Cohere is an AI startup that builds multilingual LLMs for enterprise businesses to streamline tasks.,https://explodingtopics.com/blog/generative-ai-startups
Hugging Face,"Hugging Face is a collaborative AI community that creates tools for developers, offering over 61,000 pre-trained models and 7,000 datasets.",https://explodingtopics.com/blog/generative-ai-startups
Tabnine,Tabnine is an AI assistant for software developers that uses generative AI to predict or suggest the next lines of code.,https://explodingtopics.com/blog/generative-ai-startups
Soundraw,Soundraw is a royalty-free AI music generator allowing creators to make original songs.,https://explodingtopics.com/blog/generative-ai-startups
Tome.app,Tome is an AI-powered storytelling platform that helps users create presentations using generative AI.,https://explodingtopics.com/blog/generative-ai-startups
AssemblyAI,AssemblyAI is an AI-as-a-service startup providing APIs in 80 different languages for automated speech transcription.,https://explodingtopics.com/blog/generative-ai-startups
Promptbase,Promptbase is a marketplace for buying and selling prompts to generate content with AI tools.,https://explodingtopics.com/blog/generative-ai-startups
Photoroom,PhotoRoom is an AI-powered photo editing tool that combines generative AI with traditional editing tools.,https://explodingtopics.com/blog/generative-ai-startups
Taskade,Taskade is a generative AI productivity tool for task management and team collaboration.,https://explodingtopics.com/blog/generative-ai-startups
Synthesia,Synthesia AI is a generative AI video maker that creates videos from text in multiple languages.,https://explodingtopics.com/blog/generative-ai-startups
Humata AI,Humata AI is a tool integrating with your desktop to answer questions about documents using generative AI.,https://explodingtopics.com/blog/generative-ai-startups
Chatbase,"Chatbase is a chatbot integrated into websites, providing instant answers to users.",https://explodingtopics.com/blog/generative-ai-startups
Stability AI,"Stability AI is known for creating Stable Diffusion, a deep learning text-to-image AI model.",https://explodingtopics.com/blog/generative-ai-startups
Anyword,Anyword is a generative AI content generation platform that uses natural language processing for copywriting.,https://explodingtopics.com/blog/generative-ai-startups
Rephrase AI,Rephrase AI is a text-to-video generation platform that allows customers to create personalized videos.,https://explodingtopics.com/blog/generative-ai-startups
Inworld AI,Inworld AI specializes in AI-powered character generation for video games.,https://explodingtopics.com/blog/generative-ai-startups
Runway,Runway is a generative AI video editing platform that produces videos based on text prompts.,https://explodingtopics.com/blog/generative-ai-startups
Sudowrite,Sudowrite is a generative AI writing assistant designed for novel writing and storytelling.,https://explodingtopics.com/blog/generative-ai-startups
Steve.ai,Steve.ai is an online video creation platform that turns text prompts into animated videos.,https://explodingtopics.com/blog/generative-ai-startups
PlayHT,PlayHT is a text-to-speech software that uses generative AI to create audio from text.,https://explodingtopics.com/blog/generative-ai-startups
Elicit,Elicit is a generative AI research tool for finding and analyzing academic papers.,https://explodingtopics.com/blog/generative-ai-startups
TalkPal,TalkPal is an AI-powered language learning platform that personalizes sessions based on the user's level.,https://explodingtopics.com/blog/generative-ai-startups
Dubverse,Dubverse is an AI video dubbing platform capable of translating videos into multiple languages.,https://explodingtopics.com/blog/generative-ai-startups
Codeium,Codeium is an AI-powered toolkit for developers that auto-generates and explains code.,https://explodingtopics.com/blog/generative-ai-startups
Fliki,Fliki is an AI video and audio generation platform that incorporates text to speech capabilities.,https://explodingtopics.com/blog/generative-ai-startups
LOVO AI,LOVO is an AI voice generator startup focused on text-to-speech and voice cloning.,https://explodingtopics.com/blog/generative-ai-startups
Decktopus,"Decktopus creates presentations from prompts, streamlining slide generation.",https://explodingtopics.com/blog/generative-ai-startups
Character.ai,Character AI is a generative AI platform that generates customizable animated chatbots.,https://explodingtopics.com/blog/generative-ai-startups
Descript,Descript is a generative AI video and audio editing application catering to podcasters and videographers.,https://explodingtopics.com/blog/generative-ai-startups
Papercup,"Papercup uses AI to translate speech and dubbing, creating realistic voiceovers.",https://explodingtopics.com/blog/generative-ai-startups
Vizcom,Vizcom is a generative AI tool that aids designers in creating 3D concept drawings.,https://explodingtopics.com/blog/generative-ai-startups
Vidnoz,Vidnoz is a free AI video platform aimed at reducing costs and increasing productivity.,https://explodingtopics.com/blog/generative-ai-startups
Scalenut,Scalenut is an AI-powered SEO and content marketing platform that automates content creation.,https://explodingtopics.com/blog/generative-ai-startups
Huma.AI,"A generative AI for life sciences SaaS platform, recognized by Gartner in multiple reports and collaborating with OpenAI for a validated GenAI solution for medical affairs.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Viz.ai,"A medical imaging startup specializing in stroke care and expanded into cardiology and oncology, using LLMs for early disease detection.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Arionkoder,"A product development studio and AI lab specializing in AI, computer vision, and ML solutions for healthcare.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
HeHealth,Delivers AI and LLM technologies for efficient recommendations for male healthcare.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
HOPPR,A multimodal imaging platform improving communication and medical processes through deep image analysis.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Medical IP,A medical metaverse solution utilizing generative AI for streamlined medical imaging segmentation.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
NexusMD,An LLM-powered medical imaging platform automating medical imaging data capture across service sites.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Abridge,"A leading generative AI for clinical documentation, converting patient-clinician conversations into structured notes.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Autonomize AI,A healthcare-optimized AI platform that cuts clinical administrative time and accelerates care gap closures.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
DeepScribe,"A med-tech firm leveraging LLMs to automate clinical documentation, reducing clinician burnout.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
HiLabs,Utilizes AI and LLMs to refine data and identify care gaps for large health plans.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Nabla,"Offers Copilot, an ambient AI for physicians that streamlines clinical note generation.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
AgentifAI,A voice-first AI assistant for healthcare enhancing patient experience.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Artisight,An end-to-end sensor fusion platform deployed in hospitals to enhance operational efficiency.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
dacadoo,"A digital health platform connecting to various devices, with plans to incorporate an LLM-based streaming model.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Hippocratic AI,Developing a safety-focused LLM for patient-facing applications.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Idoven,An AI-powered cardiology platform with deep-learning models for patient diagnosis.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Inference Analytics,A generative AI healthcare platform trained on a vast dataset for various impactful healthcare use cases.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Pingoo,"An AI health chatbot providing personalized health education, serving various health systems.",https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Talkie.ai,Automates patient phone interactions using AI voice and LLM technology for healthcare organizations.,https://www.linkedin.com/pulse/20-gen-ai-healthcare-startups-shaping-future-recap-from-renee-yao-q7lkc
Jasper,Jasper (YC GenAI company) who became one of the fastest growing startups of all time is losing customers fast. It is often cited as an example of how GenAI companies struggle to develop a moat.,https://www.reddit.com/r/ycombinator/comments/16xhwz7/is_it_really_impossible_for_genai_startups_to/
Unnamed GenAI Startup,"We are a GenAI startup that automates tasks in a specific niche area and utilizes a network of LLMs. Our MVP is looking great, and we have a substantial interest from investors.",https://www.reddit.com/r/ycombinator/comments/16xhwz7/is_it_really_impossible_for_genai_startups_to/
beautiful.ai,A startup providing tools for creating presentations with an innovative approach.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
Tome,A startup focused on revolutionizing presentation tools.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
Rows,A startup rethinking spreadsheets with an LLM-first perspective.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
mem,A note-taking startup utilizing LLM technology.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
Clio,"A practice management solution for law firms, sitting on a wealth of data to build AI solutions.",https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
Bench,An accounting startup that has implemented auto-pilot strategies.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
Pilot,A recent entrant in the accounting space following a similar auto-pilot approach.,https://medium.com/point-nine-news/where-are-the-opportunities-for-new-startups-in-generative-ai-f48068b5f8f9
a16z,"A venture capital firm that invests in technology companies, with a focus on artificial intelligence and related sectors.",https://a16z.com/ai/
AI Stack Products,"A collection of open-source AI stacks and tools for developers, including projects for building AI companions and chatbots.",https://a16z.com/ai/
Llama2 Chatbot,A 13 billion parameter language model fine-tuned for chat completions systems.,https://a16z.com/ai/
AI Grants,"Grant funding for AI developers focused on LLM training, hosting, and evaluation.",https://a16z.com/ai/
AI Canon,"A curated collection of impactful papers, posts, courses, and guides on modern artificial intelligence.",https://a16z.com/ai/
Brain Trust,A community-driven platform aimed at training AI models with human data.,https://a16z.com/ai/
Character.AI,A platform for creating and interacting with AI characters.,https://a16z.com/ai/
Civiti,A startup focused on deploying community-driven AI models.,https://a16z.com/ai/
Creta,A developer's assistant using AI for coding support.,https://a16z.com/ai/
Databricks,A company that provides a Unified Analytics Platform powered by Apache Spark.,https://a16z.com/ai/
ElevenLabs,An AI company that specializes in voice generation and text-to-speech technologies.,https://a16z.com/ai/
Freeno,A healthcare-focused AI startup working on early detection systems.,https://a16z.com/ai/
OpenAI,An AI research lab dedicated to ensuring that artificial general intelligence benefits all of humanity.,https://a16z.com/ai/
Zuma,An AI startup aimed at enhancing user experience through intelligent design.,https://a16z.com/ai/
Nautilus Biotechnology,A company transforming the experience and outcome of biotech with AI applications.,https://a16z.com/ai/
Saronic,An AI model focused on enhancing predictive analytics in business settings.,https://a16z.com/ai/
Mistral AI,A company developing scaled AI technologies for multiple applications.,https://a16z.com/ai/
Turquoise Health,An AI-driven health technology startup offering transparent healthcare pricing.,https://a16z.com/ai/
Rasa,An open-source framework for building AI assistants.,https://a16z.com/ai/
Viggle,A startup revolutionizing how audiences engage with multimedia through AI.,https://a16z.com/ai/
Waymark,A company dedicated to automating video production through generative AI techniques.,https://a16z.com/ai/
Yolo AI,An emerging company specializing in real-time object detection technology.,https://a16z.com/ai/
Luma AI,An innovative AI platform designed to enhance the visual experience in various sectors.,https://a16z.com/ai/
OpenAI,"OpenAI is the highest profile company in the generative AI space. Along with its prebuilt AI solutions, OpenAI also offers API and application development support for developers who want to use its models as baselines. Its close partnership with Microsoft and growing commitment to ethical AI continue to boost its reputation and reach.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Anthropic,"Anthropic’s Claude platform is similar to OpenAI’s ChatGPT, with its large language model and content generation focus. Claude has evolved into an enterprise-level AI assistant with high-level conversational capabilities.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Cohere,Cohere offers natural language processing (NLP) solutions that are specifically designed to support business operations. Its conversational AI agent allows enterprise users to quickly search for and retrieve company information.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Glean,"Glean is a generative AI enterprise search company that connects to a variety of enterprise apps and platforms, enabling easy access to business information sources with a focus on AI privacy and governance.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Jasper,"Jasper’s core product is designed for marketing content generation, effective for establishing a consistent brand voice and managing digital marketing campaigns. Jasper also acquired the AI image platform Clickdrop.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Hugging Face,"Hugging Face is a community forum focused on AI and ML model development, offering access to BLOOM, an open-source LLM that can generate content in multiple languages.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Inflection AI,"Inflection AI, founded by former leaders from LinkedIn and DeepMind, focuses on creating conversational AI tools, recently releasing Pi, a personal AI tool.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Stability AI,"Stability AI specializes in generative AI for image and video content generation, with its app Stable Diffusion being a popular solution in the industry.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
MOSTLY AI,"MOSTLY AI specializes in synthetic data generation, balancing data democratization with anonymity and security requirements particularly useful in banking and telecommunications.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Lightricks,"Lightricks is known for its social media-friendly image editing app, Facetune, and uses AI for content generation and avatar creation.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
AI21 Labs,"AI21 Labs creates enterprise tools focusing on contextual natural language processing, allowing third-party developers to build on their language models.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Tabnine,"Tabnine offers generative AI code assistance for software development, helping with code completion and other programming tasks.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Mistral AI,"Mistral AI provides developer-facing open AI models and deployment resources, focusing on scalable AI solutions.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Codeium,"Codeium is a generative AI company that provides resources for generating logical code, with features for autocomplete and contextual knowledge.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Clarifai,"Clarifai's multipurpose platform allows users to build, deploy, and manage AI data projects across various sectors.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Gong,"Gong provides revenue intelligence solutions that use generative AI to enhance sales coaching, customer service engagement, and revenue forecasting.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Twain,"Twain is an AI writing assistant that helps sales professionals generate captivating content, particularly for outreach emails.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Bertha.ai,"Bertha.ai specializes in content generation solutions for WordPress and similar platforms, assisting with written content and imagery.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Tome,Tome is a creative generative AI platform known for its versatile interface to create presentations and reports.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
CopyAI,CopyAI's platform supports marketing and sales professionals in generating effective go-to-market strategies.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Synthesia,"Synthesia focuses on AI-driven video creation, allowing users to generate professional-quality videos based on simple text inputs.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Midjourney,"Midjourney offers a generative AI solution for image and artwork creation, notable for its advanced editing features.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
MURF.AI,"MURF.AI provides text-to-speech solutions with bidirectional voice capabilities, designed for creative content production.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
PlayHT,PlayHT specializes in AI voice generation and personalized podcast content creation.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
ElevenLabs,ElevenLabs is renowned for its high-quality voice generation technology and enterprise scalability.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Colossyan,Colossyan offers tools for creating corporate training videos without the need for actors or original scripting.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
AssemblyAI,AssemblyAI provides speech-to-text modeling and transcription solutions with strong analysis capacities.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Plask,Plask automates animation processes and simplifies creation of hyper-realistic 3D motion videos.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
LOVO,LOVO delivers video and voice AI generation solutions through its comprehensive platform called Genny.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
DeepBrain AI,"DeepBrain AI produces AI-generated videos including interactive virtual assistants, enhancing accessibility in public service.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Elai.io,"Elai.io provides collaborative tools for AI video generation, tailored for business audiences.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Sudowrite,"Sudowrite supports writers by expanding on story outlines, generating ideas, and creating AI art.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Tavus,Tavus enables automated video generation personalized for each viewer's characteristics.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Hippocratic AI,Hippocratic AI offers a generative AI platform for healthcare focused on patient care and HIPAA compliance.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Paige AI,Paige AI integrates generative AI for optimizing cancer diagnostics and pathology.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Iambic Therapeutics,Iambic Therapeutics optimizes drug discovery using machine learning in the oncology sector.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Insilico Medicine,Insilico Medicine uses AI for efficient drug development across various medical fields.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Etcembly,Etcembly enhances T-cell receptor immunotherapies through machine learning advancements.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Biomatter,Biomatter employs AI for intelligent architecture in protein design across multiple sectors.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Activ Surgical,Activ Surgical utilizes AI for enhanced surgical guidance and visualization.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Kaliber Labs,Kaliber Labs designs AI-powered surgical software for improved communication and patient experiences.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Osmo,Osmo utilizes machine learning in olfactory science to predict smells based on molecular structure.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Aqemia,Aqemia focuses on AI-assisted drug discovery incorporating both quantum and statistical mechanics.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Synthetaic,Synthetaic's platform generates AI models for analyzing unstructured and unlabeled datasets.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Synthesis AI,Synthesis AI develops synthetic data-driven imagery and human simulations for ethical AI applications.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Syntho,Syntho generates synthetic data twins for analytics and product demos while ensuring ease of use.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
GenRocket,GenRocket emphasizes automation in synthetic data generation and management for various industries.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Gridspace,Gridspace creates hybrid voice AI and human agent solutions for improved contact center management.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Revery AI,Revery AI utilizes generative AI to create virtual dressing rooms and smart shopping assistants.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Veesual,Veesual offers deep learning-based virtual try-on solutions for e-commerce.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Frame AI,Frame AI analyzes customer interactions to provide insights for improving customer service.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Zowie,Zowie specializes in AI customer service technology tailored for e-commerce environments.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Forethought,Forethought provides generative AI solutions for optimizing customer service workflows.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Lily AI,Lily AI employs AI to enhance product management and customer service experiences for retailers.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Runway,Runway enables filmmakers to use AI for cinema-quality video production.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Latitude.io,"Latitude.io offers AI-driven gaming experiences, allowing users to create dynamic narratives.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Character.AI,Character.AI allows users to develop and interact with user-created virtual characters.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Charisma Entertainment,Charisma Entertainment creates engaging narratives and character-driven storylines for various media.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Replika,Replika generates AI companions for personalized conversations and social interactions.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Aimi.fm,Aimi.fm provides users with a generative AI music player for composing customized music loops.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Inworld AI,Inworld AI utilizes generative AI to enhance the realism of non-player characters in gaming and media.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
SOUNDRAW,SOUNDRAW enables tailored music composition for various media including videos and games.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Notion,Notion offers AI-assisted task management tools for improved workflow efficiency.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Harvey,Harvey targets the legal sector with generative AI-driven professional services support.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Ironclad,Ironclad provides AI contract management tools for simplifying contract workflows across industries.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Taskade,Taskade focuses on AI-powered task management and collaborative tools for creative projects.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Humata,"Humata helps users extract useful insights from documents and files, enhancing knowledge management.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Simplifai,"Simplifai automates banking and finance processes, offering solutions tailored to regulatory requirements.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
PatentPal,"PatentPal generates drafts for patent specifications, optimizing the intellectual property protection process.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Adept AI,Adept AI utilizes natural language processing to enhance workplace interactions and automate workflows.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Perplexity AI,"Perplexity AI offers a personalized AI search engine, resembling chatbots with more detailed outputs.",https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Andi,Andi is a friendly generative AI search bot that summarizes web information efficiently.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
You.com,You.com is a private search engine that uses AI to summarize and personalize search results.,https://www.eweek.com/artificial-intelligence/generative-ai-startups/
Cohere Command,"Command models are used by companies to build production-ready, scalable and efficient AI-powered applications.",https://cohere.com/
Cohere Embed,"Unlocking the full potential of your enterprise data with the highest performing embedding model, supporting over 100 languages.",https://cohere.com/
Cohere Rerank,"Surfaces the industry’s most accurate responses, combining Rerank and Embed for reliable and up-to-date responses.",https://cohere.com/
```
