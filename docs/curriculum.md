# Class-by-Class Curriculum

Fifteen weekday sessions of two hours each, **Monday, September 14 – Friday,
October 2, 2026**. October 3 (Saturday) is an optional showcase / office-hours
day. The bootcamp is practice-first: every class contains a short explanation, a
live implementation, a guided lab, and a concrete artifact. Linked external
courses are optional pre-work, never required homework.

## Course promise

By the end, each learner can configure a coding assistant, write assistant-facing
project instructions, call an LLM from Python, request structured outputs, add
tools and retrieval, create a reusable agent skill, trace and evaluate an agent,
and connect an agent to a documented API surface through MCP in a safe
recorded/hosted mode. The final artifact is a small agent that can explain its
sources and failure modes rather than merely produce an impressive demo.

## Teaching rhythm (every class)

| Minutes | Segment | Purpose |
|---:|---|---|
| 0–10 | Retrieval warm-up | Review the previous class; one tiny question or code correction. |
| 10–30 | Concept lesson | One mental model + the minimum vocabulary for the lab. |
| 30–55 | Instructor live coding | Build the smallest working version, narrating decisions and errors. |
| 55–65 | Break | Screens off; environment issues get resolved. |
| 65–105 | Guided lab | Learners implement a variation, in pairs or solo, with checkpoints. |
| 105–115 | Share and debug | Compare approaches; inspect one failure or surprise. |
| 115–120 | Exit ticket | What works, what is unclear, the next action. |

One major new abstraction per class, maximum. An unfinished lab moves to
homework; the lecture never extends into the lab.

## Concept threads

| Thread | Sessions | Guide |
|---|---|---|
| Loop engineering — budgets, stopping conditions, refusal-first design | 5, 8 | [loop-engineering](guides/loop-engineering.md) |
| Graph engineering — retrieval metadata → state graphs → API surface graphs | 6–8, 13 | [graph-engineering](guides/graph-engineering.md) |
| Harness engineering — instructions, evals, traces, CI around the model | 4, 9, 14 | [harness-engineering](guides/harness-engineering.md) |

## Shared capstone thread

Every week contributes to the same capstone: a **source-grounded developer
research assistant** (`src/bootcamp_agent/` is its final shape). It answers
questions about a small versioned corpus, cites its documents, refuses to invent
unsupported facts, and exposes traces and evaluation results.

---

# Week 1 — Foundations and coding-assistant setup (Sep 14–18)

**Weekly outcome:** a reproducible uv-managed repository, one configured coding
assistant, safe LLM calls from Python, and a small tool-using assistant with
typed output.

### Session 1 — Orientation: from LLM calls to agentic systems (Mon Sep 14)

- **Objectives.** Distinguish model / prompt / tool / workflow / agent / MCP
  server / coding assistant. Describe the capstone. Identify where an LLM is
  probabilistic and why evaluation and human review are necessary.
- **Flow.** Baseline exercise: use your current assistant to explain a small
  repository and record where its answer is uncertain. Teach the
  request–context–model–tool–verification mental model. Show the capstone
  roadmap and this repository's layout.
- **Lab.** A minimal `hello_agent` call through the `FakeLLM` (no framework, no
  key) so the request/response boundary is visible.
- **Artifact.** Working environment, a baseline call, and a written definition of
  "reliable enough for this bootcamp."
- **Homework.** Finish `SETUP.md`; write three developer tasks an assistant could
  help with but must not complete without review.

### Session 2 — Python for AI engineers (Tue Sep 15)

- **Objectives.** uv workflows; typed functions; dataclasses; exceptions; file
  I/O and JSON; separating package code from a script entry point.
- **Flow.** Short diagnostic; teach only the language features the capstone uses.
  Walk `config.py` / `llm.py` / `cli.py` as the worked example of a typed
  package with a provider seam.
- **Lab.** Implement a `Document` structure and a Markdown loader with validation
  for missing files and malformed headers; compare with
  `bootcamp_agent.documents`. Ask an assistant to propose tests; review and
  correct them.
- **Artifact.** A typed loader with tests for at least two failure cases.
- **Homework.** Add three tests and a short CONTRIBUTING note on running locally.

### Session 3 — Prompts and structured outputs (Wed Sep 16)

- **Objectives.** Separate system instructions from user input and retrieved
  context; write prompts with explicit constraints; request and strictly
  validate structured output; handle refusal and parse failure.
