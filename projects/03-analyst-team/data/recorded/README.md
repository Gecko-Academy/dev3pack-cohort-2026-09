# The recorded run

One real run of the analyst team, kept so the notebook works with no local model
and no key. Nothing here is a benchmark: it is one 7B model, on one day, on the
passages project 02's index returned that day.

## What is in `recorded.json`

| key | what it holds |
|---|---|
| `_provenance` | model, date, `auth_sent: "none"`, and what the file is and is not evidence of |
| `chunk_fingerprint` | project 02's fingerprint. Chunks that do not match it no longer match the vectors |
| `vectors` | relative paths to project 02's `chunk_vectors.npy` and `query_vectors.npy`. They are not copied: one corpus, one set of vectors |
| `queries` | the 25 recorded questions, in the order `query_vectors.npy` holds them |
| `runs` | one row per question: the ticker it routed to, the calls it spent, the revisions, the exit |
| `replies` | model reply, keyed by the first two lines of the prompt that asked for it |

## What the recorded run did

25 questions, 80 model calls. The router sent 18 by a domain word and 2 by the
company name, and left 5 to every filing. The critic approved 10 first drafts
and sent 15 back, and all 15 stopped at the revision cap still unapproved.

Read that last number twice before trusting the critic. A reviewer that rejects
three drafts in five is not obviously better than one that approves everything:
both are cheap to produce and neither has been measured against a human. What
the run does prove is the cost: a rejected draft doubles the bill.

## Why the replies are keyed that way

`FakeLLM` returns the first key it finds, case-insensitively, inside the user
message. So the key is the opening of the prompt itself:

```python
from bootcamp_agent.projects.analyst_team import reply_key

reply_key("writer", question)  # "Write the answer.\nQuestion: ..."
reply_key("critic", question)  # "Review the draft answer.\nQuestion: ..."
```

The writer and the critic open differently, so no critic reply can ever be
handed to the writer. Build the fake straight from the file:

```python
model = FakeLLM(responses=json.loads(path.read_text())["replies"])
```

A question that was not recorded falls through to `FakeLLM`'s default, which is
the refusal. That is the honest outcome: nothing was recorded, so nothing is
known. Start Ollama to ask your own.

A revision reuses the writer's key, because the key is the question and not the
critic's note. The recording keeps the FIRST reply, so a replayed revision
repeats the first draft. Live, it does not.

## Regenerating it

Needs Ollama running with `qwen2.5:7b-instruct` and `nomic-embed-text`:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
uv run --extra projects python projects/03-analyst-team/data/recorded/record.py
```

It rebuilds project 02's chunks by executing project 02's own `clean` and
`chunk_all` cells, checks the fingerprint, loads the chunk vectors from project
02 by path, embeds each question live, and runs the team once per question. It
takes about half an hour on a laptop CPU and costs nothing.

If the fingerprint check fails, project 02's cleaning or chunking moved. Fix
that first: vectors made from other chunks retrieve the wrong passages.
