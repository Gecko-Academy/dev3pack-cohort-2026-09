---
marp: true
paginate: true
theme: default
---

# Session 2: Python for AI engineers
## The minimum useful foundation

Dev3Pack AI-Engineering Bootcamp · Tuesday, September 15, 2026

---

## uv in four commands

```bash
uv sync --group dev      # env + deps, reproducibly
uv run pytest -q         # run anything inside the env
uv run bootcamp-agent "..."
uv python install 3.11   # Python itself, managed
```

Never activate a venv by hand. Never bare `pip`. The preflight cell tells you if the kernel is wrong.

---

# Lesson 1
## The data shape first

---

## Data that crosses a boundary gets a type

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MiniDocument:
    doc_id: str
    title: str
    text: str


sample = MiniDocument(doc_id="demo", title="Demo", text="Hello corpus.")
print(sample)
```

---

## Output

```
MiniDocument(doc_id='demo', title='Demo', text='Hello corpus.')
```

- Frozen: nothing mutates it behind your back
- Named fields: no `doc["titel"]` typos
- **No bare dicts as contracts**

---

## Summary: dict vs dataclass

| | `dict` | `dataclass` |
|---|---|---|
| Field typo | silent `KeyError` later | error at the boundary |
| Type of a field | anything | declared, checkable |
| Mutation | anywhere | `frozen=True` refuses |
| Reads as | data | a contract |

---

# Lesson 2
## Errors are the contract

---

## A loader with two failure modes

```python
def load_mini(path: Path) -> MiniDocument:
    if not path.is_file():
        raise ValueError(f"no such file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path.name}: first line must be '# <title>'")
    return MiniDocument(
        doc_id=path.stem,
        title=lines[0][2:].strip(),
        text="\n".join(lines[1:]).strip(),
    )
```

---

## Output

```
refused: no such file: does-not-exist.md
Class-by-Class Curriculum
```

- A loader that returns half a document on bad input is worse than one that refuses
- The message names the file and the rule
- Typed exception: callers catch *your* failure, not everything

---

## Summary: the failure-mode table

| Input | Behaviour | Message names |
|---|---|---|
| good file | `MiniDocument` | (nothing) |
| missing file | `ValueError` | the path |
| first line is not `# title` | `ValueError` | the file and the rule |
| `except: pass` anywhere | a lie | (nothing, which is the bug) |

**Let's practice:** notebook, exercise 2. The check writes a good file, a bad file, and asks for a missing one.

---

# Lesson 3
## The real loader, and the first index

---

## Package vs script

```
src/bootcamp_agent/   ← logic lives here (importable, testable)
    documents.py      ← the real loader: HTML-comment headers, typed CorpusError
    cli.py            ← thin: parse args, call package, format output
scripts/              ← operational checks, not features
```

If logic creeps into the CLI, move it into the package.

---

## Loading the teaching corpus

```python
from bootcamp_agent.documents import load_corpus

documents = load_corpus(CORPUS_DIR)
for doc in documents:
    print(f"{doc.doc_id:22} {doc.title:22} tags={list(doc.tags)}")
```

---

## Output

```
agent-loops            Agent Loops            tags=['agent', 'loop', 'tools', 'budget', 'autonomy']
evaluation-basics      Evaluation Basics      tags=['evaluation', 'testing', 'golden-set', 'tracing', 'reliability']
mcp-overview           MCP Overview           tags=['mcp', 'tools', 'protocol', 'integration', 'agents']
prompt-injection       Prompt Injection       tags=['security', 'injection', 'untrusted-input', 'safety']
rag-basics             RAG Basics             tags=['retrieval', 'rag', 'chunking', 'citations', 'grounding']
structured-outputs     Structured Outputs     tags=['llm', 'json', 'validation', 'schema']
```

Six documents, sorted by id. Every tag is a retrieval handle.

---

## The simplest index there is

```python
tag_index: dict[str, list[str]] = {}
for doc in documents:
    for tag in doc.tags:
        tag_index.setdefault(tag, []).append(doc.doc_id)
tag_index = {tag: sorted(ids) for tag, ids in tag_index.items()}
```

```
agent            ['agent-loops']
tools            ['agent-loops', 'mcp-overview']
...
```

Week 2 builds retrieval on exactly this idea: a key, a list of documents.

**Let's practice:** notebook, exercise 4, then `review("ch02")`.

---

## Recap

| Lesson | One line |
|---|---|
| The data shape | a frozen dataclass is a contract; a dict is a hope |
| Errors are the contract | refuse loudly, name the file and the rule |
| The real loader and the index | package code is importable and testable; an index is a dict |

---

## Exit ticket + homework

- Three more loader tests: empty file, title-only, wrong extension
- A CONTRIBUTING note: how to run this locally with uv
- Ask your assistant for tests, then **review and correct one**
