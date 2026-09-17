# Real-world projects

A brief, open data, and named things to deliver — the way work actually arrives.
Each one runs on a **local model** and a **vector database**. No API key.

Optional and never counted. Each task has a check so you know when you are done.

| Project | What you build |
|---|---|
| [01 — What are customers really saying?](01-clothing-reviews/notebook.ipynb) | Embeddings of 958 real clothing reviews, a 2-D map, topics, and "find reviews like this one" with ChromaDB |

## Setup, once

```bash
uv sync --extra projects          # ChromaDB, scikit-learn, pandas, matplotlib
ollama pull nomic-embed-text      # a 274 MB embedding model
```

Only 8 GB of RAM? `demos/04_ollama_on_colab.ipynb` runs the model on Colab.

The concepts behind every project are on the course site under **Real-world projects**,
and `coach(...)` answers from them.
