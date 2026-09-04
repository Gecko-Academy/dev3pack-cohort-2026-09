---
marp: true
paginate: true
theme: default
---

# Session 4: Claude Code 101
## Assistant configuration as engineering

Dev3Pack AI-Engineering Bootcamp · Thursday, September 17, 2026

---

# Lesson 1
## The same assistant, two prompts

---

## Weak

> add a search feature

```
Output: invents an architecture, touches five files, adds a dependency,
        writes a test that asserts the mock.
```

---

## Project-aware

> read AGENTS.md, then propose a plan to add a tags filter to
> search_documents in src/bootcamp_agent/tools.py. Plan only, no edits.

```
Output: names the file, follows the conventions in AGENTS.md,
        lists the three lines it would change, waits for approval.
```

The difference is not the model. It is the **harness**.

---

## Summary: what changed between the two

| | Weak | Project-aware |
|---|---|---|
| Context | none | the policy file, read first |
| Scope | open | one function, one file |
| Output | edits | a plan |
| Who decides | the assistant | you |

---

# Lesson 2
## Instructions are code

---

## Why "code"

- Executed by every assistant, on every task, thousands of times
- A wrong sentence there is a bug with fan-out
- So: version it, review diffs to it, **fix it when it fails**

Today's homework is a bugfix to an instruction file.

---

## What goes in the policy file

| Section | Holds |
|---|---|
| Architecture | what lives where, what the seams are |
| Commands | install, test, lint; exact, copy-pasteable |
| Style and tests | the rules a reviewer would enforce |
| **Do not** | the most load-bearing section |
| Safety | secrets, external calls, untrusted content |

---

## One policy, three assistants

```
AGENTS.md            ← canonical policy (THE file)
CLAUDE.md            ← points there + Claude specifics
.cursor/rules/*.mdc  ← points there + Cursor specifics
```

Duplicated policy drifts. This repo does it this way. Read all three today.

---

# Lesson 3
## The task loop, enforced by you

---

## The loop

| Step | You | The assistant |
|---|---|---|
| 1. Inspect | name the files | reads them |
| 2. Plan | read it, restrict files and commands | proposes |
| 3. Edit | ask for the smallest version | edits |
| 4. Test | `uv run pytest -q`, read failures yourself | fixes |
| 5. Review | inspect the diff, **reject what does not belong** | explains |

Convenience is not permission.

---

## Rejecting is the skill

Good rejections from past cohorts:

- "it added a dependency for a 3-line function"
- "it improved a file I did not ask about"
- "the test it wrote asserts the mock, not the behaviour"

If you rejected nothing, you were not reviewing.

---

## From tomorrow: the loop applied to every exercise

1. Give the assistant the exercise's **Context** and **Instructions**
2. Let it fill the `TODO(you)` lines
3. **You** run the `check(...)` cell and read the verdict
4. `review("chNN")` at the end is your scorecard

The assistant does not grade its own work.

---

## Let's practice: today's lab

Feature: `tags` filter on `search_documents`, in a scratch copy.

Required evidence in the notebook:
- the plan you approved
- the diff you inspected
- **one rejected change, and why**
- the risk summary you asked for

---

## Recap

| Lesson | One line |
|---|---|
| Two prompts | the harness, not the model, made the difference |
| Instructions are code | version it, review it, fix it when it fails |
| The task loop | plan, smallest edit, test, review, reject |

---

## Exit ticket + homework

Fix the instruction that let your assistant assume wrong.
Read `docs/guides/harness-engineering.md`. This session is its Layer 1.
