---
name: check-my-exercise
description: Use when a session check fails and the learner wants to know why. Runs the session check, reads the failure out loud, names the page that teaches the missing idea, and asks a question that leads to the fix. Never writes the cell.
---

# Read a failing check

## When to use

The learner ran a check and it did not pass, or they want to know where they
stand before handing in. Sessions are numbered `chNN`: session 4 is `ch04`.

## The steps

1. **Ask them to save the notebook first.** A check reads the file on disk. An
   unsaved cell is not in the file, so the check grades the old version. In
   Jupyter that is Ctrl+S, or Cmd+S on a Mac.
2. Run the check:
   ```bash
   uv run bootcamp check ch04
   ```
3. **Read the output before you say anything.** Name the check that failed,
   quote the line that says why, and translate it into plain words. One
   sentence.
4. Open the learner's cell and say what it does, not what it should do. "Your
   function returns the whole list" is useful. "This is wrong" is not.
5. Find the page that teaches the missing idea. It is in the same session
   directory, usually a `concepts-N.mdx`. Name the file path and the heading.
6. **Ask one question** that the learner can answer and that gets them to the
   fix. Examples: "what should happen when the list is empty?", "where does the
   check say the citation has to appear?". Then wait.
7. When they change the cell, ask them to save and run the check again. Let them
   run it, or run it for them if they ask. Never claim it passed without the
   output in front of you.

## When they are stuck anyway

- `hint(reveal=True)` inside the notebook shows the worked answer. It costs
  marks. Say that before you suggest it.
- `coach("your question")` inside any notebook answers from the course pages,
  offline and free.

## Never

- Never write the `TODO(you)` cell, in whole or in part. Not as a "sketch", not
  as pseudocode the learner can paste, not as "here is how I would do it". If
  the learner asks, refuse in one sentence and ask the next question instead.
  `AGENTS.md` sets this rule: explain the idea, name the page, let them write it.
- Never edit any notebook to make a check pass.
- Never open a `solutions/` directory.
- Never say a command ran unless you ran it and read the output.
