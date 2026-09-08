# Unit 10: Resources, prompts, and the LLM

**Self-paced · about 60 minutes · Course B, chapter 2 of 3**

## Learning objectives

- Serve a resource, and say why read-only context is not a tool.
- Serve a prompt, and keep its name and its title straight.
- Write the five steps of a tool call, including the one that gets left out.
- Answer an unanswerable request with a question instead of a number.

## Lessons

| Lesson | What you leave with |
|---|---|
| 1. Resources in MCP servers | `@mcp.resource(uri)`, `list_resources`, `read_resource`, and one thing per line |
| 2. Prompts in MCP servers | `@mcp.prompt(title=...)`, and the name the client asks for |
| 3. MCP and LLMs: tools | The five-step workflow, and the trace that shows step four missing |
| 4. MCP and LLMs: prompts and resources | The ambiguous request, and clarification as an answer |

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped and gives a wrong or incomplete
answer (marked `<------ EDIT THIS LINE`), the expected output, and a
`check(...)` cell that prints ✅ or ❌ with the fix named. The last cell,
`review("w10")`, is the scorecard.

The checks judge behaviour. The resource is compared as the client received it,
not as your source reads. The prompt check refuses a name equal to its title,
which is the deck's own trap. The loop check reads the trace and then the answer,
because a five-step trace with the wrong answer is the case worth catching. The
last check refuses any clock time at all: a converted time for "what time is it
in Canada?" is a guess with a decimal point on it.

Working with a coding assistant: give it the exercise's context and
instructions, let it edit the marked lines, then run the check cell yourself.
You read the verdict, not the assistant. `solutions/notebook.ipynb` is the
reference; open it after the check, not before.

## Offline, and honest about it

The deck calls Claude through the Anthropic Messages API. That needs a key, and
a model's choice is not reproducible, so this unit does two things instead.

The **seam** is real: `FakeLLM` in `src/bootcamp_agent/llm.py` takes the same
`complete(system, user)` call every provider adapter in this repo takes. Set
`BOOTCAMP_PROVIDER` (see `SETUP.md`) and `get_client(...)` returns Anthropic,
OpenAI, OpenRouter or a local Ollama instead. The loop does not change.

The **decision** is a router you can read: two places named means convert, a
country with several zones means ask. That is the one thing a model would do
that a fake cannot, so it is written out as rules rather than mocked. When you
swap a real model in, the router is what it replaces.

The server, the client, the protocol and the conversion are the real thing. The
conversion reads `unit-09-mcp-first-server/fixtures/timezones.json`, twelve
zones with their January offset, which is why every example here is a January
date. Seven of those zones move an hour in summer and the table does not know it.

## What unit 9 already covered

The `FastMCP` to `MCPServer` rename, and why this repository teaches the second
name: see unit 9's README and the last slide of its deck. This unit uses
`MCPServer` throughout and does not repeat the explanation.

One thing did change between the SDK versions in this chapter's material: the
deck lists the locations resource as `file://locations.txt/`, with a trailing
slash. Version 2 lists it as `file://locations.txt`. Read the URI off
`list_resources` rather than typing it from the slide.

## Slides

`slides.md` is a [Marp](https://marp.app) deck. Read it as Markdown, or render it:

```bash
npx @marp-team/marp-cli slides.md -o slides.pdf
```
