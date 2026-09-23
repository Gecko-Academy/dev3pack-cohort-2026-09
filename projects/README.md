# Real-world projects

A brief, open data, and named things to deliver — the way work actually arrives.
Each one runs on a **local model** and a **vector database**. No API key.

Optional and never counted. Each task has a check so you know when you are done.

| Project | What you build |
|---|---|
| [01 — What are customers really saying?](01-clothing-reviews/notebook.ipynb) | Embeddings of 958 real clothing reviews, a 2-D map, topics, and "find reviews like this one" with ChromaDB |
| [02 — What are these companies worried about?](02-sec-filings/notebook.ipynb) | A RAG pipeline on the risk sections of eight real annual reports: clean the HTML, chunk without losing a word, embed into ChromaDB, answer with the paragraph it came from, and measure keyword search against embeddings on 20 labelled questions |
| [03 — Did the extra agents earn their calls?](03-analyst-team/notebook.ipynb) | A coordinator, a researcher with read-only tools, a writer and a critic over project 02's filings index: the same team written as a LangGraph state graph and as plain Python, with routing measured on its own and the team's model calls counted against a single loop's |

## Reference tutorials

Not projects and not graded. Each one is a slow, worked walk through one skill the projects
use, and each runs on a recorded lane with no model and no key.

| Tutorial | What it walks through |
|---|---|
| [01 — Calling a model from Python](tutorials/01-calling-a-model.ipynb) | Lanes, one call, tuning a reply, strict JSON, embeddings, errors and what a call costs |
| [02 — Tools the model can call, with limits](tutorials/02-tools-with-limits.ipynb) | A tool's contract, letting a model ask and your code decide, and a loop with four named exits |
| [03 — Build a team with LangGraph](tutorials/03-build-a-team-with-langgraph.ipynb) | The state and its reducer, the team as data, each node under the prompt it sends, the wiring, the drawn graph and a streamed run |

**Ask your assistant.** Each project folder has an `AGENTS.md`: what the project is for, how
to run it, and the rules a coding assistant follows. It explains; it does not write the answers.

**Start a new project** by copying [`_template/`](_template/README.md). Its README lists the steps
and the checklist a project passes before it ships.

## Setup, once

```bash
uv sync --extra projects          # ChromaDB, scikit-learn, pandas, matplotlib
ollama pull nomic-embed-text      # a 274 MB embedding model
ollama pull qwen2.5:7b-instruct   # project 02 only: the model that writes the answers (4.7 GB)
uv sync --extra projects --extra agents   # project 03 and tutorial 03: LangGraph and the web tool
```

No room for the 7B model? Project 02 has a recorded lane: it replays one real run and
says `[recorded]` on the first line, so every step still runs.

Only 8 GB of RAM? `demos/04_ollama_on_colab.ipynb` runs the model on Colab.

The concepts behind every project are on the course site under **Real-world projects**,
and `coach(...)` answers from them.