- **Flow.** Compare an unconstrained answer with a typed one. Prompt templates,
  output schemas, and "parsing is an application responsibility." Walk the
  `ResearchAnswer` schema (`answer`, `citations`, `confidence`,
  `needs_human_review`) and its strict parser.
- **Lab.** Convert the assistant into a document-questioning function; author
  three test questions: answerable, ambiguous, unsupported. The assistant must
  say it does not know when the corpus lacks evidence.
- **Artifact.** A structured-output call with validation and a small golden set.
- **Homework.** Add two adversarial questions; compare unstructured vs structured
  behavior.

### Session 4 — Claude Code 101 and assistant configuration (Thu Sep 17)

*Thread: harness engineering.*

- **Objectives.** Configure a coding assistant for a repository; write durable
  project instructions; use the inspect–plan–edit–test–review loop; distinguish
  convenience from permission. Explain `CLAUDE.md` vs `AGENTS.md` vs Cursor
  rules.
- **Flow.** Demonstrate a weak prompt vs a project-aware prompt. Walk this
  repository's own `AGENTS.md` (architecture, commands, style, testing, "do
  not" constraints) and how one policy serves three assistants without
  duplication.
- **Lab.** Ask an assistant to add a feature to the document loader: request a
  plan first, inspect the diff, run tests, and **reject at least one unsafe or
  unnecessary change**.
- **Artifact.** Configuration files, a reviewed feature commit, a short
  assistant-use policy.
- **Homework.** Improve the project instructions after observing one wrong
  assumption the assistant made.

### Session 5 — Tools: controlled capabilities (Fri Sep 18)

*Thread: loop engineering.*

- **Objectives.** Define a tool with a narrow input/output contract; validate
  arguments at the boundary; separate planning from execution; prevent silent
  side effects.
- **Flow.** Tool schemas, tool selection, idempotence, permissions, human
  approval. Walk `tools.py`: `search_documents` (capped results),
  `get_document_metadata` (helpful unknown-id error), `summarize_document`.
  Show the loop in `agent.py` choosing between answering and calling a tool,
  logging every decision.
- **Lab.** Add a third tool variant with a maximum-result limit, an explicit
  error message, and a test showing invalid arguments are rejected.
- **Artifact.** A tool-using assistant with three read-only tools and boundary
  tests.
- **Homework.** Record one example where the assistant should NOT use a tool and
  one where it should ask for confirmation.

---

# Week 2 — Retrieval, agent architecture, reliability, skills (Sep 21–25)

**Weekly outcome:** answers grounded in a corpus with citations, an articulated
choice of agent pattern, inspectable traces, a working evaluation, and one
reusable skill.

### Session 6 — RAG fundamentals (Mon Sep 21)

*Thread: graph engineering.*

- **Objectives.** Explain chunking, indexing, retrieval, and generation; tell a
  retrieval failure from a generation failure.
- **Flow.** Start from a keyword baseline (`retrieval.py` — deterministic,
  inspectable); why retrieval quality beats a bigger prompt; where an embedding
  index would slot in and what it costs.
- **Lab.** Ingest the six-document corpus, retrieve top-k with metadata, generate
  an answer with citations; build a failure table (missed / irrelevant /
  duplicated context).
- **Artifact.** A local RAG pipeline with inspectable retrieved context.
- **Homework.** Change chunk size or top-k; document one improvement AND one
  regression.

### Session 7 — Retrieval quality and query optimization (Tue Sep 22)

- **Objectives.** Metadata filters, query rewriting, reranking as a concept;
  measure retrieval with a small labeled set; latency/cost trade-offs.
- **Flow.** Precision, recall, hit rate, context size as practical metrics;
  pre- vs post-filtering; fewer better passages beat more context. Implement an
  evaluation comparing expected vs retrieved doc ids.
- **Lab.** Five labeled questions; baseline measurement; one change (filtering or
  query expansion); report the delta honestly.
- **Artifact.** A retrieval evaluation report with no hidden regressions.
- **Homework.** Add three cases including one whose correct answer is "not found."

### Session 8 — Agentic design patterns (Wed Sep 23)

*Threads: loop + graph engineering.*

- **Objectives.** Fixed workflow vs agent loop; tool use, reflection, planning,
  multi-agent; choose the least autonomous pattern that solves the problem.
- **Flow.** The same task three ways: deterministic chain, tool-using loop,
  reflection step. Degrees of autonomy, stopping conditions, budgets. State
  graphs as the way to make transitions explicit (LangGraph conceptually; a
  small hand-rolled state machine in practice).
