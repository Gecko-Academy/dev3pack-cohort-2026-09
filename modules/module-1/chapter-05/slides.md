---
marp: true
paginate: true
theme: default
---

# Session 5: Tools
## From text generation to bounded action

Dev3Pack AI-Engineering Bootcamp · Friday, September 18, 2026 · Thread: loop engineering

---

# Lesson 1
## What a tool is

---

## A function the app executes when the model asks

```python
@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    run: Callable[..., str]
```

```python
tools = build_tools(documents, client)
for tool in tools.values():
    print(f"{tool.name:24} {tool.description}")
```

---

## Output

```
search_documents         Search the corpus for passages relevant to a query (max_results capped at 5).
get_document_metadata    Return title, source, tags, and length for a known doc_id.
summarize_document       LLM-summarize one document by doc_id (read-only).
```

The model proposes. The app validates and disposes. The description is the model's manual.

---

## Summary: contracts, not capabilities

| Tool | Contract | Guard |
|---|---|---|
| `search_documents` | query, max_results | **capped at 5, clamped by the app** |
| `get_document_metadata` | doc_id | unknown id names the valid ids |
| `summarize_document` | doc_id | read-only, output prefixed with its source |

Bad: "search anything, return everything".

---

# Lesson 2
## Validate at the boundary

---

## Caps and helpful errors

```python
print(tools["search_documents"].run(query="prompt injection defenses", max_results=999))
try:
    tools["get_document_metadata"].run(doc_id="totally-made-up")
except ToolError as error:
    print(f"ToolError: {error}")
```

---

## Output

```
[prompt-injection] (score 6.79)
Any channel that feeds text into the prompt is an injection surface. For a RAG
assistant that means the corpus itself: a document ...
...                                      <- 5 results, not 999

ToolError: get_document_metadata: unknown doc_id 'totally-made-up';
           valid ids: ['agent-loops', 'evaluation-basics', 'mcp-overview', ...]
```

Never trust arguments the model produced. A helpful error teaches the model to recover; a stack trace does not.

---

## Summary: the four-clause contract of `list_documents`

| Call | Behaviour |
|---|---|
| `list_documents()` | every doc_id, one per line |
| `list_documents(tag="retrieval")` | only documents carrying the tag |
| `list_documents(tag="nope")` | `ToolError` naming the valid tags |
| `list_documents(tag="")` | `ToolError`; validate at the boundary |

**Let's practice:** notebook, exercise 3.

---

# Lesson 3
## A tool that reaches the outside world

---

## The five-step loop

| Step | Who | What |
|---|---|---|
| 1 | you | tool definitions + the user message |
| 2 | model | a tool call with arguments |
| 3 | **you** | execute the function |
| 4 | you | send the result back |
| 5 | model | the final answer |

Step 3 is where the boundary lives. Today's outside world: frankfurter.dev, free, keyless, read-only.

---

## Fetch, then convert

```python
def fetch_rates(base: str) -> dict[str, float]:
    url = f"https://api.frankfurter.dev/v1/latest?base={base}"
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read())["rates"]


def convert_currency(amount, source, target, fetch=fetch_rates) -> str:
    if amount <= 0:
        raise ToolError("convert_currency: 'amount' must be positive")
    ...
    rates = fetch(source)
    if target not in rates:
        raise ToolError(f"convert_currency: no rate {source}->{target}; known: {sorted(rates)}")
    return f"{amount} {source} = {amount * rates[target]:.2f} {target} (rate {rates[target]})"
```

---

## Output

```
100 USD = 86.62 EUR (rate 0.86625)          <- live, when the network is there
100 USD = 50.00 EUR (rate 0.5)              <- the check's injected table, offline
```

`fetch` is injected. The check never touches the network. Neither does CI.

---

## Summary: validate before you fetch

| Argument | Rule | Before or after the network call |
|---|---|---|
| `amount` | positive | before |
| `source`, `target` | 3 uppercase letters | before |
| `target` in rates | known, or name the known ones | after, on the fetched data |

A model will call this with whatever it guesses. Refuse first, fetch second.

**Let's practice:** notebook, exercise 5.

---

# Lesson 4
## Budgets: the loop that cannot run away

---

## The same question, two budgets

```python
for budget in (3, 1):
    result = answer_question(question, documents, FakeLLM(), max_tool_calls=budget)
    print(f"budget={budget}: {[e.kind for e in result.trace]}")
```

```
budget=3: ['retrieve', 'llm_call', 'decision']
budget=1: ['retrieve', 'llm_call', 'decision']
```

With our corpus the direct path rarely needs tools. The point: the bound exists and the trace shows it.

---

## Summary: the loop's exit table

| Exit | State |
|---|---|
| answer parsed | return it |
| nothing retrieved | refuse, **before** the LLM call |
| parse failed twice | flagged refusal |
| budget exhausted | stop, visible in the trace |

Every exit designed. No silent truncation. `max_tool_calls=3` is a product decision: this feature is worth at most three calls of latency and cost.

**Let's practice:** notebook, exercise 6, then `review("ch05")`.

---

## Read-only first

Every tool today reads, searches, summarizes, or converts. Nothing writes, spends, or mutates.

Why? **Blast radius.** An injected instruction into a read-only system is an incident. Into a write-capable one, a breach. Session 13 shows the grown-up version of this idea.

---

## Recap

| Lesson | One line |
|---|---|
| What a tool is | a function with a contract; the description is the model's manual |
| Validate at the boundary | clamp caps, refuse bad ids, name the valid options |
| The outside world | five steps; step 3 is yours; refuse before you fetch |
| Budgets | every loop exit is designed and visible |

---

## Exit ticket + homework

- One case where the assistant should NOT use a tool
- One case where it should ask a human first
- Read `docs/guides/loop-engineering.md`. Today was its Level 2.
