---
marp: true
paginate: true
theme: default
---

# Week 0 · Course C: Data structures for agents
## The structures an agent loop is made of

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Big-O in one slide, then measure

| Cost | Reads as | In this course |
|---|---|---|
| O(1) | the same time whatever n is | `by_id["rag-basics"]`, a dict lookup by doc id |
| O(log n) | halve the problem each step | `bisect` on a sorted list of scores; nothing here needs it yet |
| O(n) | look at everything once | `retrieve()` scores every chunk of every document |
| O(n log n) | sort everything | `scored.sort(...)` in `retrieval.py` before `[:top_k]` |
| O(n²) | compare everything with everything | dedupe citations by scanning the list for each citation |

Big-O says how the cost grows. It does not say what the cost is. For that you measure.

---

## Measuring: a scan against a dict lookup

```python
import timeit
from bootcamp_agent.documents import load_corpus

docs = load_corpus(REPO_ROOT / "data" / "corpus")
doc_ids = [f"{doc.doc_id}-{copy}" for copy in range(10_000) for doc in docs]  # 60,000
target = doc_ids[-1]
index = {doc_id: position for position, doc_id in enumerate(doc_ids)}  # built once


def scan(wanted):
    for position, doc_id in enumerate(doc_ids):
        if doc_id == wanted:
            return position


linear_ms = min(timeit.repeat(lambda: scan(target), number=20, repeat=5)) / 20 * 1000
dict_ms = min(timeit.repeat(lambda: index[target], number=20, repeat=5)) / 20 * 1000
print(f"linear scan: {linear_ms:.3f} ms    dict lookup: {dict_ms:.6f} ms")
print(f"ratio: {linear_ms / dict_ms:,.0f}x")
```

---

## Output

```
linear scan: 0.561 ms    dict lookup: 0.000032 ms
ratio: 17,780x
```

Your numbers differ. The ratio does not, by much: one is O(n), the other O(1), and n is 60,000. `min()` of five repeats is the honest figure; every slower run was the same code plus noise.

---

## Why this matters on Monday

- Retrieval over six documents is fine. `retrieve()` scores every chunk, sorts them, keeps `top_k`. That is O(n log n) and it takes no time at all, because n is 23.
- Over 60,000 documents it is not fine, and nothing in the code changes to tell you. The number that tells you which world you are in is the one you measured.
- Session 7 measures retrieval quality. This is how you measure retrieval cost, and both are numbers, not opinions.

---

## Summary: which cost is this?

| The code does | Cost | Fast enough when |
|---|---|---|
| one dict or set lookup | O(1) | always |
| a `for` over everything | O(n) | n is small, and you measured it |
| `sorted(...)` over everything | O(n log n) | n is small, and you measured it |
| a `for` inside a `for` over the same list | O(n²) | n is tiny; rewrite with a dict or a set |

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## list, dict, set

---

## One of each, by key, in the order seen

```python
from bootcamp_agent.documents import load_corpus
from bootcamp_agent.retrieval import chunk_document

docs = load_corpus(REPO_ROOT / "data" / "corpus")
by_id = {doc.doc_id: doc for doc in docs}  # dict: one per id, O(1) by id
tags = {tag for doc in docs for tag in doc.tags}  # set: one of each, no order
chunks = [chunk for doc in docs for chunk in chunk_document(doc)]
by_chunk = {(chunk.doc_id, chunk.position): chunk for chunk in chunks}  # tuple as key
citations = ["rag-basics", "agent-loops", "rag-basics", "mcp-overview", "agent-loops"]

print(by_id["rag-basics"].title)
print(len(tags), "distinct tags")
print(len(by_chunk), "chunks keyed by (doc_id, position)")
print(list(set(citations)))  # one of each, order forgotten
print(list(dict.fromkeys(citations)))  # one of each, order kept
```

---

## Output

```
RAG Basics
27 distinct tags
23 chunks keyed by (doc_id, position)
['agent-loops', 'mcp-overview', 'rag-basics']
['rag-basics', 'agent-loops', 'mcp-overview']
```

The fourth line is one of six orders a set can print; restart the kernel and it can change. The fifth line is the order the agent cited them in, every time. A dict key must be hashable: a string, a number, a tuple of those. A list is not, and Python says so with `TypeError: unhashable type`.

---

## Why this matters on Monday

- `documents.py` loads the corpus as a list sorted by doc id, and every consumer that needs one document by id builds the dict first. That is the O(1) from lesson 1.
- The evaluator reads `data/evals/golden.jsonl` as one case per line. Look a case up by its question and you have keyed it: one dict, no scan.
- `agent.py` checks every cited doc id against the retrieved set. Membership in a set is O(1), and that check runs on every answer.

---

## Summary: which structure?

