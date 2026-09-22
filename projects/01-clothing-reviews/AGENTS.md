# Project 01 for coding assistants: What are customers really saying?

This file tells a coding assistant what this project is and how to help with it. It
adds to the repository's root `AGENTS.md` and never overrides it.

## Purpose

An online clothing shop has a thousand reviews and nobody with time to read them. The
support team wants to know what people keep talking about, and, when a new review
arrives, to see the reviews most like it. The learner builds both with an embedding
model on their own machine and ChromaDB.

## Goals

By the end, the learner can:

- turn text into embeddings with a local model, in batches;
- drop empty rows before embedding, and say why;
- reduce embeddings to 2-D with t-SNE and read the plot for neighbourhoods only;
- search by topic with cosine distance, and read the whole result before judging it;
- measure a documented setting (the `search_document:` and `search_query:` prefixes) instead of assuming it helps;
- store embeddings in ChromaDB and leave the query itself out of its own results.

## Who it is for

Beginners who have run a notebook before. No session is required, but session 6
(`units/en/unit2/session-06-retrieval-baseline/`) makes the search part easier to follow.
The ideas are on the projects track page, `units/en/tracks/projects/introduction.mdx`.

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| Laptop, `[live]` | Ollama and `nomic-embed-text` (274 MB). 8 GB of RAM is enough | `ready: chromadb <version>, model nomic-embed-text` |
| Colab, `[live]` | A Google account. The Colab cell installs Ollama and the model, in about 3 minutes | the same `ready:` line |

This project has **no recorded lane**. Every task calls the model. Without Ollama the
setup cell stops with a message that says what to run. The notebook starts with
`# manual-run:`, so CI does not execute it.

```bash
uv sync --extra projects          # ChromaDB, scikit-learn, pandas, matplotlib
ollama pull nomic-embed-text      # 274 MB
ollama list                       # nomic-embed-text must be in the list
uv run jupyter lab                # open projects/01-clothing-reviews/notebook.ipynb
```

On a laptop, skip the Colab cell and run the setup cell after it. If the setup cell
says there is no Ollama server, run `ollama serve` in a terminal and run it again.

## Deliverables and checks

| Variable | Check | What the check guards |
|---|---|---|
| `embeddings` | `project-01-e1` | One vector per review with text (958), all the same length, not all identical. It names the 42 empty reviews if they are included |
| `embeddings_2d` | `project-01-e2` | One 2-D point per review, numbers only, spread out |
| `topic_reviews` | `project-01-e3` | At least three topics, each pointing at real reviews, not all the same ones |
| `most_similar_reviews` | `project-01-e4` | Three distinct real reviews, and not the review searched with |

The checks live in `src/bootcamp_agent/projects/clothing_reviews.py`. They are not
counted toward marks. They pin no dimension and no neighbour, so they hold for any
embedding model.

## The data

`data/reviews.csv`: 1,000 rows of *Women's E-Commerce Clothing Reviews*, published by
Nick Brooks on Kaggle under CC0 1.0 (public domain). 42 rows have no review text, so
958 reviews remain. The publisher anonymised it. See `data/LICENSE.md`.

## How the notebook is laid out

| Part | What it does |
|---|---|
| Get the model | Laptop or Colab, then the setup cell |
| Look at the data | Loads the CSV and counts the empty reviews |
| Task 1 | Embeds every review with text, 64 at a time |
| Task 2 | Reduces to 2-D with t-SNE and plots by rating |
| Task 3 | Finds the reviews closest to each topic word |
| Stand above it | Reads the whole review, then measures the prefixes |
| Task 4 | Stores the reviews in ChromaDB and finds the three most similar |
| What you just built | A summary, and `coach(...)` for questions about the ideas |
| Your turn | Three unchecked cells to change and run again |

## Rules for the assistant

- **Explain, and point to the step.** Name the task and the cell. Every task is already written; help the learner read it.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions** of any project or of the final assignment.
- **Never commit secrets or `.env`.** This project needs no key and no account.
- **Say when you are unsure.** Embeddings differ between models and runs. Do not claim a cell ran unless it ran.
- **Keep the checks model-free.** They read `data/reviews.csv` to know the 958 reviews. Do not edit that file, and do not add a check that pins a vector, a dimension or a neighbour.
- **Do not invent a recorded lane.** This project needs Ollama. If the learner has none, point to Colab.

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain what projects/01-clothing-reviews/notebook.ipynb builds, task by task. Do not change the code."
> - "Explain why Task 1 drops the empty reviews before it embeds anything. Do not change the code."
> - "Why is the review I search with always its own nearest neighbour in Task 4?"
> - "How do I run this project on Colab instead of my laptop?"
