"""The course app's question route: `GET <API>/api/dev3pack/questions?set=...`.

It returns the questions and never their answer keys. Before the final opens it
answers 403 with `opens_at`; before a set is published it answers 503.

THE BASE URL IS NEVER IN CODE. The founder hands it out, and a student passes it
as `--api` or `DEV3PACK_API_BASE`. So it is untrusted input, and it is checked
before anything is fetched: https only, no credentials in it, and no address
that points back inside the student's own network.

The transport is injected. Tests serve a payload from a function, so nothing
here needs a network to be tested.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

QUESTIONS_PATH = "/api/dev3pack/questions"
API_ENV = "DEV3PACK_API_BASE"

#: Generous for a question set of a few dozen; a reply past this is not one.
MAX_BODY_BYTES = 2_000_000
MAX_QUESTIONS = 500
MAX_QUESTION_CHARS = 4000

#: (status, body) for a GET of `url` within `timeout` seconds.
Transport = Callable[[str, float], tuple[int, bytes]]


class QuestionsError(Exception):
    """The questions could not be fetched or read. Safe to show as is."""


class FinalNotOpen(QuestionsError):
    def __init__(self, opens_at: str) -> None:
        super().__init__(f"the final questions open at {opens_at}")
        self.opens_at = opens_at


class NotPublished(QuestionsError):
    pass


@dataclass(frozen=True)
class Question:
    task_id: str
    category: str
    question: str
    expected_behavior: str


@dataclass(frozen=True)
class QuestionSet:
    set_name: str
    question_set_id: str
    questions: tuple[Question, ...]


def _blocked_address(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def check_api_base(url: str) -> str:
    """The API base, validated and without a trailing slash. Refuses anything else.

    A host NAME is only checked for the obvious local ones here. What it
    resolves to is checked by the transport at fetch time, where the answer is
    the one actually used.
    """
    parts = urlsplit(url.strip())
    if parts.scheme != "https":
        raise QuestionsError(f"the API address must start with https:// (got {url!r})")
    host = parts.hostname
    if not host:
        raise QuestionsError(f"the API address has no host: {url!r}")
    if parts.username or parts.password:
        raise QuestionsError("the API address must not carry a user name or password")
    if parts.query or parts.fragment:
        raise QuestionsError("the API address is a base: no ?query and no #fragment")
    lowered = host.lower().rstrip(".")
    if lowered == "localhost" or lowered.endswith((".localhost", ".local", ".internal")):
        raise QuestionsError(f"the API address points at this machine or its network: {host}")
    try:
        literal = _blocked_address(lowered)
    except ValueError:
        literal = False
    if literal:
        raise QuestionsError(f"the API address points at a private network: {host}")
    return f"{parts.scheme}://{parts.netloc}{parts.path.rstrip('/')}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # A redirect could lead anywhere, including inside the network the host
    # check just kept us out of. The route never redirects, so none is followed.
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise urllib.error.HTTPError(newurl, code, "redirects are not followed", headers, fp)


def urllib_transport(url: str, timeout: float) -> tuple[int, bytes]:
    """The real GET: the host must resolve only to public addresses."""
    host = urlsplit(url).hostname or ""
    try:
        resolved = {info[4][0] for info in socket.getaddrinfo(host, 443)}
    except socket.gaierror as error:
        raise QuestionsError(f"could not find {host}: {error}") from error
    if not resolved or any(_blocked_address(str(address)) for address in resolved):
        raise QuestionsError(f"{host} resolves to a private address; not fetching it")
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read(MAX_BODY_BYTES + 1)
    except urllib.error.HTTPError as error:
        return error.code, error.read(MAX_BODY_BYTES + 1) if error.fp else b""
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise QuestionsError(f"could not reach {host}: {error}") from error


def _json(body: bytes) -> object:
    if len(body) > MAX_BODY_BYTES:
        raise QuestionsError("the questions reply is too large to be a question set")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QuestionsError(f"the questions reply is not JSON: {error}") from error


def _text(payload: dict, key: str, limit: int = 200) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise QuestionsError(f"the questions reply has no usable {key!r}")
    return value


def parse_question_set(payload: object, expected_set: str) -> QuestionSet:
    if not isinstance(payload, dict):
        raise QuestionsError("the questions reply is not an object")
    set_name = _text(payload, "set")
    if set_name != expected_set:
        raise QuestionsError(f"asked for the {expected_set} set, got {set_name!r}")
    raw = payload.get("questions")
    if not isinstance(raw, list) or not raw or len(raw) > MAX_QUESTIONS:
        raise QuestionsError("the questions reply has no usable question list")
    questions: list[Question] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise QuestionsError("a question in the reply is not an object")
        question = Question(
            task_id=_text(entry, "task_id"),
            category=_text(entry, "category"),
            question=_text(entry, "question", MAX_QUESTION_CHARS),
            expected_behavior=_text(entry, "expected_behavior"),
        )
        if question.task_id in seen:
            raise QuestionsError(f"the reply repeats task_id {question.task_id!r}")
        seen.add(question.task_id)
        questions.append(question)
    return QuestionSet(set_name, _text(payload, "question_set_id"), tuple(questions))


def fetch_questions(
    api_base: str,
    set_name: str = "final",
    *,
    transport: Transport = urllib_transport,
    timeout: float = 20.0,
) -> QuestionSet:
    """The question set, or a typed refusal: not open yet, not published, or broken."""
    url = f"{check_api_base(api_base)}{QUESTIONS_PATH}?{urlencode({'set': set_name})}"
    status, body = transport(url, timeout)
    if status == 403:
        payload = _json(body) if body else {}
        opens_at = payload.get("opens_at") if isinstance(payload, dict) else None
        raise FinalNotOpen(opens_at if isinstance(opens_at, str) else "a date not given")
    if status == 503:
        raise NotPublished(f"the {set_name} questions are not published yet")
    if status != 200:
        raise QuestionsError(f"the questions route answered HTTP {status}")
    return parse_question_set(_json(body), set_name)