- **Lab.** Add draft → critique → revise with a **maximum of one revision**;
  compare quality and latency against the direct answer; decide if it is
  justified.
- **Artifact.** A workflow diagram, implementation, and comparison table.
- **Homework.** One-page design note: where should autonomy stop in the capstone?

### Session 9 — Reliability: tracing, evaluation, error analysis (Thu Sep 24)

*Thread: harness engineering.*

- **Objectives.** Define an evaluation set; code-based vs LLM-as-judge checks;
  trace a run; classify failures; pick the next improvement by evidence.
- **Flow.** The lifecycle: baseline → trace → inspect → evaluate → change ONE
  component → rerun. Walk `evals.py` and the golden set; failure buckets:
  retrieval, tool selection, instruction-following, formatting, unsupported
  claims.
- **Lab.** Run ten cases, label the failures, implement one targeted fix, inspect
  the evaluator itself for false positives.
- **Artifact.** A reproducible evaluation command, a results file, an
  error-analysis note.
- **Homework.** A regression test for the fixed failure, with a sentence on why
  it would catch the regression.

### Session 10 — Agent skills, MCP, and subagents (Fri Sep 25)

- **Objectives.** What a skill is; `SKILL.md` with progressive disclosure; skill
  vs tool vs MCP server; when a subagent is justified.
- **Flow.** Inspect a simple skill folder. Create a skill for "answer questions
  from the bootcamp corpus with citations": purpose, when-to-use, inputs,
  workflow, output format, failure rules. Show on-demand loading vs
  every-prompt insertion. Short MCP bridge to next week.
- **Lab.** A second skill (code review or test generation); run before/after,
  compare, improve the instructions from observed failures.
- **Artifact.** One custom skill with a test scenario, before/after evidence, and
  a safety boundary.
- **Homework.** Review another learner's skill for ambiguity, hidden assumptions,
  or unsafe permissions.

---

# Week 3 — Production thinking, Gecko, capstone delivery (Sep 28 – Oct 2)

**Weekly outcome:** an integrated, hardened capstone; a verified external MCP
connection in safe mode; evidence-based demos.

### Session 11 — Memory and long-running agents (Mon Sep 28)

- **Objectives.** Conversation state vs long-term memory; semantic / episodic /
  procedural memory; what to store, how to correct it, when it expires; privacy
  and staleness risks.
- **Flow.** Extend the capstone with short-lived conversation state; a memory
  decision framework; a tiny preference store with nothing sensitive in it.
- **Lab.** Add one non-sensitive preference and one episodic example; test
  before/after; add a reset command; document the storage policy.
- **Artifact.** A stateful assistant with explicit memory policy, reset, tests.
- **Homework.** A "what we refuse to remember" section for the project README.

### Session 12 — Capstone build sprint I (Tue Sep 29)

**Milestone: the complete project exists before Gecko enters.**

- **Objectives.** Integrate retrieval, tools, structured output, skills, and a
  bounded loop while keeping components independently testable.
- **Flow.** Integration checklist + reference architecture; instructor performs a
  short end-to-end build and intentionally breaks one component. Three
  checkpoints: answer one supported question; reject one unsupported question;
  produce a trace.
- **Lab.** Build capstone v1: citations required, a maximum tool-call budget, a
  clear human-review flag.
- **Artifact.** End-to-end capstone v1 + an issue list ranked by impact.
- **Homework.** Finish the happy path; prepare a five-case smoke-test transcript.

### Session 13 — Orquestra + Gecko: verified API interaction (Wed Sep 30)

*Thread: graph engineering. The course's external-integration payoff.*

- **Objectives.** Explain MCP practically; browse a catalogue of real programs;
  inspect a comprehension graph and its provenance; run a full verified loop on
  a fork; explain why the naive alternative guesses.
- **Flow.** Students connect their MCP client (Claude Code / Cursor) to the
  **instructor-hosted Gecko MCP surface backed by a surfpool fork**
  (`<HOSTED_GECKO_MCP_URL>` — provided in class). The lab follows the order the
  surface itself enforces:
  1. **Browse** — `list_stores` / `find_start`: route a plain-English intent to
     the right starting instruction of a real Solana program from the Orquestra
     catalogue.
  2. **Comprehend** — `comprehend_program`: inspect the instruction↔PDA graph,
     provenance tiers, and what "callable" actually requires.
  3. **Compare** — ask a naive assistant the same "how do I call this?"
     question; watch it invent. The whole course thesis in one contrast.
  4. **Full loop** — `prepare_purchase` → `try_purchase` on the fork: throwaway
     key, funded by cheatcode, judged by **what actually moved**. Read the
     receipt.
  5. **Safety framing** — why the signing key cannot exist unless the endpoint
     proves it is a fork; recorded vs live modes; spec/prompt poisoning and why
     credentials stay outside assistant configuration.