| I need | Use | Because |
|---|---|---|
| things in order, repeats allowed | `list` | position matters, `append` is O(1) |
| one thing per key, found by key | `dict` | O(1) lookup, and order is kept |
| one of each, membership tests | `set` | O(1) `in`, no order |
| one of each, order kept | `dict.fromkeys(items)` | a dict with no values is an ordered set |
| a key made of two values | `tuple` | hashable; a list is not |

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Stack, queue, recursion

---

## The agent loop is a queue with a budget

```python
from collections import deque

pending = deque([("search", "chunking")])  # first in, first out
budget, done = 2, []
while pending and len(done) < budget:  # two ways to stop, both written first
    tool, argument = pending.popleft()
    done.append(f"{tool}({argument!r})")
    if tool == "search":  # a search queues the reads it found
        pending.append(("get_document", "rag-basics"))
        pending.append(("get_document", "evaluation-basics"))
print(done)
print("left in the queue:", list(pending))
```

---

## Output

```
["search('chunking')", "get_document('rag-basics')"]
left in the queue: [('get_document', 'evaluation-basics')]
```

The budget ran out with work still queued, and the loop said so. A queue is `popleft()`; a stack is `pop()` from the same `deque`, last in, first out. Recursion is a stack you did not write: every call waits on the stack for the calls it made. Give it a budget or the interpreter gives it `RecursionError`.

---

## Why this matters on Monday

- Session 5's loop is this queue. `answer_question(..., max_tool_calls=3)` in `agent.py` is the budget, and the loop cannot exceed it.
- `docs/guides/loop-engineering.md`: write the stopping conditions before the loop body. Budget exhausted is a defined state, and it sets `needs_human_review`, not a silent cut.
- A tool that calls the tool that called it is a tree that contains itself. Nothing in the data stops that walk. The budget does.

---

## Summary: stack, queue or recursion?

| The work is | Use | Stops when |
|---|---|---|
| do the oldest pending thing first | `deque.popleft()` | the queue is empty, or the budget is spent |
| do the newest pending thing first | `list.pop()` | the stack is empty, or the budget is spent |
| the same thing on each child | a function calling itself | the budget check at the top of the function returns |
| any of the above with no budget | nothing | it does not, and that is the bug |

**Let's practice:** notebook, exercise 3.

---

# Lesson 4
## Trees and graphs

---

## Derive order is a topological sort

```python
from collections import deque

edges = [
    ("authority", "store"),
    ("store", "item"),
    ("item_index", "item"),
    ("buyer", "buyer_token_account"),
    ("mint", "buyer_token_account"),
    ("item", "mint"),
]


def derive_order(edges):
    nodes = list(dict.fromkeys(node for edge in edges for node in edge))
    incoming = {node: 0 for node in nodes}
    for _before, after in edges:
        incoming[after] += 1
    ready = deque(node for node in nodes if incoming[node] == 0)
    order = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for before, after in edges:
            if before == node:
                incoming[after] -= 1
                if incoming[after] == 0:
                    ready.append(after)
    return order if len(order) == len(nodes) else None


print(derive_order(edges))
print(derive_order([("store", "item"), ("item", "mint"), ("mint", "store")]))
```

---

## Output

```
['authority', 'item_index', 'buyer', 'store', 'item', 'mint', 'buyer_token_account']
None
```

The edges are the fixture's: `cookbook/fixtures/program-graph-example.json`, an instruction-to-account graph in the shape Gecko produces. A node is placed only when everything it needs is placed, so every edge holds. On a cycle no node ever becomes ready, the queue runs dry with nodes left, and the answer is `None`: a cycle is a gap, not an order.

---

## Why this matters on Monday

- Session 13: "callable is a graph property". `purchase` needs `buyer_token_account`, which needs `mint`, which is read from `item`, which needs `store`. The first call is decided by the edges, not by which name sounds right.
- `docs/guides/graph-engineering.md`: keep the relationships, not just the items, and ask where each edge came from. The fixture tags every account `declared`, `recovered`, `measured` or `inferred`.
- BFS is the queue from lesson 3 walking a graph; DFS is the stack. Topological order is BFS that waits for every incoming edge.

---

## Summary: which walk?

| I need | Walk | Structure |
|---|---|---|
| everything, nearest first | BFS | a `deque`, `popleft()` |
| everything, deepest first | DFS | a stack, or recursion with a budget |
| an order that respects "X before Y" | topological sort | incoming counts and a queue of ready nodes |
| to know whether an order exists | topological sort | nodes left over means a cycle: return `None` |

**Let's practice:** notebook, exercise 4.

---

## Exit ticket + homework

- One thing that works: a lookup you timed, and the ratio you got between the scan and the dict.
- One thing unclear: which of the four walks (BFS, DFS, topological, recursive with a budget) you could not yet write from a blank cell.
- Your next action: open `src/bootcamp_agent/agent.py`, find `max_tool_calls`, and write down every way the loop stops.

**Next:** session 1 on Monday.
