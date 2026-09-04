---
marp: true
paginate: true
theme: default
---

# Session 1: Orientation
## From LLM calls to agentic systems

Dev3Pack AI-Engineering Bootcamp · Monday, September 14, 2026

---

## What this bootcamp is

- **3 weeks, 15 sessions, one capstone**: a source-grounded research assistant
- Practice-first: every class ends with something that runs and a check that says so
- The last week connects your assistant to **real external APIs, safely**

Not a survey course. One coherent stack, built and tested by you.

---

## Before the lesson: the preflight cell

Every notebook starts with the same cell. Run it first.

```
✅ Python 3.11 (need >= 3.11)
✅ kernel is the repo .venv
✅ corpus loads (6 documents)
✅ lane = ollama (qwen2.5:7b-instruct at http://localhost:11434/v1)
ready. LIVE is the ollama lane.
```

A ❌ line carries its fix. The notebook continues on `FakeLLM` either way.

---

# Lesson 1
## The smallest possible agent

---

## The vocabulary (pin this)

| Word | Means |
|---|---|
| Model | The probabilistic text engine |
| Prompt | Everything the model sees this call |
| Tool | A bounded capability the app executes |
| Workflow | Fixed steps, no decisions |
| Agent | A **loop** where the model decides |
| MCP server | Tools packaged behind a protocol |
| Coding assistant | An agent whose tools edit code |

---

## One call, nothing around it

```python
from bootcamp_agent.llm import FakeLLM

hello_llm = FakeLLM(
    responses={
        "hello": "Hello! I am a deterministic stand-in for a language model.",
        "agent": "An agent is a loop around a model: perceive, decide, act, observe.",
    },
    default="I have no canned answer for that — a real model would improvise here.",
)

print(hello_llm.complete(system="You are concise.", user="Say hello to the bootcamp"))
```

---

## Output

```
Hello! I am a deterministic stand-in for a language model.
```

- `system`: how to behave. `user`: the task. The return: text.
- This is the boundary every framework wraps.
- The fake answers from a keyword table. Same question, same answer, always.

---

## Summary: the three paths through a fake

| Question contains | Answer |
|---|---|
| `agent` | the `agent` canned line |
| `hello` | the `hello` canned line |
| neither | the `default` |

**Let's practice:** notebook, exercise 2. Three questions, three paths, one check.

---

# Lesson 2
## Where does the model actually run?

---

## The seam

```python
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return the model's text for one system+user exchange."""
        ...
```

`FakeLLM`, `OllamaClient`, `AnthropicClient`, `OpenAICompatibleClient`: one method each.
Application code never knows which one it got.

---

## The lanes

| `BOOTCAMP_PROVIDER` | Runs where | Key | Deterministic | Cost |
|---|---|---|---|---|
| `fake` | your CPU, no model | no | yes | 0 |
| `ollama` | your machine, qwen2.5:7b | no | no | 0 |
| `anthropic` | Anthropic's API | yes | no | per token |
| `openai` | OpenAI or OpenRouter | yes | no | per token |

Swap = one line in `.env`. Zero code changes. `LIVE` is whichever lane you picked.

---

## The same question, twice, on two lanes

```python
question = "Explain in one sentence what an agent is."
runs = {
    "fake": [hello_llm.complete(system="You are concise.", user=question) for _ in range(2)],
    "live": [LIVE.complete(system="You are concise.", user=question) for _ in range(2)],
}
```

---

## Output

```
[fake] same answer twice? True
   An agent is a loop around a model: perceive, decide, act, observe.
   An agent is a loop around a model: perceive, decide, act, observe.
[live] same answer twice? False
   An agent is a program that uses a model to decide which actions to take toward a goal.
   An agent is software that plans, calls tools, and checks results until a task is done.
```

Same question. Two answers. Both fine. Neither testable by string equality.

---

## Summary: what determinism buys you

| Lane | Tests | Cost | Teaches |
|---|---|---|---|
| fake | exact, offline, in CI | 0 | the seam, the loop, the refusal path |
| ollama | tolerant (shape, behaviour) | 0 | what a real model does with your prompt |

That difference is why Week 2 spends a whole session on evaluation.

**Let's practice:** notebook, exercise 4.

---

# Lesson 3
## Your reliability bar

---

## Where the model is probabilistic

- Same question, different phrasing, different answer
- Confident tone is not correct content
- It cannot reliably say "I don't know" unless you **engineer the refusal**

The mental model: **request → context → model → tool → verification**.
You control context, tools, and verification. The model fills one gap.

---

## The capstone, and its bar

A research assistant that:

- answers from a **versioned 6-document corpus**
- **cites** doc ids, verified, not decorative
- **refuses** unsupported questions
- shows its **trace** and its **eval results**

`src/bootcamp_agent/` is its final shape. You rebuild the pieces, week by week.

---

## Three sentences, written today

```python
reliability_bar = {
    "reliable_when": "it cites a corpus document I can open, or plainly says it does not know.",
    "review_when": "the answer would change money, credentials, or anything in production.",
    "never_unreviewed": "rotate a secret or delete a branch on the shared repository.",
}
```

Concrete: a kind of task, a kind of data, a kind of risk. Yours will differ.

**Let's practice:** notebook, exercise 5, then `review("ch01")`.

---

## Recap

| Lesson | One line |
|---|---|
| The smallest agent | `complete(system, user) -> str` is the whole boundary |
| The seam and the lanes | one protocol, four clients, one `.env` line to swap |
| The reliability bar | decide what "good enough" means before the first real answer |

---

## Exit ticket

- One thing that works
- One thing that is unclear
- Your next action

**Homework:** SETUP green, doctor screenshot, and three tasks an assistant may help with but must not complete unreviewed.
