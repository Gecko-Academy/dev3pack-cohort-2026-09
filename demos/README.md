# Demos

Short notebooks to **run in class and again afterwards**. Each one makes a single
idea concrete in a few minutes.

These are not exercises. Nothing here is graded, nothing is submitted, and no
check reads them. Run them, change a line, run them again — that is the whole
intent.

| Notebook | The idea |
|---|---|
| [1 — An API request, up close](01_api_request_up_close.ipynb) | Real calls to a public pet API — read it, **write to it**, read your own thing back, then meet a 404 whose body is not JSON |
| [2 — One question, three ways](02_one_question_three_ways.ipynb) | A prompt, an API, and an MCP tool answering the same question — and why the third exists |
| [3 — Regex, parsing, retrieval](03_regex_parsing_retrieval.ipynb) | Three ways to get data out of text, each doing its job and then failing at somebody else's |
| [4 — Ollama on Google Colab](04_ollama_on_colab.ipynb) | **If your laptop has 8 GB of RAM.** Run a real 7B model on Colab's free GPU instead — no key, no card, nothing installed locally |
| [5 — The coach, up close](05_the_coach_up_close.ipynb) | Ask the course a question, open the page it came from, watch it refuse and miss, find out why — and turn a wrong answer into your first pull request |
| [6 — Jupyter for beginners](06_jupyter_for_beginners.ipynb) | **Never used a notebook?** Cells, run order, the kernel, how to read an error, and the restart habit that saves the most time |
| [7 — The coach, in a chat](07_the_coach_in_a_chat.ipynb) | Session 5's four exits as four replies to a person, on a recorded chat — then a real one, if you have a token |
| [8 — The weekly challenge](08_the_weekly_challenge.ipynb) | Ana's expense bot: three tools that refuse by name, a page that talks to the model, and the week-1 challenge scored 300/500 |
| [9 — RAG on your laptop](09_rag_on_your_laptop.ipynb) | Today's retriever plus a model on your laptop. Alone, the model invents. With the right pages it answers and cites them. An empty search refuses before the model runs, and the wrong pages still come back with confidence 1.0 |

## They run offline

Every one works with no key and no account. Demo 1 makes **real** calls to the
public [Swagger Petstore](https://petstore3.swagger.io/) — including a write —
and every cell degrades to a printed "offline" note if there is no network, so a
bad conference connection costs you nothing. Demo 2 does the same against GitHub.
Demo 9 uses a local model through Ollama, and without one it replays a single
recorded run and says so.

Nothing in any demo can cost money or needs a credential.

```bash
uv run jupyter lab demos/
```

## Where to start

Each demo ends with a **Your turn** block: a few things to change and re-run,
never marked, never submitted. That is where the learning actually happens.

**Never used a notebook before? Run 6 first.** If you have twenty minutes before a session, run **3**. Regex, parsing and
retrieval turn up in almost every session after week 0, and the silent-failure
example in section 1 is the one people remember a month later.

The same list, plus things to open in a browser and play with, is on the course
site under **Demos and explainers**.
