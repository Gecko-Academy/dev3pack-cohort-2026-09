"""An MCP server in the standard library, so a stranger's client can call your work.

WHY WRITE THE PROTOCOL RATHER THAN IMPORT IT. MCP over stdio is JSON-RPC 2.0 with
four methods that matter, and the whole of it fits on a screen. This repository
does carry an `mcp` package in its dev group, for session 12's material -- and
this file still does not use it, because this is the file you are meant to COPY,
and you are far likelier to copy something you have read all of.

WHAT MAKES IT TESTABLE. :func:`handle` is pure: one request dict in, one response
dict out, no I/O. Every check in this track drives it over in-memory dicts, so CI
never spawns a process and cannot hang waiting on a pipe. A server you can only
test by launching it is a server nobody tests.

THE ONE RULE ABOUT NOTIFICATIONS. A request with no `id` is a notification, and
replying to one is a protocol violation that some clients treat as fatal.
:func:`handle` returns ``None`` for those. It is the single easiest thing to get
wrong here, which is why it has its own check.

A TOOL IS A CONTRACT, NOT A FUNCTION NAME. What makes a surface callable by an
agent that has never seen it is the description and the schema -- what the tool
is for, what its arguments mean, and which are required. A tool named `run` with
an empty schema is invisible to a model, however well it works.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

#: Echoed back when the client asks for one we can speak. A server that insists
#: on its own version breaks against a newer harness for no reason.
DEFAULT_PROTOCOL = "2025-06-18"
SUPPORTED = ("2025-06-18", "2025-03-26", "2024-11-05")

#: A tool as this server holds it: the contract the client reads, and the
#: callable behind it. They travel together so they cannot disagree.
Tool = tuple[dict[str, Any], Callable[..., Any]]


def text(body: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": body}]}


def failed(body: str) -> dict[str, Any]:
    """A tool that could not answer, said in the protocol's own words.

    NOT an exception and NOT a cheerful default. `isError` is how a client learns
    the call failed without the session dying, and a tool that returns a plausible
    wrong answer instead is the failure this whole course is about.
    """
    return {"content": [{"type": "text", "text": body}], "isError": True}


def _call(tools: dict[str, Tool], name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    contract, function = tools[name]
    required = contract.get("inputSchema", {}).get("required", [])
    missing = [key for key in required if key not in arguments]
    if missing:
        return failed(f"{name} needs {', '.join(missing)}")
    try:
        answer = function(**arguments)
    except TypeError as error:
        # An argument the schema allowed and the function will not take. The
        # schema and the function have disagreed; say so rather than crashing.
        return failed(f"{name} could not be called: {error}")
    except Exception as error:  # noqa: BLE001 - a tool must not take the server down
        return failed(f"{name} failed: {error}")
    return text(answer if isinstance(answer, str) else json.dumps(answer, indent=2))


def handle(
    request: dict[str, Any],
    tools: dict[str, Tool],
    *,
    name: str = "my-store",
    version: str = "0.1.0",
) -> dict[str, Any] | None:
    """One JSON-RPC request in, one response out -- or ``None`` for a notification."""
    method = request.get("method", "")
    identifier = request.get("id")

    if method == "initialize":
        asked = (request.get("params") or {}).get("protocolVersion")
        result: dict[str, Any] = {
            "protocolVersion": asked if asked in SUPPORTED else DEFAULT_PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": name, "version": version},
        }
    elif method.startswith("notifications/"):
        return None
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [contract for contract, _ in tools.values()]}
    elif method == "tools/call":
        params = request.get("params") or {}
        called = params.get("name", "")
        if called not in tools:
            return {
                "jsonrpc": "2.0",
                "id": identifier,
                "error": {"code": -32602, "message": f"no tool called {called!r}"},
            }
        result = _call(tools, called, params.get("arguments") or {})
    else:
        return {
            "jsonrpc": "2.0",
            "id": identifier,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


def serve(tools: dict[str, Tool], stdin: Any = None, stdout: Any = None, **info: str) -> int:
    """Newline-delimited JSON-RPC in, answers out.

    ``stdin``/``stdout`` are arguments so tests can drive this over a pair of
    pipes instead of a subprocess.
    """
    source = stdin or sys.stdin
    sink = stdout or sys.stdout
    for line in source:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            # There is no id to answer to, so saying nothing is the only honest
            # move. Exiting would take the whole session down over one bad line.
            continue
        response = handle(request, tools, **info)
        if response is None:
            continue
        sink.write(json.dumps(response) + "\n")
        sink.flush()
    return 0


__all__ = ["DEFAULT_PROTOCOL", "SUPPORTED", "Tool", "failed", "handle", "serve", "text"]
