<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

## <h1 align="center" id="heading">Session 10: LLM Servers</h1>

| 📰 Session Sheet                                  | ⏺️ Recording                           | 🖼️ Slides                                   | 👨‍💻 Repo       | 📝 Homework                                              | 📁 Feedback                        |
| ------------------------------------------------- | -------------------------------------- | ------------------------------------------- | ------------- | -------------------------------------------------------- | ---------------------------------- |
| [Session 10: LLM Servers](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/10_LLM_Servers) |[Recording!](https://us02web.zoom.us/rec/share/zXd6__uO2RwCmJUmNyGKY01sbwYjjrkpDDNPbfK_Es0MANaqRpFOqqYX4sEVYY1d.gJwTZk1729siXnjj) <br> passcode: `^1$@$R@.`| [Session 10 Slides](https://canva.link/953giejzt5igxvw) |You are here! | [Session 10 Assignment](https://forms.gle/hKxFnEM8U16fCCnG8) | [Feedback 7/2](https://forms.gle/uj2QvYjHfHKFFQ8a6) |

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU'RE FINISHED YOUR ASSIGNMENT !!!⚠️**

# Build 🏗️

In today's assignment, we'll be creating Fireworks AI endpoints, and then building a RAG application.

- 🤝 Breakout Room #1
  - Set-up Open Source Endpoint (Instructions [here](./ENDPOINT_SETUP.md)) ((This process may take 15-20min.))
  - Test Endpoint and Embeddings with the `endpoint_slammer.ipynb` notebook.

- 🤝 Breakout Room #2
  - Use the Open Source Endpoints to build a RAG LangGraph application

# Ship 🚢

The completed notebook and your RAG app/notebook!

### Deliverables

- A short Loom of either:
  - the notebook and the RAG application you built for the Main Homework Assignment; or
  - the notebook you created for the Advanced Build

# Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a RAG application powered by open-source endpoints! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and question-answering. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#LangChain #QuestionAnswering #RetrievalAugmented #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

# Submitting You Homework

## Main Homework Assignment

Follow these steps to prepare and submit your homework assignment:

1. Follow the instructions in `ENDPOINT_SETUP.md`
2. Replace both `model` values in `endpoint_slammer.ipynb` with the `gpt-oss` endpoint you created in Step 1
3. Run the code cells in `endpoint_slammer.ipynb`
4. Respond to the questions in the section below
5. Build a sample RAG
6. Record a Loom video reviewing what you have learned from this session

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU HAVE FINISHED YOUR ASSIGNMENT !!!⚠️**

## Questions

### ❓ Question #1:

What is the difference between serverless and dedicated endpoints?

#### ✅ Answer:

The difference between serverless / dedicated endpoints

Serverless:
- compute: serverless uses shared compute vs dedicated having reserved GPU's just for your use
- Serverless is convenient, and likely best for unpredictable traffic patterns, particularly on the low side (spiky traffic likely from early usage,  experimentation, or simply because that's the natural traffic pattern of the use case)
- Latency likely varies because its shared resources, depending on 'noisy neighbor issues'
throughput is presumably capped as well to avoid (as much as possible) noisy neighbors
- Also easiest to setup since there's little, if anything, to manage

Dedicated:
Dedicated allows reserving GPU's for inference to avoid the issues of shared resources, likely in response to a better understood, higher volume or more sustained traffic patterns.. or potentially a need for more predictable latency by avoiding noisy neighbors with dedicated resources. It will, however require additional setup to define the infra that supports the expected level of activity.

### ❓ Question #2:

Why is it important to consider token throughput and latency when choosing an LLM for user-facing applications?

#### ✅ Answer:

The key reason to consider latency and throughput is the user experience. A poor user experience may make an otherwise good solution unusable from the consumers perspective
Latency 
- time for user to get a useful response (e.g. time-to-first-token, end to end response time). With high latency, app seems broken even if answers are good
- Throughput - handling of concurrent requests in a given time period. If users experience queueing, timeouts, or degraded UX, then app seems broekn
- Bigger models may mean better answers, but at the cost of latency and throughput... 



## Activity 1: RAGAS Evaluation with Cost Analysis

Use RAGAS to evaluate your open-source Fireworks AI powered RAG app against an OpenAI `gpt-4.1-mini` powered equivalent. Compare retrieval quality, answer faithfulness, and end-to-end accuracy across both providers.

Additionally, instrument both pipelines with **LangSmith** to capture token usage and cost per query. Use LangSmith's tracing and cost dashboards to compare the total cost of running each provider at scale. Include your evaluation results, cost breakdown, and analysis in your Loom video.

### ✅ Activity 1 Results

Notebook: [`activity1_ragas_cost.ipynb`](./activity1_ragas_cost.ipynb)

Same 5 cat-health questions, shared Fireworks embeddings, generators compared: Fireworks `gpt-oss-20b` vs OpenAI `gpt-4.1-mini`.

| Metric | Fireworks | OpenAI |
|---|---:|---:|
| Faithfulness | 0.9765 | 1.0000 |
| Answer relevancy | 0.9004 | 0.9434 |
| Context precision | 0.8056 | 0.7944 |

LangSmith (`session10-activity1`), tagged generator calls:
- Fireworks: ~$0.0037 / ~40k tokens
- OpenAI: ~$0.0095 / ~33k tokens

**Takeaway:** Quality was close; Fireworks generator cost was roughly one-third of OpenAI on this batch, with higher or more variable latency on some calls — a solid managed-OSS MVP tradeoff if UX SLOs allow it.

## Advanced Activity: Local Models

Swap out the Fireworks AI endpoints for **locally-running open-source models** using [Ollama](https://ollama.com/) or another local inference server of your choice. Run both your embedding model and your chat model locally, and rebuild the RAG pipeline on top of them.

- Compare quality and latency between the local setup and your Fireworks AI hosted endpoint.
- Reflect: what are the trade-offs of local models vs. managed endpoints in a production setting?

Include your findings and a demo in your Loom video.
