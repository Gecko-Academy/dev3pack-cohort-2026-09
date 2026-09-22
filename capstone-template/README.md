# {{capstone_name}}

<!-- write this: one sentence. What it answers, from what, and what it does when
the sources say nothing. -->

{{badge_line}}

## The problem

<!-- write this: who has the problem, and what goes wrong for them today. Two to
four sentences: minute 1 of your demo, in writing. -->

## Demo

Two runs, pasted exactly as the commands printed them. Never an edited one.
`trace` prints every step the agent took, then the answer.

### One supported answer

```bash
uv run bootcamp capstone trace "How does chunking work in RAG?"
```

```text
<!-- paste this: the output. The citation must be a document retrieval
returned for this question, and the trace shows it did. -->
```

### One refusal

```bash
uv run bootcamp capstone trace "What is the capital city of Mongolia?"
```

```text
<!-- paste this: the output. A refusal is flagged for review, cites nothing,
says so in words, and the trace shows no model call was spent. -->
```

## Architecture

<!-- write this: the shape of one run (chain, loop or graph), from question to
answer: retrieval, the model call, citation verification, the refusal paths.
Name the model calls one question costs. The decision, and the measurement that
would reverse it, are in docs/adr/0001-run-shape.md. -->

See [docs/adr/0001-run-shape.md](docs/adr/0001-run-shape.md).

## Measured results

Every number here comes from a command in this table, run on this commit. Say
which model produced it: CI has no keys, so a CI number is always the offline
fake model's.

| What | Command | Model | Result |
|---|---|---|---|
| Contract tests | `uv run pytest` | fake | <!-- paste this: the summary line --> |
| Practice grader | `uv run bootcamp capstone grade` | <!-- write this --> | <!-- paste this: the `score:` line --> |
| Evaluation, before and after | see [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md) | <!-- write this --> | <!-- paste this: the two pass rates --> |

## The honest limitation

<!-- write this: rank 1 of docs/ISSUES.md in one sentence, and the next step
you would take. Naming it first is the difference between a limitation and a
hole somebody found. -->

The full ranked list is in [docs/ISSUES.md](docs/ISSUES.md).

## How to run it

```bash
git clone https://github.com/{{github_slug}} && cd {{repo_name}} && uv sync && uv run pytest
```

No key needed: without a `.env` it runs on the offline fake model. For a real
model, copy `.env.example` to `.env`, fill in your provider, and
`uv sync --extra anthropic` (or `--extra openai`).

To hand in the final assignment, commit and push, then run
`uv run bootcamp capstone submit --github <you>`. It runs the practice set
first, then answers the final questions and opens the pull request.
`--dry-run` shows the bundle without handing anything in.

## Sources

<!-- optional. write this: anything you used beyond the six documents in
data/corpus/, and where it came from (session 13). Delete the section if none. -->

## Credits

<!-- optional. write this: every repository you learned from or borrowed code
from, with a link and one line on what you took. Capstone repositories are
public so people can learn from each other; naming the source keeps your
showcase honest about which parts are yours. Delete the section if none. -->

## Rollback

<!-- optional. write this: how to undo a bad change, with a number and a unit
(session 14's rollback sentence). Delete the section if you have none yet. -->

---

| Path | What it is |
|---|---|
| `agent.py` | The agent: `YourAgent`, the class the tests, `trace` and the grader run |
| `tests/test_contract.py` | The capstone contract, as tests (`uv run pytest -k refusal`, `-k injection`, ...) |
| `data/corpus/` | The six source documents, versioned; nothing here writes to them |
| `docs/EVAL_REPORT.md` | Numbers you produced, before and after, with the command behind each |
| `docs/SKILL.md` | A skill another assistant can load (session 10) |
| `docs/adr/0001-run-shape.md` | The architecture decision and what would reverse it (session 10) |
| `docs/RETENTION.md` | What a session remembers, and what it refuses to (session 11) |
| `docs/ISSUES.md` | The ranked issue list (session 9, kept until 14) |

Built during the Dev3Pack AI Engineering bootcamp, on the course package at
commit `{{course_ref}}` of {{course_url}}.
