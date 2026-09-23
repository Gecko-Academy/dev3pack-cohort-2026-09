---
name: study-a-session
description: Use when a learner wants to understand one bootcamp session before doing its exercise. Reads that session's pages, explains them in plain words, then quizzes the learner a few questions at a time. Never writes the exercise answer.
---

# Study one session

## When to use

A learner says "teach me session 6", "what is session 9 about", or "I have read
the pages and I still do not get it". Use this before the exercise, not instead
of it.

Do not use this to answer a graded cell. That is what the "Never" section below
is for.

## Find the pages

Sessions live in one directory each:

| Sessions | Directory |
|---|---|
| 1 to 5 | `units/en/unit1/session-NN-*/` |
| 6 to 10 | `units/en/unit2/session-NN-*/` |
| 11 to 15 | `units/en/unit3/session-NN-*/` |

`NN` is two digits. Session 6 is `units/en/unit2/session-06-retrieval-baseline/`.

Read the pages in this order, skipping any the session does not have:

1. `introduction.mdx`
2. `concepts-1.mdx`, `concepts-2.mdx`, `concepts-3.mdx`
3. `follow-along.mdx`
4. `quiz.mdx`
5. `conclusion.mdx`

Never open `solutions/`. It is withheld on purpose.

## The steps

1. Ask which session, if the learner did not say.
2. Read every page above. Read them all before you explain anything.
3. Explain one idea at a time, in plain words, about a paragraph each. Use the
   learner's own words back to them. Skip the jargon until you have explained
   the thing it names.
4. After each idea, cite where it came from, like this:
   `units/en/unit2/session-06-retrieval-baseline/concepts-2.mdx`.
5. Stop and quiz. Ask two or three questions, then wait. Do not ask ten at once
   and do not answer them yourself.
6. When the learner answers, say what was right before you say what was missing,
   and name the page that settles it.
7. When the learner is ready, point them at the session's `notebook.ipynb` and
   stop. They write the exercise.

## Citing

Every claim you make about the course comes from a page you read, and you name
that page. If the learner asks something the pages do not cover, say
"not in these pages" and say where you would look instead. Do not fill the gap
from memory: a confident sentence with nothing behind it is the exact failure
this course is about.

## Never

- Never write into a `TODO(you)` cell, and never dictate the code that belongs
  in one. Explain the idea, name the page that teaches it, and let the learner
  write it. That rule is in `AGENTS.md` and it is not negotiable.
- If the learner asks for the answer outright, refuse in one sentence, then ask
  the question that gets them to it.
- Never open a `solutions/` directory.
- Never edit the notebook. Studying does not change files.
