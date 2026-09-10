---
marp: true
paginate: true
theme: default
---

# Week 0 · Course B, Chapter 2: Resources, prompts, and the LLM
## MCP: AI apps as easy as 1, 2, 3

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## Resources in MCP servers

---

## What a resource is

- **Read-only data**, fetched by the MCP client
- Not necessarily called by an LLM, and that is the point
- **Application-driven**: user preferences, a config, a supported-values list
- **User-driven**: a file somebody uploaded

A tool is something the model decides to do. A resource is something that is already true.

---

## A URI, not a function name

```python
@mcp.resource("file://locations.txt")
def get_locations() -> str:
    """Every timezone this server can convert, one per line."""
    return "\n".join(sorted(ZONES))
```

The URI is the address. It can point at a local file, an API, a remote server, and it can carry a
parameter, like a user id. The function name is not how anybody reaches it.

---

## Listing and reading, from the client

```python
listed = await session.list_resources()
print([str(item.uri) for item in listed.resources])

read = await session.read_resource("file://locations.txt")
print(read.contents[0].text)
```

---

## Output

```
['file://locations.txt']
Africa/Abidjan
America/Halifax
America/New_York
...
Europe/Paris
```

The deck's SDK listed this as `file://locations.txt/`, with a trailing slash. Version 2 does
not add one. Read the URI off `list_resources` instead of typing it from a slide.

---

## One per line, and why it is not a style question

A resource is context, and context is read by something else. Twelve zones on twelve lines split
on a newline. The same twelve joined by commas is one string that every reader has to take apart
first, and one of them will take it apart wrongly.

The deck's server opens `locations.txt` and returns a `FileNotFoundError` message on failure.
That is the same shape: the caller gets text either way, and the text says what happened.

---

## Summary: tool or resource

| The data is | Use | Because |
|---|---|---|
| dynamic, depends on the arguments | a tool | the model has to choose the arguments |
| a write, or has an effect | a tool | effects are decisions |
| static reference, the same for everyone | a resource | nothing about reading it is a decision |
| guidelines, policies, supported values | a resource | it is context, not an action |

**Why this matters on Monday.** Session 5 separates a capability from a fact. A resource is how you hand an agent a fact without giving it another thing it can do, and the smaller the set of things it can do, the less there is to get wrong.

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## Prompts in MCP servers

---

## What a prompt is

- A **reusable instruction template** for one task
- Written once, on the server, so every client gets the same rules
- Chosen by the person, not by the model
- Takes the load off the person, who otherwise retypes the rules every time

---

## The template the deck writes

```
You are a timezone conversion engine.

Your task is to:
1. Extract the source datetime from the user's natural language input.
2. Identify the source timezone, explicit or inferred.
3. Convert the datetime into the target timezone.

Rules:
- If the date is ambiguous, resolve it against the provided datetime.
- If the input cannot be resolved confidently, seek clarification.
```

The last rule is the one lesson 4 turns on.

---

## Serving it

```python
@mcp.prompt(title="Timezone Conversion")
def convert_timezone_prompt(timezone_request: str) -> str:
    """The timezone conversion task, its rules, and the person's request."""
    return f"""You are a timezone conversion engine.
...
User's timezone conversion request: {timezone_request}"""
```

The argument is interpolated at the end, so what the model reads contains what the person asked.

---

## The trap: the name is not the title

```python
listed = await session.list_prompts()
print([item.name for item in listed.prompts])
print([item.title for item in listed.prompts])
```

---

## Output

```
['convert_timezone_prompt']
['Timezone Conversion']
```

The **title** went to the decorator, for a person to read in a client's menu. The **name** is the
decorated function's name, and the name is what `get_prompt` wants. Asking for the title gets
`Unknown prompt: Timezone Conversion`.

---

## Rendering it

```python
rendered = await session.get_prompt(
    "convert_timezone_prompt",
    arguments={
        "timezone_request": "It is 9:50 AM in the UK in January. What time is it in Lisbon, Portugal?"
    },
)
print(rendered.messages[0].content.text)
```

---

## Output

```
You are a timezone conversion engine.

Your task is to:
1. Extract the source datetime from the user's natural language input.
...
User's timezone conversion request: It is 9:50 AM in the UK in January. What time is it in
Lisbon, Portugal?
```

---

## Summary: which name, and who reads it

| The thing | Where it comes from | Who reads it |
|---|---|---|
| the prompt's **name** | the decorated function's name | the client, calling `get_prompt` |
| the prompt's **title** | `@mcp.prompt(title=...)` | a person, choosing from a menu |
| the **description** | the function's docstring | a person, or a model deciding |
| the rendered text | the return value, argument filled in | the model |

**Why this matters on Monday.** Session 10 packages a skill, and a skill is this: an instruction template plus a note on when to use it. Serving one over MCP and shipping one as a skill are the same discipline in two formats.

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## MCP and LLMs: tools

---

## MCP tools are not LLM tools

- Tool and model integration is model-specific: every provider takes tools in its own shape
- MCP gives you one schema; each provider wants that schema in its own field
- The deck uses Claude, through Anthropic's Messages API

```python
anthropic_tools = [
    {"name": tool.name, "description": tool.description or "", "input_schema": tool.input_schema}
    for tool in mcp_tools
]
```

One rename to watch: version 1 of the SDK called that attribute `inputSchema`.

---

## The deck's call, for reference

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key="<ANTHROPIC_API_TOKEN>")
response = await client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": user_query}],
    tools=anthropic_tools,
)
```

This is the source. It needs a key, and its answer is different every run.

---

## The same seam, offline

```python
from bootcamp_agent.llm import FakeLLM

