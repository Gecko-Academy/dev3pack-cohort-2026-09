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

## They run offline

Every one works with no key and no account. Demo 1 makes **real** calls to the
public [Swagger Petstore](https://petstore3.swagger.io/) — including a write —
and every cell degrades to a printed "offline" note if there is no network, so a
bad conference connection costs you nothing. Demo 2 does the same against GitHub.

Nothing in any demo can cost money or needs a credential.

```bash
uv run jupyter lab demos/
```

## Where to start

Each demo ends with a **Your turn** block: a few things to change and re-run,
never marked, never submitted. That is where the learning actually happens.

If you have twenty minutes before a session, run **3** first. Regex, parsing and
retrieval turn up in almost every session after week 0, and the silent-failure
example in section 1 is the one people remember a month later.

See also [docs/guides/visual-explainers.md](../docs/guides/visual-explainers.md)
— things to open in a browser and play with, mapped to the sessions they help.
