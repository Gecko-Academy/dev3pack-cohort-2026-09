"""Checkers for Course B, units 9 and 10: an MCP server, its client, and the loop around an LLM.

The learner writes a real server file and the checker talks to it the way any
MCP client would: it starts the file as a child process over stdio, asks it one
thing, and ends the whole process tree. Nothing here reads the learner's answer
off the page when it can ask the server instead. The one exception is the
server file itself, which is parsed with `ast` for the two things a client
cannot see at runtime: whether the type hints and the docstring are there.

THE PROCESS RULE. A probe is a child interpreter in its own session, with a
deadline. When the deadline passes the session is killed, server included,
because a learner's server that never answers must not outlive the check. A
server that answers is gone the moment the probe's `async with` blocks close:
stdio servers die when their client closes the pipe.
"""

from __future__ import annotations

import ast
import json
import os
import re
import signal
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bootcamp_agent.checks import register
from bootcamp_agent.week0_checks.fast_lane import _unwritten

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "modules" / "module-0" / "unit-09-mcp-first-server" / "fixtures"
TIMEZONES = FIXTURES / "timezones.json"

#: How long a probe gets to start the learner's server, ask it one thing, and exit.
PROBE_SECONDS = 30.0

#: The deck's two requests. The first is the tool call in unit 9, the second is
#: the prompt argument and the loop's input in unit 10.
NEW_YORK_TO_TOKYO = {
    "date_time": "2025-01-20T14:30:00",
    "from_timezone": "America/New_York",
    "to_timezone": "Asia/Tokyo",
}
UK_TO_LISBON_REQUEST = "It is 9:50 AM in the UK in January. What time is it in Lisbon, Portugal?"
LOCATIONS_URI = "file://locations.txt"

_CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b")


def zone_offsets() -> dict[str, float]:
    """Zone -> UTC offset in hours for January, from the fixture."""
    return json.loads(TIMEZONES.read_text(encoding="utf-8"))["zones"]


def zone_list() -> list[str]:
    """The fixture's zones, sorted, which is also the text of the locations resource."""
    return sorted(zone_offsets())


def expected_conversion(date_time: str, from_timezone: str, to_timezone: str) -> str:
    """The ISO text a correct conversion prints, from zoneinfo when this machine has it.

    A machine without a time zone database (Windows without `tzdata`) falls back
    to the fixture's January offsets. The two agree for January dates, which is
    the only month the exercises use.
    """
    try:
        from zoneinfo import ZoneInfo

        moment = datetime.fromisoformat(date_time).replace(tzinfo=ZoneInfo(from_timezone))
        return moment.astimezone(ZoneInfo(to_timezone)).isoformat()
    except Exception:  # noqa: BLE001 - any zoneinfo failure means "no database here"
        offsets = zone_offsets()
        moment = datetime.fromisoformat(date_time).replace(
            tzinfo=timezone(timedelta(hours=offsets[from_timezone]))
        )
        return moment.astimezone(timezone(timedelta(hours=offsets[to_timezone]))).isoformat()


# ======================================== the probe: one child, one question, then gone

_PROBE = textwrap.dedent(
    """
    import asyncio, json, sys
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def main(server_path, request):
        params = StdioServerParameters(command=sys.executable, args=[server_path])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                report = {}
                tools = await session.list_tools()
                report["tools"] = [tool.name for tool in tools.tools]
                if "resource" in request:
                    listed = await session.list_resources()
                    report["resources"] = [str(item.uri) for item in listed.resources]
                    if request["resource"] in report["resources"]:
                        read = await session.read_resource(request["resource"])
                        report["resource_text"] = read.contents[0].text
                if "prompt" in request:
                    listed = await session.list_prompts()
                    report["prompts"] = [item.name for item in listed.prompts]
                if "tool" in request:
                    result = await session.call_tool(request["tool"], request.get("arguments", {}))
                    report["is_error"] = bool(result.is_error)
                    report["text"] = result.content[0].text if result.content else ""
                return report

    server_path, request = sys.argv[1], json.loads(sys.argv[2])
    print(json.dumps(asyncio.run(main(server_path, request))))
    """
)


