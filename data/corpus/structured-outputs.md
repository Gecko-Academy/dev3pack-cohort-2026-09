<!-- title: Structured Outputs -->
<!-- tags: llm, json, validation, schema -->

# Structured Outputs

A language model produces text. Software needs data. Structured outputs are the
contract between the two: instead of asking a model to "answer the question," you
ask it to return a specific shape — usually JSON with named fields — and your
application validates that shape before using it.

## Why free text is not enough

An unconstrained answer cannot be safely consumed by code. If the model answers a
question about API authentication with three paragraphs of prose, a program that
needs the confidence level, the cited sources, or a yes/no flag has to guess where
those live. Guessing with string manipulation is brittle; a slightly different
phrasing breaks the parser. The failure is silent, which is the worst kind.

## The schema is a promise, parsing is your job

A schema like the following turns the answer into a checkable artifact:

```json
{
  "answer": "string",
  "citations": ["doc-id"],
  "confidence": 0.0,
  "needs_human_review": false
}
```

Two rules keep this honest. First, the application — not the model — is responsible
for parsing and validation. Treat the model's output as untrusted input: parse it
strictly, reject unknown fields, and fail loudly on malformed JSON. Second, design
the schema so that refusal is expressible. A model that cannot say "I don't know"
inside the schema will be pushed toward inventing an answer that fits.

## Handling failure

Parsing can fail even with a good prompt. A robust pattern is: attempt to parse;
on failure, retry once with a corrective instruction ("return only the JSON
object, no prose"); on a second failure, return a typed refusal with
`needs_human_review` set to true. This keeps the failure visible and bounded
instead of letting malformed output leak into downstream code.

## What to remember

Structured output is not about making the model smarter. It is about making the
boundary between probabilistic text and deterministic software explicit,
validated, and testable. Every field you add to a schema is a claim you can now
write a test against.
