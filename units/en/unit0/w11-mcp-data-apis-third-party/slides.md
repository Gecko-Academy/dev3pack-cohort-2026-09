---
marp: true
paginate: true
theme: default
---

# Week 0 · Course B, Chapter 3: Databases, APIs, and third-party servers
## MCP: AI apps as easy as 1, 2, 3

Dev3Pack AI-Engineering Bootcamp · Week 0 (self-paced)

---

# Lesson 1
## MCP database integrations

---

## Why put a database behind a tool

- **Query power**: filter, search and sort without loading the whole dataset
- **Scale**: an index makes a lookup fast at a size a file is not
- **Concurrency**: several tool calls, or several clients, hitting it safely
- **Production**: backups, replication, and one source of truth

A file gets you a list. A database gets you a question.

---

## Which primitive, again

| | Tool | Resource |
|---|---|---|
| The data is | dynamic, depends on the caller's input | read-only, static, reference |
| It can | write, and have effects | be read, and nothing else |
| Example | a lookup, an analysis, an operation | guidelines, docs, policies |

The same table can be both: a resource that lists every zone, and a tool that searches them.

---

## The connection lifecycle

```python
import sqlite3

# Open once, at startup. Every handler reuses it.
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    finally:
        conn.close()
```

Opening a connection per call costs more than the query. Never closing one leaks until the
process ends, which for a stdio server is when the client goes away.

---

## The tool, the way it should be written

```python
@mcp.tool()
def lookup_locations(prefix: str) -> str:
    """Find the timezones whose name contains the given text."""
    sql = "SELECT timezone FROM locations WHERE timezone LIKE ? LIMIT 50"
    try:
        rows = conn.execute(sql, (f"%{prefix}%",)).fetchall()
    except sqlite3.Error as error:
        return f"Error: {error}"
    return "\n".join(row["timezone"] for row in rows)
```

Three habits in four lines: a `?`, a `LIMIT`, and an error that comes back as text.

---

## Output

```
prefix='Europe'
Europe/Berlin
Europe/Lisbon
Europe/London
Europe/Paris
```

The wildcards live in the **value**, not in the query. `'%' + prefix + '%'` is what you are
matching against, and it is data.

---

## The same tool with the value inside the SQL

```python
sql = f"SELECT timezone FROM locations WHERE timezone LIKE '%{prefix}%' LIMIT 50"
rows = conn.execute(sql).fetchall()
```

Now send it `' UNION SELECT 'pwned' --`

---

## Output

```
Africa/Abidjan
America/Halifax
...
Europe/Paris
pwned
```

Thirteen rows out of a twelve-row table. The caller closed the quote, added a second query, and
commented out the rest. Nothing crashed, nothing logged, and the tool had been answering
correctly all morning.

---

## Safety and production habits

- **Parameterised (`?`) queries.** Never string-format a caller's or a model's text into SQL
- Prefer **read-only** and tightly scoped database access for an MCP server
- Apply **limits**: a maximum row count, and a timeout

The value a tool was handed came from outside. That is the same rule
`cookbook/advanced/08_anti_poisoning.ipynb` applies to an ingested spec, one level down.

---

## Summary: where does the value go

| You write | The database sees | A quote in the input |
|---|---|---|
| `LIKE ?` with a tuple | one statement, one value | is matched as text |
| an f-string | whatever the caller composed | ends the string and starts a new clause |
| `%` or `.format()` | the same thing, spelled differently | the same |
| `+` concatenation | the same thing again | the same |

**Why this matters on Monday.** Session 5 draws the boundary of a capability. A tool that runs SQL a caller helped write is not a bounded capability: its real surface is the whole database, and no docstring says so.

**Let's practice:** notebook, exercise 1.

---

# Lesson 2
## MCP API integrations

---

## Timeout and error handling

```python
import requests


@mcp.tool()
def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) -> str:
    payload = {"dateTime": date_time, "fromTimezone": from_timezone, "toTimezone": to_timezone}
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        return f"Time in {to_timezone}: {response.json().get('dateTime', 'N/A')}"
    except requests.exceptions.RequestException as error:
        return f"Error converting timezone: {error}"
```

This is the deck's code, and it is the source for this lesson. `requests` is not installed in
this repo, so the notebook's tool builds the same headers and payload and then converts locally.

---

## Output

```
Time in Asia/Tokyo: 2025-01-21T04:30:00+09:00
```

Three things it gets right and one loop depends on: a `timeout`, so a hung API is not a hung
agent; `raise_for_status`, so a 500 is not parsed as an answer; and a failure that comes back as
**text**, so the model that called the tool can read what went wrong.

---

## API authentication: the do's

- An API key is always accessed **server-side**
- Local host: environment variables, a `.env` file
- Remote host: environment variables, managed secrets

**The client never sends, receives or accesses the credential.**

---

## API authentication: the don'ts

- Not **hardcoded**, not inserted into a URL, not **logged**
- Not a **tool argument**, and not part of a **tool result**

A tool's parameters are its input schema, and the input schema is published to every client that
lists the tools. A tool result travels back to the client and into the model's context, which is
a transcript somebody will paste somewhere.

---

## The key, read where it belongs

```python
import os


@mcp.tool()
def convert_timezone(date_time: str, from_timezone: str, to_timezone: str) -> str:
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("TIMEZONE_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    ...
```

---

## Output

