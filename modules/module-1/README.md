# Week 1 — Foundations and assistant setup (Sep 14–18)

**Goal:** move from a raw LLM call to a small, typed, testable Python assistant
with a configured coding assistant and bounded read-only tools.

| Session | Topic | Checkpoint |
|---:|---|---|
| [1](chapter-01/) | LLM and agent mental models | Baseline FakeLLM call + written reliability bar |
| [2](chapter-02/) | Python for AI engineers | Typed loader with two tested failure modes |
| [3](chapter-03/) | Prompts and structured outputs | Validated schema + three golden questions |
| [4](chapter-04/) | Claude Code & assistant configuration | Reviewed feature + one rejected change |
| [5](chapter-05/) | Tools with bounded contracts | A fourth tool passing boundary tests |

Each session folder contains `README.md` (lesson guide), `slides.md` (Marp),
`notebook.ipynb` (exercises — has TODOs), and `solutions/notebook.ipynb`
(executable; CI runs it).

**The week is complete when you can:** create the environment, run the tests,
explain the project instructions, inspect a diff from an assistant, and
demonstrate one supported and one unsupported question.

```bash
uv sync --group dev
uv run pytest -q
uv run jupyter lab modules/module-1/chapter-01/notebook.ipynb   # or open in your editor
```
