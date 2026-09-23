---
name: hand-my-work-in
description: Use when a learner is ready to submit a session. Saves the notebook first, runs the session check, then submits. Covers the browser route for a learner with no GitHub CLI. Never writes the answer to get a check green.
---

# Hand one session in

## When to use

The learner has finished a session and wants it counted. Sessions are numbered
`chNN`: session 4 is `ch04`.

## The order, and it matters

### 1. Save the notebook

The outputs only reach the file when the learner saves. They are the evidence.
Skip this and they hand in an empty notebook. Ctrl+S, or Cmd+S on a Mac.

### 2. Pull first

```bash
git pull
```

Fixes reach a learner this way. If it stops with a local-changes error, use the
`fix-my-setup` skill before going on.

### 3. Run the check

```bash
uv run bootcamp check ch04
```

Read the output. If it is not green, stop here and switch to the
`check-my-exercise` skill. Submitting a red session wastes the round trip.

### 4. Submit

```bash
uv run bootcamp submit ch04 --github YOUR-LOGIN --push
```

`YOUR-LOGIN` is the GitHub login, the one in the profile URL, not a display
name. `--push` opens the pull request against the submissions repository. The
work never goes to the course repository.

## No GitHub CLI? The browser route

`--push` needs the `gh` CLI. Without it the command says so and stops. The long
way works and needs nothing installed:

1. Drop `--push`:
   ```bash
   uv run bootcamp submit ch04 --github YOUR-LOGIN
   ```
   That writes `submissions/YOUR-LOGIN/ch04/` on disk.
2. Check it:
   ```bash
   uv run python scripts/verify_submission.py submissions/YOUR-LOGIN/ch04
   ```
3. Fork the submissions repository in the browser, once. Press **Fork** on
   <https://github.com/Gecko-Academy/dev3pack-submissions>.
4. Copy that folder into the fork, commit, push, and open a pull request in the
   browser.

In the pull request's *Files changed* tab, every file must start with
`submissions/YOUR-LOGIN/`. Green CI means accepted, and merging is automatic.
Submitting again replaces the earlier attempt.

## Keep spaces out of the path

The course folder has to live somewhere with no spaces in the path.
`~/courses/dev3pack-cohort-2026-09` works. `~/My Documents/dev3pack` breaks
commands in ways whose errors point at the wrong thing. If the learner is in a
path with a space, move the folder and clone again rather than debugging it.

## Never

- Never write or edit a `TODO(you)` cell to make a check go green. The exercise
  is the assessment. Explain the idea, name the page that teaches it, and let
  the learner write it.
- Never open a `solutions/` directory.
- Never commit for the learner without showing them the diff first.
- Never submit on the learner's behalf without them reading the check output.
