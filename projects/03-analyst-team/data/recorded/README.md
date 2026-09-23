# The recorded run

One real run of the analyst team, kept so the notebook works with no local model
and no key. Nothing here is a benchmark: it is one 7B model, on one day, on the
passages the notebook's index returned that day.

## What is in `recorded.json`

| key | what it holds |
|---|---|
| `_provenance` | model, date, `auth_sent: "none"`, which retrieval produced the passages, and what the file is and is not evidence of |
| `questions` | `demo` is `analyst_team.DEMO_QUESTIONS`, the questions the notebook asks a model. `labelled` is project 02's twenty |
| `queries` | every question that was run, demo first, in order |
| `runs` | one row per question: the ticker it routed to, the calls it spent, the revisions, the exit, what it cited and what was dropped |
| `replies` | the model's reply, keyed by the first two lines of the prompt that asked for it |

## The recording is made against the notebook's own index

This is the part that broke once, so it is written down. The first version of
`record.py` searched with project 02's **embedding** vectors while the notebook
searches by **keyword**. The replies were real, and every citation in them named a
chunk the notebook never retrieved. The writer dropped all of them, exactly as it
should, and a learner on the recorded lane saw an answer with no citations and a
`needs_human_review` flag on every single run.

Nothing errored. The lane simply taught the wrong thing quietly, which is this
project's own failure mode pointed back at itself.

So `record.py` now builds the search by **executing the notebook's own index and
search cells**. No embeddings, no vectors, no second model. If the notebook's
retrieval changes, the recording is regenerated from it rather than drifting from
it.

## One list of questions, not two

`analyst_team.DEMO_QUESTIONS` holds every question the notebook asks a model.
The notebook reads it as `DEMO`, and `record.py` imports the same object. A
question typed into the notebook instead of read from that list would eventually
fall off the recording, replay as a refusal, and still print something that looks
like an answer. Two tests hold the line: one asserts every demo question has a
recorded writer reply, the other asserts none of them is typed into the notebook.

## Why the replies are keyed that way

`FakeLLM` returns the first key it finds, case-insensitively, inside the user
message. So the key is the opening of the prompt itself:

```python
from bootcamp_agent.projects.analyst_team import reply_key

reply_key("writer", question)  # "Write the answer.\nQuestion: ..."
reply_key("critic", question)  # "Review the draft answer.\nQuestion: ..."
```

The writer and the critic open differently, so no critic reply can ever be handed
to the writer. Build the fake straight from the file:

```python
model = FakeLLM(responses=json.loads(path.read_text())["replies"])
```

A question that was not recorded falls through to `FakeLLM`'s default, which is
the refusal. That is the honest outcome: nothing was recorded, so nothing is
known. Start Ollama to ask your own.

**A recording is keyed to a prompt, not to a question.** Step 2's one-call loop
writes its own prompt rather than the team's, so nothing in this file matches it
and the recorded lane shows the stand-in refusal there. The cell says so. The call
count is still real, because the call was still made.

A revision reuses the writer's key, because the key is the question and not the
critic's note. The recording keeps the FIRST reply, so a replayed revision repeats
the first draft. Live, it does not, and that is the main reason the two lanes can
disagree about how many calls a run spends.

## Regenerating it

Needs Ollama with `qwen2.5:7b-instruct`, and nothing else:

```bash
ollama pull qwen2.5:7b-instruct
uv run python projects/03-analyst-team/data/recorded/record.py
```

It takes about half an hour on a laptop CPU and costs nothing. The summary line at
the end prints the questions, the model calls, how many first drafts were approved,
and how many citations were dropped. **A dropped citation is the number to read.**
If it is not zero, the recording and the notebook are retrieving different
passages, which is the failure described at the top of this file.
