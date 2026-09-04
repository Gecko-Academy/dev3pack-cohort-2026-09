# Session 4 — Claude Code 101 and assistant configuration

**Thursday, September 17, 2026 · 2h · Thread: harness engineering**

## Learning objectives

- Configure a coding assistant for a repository; write durable project
  instructions.
- Use the inspect → plan → edit → test → review loop; distinguish convenience
  from permission.
- Explain the roles of `CLAUDE.md`, `AGENTS.md`, and Cursor rules — and why one
  canonical policy beats three copies.

## Class flow

1. **Warm-up (10m).** One adversarial-question result from homework.
2. **Concept (20m).** Instructions are code: executed by every assistant, on
   every task, forever. What belongs in a policy file: architecture, commands,
   style, testing requirements, "do not" constraints. The canonical-file
   pattern (`AGENTS.md` here; the others point at it).
3. **Live demo (25m).** Weak prompt vs project-aware prompt on this repo, in ONE
   assistant. Then the full loop on a small feature: plan → restrict → smallest
   diff → tests → reject something → risk summary.
4. **Lab (40m).** In your own assistant (the notebook is the checklist): add a
   `tags` filter to `search_documents` in a scratch copy. You must request a
   plan first, inspect the diff, run tests, and **reject at least one change**.
5. **Share (10m).** Rejected changes read aloud — the best rejection wins.
6. **Exit ticket (5m).**

## Artifact

Configuration files, a reviewed feature commit, one documented rejection, and a
short assistant-use policy.

## Homework

Find one wrong assumption your assistant made today; fix `AGENTS.md` so it
cannot happen again. Read `docs/guides/harness-engineering.md`.

## Optional pre-work

Anthropic Skilljar catalog; DeepLearning.AI *Agent Skills with Anthropic*.

## Note

This session's notebook is a **checklist/logbook** (marked `manual-run`) — the
work happens in your assistant, the evidence lands in the notebook.
