# Unit 9: Your first MCP server

**Self-paced · about 60 minutes · Course B, chapter 1 of 3**

## Learning objectives

- Name the three parts of an MCP connection, and say which one starts which.
- Write a tool whose type hints become its schema and whose docstring becomes its description.
- Connect a client to a server over stdio, list its tools, and call one with the argument names the schema declares.

## Lessons

| Lesson | What you leave with |
|---|---|
| 1. The problem MCP solves | Host, client and server, and the three primitives: tools, resources, prompts |
| 2. Your first server | `MCPServer`, `@mcp.tool()`, and why the hints and the docstring are the contract |
| 3. Client and server talking | stdio against Streamable HTTP, `ClientSession`, `list_tools`, `call_tool` |

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped and gives a wrong or incomplete
answer (marked `<------ EDIT THIS LINE`), the expected output, and a
`check(...)` cell that prints ✅ or ❌ with the fix named. The last cell,
`review("w09")`, is the scorecard.

The checks here judge behaviour, not text. Two of the three do not read your
answer at all: they start your server as a child process, ask it the same
question any client would, and end the process tree. The third parses your
server file, because type hints and a docstring are the two things a client
cannot see at runtime.

Working with a coding assistant: give it the exercise's context and
instructions, let it edit the marked lines, then run the check cell yourself.
You read the verdict, not the assistant. `solutions/notebook.ipynb` is the
reference; open it after the check, not before.

## Offline, and honest about it

The deck calls a public timezone API with `requests`. This unit computes the
conversion locally, from `zoneinfo` and `fixtures/timezones.json`: twelve zones
with their January offset, recorded on 2026-09-07. The protocol you exercise is
the real one. Only the arithmetic behind the tool is local, and the fixture says
what it is and is not evidence of.

Seven of those twelve zones move an hour in summer. The recorded table does not
know that, which is why every example in this unit is a January date.

## One thing the deck cannot tell you

The deck was recorded against version 1 of the Python SDK, where the server
class was called `FastMCP`. Version 2 renamed it to `MCPServer`, and renamed
the schema attribute from `inputSchema` to `input_schema`. This unit teaches
version 2, because that is what `pip install mcp` gives you today, so the code
you write here runs outside this repository too.

You will still meet `FastMCP` in almost every MCP tutorial, the source deck
included. It is the same object with its old name, and the
[migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/) lists
the rest. The protocol did not change. The names did.

## Slides

`slides.md` is a [Marp](https://marp.app) deck. Read it as Markdown, or render it:

```bash
npx @marp-team/marp-cli slides.md -o slides.pdf
```
