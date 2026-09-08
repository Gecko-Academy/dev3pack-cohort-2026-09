---
marp: true
paginate: true
theme: default
---

# Week 0 · Course B, Chapter 1: Your first MCP server
## MCP: AI apps as easy as 1, 2, 3

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## The problem MCP solves

---

## The big LLM problem

- A model can reason about your data and cannot reach it
- Every integration is bespoke: N models times M tools is N times M adapters
- Each one invents its own auth, its own errors, its own shape
- Nothing tells the model what is available, so it guesses

A model that cannot see what it can do will improvise something that does not exist.

---

## MCP to the rescue

- One protocol between models and capabilities, so the N times M becomes N plus M
- **Dynamic tool discovery**: the client asks, the server answers, the model sees
- Three parts: the **host** (the app), the **client** (its connector), the **server** (the capability)

The host you already use: Claude Code, Cursor, Claude on the web.

---

## Who starts what

| Part | Is | Starts |
|---|---|---|
| Host | the application a person uses | the client |
| Client | one connection, one server | the server, for stdio |
| Server | the tools, resources and prompts | nothing |

The direction matters in lesson 3, where getting it wrong is the commonest failure in the protocol.

---

## The three primitives

- **Tools**: things that *do*. Model-facing, chosen by the model, can have effects
- **Resources**: things that *are*. Read-only context, chosen by the application or the person
- **Prompts**: reusable instruction templates, chosen by the person

This unit builds a tool. Unit 10 adds the other two.

---

## Summary: which primitive

| You want | Use |
|---|---|
| the model to act, or compute something | a tool |
| to hand the model read-only context | a resource |
| a task's instructions written once | a prompt |

**Why this matters on Monday.** Session 1's vocabulary table separates *tool* from *MCP server*: a tool is a bounded capability, a server is a set of them behind a protocol. Session 13 connects your client to a hosted MCP surface and asks it to plan a real transaction.

**Let's practice:** notebook, exercise 1 comes after the next lesson.

---

# Lesson 2
## Your first server

---

## Step 1: the server object

```python
from mcp.server.mcpserver import MCPServer

# One server, one name. The name is what a client shows a person.
mcp = MCPServer("Timezone Converter")
```

Forty lines from here to a running server.

---

## Step 2: a function becomes a tool

```python
@mcp.tool()
def convert_timezone(date_time, from_timezone, to_timezone):
    moment = datetime.fromisoformat(date_time).replace(tzinfo=_zone(from_timezone))
    converted = moment.astimezone(_zone(to_timezone)).isoformat()
    return f"Time in {to_timezone}: {converted}"
```

This works. It is also unusable by anything that has not read the source.

---

## Step 3: the two things that make it usable

```python
@mcp.tool()
def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) -> str:
    """Convert a datetime from one timezone to another.

    Args:
        date_time: the datetime in ISO format, for example 2025-01-20T14:30:00
        from_timezone: the source zone, for example America/New_York
        to_timezone: the target zone, for example Asia/Tokyo

    Returns:
        A line naming the target zone and the converted datetime.
    """
```

---

## Output: what the client received

```
 - convert_timezone: Convert a datetime from one timezone to another.
   Args:
       date_time: the datetime in ISO format, for example 2025-01-20T14:30:00
       from_timezone: the source zone, for example America/New_York
       to_timezone: the target zone, for example Asia/Tokyo
```

The hints became the schema. The docstring became the description. Neither is documentation: both are the wire.

---

## Summary: the contract is the signature

| You wrote | It became | Who reads it |
|---|---|---|
| `date_time: str` | a JSON Schema property | the client, validating |
| the docstring | the tool's description | the model, deciding |
| no hint | no schema | nobody, correctly |

**Why this matters on Monday.** A tool's docstring is its contract, and this is the whole thesis of the layer session 13 uses: the surface already says how to call it correctly, so an agent that guesses is the problem being solved.

**Let's practice:** notebook, exercise 1.

---

# Lesson 3
## Client and server talking

---

## Two transports

| | stdio | Streamable HTTP |
|---|---|---|
| Where | same machine | anywhere |
| Lifetime | the client starts it, it dies with the client | runs on its own |
| Setup | none | a URL, and usually auth |
| Use it for | your own tools, local files | a hosted surface, many clients |

Session 13 connects to a Streamable HTTP surface. This unit uses stdio, because you are the one starting it.

---

## The client: connect and ask

```python
params = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])

async with stdio_client(params) as (reader, writer):
    async with ClientSession(reader, writer) as session:
        await session.initialize()
        response = await session.list_tools()
        return [tool.name for tool in response.tools]
```

`sys.executable` is this interpreter. `SERVER_PATH` is absolute, and that is not a style choice.

---

## Output

```
 - convert_timezone: Convert a datetime from one timezone to another.
tool_names = ['convert_timezone']
```

A stdio server is a child process. The client starts it wherever the client happens to be, so a bare filename is found only by luck.

---

## The call, and the names it wants

```python
listed = await session.list_tools()
schema = listed.tools[0].input_schema
print(sorted(schema["properties"]))

result = await session.call_tool(
    "convert_timezone",
    {
        "date_time": "2025-01-20T14:30:00",
        "from_timezone": "America/New_York",
        "to_timezone": "Asia/Tokyo",
    },
)
```

---

## Output

```
['date_time', 'from_timezone', 'to_timezone']
Time in Asia/Tokyo: 2025-01-21T04:30:00+09:00
```

14:30 in New York is the next morning in Tokyo, fourteen hours ahead in January. The argument names came off the schema, not out of memory.

---

## In a script, and in a notebook

```python
# a script has no event loop until it makes one
asyncio.run(call_mcp_tool("convert_timezone", arguments))

# a notebook already has one running
await call_mcp_tool("convert_timezone", arguments)
```

Same code, one less wrapper. And wrap either in `asyncio.wait_for`: a client that waits forever for a server that will never answer is a hung agent.

---

## Summary: what goes wrong, and what it looks like

| Symptom | Cause |
|---|---|
| the connection closed, no "file not found" | a relative path; the child died before answering |
| a validation error instead of an answer | argument names from memory, not from the schema |
| the notebook hangs | no timeout around the call |
| the model never calls your tool | no docstring, so nothing to decide on |

**Why this matters on Monday.** Session 5 builds the agent loop, where refusal is a first-class outcome. A tool call that fails should say why, not hang.

**Let's practice:** notebook, exercises 2 and 3, then `review("w09")`.

---

## One thing the deck cannot tell you

The deck was recorded against version 1 of the SDK, where the server class was called `FastMCP`:

```python
from mcp.server.fastmcp import FastMCP  # the deck, and most tutorials

mcp = FastMCP("Timezone Converter")

from mcp.server.mcpserver import MCPServer  # version 2, what you just wrote

mcp = MCPServer("Timezone Converter")
```

This unit teaches the second, because it is what `pip install mcp` gives you today, so the code you write here runs outside this repository too. The schema attribute moved with it: `inputSchema` became `input_schema`.

Expect `FastMCP` in almost every MCP tutorial you read. Same object, older name. The protocol did not change; the names did.

---

## Exit ticket + homework

- One thing that works: you started a server and called a tool correctly
- One thing that is unclear: write it down before you close the notebook
- Your next action: reread your docstring and ask whether a model could choose your tool from it alone

**Homework:** add a second tool to your server, `list_zones`, that returns the fixture's zones. Then decide, in one sentence, whether it should have been a resource instead.

**Next:** unit 10, resources and prompts, and a model in the loop.