```
the schema wants: ['date_time', 'from_timezone', 'to_timezone']
Time in Asia/Tokyo: 2025-01-21T04:30:00+09:00
the key is in the result: False
```

`if api_key:` is not politeness. A missing credential is a header you leave off, so the tool
still answers, and whoever runs the server finds out from a 401 rather than a traceback.

---

## Summary: four places a key must not be

| Place | Why not |
|---|---|
| a tool parameter | it is in the published input schema; every client is told to supply one |
| a tool result | the result reaches the client and the model's context |
| a string in the source | the source is in a repository |
| a URL, or a log line | both are read by more people than you think |

**Why this matters on Monday.** The README's Safety Boundary section already says: never a secret in `CLAUDE.md`, in MCP JSON, in an issue, in a prompt or in a commit. This lesson adds the two places that look like code rather than config, and are worse for it.

**Let's practice:** notebook, exercise 2.

---

# Lesson 3
## Third-party MCP servers

---

## Why use one

- **Speed**: filesystem or database access without writing a server
- **Maintained by somebody else**: you work on the client and the application
- **Integration**: the same client code talks to any of them

Your `stdio_client` and `ClientSession` do not change. That is the whole promise of a protocol.

---

## Three questions to ask first

- **Trust.** The server runs code and may call external APIs. Check those sources
- **Security.** It needs careful handling of private data and credentials
- **Surface area.** More tools means more the model can decide to do. Know what is exposed

None of the three is answered by "it has a lot of stars".

---

## The deck's example

```python
params = StdioServerParameters(command="open-library-server", args=[])

async with stdio_client(params) as (reader, writer):
    async with ClientSession(reader, writer) as session:
        await session.initialize()
        response = await session.list_tools()
        print("Tools:", [tool.name for tool in response.tools])
        result = await session.call_tool("get_book_by_title", {"title": "Dune"})
```

---

## Output

```
Tools: ['get_book_by_title', 'get_authors_by_name', 'get_author_info',
        'get_author_photo', 'get_book_cover', 'get_book_by_id']

Tool Call Result: [{"title": "Dune", "authors": ["Frank Herbert"],
                    "first_publish_year": 1965, ...}]
```

Six tools over the Internet Archive's Open Library API, no key needed. This unit does not install
it. It asks the three questions about a surface you will actually connect to instead.

---

## The surface session 13 uses

```
surface:  https://mcp.geckovision.tech/orquestra/mcp
recorded: 2026-09-03, protocol 2025-11-25
tools (16): start, find_start, list_programs, comprehend_program,
            prepare_purchase, try_purchase, list_stores, plan_payment, ...
```

A **recorded** list, read from `fixtures/orquestra-tools.json`, not fetched. Its own provenance
note says what it is evidence of: what the surface listed on the day it was read, and nothing
about what any of those tools does when called.

---

## Summary: answering the three questions

| Question | What counts as an answer |
|---|---|
| Trust | who runs it, and whether you can read what a tool does before calling it |
| Security | which of your secrets it would be able to reach, and which it never needs |
| Surface area | the number of tools, and whether the model needs all of them |

**Why this matters on Monday.** Session 13 connects a client to that hosted surface and asks it to plan a real transaction. It is a third-party MCP server, so these three questions are the pre-flight, and the answer to the third one is a number you can look up rather than a feeling.

**Let's practice:** notebook, exercise 3.

---

# Lesson 4
## Course recap

---

## Chapter 1: unit 9

- MCP is one protocol between models and capabilities, so N times M becomes N plus M
- A tool is a function with `@mcp.tool()`, and its **type hints are its schema**
- Its **docstring is its description**, which is all a model reads before deciding
- A stdio server is a child process, so the path is absolute and the call has a timeout

---

## Chapter 2: unit 10

- **Resources** are read-only context, addressed by a URI, chosen by the application
- **Prompts** are instruction templates, chosen by the person, and their **name is the function's name**
- The tool-calling loop has five steps, and step four is the one that gets left out
- An unanswerable request gets a question back, not a number

---

## Chapter 3: unit 11

- **Databases**: one connection, parameterised queries, read-only scope, row limits
- **APIs**: timeouts, `raise_for_status`, and failures returned as text
- **Auth**: the key is read server-side and never appears in a schema, a result, or the source
- **Third-party servers**: trust, security, surface area, asked before you connect

---

## Summary: the three things that carry

| | The rule |
|---|---|
| Contracts | a tool's signature and docstring are read by machines, so write them for a reader who cannot ask |
| Untrusted input | a value from outside is data, never code, whether it lands in SQL or in a prompt |
| Credentials | the key belongs to the server, so the client never has to be trusted with it |

**Why this matters on Monday.** Session 1 puts *tool* and *MCP server* in the vocabulary table and you already have both. Session 10 packages a skill, which is unit 10's prompt with a when-to-use attached. Session 13 connects to a hosted surface, and you have already asked it the three questions.

**Let's practice:** notebook, `review("w11")`.

---

## Exit ticket + homework

- One thing that works: you watched a working tool answer with a row that was not in the table
- One thing that is unclear: write it down before you close the notebook
- Your next action: open any MCP server config you already have and count its tools

**Homework:** take the unit 10 server and add `lookup_locations` to it, backed by the database
from this unit, so one server carries a tool, a resource, a prompt and a query. Then write down
which of its four pieces would be the most expensive to get wrong, and why.

**Next:** unit 12, the data structures an agent loop is made of. Then session 1 on Monday.
