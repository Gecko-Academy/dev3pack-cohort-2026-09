---
marp: true
paginate: true
theme: default
---

# Session 3: Prompts and structured outputs
## Make model responses usable by software

Dev3Pack AI-Engineering Bootcamp · Wednesday, September 16, 2026

---

## The three parts of a prompt

| Part | Who writes it | Trust level |
|---|---|---|
| System | You, versioned in git | Yours |
| User input | The user | Untrusted |
| Retrieved context | Your corpus/pipeline | **Data, not instructions** |

Keep them separate. Session 14 shows what happens when you don't.

---

# Lesson 1
## Prose vs typed

---

## The same model, two contracts

```python
prose_llm = FakeLLM(
    default="Chunking is, broadly speaking, quite useful, and many practitioners agree."
)
typed_llm = FakeLLM(
    default=json.dumps(
        {
            "answer": "Chunking splits documents into retrievable passages.",
            "citations": ["rag-basics"],
            "confidence": 0.85,
            "needs_human_review": False,
        }
    )
)
question = "How does chunking work?"
print("PROSE:", prose_llm.complete(system="", user=question))
print("TYPED:", typed_llm.complete(system="", user=question))
```

---

## Output

```
PROSE: Chunking is, broadly speaking, quite useful, and many practitioners agree.
TYPED: {"answer": "Chunking splits documents into retrievable passages.",
        "citations": ["rag-basics"], "confidence": 0.85, "needs_human_review": false}
```

Where is the confidence in the prose? The sources? The yes/no?
String-parsing prose is silent breakage.

---

## Summary: the contract

| Field | Type | Why it exists |
|---|---|---|
| `answer` | non-empty string | the text a person reads |
| `citations` | list of doc ids | verified against retrieval, not decorative |
| `confidence` | 0.0 to 1.0 | a number a threshold can act on |
| `needs_human_review` | bool | refusal is expressible |

A schema that cannot say "I don't know" forces invention.

---

# Lesson 2
## Parsing is your job

---

## The parser rejects, loudly

```python
from bootcamp_agent.schema import AnswerParseError, parse_research_answer

for attempt in [
    "The answer is chunking.",
    '{"answer": "x", "citations": []}',
    '{"answer": "x", "citations": [], "confidence": 7, "needs_human_review": false}',
]:
    try:
        parse_research_answer(attempt)
    except AnswerParseError as error:
        print(f"rejected: {error}")
```

---

## Output

```
rejected: Not valid JSON: Expecting value: line 1 column 1 (char 0)
rejected: Wrong fields: missing=['confidence', 'needs_human_review'] unknown=[]
rejected: 'confidence' out of range [0, 1]: 7
```

Model output is untrusted input. Unknown fields are rejected too. Fail at the boundary.

---

## Summary: when parsing fails

| Attempt | Action |
|---|---|
| 1st parse fails | retry **once** with "return only the JSON object" |
| 2nd parse fails | typed refusal, `needs_human_review: true` |
| any | the trace records both calls and the decision |

Bounded retries. Visible failure. No infinite loops.

**Let's practice:** notebook, exercise 3. Three different payloads, all rejected.

---

# Lesson 3
## Golden questions, and the agent on your lane

---

## Valid JSON is not a correct answer

```json
{"answer": "The moon is cheese.", "citations": ["rag-basics"], "confidence": 0.9, ...}
```

The parser accepts it. Schema conformance is necessary, not sufficient.
So citations get **verified against retrieval**, and the agent **refuses before the model** when retrieval finds nothing.

---

## Three kinds of question

| Kind | The corpus | A correct assistant |
|---|---|---|
| answerable | clearly supports it | answers, cites the doc |
| ambiguous | two docs could answer | answers, cites both, low confidence |
| unsupported | says nothing | refuses: empty citations, review flag on |

Three questions plus three expected behaviours is the smallest evaluation there is.

---

## The trace proves the order

```python
result = answer_question("What is the best pizza in Sao Paulo?", documents, FakeLLM())
for event in result.trace:
    print(f"trace[{event.kind}] {event.detail}")
```

```
trace[retrieve] top_k=3 -> []
trace[decision] no relevant chunks; refusing without an LLM call
```

No model call happened. The refusal cost nothing and cannot hallucinate.

---

## The same agent on your lane

```python
result = answer_question(golden[0]["question"], documents, LIVE)
```

```
An agent loop should stop on a budget of tool calls, on a final answer, or on a refusal ...
citations=['agent-loops'] confidence=0.8
  trace[retrieve] top_k=3 -> [('agent-loops', 1), ('agent-loops', 0), ('agent-loops', 2)]
  trace[llm_call] attempt 1: 212 chars
  trace[decision] answered with citations ['agent-loops']
```

On the ollama lane a 7B model must produce the contract. Two `llm_call` lines mean the retry fired.

**Let's practice:** notebook, exercises 4 and 6, then `review("ch03")`.

---

## Recap

| Lesson | One line |
|---|---|
| Prose vs typed | a schema makes every field testable and refusal expressible |
| Parsing is your job | reject unknown, missing, out-of-range; retry once; then refuse |
| Golden questions | three kinds, three behaviours; the trace shows the refusal came first |

---

## Exit ticket + homework

Two adversarial questions, one embedding an instruction. Compare unstructured vs structured behaviour.