LLM = FakeLLM()


def model(message, locations, system=""):
    LLM.responses = {message: decide(message, locations)}
    return LLM.complete(system=system, user=message)
```

`complete(system, user)` is the signature every adapter in this repo takes. Set
`BOOTCAMP_PROVIDER` (`SETUP.md`) and `get_client(...)` returns Anthropic, OpenAI, OpenRouter or a
local Ollama instead. `decide` is the one thing a fake cannot do, so the notebook writes it out
as rules: two places named means convert, a country with several zones means ask.

---

## The five steps

| # | Step | Who acts |
|---|---|---|
| 1 | the query and the tool schemas go to the model | you |
| 2 | the model answers with a tool call | the model |
| 3 | the tool runs, over MCP | you |
| 4 | **the result goes back to the model** | you |
| 5 | the model writes the answer | the model |

Step 4 is the one that gets left out, and leaving it out is quiet.

---

## Step 2: the model chose a tool

```python
if response.stop_reason == "tool_use":
    tool_use = next(block for block in response.content if block.type == "tool_use")
    result = await call_mcp_tool(tool_use.name, tool_use.input)
```

---

## Output

```
Model decided to call: convert_timezone
Arguments: {'date_time': '2025-01-20T09:50:00', 'from_timezone': 'Europe/London', 'to_timezone': 'Europe/Lisbon'}
Time in Europe/Lisbon: 2025-01-20T09:50:00+00:00
```

9:50 in London is 9:50 in Lisbon. They share an offset in January, and the deck picks that pair
on purpose: an answer that looks like nothing happened is still the right answer.

---

## Steps 4 and 5: the result goes back

```python
tool_result = {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
followup = await client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": response.content},
        {"role": "user", "content": [tool_result]},
    ],
    tools=anthropic_tools,
)
```

Three messages, and the third is the whole reason there is a second call.

---

## Output

```
Assistant: It's 9:50 AM in Lisbon as well.
```

Send the query alone and the model calls the tool again, because from where it sits nothing has
happened yet. That failure is a working loop with a useless answer.

---

## Summary: reading a trace

| The trace shows | It means |
|---|---|
| one `llm` step | step 4 is missing; the model never saw the result |
| `tool_use` with no `tool_result` | the call failed, or nobody ran it |
| a `tool_result` and a final answer that ignores it | the follow-up message dropped it |
| five steps and the right answer | the loop is closed |

**Why this matters on Monday.** Session 9 is tracing and error analysis. A trace is not logging: it is the record that tells you which of five steps went wrong, and the answer on its own never tells you that.

**Let's practice:** notebook, exercise 3.

---

# Lesson 4
## MCP and LLMs: prompts and resources

---

## All three primitives, one server

```python
@mcp.tool()
def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) -> str: ...


@mcp.resource("file://locations.txt")
def get_locations() -> str: ...


@mcp.prompt(title="Timezone Conversion")
def convert_timezone_prompt(timezone_request: str) -> str: ...
```

The tool acts. The resource is the read-only context. The prompt is the instructions.

---

## Fetching the context before the call

```python
resource_text = (await session.read_resource("file://locations.txt")).contents[0].text
prompt_result = await session.get_prompt(
    "convert_timezone_prompt", arguments={"timezone_request": user_query}
)
prompt_text = prompt_result.messages[0].content.text
```

The deck concatenates the two into one user message. The notebook puts the rules and the
locations in the system message and the request in the user turn: the same two pieces, in the
two slots a provider gives you.

---

## The ambiguous request

```python
await call_llm_with_context("What time is it in Canada?")
```

---

## Output

```
Assistant: Canada has several time zones. Which city or region do you mean?
For example, Toronto, Vancouver, or Halifax?
```

There is no right conversion here, and the prompt's own last rule says so: *if the input cannot
be resolved confidently, seek clarification*. The zones it offers came from the resource. Without
that list a model can only guess which ones exist.

---

## The clear request, same loop

```python
await call_llm_with_context(
    "It is 9:50 AM in the UK in January. What time is it in Lisbon, Portugal?"
)
```

---

## Output

```
Assistant: It's 9:50 AM in Lisbon as well.
```

Same server, same prompt, same resource, same five steps. The only difference is that this
request can be resolved, and the loop is what notices.

---

## Summary: what each primitive did

| Primitive | Its job in the loop | What goes wrong without it |
|---|---|---|
| tool | does the conversion | the model does arithmetic, badly |
| resource | says which zones exist | the model offers zones that do not |
| prompt | sets the rules, including when to ask | the model answers anyway |
| the trace | records all five steps | you debug the answer instead of the loop |

**Why this matters on Monday.** `docs/guides/loop-engineering.md` puts it first: design the refusal before the happy path. In `agent.py` the refusal object is reached from three places. A loop that cannot say "I need more from you" will invent the rest.

**Let's practice:** notebook, exercise 4, then `review("w10")`.

---

## Exit ticket + homework

- One thing that works: you asked a server for a resource and a prompt, and closed a five-step loop
- One thing that is unclear: write it down before you close the notebook
- Your next action: open the trace from exercise 3 and say, in one line, which step you would have blamed if all you had was the answer

**Homework:** add a `@mcp.prompt` for a second task to the server, give it a title that is not
its name, and write one sentence saying when somebody should pick it. That sentence is what
session 10 calls a when-to-use.

**Next:** unit 11, a database and an API behind the tool, and a server somebody else wrote.