- **Lab.** The five steps above, plus a comparison transcript (Gecko-guided vs
  naive) and a completed safety checklist.
- **Artifact.** A working MCP configuration, an inspected comprehension graph, a
  receipt from the fork, the comparison transcript, the checklist.
- **Safety boundary.** No wallet, no payment credential, no production key, no
  mainnet path — structurally impossible on the hosted fork surface, and that
  impossibility is itself the lesson.
- **Homework.** Add an "external tools" section to your project instructions:
  allowed hosts, data handling, approval requirements.

### Session 14 — Capstone build sprint II: hardening (Thu Oct 1)

*Thread: harness engineering.*

- **Objectives.** Regression tests, timeouts and budgets, tool-error handling,
  instruction-injection defense in retrieved content, measurable evidence.
- **Flow.** Failure clinic with four injected problems: missing document,
  malformed tool arguments, retrieved text containing an embedded instruction,
  simulated timeout. Patch one at a time; rerun the evaluation set each time.
- **Lab.** Hardening checklist: deterministic tests, unsupported-question
  behavior, tool-error behavior, bounded loops, a prompt-injection test, a
  secret scan, before/after evaluation results.
- **Artifact.** Capstone v2, regression suite, security notes, a two-minute demo
  script.
- **Homework.** Rehearse the demo; prepare one honest limitation to share.

### Session 15 — Demo day (Fri Oct 2)

- **Format (six minutes per learner).** 1 min problem/context · 2 min demo ·
  1 min architecture + assistant configuration · 1 min evaluation evidence ·
  1 min limitation + next step.
- **Demo requirements.** Answer one supported question with citations; reject or
  qualify one unsupported question; show one tool or retrieval trace; include a
  reusable skill or instruction file; report one measured quality or
  reliability result.
- **Final grading + certificate.** Each learner's `final_assignment/` agent is
  graded on the instructor's private question set (pass bar 70%); a passing
  score plus a completed demo earns the instructor-signed certificate. See
  `final_assignment/README.md`.
- **Closing.** Retrospective and an individual next-step roadmap (long-term
  memory, knowledge graphs, deeper LangGraph, production deployment).

### Optional — Saturday Oct 3

Non-required showcase and office hours: unfinished projects, peer review,
advanced-path discussion.

---

## Assessment model

Grade evidence of engineering practice, not chat-interface polish.

| Area | Weight | Evidence |
|---|---:|---|
| Environment and assistant workflow | 15% | Reproducible setup, project instructions, reviewed diffs, safe task loop |
| Python and application foundations | 15% | Typed code, configuration, error handling, tests |
| Grounding and tool use | 20% | Retrieval/tool contracts, citations, unsupported-question behavior, boundary tests |
| Reliability and evaluation | 20% | Evaluation set, traces, error analysis, regression test, measured change |
| Skills/MCP integration | 15% | Reusable skill, safe-mode MCP connection, provenance inspection, safety checklist |
| Capstone explanation | 15% | Clear demo, architecture, limitation, next-step reasoning |

Per-area descriptors: [instructor/assessment-rubric.md](instructor/assessment-rubric.md).

## Deliberately out of the core schedule

Semantic caching, long-term memory implementations, knowledge-graph
construction, multi-agent orchestration, and any live Solana interaction. These
are valuable follow-ups — offered as pointers on demo day — but they would
compete with configuration, testing, retrieval, tools, and reliability.

## Optional external references

DataCamp (AI Engineering with LangChain; Python Programming Fundamentals;
Associate AI Engineer for Developers), LangChain Academy (Introduction to
LangChain; Building Reliable Agents; Deep Agents), DeepLearning.AI (Agentic AI;
Agent Skills with Anthropic; RAG; Prompt Compression and Query Optimization;
Semantic Caching; Long-Term Agentic Memory; Agentic Knowledge Graph
Construction), Anthropic Skilljar Academy, and the
[Gecko Surf repository](https://github.com/GeckoVision/gecko-surf) with its
`use-any-api` and `anti-poisoning` skills.