def _end(process: subprocess.Popen) -> None:
    """Kill the probe and everything it started. The server is its child."""
    try:
        if hasattr(os, "killpg"):
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - Windows has no process groups
            process.kill()
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def _last_line(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    errors = [line for line in lines if "Error" in line and not line.startswith("File")]
    return (errors or lines or ["no output"])[-1].lstrip("| ")


def probe(server_path: Path, request: dict) -> dict | str:
    """Start the learner's server in a child, ask it one thing, end the process tree.

    Returns the probe's report, or a sentence about why there is none. The cwd is
    NOT the server's directory, on purpose: a stdio server starts wherever its
    client is, and a file the server opens by a relative name is not found. The
    notebook has the same cwd, so learner and checker see the same failure.
    """
    process = subprocess.Popen(
        [sys.executable, "-c", _PROBE, str(server_path), json.dumps(request)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=PROBE_SECONDS)
    except subprocess.TimeoutExpired:
        _end(process)
        return (
            f"the server did not answer within {PROBE_SECONDS:.0f}s. Does the file end with "
            "mcp.run(transport='stdio') under if __name__ == '__main__'?"
        )
    if process.returncode != 0 or not stdout.strip():
        return f"talking to the server failed: {_last_line(stderr)}"
    return json.loads(stdout.strip().splitlines()[-1])


def _server_file(path: object) -> str | None:
    if not isinstance(path, Path) or not path.is_file():
        return "expected the Path to the server file the cell wrote"
    return None


# ======================================== unit 09 · lesson 2: the server file


def _is_decorator(node: ast.expr, name: str) -> bool:
    target = node.func if isinstance(node, ast.Call) else node
    return isinstance(target, ast.Attribute) and target.attr == name


def _function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


@register("w09-e1")
def _w09_e1(path: object) -> str | None:
    """The tool has type hints on every parameter and the return, and a docstring."""
    problem = _server_file(path)
    if problem:
        return problem
    assert isinstance(path, Path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        return f"the server file does not parse: line {error.lineno}: {error.msg}"
    function = _function(tree, "convert_timezone")
    if function is None:
        return "the file defines no function called convert_timezone"
    if not any(_is_decorator(item, "tool") for item in function.decorator_list):
        return (
            "convert_timezone is not decorated with @mcp.tool(); without the decorator the "
            "server has a function and no tool"
        )
    params = [item.arg for item in function.args.args]
    if params != ["date_time", "from_timezone", "to_timezone"]:
        return f"the tool's parameters are date_time, from_timezone, to_timezone; got {params}"
    unhinted = [item.arg for item in function.args.args if item.annotation is None]
    if unhinted:
        return (
            f"{unhinted[0]!r} has no type hint. Every parameter needs one: the hints become the "
            "input schema, and the schema is what the client and the model read"
        )
    if function.returns is None:
        return "the return value has no type hint; add -> str"
    doc = ast.get_docstring(function)
    if not doc or _unwritten(doc):
        return (
            "the docstring is missing. It becomes the tool's description, which is the only "
            "thing a model sees before it decides to call the tool"
        )
    unnamed = [name for name in params if name not in doc]
    if unnamed:
        return (
            f"the docstring never mentions {unnamed[0]!r}; describe every argument, with an "
            "example, the way the deck's Args block does"
        )
    return None


# ======================================== unit 09 · lesson 3: the client


@register("w09-e2")
def _w09_e2(answer: object) -> str | None:
    """The tool names the server lists, read off list_tools() rather than off memory."""
    if not isinstance(answer, tuple) or len(answer) != 2:
        return "expected a tuple: (server_path, tool_names)"
    path, names = answer
    problem = _server_file(path)
    if problem:
        return "the first item must be the Path to the server file"
    assert isinstance(path, Path)
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        return "the second item must be a list of tool names, as strings, from response.tools"
    if not names:
        return (
            "no tool names came back. If the connection closed, the server never started: the "
            "child process starts in the notebook's directory, so the path to the file must be "
            "absolute, and the command must be sys.executable"
        )
    report = probe(path, {})
    if isinstance(report, str):
        return report
    if names != report["tools"]:
        if sorted(names) == sorted(report["tools"]):
            return "right names, wrong order; keep the order the server listed them in"
        return (
            f"the server lists {report['tools']} and you returned {names}. Read tool.name off "
            "each item of response.tools"
        )
    return None


@register("w09-e3")
def _w09_e3(text: object) -> str | None:
    """The deck's New York to Tokyo call, and the text that comes back."""
    if not isinstance(text, str) or not text.strip():
        return "expected the text of the tool result: result.content[0].text"
    expected = expected_conversion(**NEW_YORK_TO_TOKYO)
    if "validation" in text.lower() or "error" in text.lower():
        return (
            "the server answered with an error, not a conversion. The argument names come from "
            "tool.input_schema['properties'], not from memory; read them off the schema"
        )
    if expected not in text:
        return (
            f"the converted time should read {expected}: 14:30 in New York is the next morning "
            "in Tokyo, fourteen hours ahead in January"
        )
    if NEW_YORK_TO_TOKYO["to_timezone"] not in text:
        return "the result names the target zone: 'Time in Asia/Tokyo: ...'"
    return None


# ======================================== unit 10 · lesson 1: a resource


@register("w10-e1")
def _w10_e1(text: object) -> str | None:
    """The locations resource, as the client read it back: one zone per line."""
    if not isinstance(text, str):
        return (
            "expected the resource's text, the way the client received it "
            "(read.contents[0].text). A list is what the server function built, not what came "
            "back over the wire: a resource answers with text"
        )
    if not text.strip():
        return (
            "the resource came back empty. Is the function decorated with "
            f"@mcp.resource({LOCATIONS_URI!r}), and does the client read that same URI?"
        )
    lowered = text.lower()
    if "traceback" in lowered or "error:" in lowered or "failed" in lowered:
        return f"the client never read the resource: {text.strip().splitlines()[0]}"
    expected = zone_list()
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) == 1 and len(expected) > 1:
        return (
            "the whole table came back as one line. A resource that lists things puts one per "
            "line, so whatever reads it can split it: '\\n'.join(sorted(ZONES)), not "
            "', '.join(sorted(ZONES))"
        )
    if lines != expected:
        missing = [zone for zone in expected if zone not in lines]
        extra = [line for line in lines if line not in expected]
        if missing:
            return (
                f"{len(missing)} of the fixture's {len(expected)} zones are missing, starting "
                f"with {missing[0]!r}. The resource returns every zone in the table, sorted"
            )
        if extra:
            return f"{extra[0]!r} is not one of the fixture's zones; return the table's keys"
        return f"the zones are out of order; sorted() gives {expected[:2]} first"
    return None


# ======================================== unit 10 · lesson 2: a prompt


@register("w10-e2")
def _w10_e2(answer: object) -> str | None:
    """The prompt's name, its title, and the text it renders for the deck's request."""
    if not isinstance(answer, tuple) or len(answer) != 3:
        return "expected a tuple: (name, title, rendered_text)"
    name, title, rendered = answer
    if not all(isinstance(item, str) for item in (name, title, rendered)):
        return (
            "all three items are strings: the prompt's .name, its .title, and "
            "prompt.messages[0].content.text"
        )
    if not name.strip():
        return "no prompt name came back; list_prompts() gives .name on each listed prompt"
    if name == title:
        return (
            "the name and the title are the same string, and they are two different things. "
            "The name is the decorated function's name (convert_timezone_prompt); the title is "
            "what the decorator was given (title='Timezone Conversion'). get_prompt() wants the "
            "name"
        )
    if not name.isidentifier():
        return (
            f"{name!r} is not a function name. A prompt's name is the name of the function you "
            "decorated, which is what the client asks for"
        )
    if _unwritten(title, minimum=4):
        return "the title is missing; the decorator takes it: @mcp.prompt(title='...')"
    if _unwritten(rendered, minimum=80):
        return (
            "the rendered text is too short to be the template. It carries the task, the rules, "
            "and the request, which is the whole point of keeping it on the server"
        )
    if UK_TO_LISBON_REQUEST not in rendered:
        return (
            "the rendered text does not contain the request verbatim. The template ends with "
            "its argument interpolated, so what the model reads includes what the person asked; "
            f"look for {UK_TO_LISBON_REQUEST!r} in the text you got back"
        )
    return None


# ======================================== unit 10 · lessons 3 and 4: the loop

#: The five steps of the deck's tool-calling workflow, in order.
LOOP_STEPS = ["llm", "tool_use", "tool_result", "llm", "final"]

#: The deck's request, resolved against the January reference date the notebook's
#: router uses. 9:50 in London is 9:50 in Lisbon, and that is the point of it.
UK_TO_LISBON_CALL = {
    "date_time": "2025-01-20T09:50:00",
    "from_timezone": "Europe/London",
    "to_timezone": "Europe/Lisbon",
}

#: The deck's ambiguous request, and the fixture zones a good answer offers.
#: Written down rather than derived: a zone name does not say which country it is in.
AMBIGUOUS_REQUEST = "What time is it in Canada?"
CANADIAN_ZONES = ("America/Halifax", "America/Toronto", "America/Vancouver")


@register("w10-e3")
def _w10_e3(trace: object) -> str | None:
    """The five-step loop, and the converted time in the sentence it ends with."""
    if not isinstance(trace, list) or not trace:
        return (
            "expected the loop's trace: a list of steps, each a dict with a 'step' and a 'detail'"
        )
    for entry in trace:
        if not isinstance(entry, dict) or "step" not in entry or "detail" not in entry:
            return "every entry in the trace is a dict with a 'step' and a 'detail'"
    steps = [entry["step"] for entry in trace]
    if steps != LOOP_STEPS:
        if steps.count("llm") < 2:
            return (
                f"the loop ran {steps}, and the model was called once. The fifth step is a "
                "second call: the tool's result goes back to the model, and the model writes "
                "the reply"
            )
        return f"the loop's steps are {LOOP_STEPS}; got {steps}"
    expected = expected_conversion(**UK_TO_LISBON_CALL)
    answer = str(trace[-1]["detail"])
    if expected not in answer:
        return (
            f"the final answer does not contain the converted time {expected}. Read the "
            "'tool_result' step: the follow-up message has to carry that text, or the model "
            "answers a question it was never given the answer to"
        )
    return None


@register("w10-e4")
def _w10_e4(answer: object) -> str | None:
    """The ambiguous request: a question naming the choices, never a converted time."""
    if not isinstance(answer, str) or not answer.strip():
        return f"expected the loop's answer for {AMBIGUOUS_REQUEST!r}, as a string"
    if _CLOCK.search(answer):
        return (
            "the answer contains a clock time. The request names a country with several zones, "
            "so a converted time here is a guess wearing an answer's clothes. The prompt's own "
            "rule is to seek clarification"
        )
    named = [zone for zone in CANADIAN_ZONES if zone in answer]
    if len(named) < 2:
        return (
            f"the answer offers {len(named)} of the fixture's Canadian zones, and a clarifying "
            "question is only useful if it offers the choices. That list is what the locations "
            "resource is for: name at least two of " + ", ".join(CANADIAN_ZONES)
        )
    if "?" not in answer:
        return "the answer is not a question. Ask which zone the person meant"
    return None
