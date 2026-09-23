# Project 02 for coding assistants: What are these companies worried about?

This file tells a coding assistant what this project is and how to help with it. It
adds to the repository's root `AGENTS.md` and never overrides it.

## Purpose

An analyst covers eight companies and answers client questions about their risks. The
learner builds a RAG pipeline over Item 1A, *Risk Factors*, of each company's latest
annual report: clean the HTML, chunk it without losing a word, embed it into ChromaDB,
answer with the paragraph the answer came from, and measure keyword search against
embeddings on labelled questions.

## Goals

By the end, the learner can:

- look at raw data and check it before trusting it;
- clean HTML with a parser, and remove page furniture with patterns;
- chunk text so that no word is lost, and prove it by counting;
- store chunks with their metadata in a vector database;
- retrieve two ways and set a floor, so a question with no good match is refused;
- ask a model for a typed answer with citations, and keep only citations that retrieval returned;
- measure two methods on the same labelled questions, split by kind.

## Who it is for

Learners who have done sessions 2, 3 and 6:

| Session | Folder | What the project reuses |
|---|---|---|
| 2, calling a model | `units/en/unit1/session-02-model-adapter/` | `model.complete(...)` and the `FakeLLM` lane |
| 3, typed JSON answers | `units/en/unit1/session-03-structured-outputs/` | `ResearchAnswer` and `parse_research_answer` |
| 6, keyword retrieval | `units/en/unit2/session-06-retrieval-baseline/` | `Document`, `chunk_document` and the keyword score |

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[live]` | Ollama with `nomic-embed-text` (274 MB) for vectors, and `qwen2.5:7b-instruct` (4.7 GB) for answers | `embeddings: [live] nomic-embed-text` and `answers: [live] qwen2.5:7b-instruct` |
| `[recorded]` | Nothing but the course | `embeddings: [recorded] 2026-09-21` and `answers: [recorded] 2026-09-21` |
| Colab | A Google account. The Colab cell installs Ollama and pulls both models | the `[live]` lines |

The two lines are independent: with only `nomic-embed-text`, vectors are live and
answers replay the recording. The recorded lane replays one real run from
2026-09-21. Every step runs on it. Only asking questions of your own needs `[live]`.
The notebook starts with `# manual-run:`, so CI does not execute it.

```bash
uv sync --extra projects
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct      # optional: without it, answers play the recording
uv run jupyter lab                   # open projects/02-sec-filings/notebook.ipynb
```

On a laptop, skip the Colab cell and run the setup cell after it.

## Deliverables and checks

| Step | Variable | Check | What the check guards |
|---|---|---|---|
| 3 | `clean` (the function) | `project-02-e1` | No HTML tag, no page furniture, opens with "Item 1A", at most 1% of words lost, on all eight filings |
| 5 | `chunks` | `project-02-e2` | No empty chunk, none over 800 characters, every word of every document present |
| 6 | `collection` | `project-02-e3` | One record per chunk, unique ids, each with `ticker` and `company` metadata |
| 9 | `measurement` | `project-02-e4` | Both methods, both kinds of question, totals that match `data/questions.json` |

Step 5 also runs `project-02-e2` on session 6's chunker. That one fails on purpose: its
message shows how many words it lost. The checks live in
`src/bootcamp_agent/projects/sec_filings.py` and are not counted toward marks. They pin
no vector and no score.

## The data

| Path | What it is |
|---|---|
| `data/raw/*.html` | Item 1A of the latest Form 10-K of Apple, Microsoft, NVIDIA, Tesla, Coca-Cola, Nike, MercadoLibre and Airbnb, exactly as EDGAR serves it apart from the cut |
| `data/sources.json` | For each file: company, CIK, accession number, period, filing date, URL and size |
| `data/recorded/` | Ours: the vectors and model replies of the 2026-09-21 run |
| `data/questions.json` | Ours: the labelled questions for step 9 |

The filings are public filings published by the SEC on EDGAR. The companies wrote
them, so they are not U.S. government works. See `data/LICENSE.md`. `fetch.py` is
instructor-only; learners never run it.

## How the notebook is laid out

| Step | What it does |
|---|---|
| 1. The model alone | Asks the model with no documents, to see it answer anyway |
| 2. Look at the data | Loads the source records, looks at the raw HTML, runs a checklist |
| 3. Clean | `clean()`: a parser for the structure, patterns for the furniture; writes one clean file |
| 4. Load | One `Document` per company |
| 5. Chunk | `chunk_all()`: paragraphs first, then sentences, then a word boundary; checks the chunks |
| 6. Embed, and store | Vectors, live or recorded, into the `risk_factors` collection |
| 7. Retrieve, two ways | Keyword scoring against nearest-vector search, and a floor for nonsense |
| 8. Answer, with citations | The prompt, typed output, the pipeline, and the architecture |
| 9. Measure | Both methods on every labelled question, in one table |
| Resources | The reference tutorials, sessions 6 and 7, demo 9 |
| Your turn | Ask your own, move the floor, filter by company |
| Ask your assistant about this project | Five prompts that explain the project and point to the step |

## Rules for the assistant

- **Explain, and point to the step.** Name the step and the cell. Every step is already written; help the learner read it.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions.** Do not repeat the questions in `data/questions.json` or `data/recorded/recorded.json`, or the final assignment's. Talk about the kind of question instead.
- **Never commit secrets or `.env`.** This project needs no key. `fetch.py` reads a contact address from the environment for one run; it is never written to a file.
- **Say when you are unsure.** A live run words its answers differently from the recording. Do not claim a cell ran unless it ran.
- **Keep the recorded lane working.** The recorded vectors were made from one exact set of chunks. Step 6 compares a fingerprint (a SHA-256 of every chunk's text) with the one in `data/recorded/recorded.json`. Change `clean()` or `chunk_all()`, and the chunks change, the fingerprint no longer matches, and step 6 stops on the recorded lane. That is correct: old vectors for new chunks would be wrong. If the learner wants to change either function, say so first, and tell them to run live with `nomic-embed-text` to embed their own chunks.

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain what clean() does in step 3 of projects/02-sec-filings/notebook.ipynb, part by part. Do not change the code."
> - "Why does session 6's chunker fail the chunk check in step 5, and what did it lose?"
> - "If I change chunk_all(), what happens on the recorded lane, and why?"
> - "How do I run this project with the embedding model live but the answers recorded?"
