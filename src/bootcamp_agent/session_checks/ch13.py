"""Session 13: the gate a read-only MCP tool consults before it fetches anything.

`ch13-e1` (the safety checklist) and `ch13-e2` (the lane comparison) live in
`checks.py`. This module adds `ch13-e4`, which judges the guard the learner
writes: `fetch_guard(url: str) -> {"allowed": bool, "reason": str}`.

WHY THIS IS A CHECK AND NOT A REVIEW. "Does this guard refuse an internal
address" is answerable by machine, and every way to get it wrong is mechanical:

  a suffix allowlist        evil-example.com ends with example.com
  the host read off the     https://example.com@evil-example.net is
    string                    evil-example.net, and the string says otherwise
  a number is not an        http://2130706433/ is http://127.0.0.1/ to every
    address                   HTTP client that will dial it
  a hand-rolled prefix      "172." is not 172.16.0.0/12
  loopback checked only     localhost is a name, and it is this machine
    as an IP literal

So the check drives the learner's function with thirty-one URLs of its own and
reads the verdict back. No sockets, no DNS, no fetch: every URL here is decided
by parsing and arithmetic, which is the only part of a guard that can be graded
on a laptop with the network unplugged.

THE CONTRACT IT JUDGES. Three rules, in this order, and the first one that fires
decides:

  1. scheme      http and https pass; every other scheme is refused
  2. address     a host that IS an address has to be a public one
  3. allowlist   the host equals a declared domain or is a subdomain of one

`reason` starts with one of three codes — `scheme`, `not-public`,
`not-allowlisted` — and anything after a colon is the learner's own detail.

WHY THE ORDER IS GRADED, given that rule 3 would refuse 127.0.0.1 anyway. Two
reasons, and neither is pedantry. The address rule is the one that survives the
allowlist being widened, and one day it will be widened. And the reason is what
the next reader acts on: `not-allowlisted` sends them to add an entry, when the
answer was that the URL pointed at the machine the server runs on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bootcamp_agent.checks import register

#: The declared allowlist. The notebook ships this exact tuple, so the guard the
#: check drives and the guard the learner wrote are answering the same question.
ALLOWED_DOMAINS = ("example.com", "docs.python.org")

#: The three reason codes. A refusal starts with one of them.
REASONS = ("scheme", "not-public", "not-allowlisted")

#: For a string that is not a URL: refuse, with any of the three codes.
ANY_REASON = "any"


@dataclass(frozen=True)
class _Case:
    """One URL, the verdict it must get, and the hint if it gets another."""

    url: str
    #: A reason code, `ANY_REASON`, or None when the URL must be allowed.
    expect: str | None
    why: str


_ALLOWED: tuple[_Case, ...] = (
    _Case(
        "https://example.com/pricing",
        None,
        "example.com is on the declared allowlist and https is a scheme this "
        "guard speaks. A guard that refuses everything is not a guard, it is an outage.",
    ),
    _Case(
        "https://api.example.com/v1/status",
        None,
        "api.example.com is a subdomain of an allowed domain: the host equals the "
        "entry, or it ends with a dot and the entry.",
    ),
    _Case(
        "https://docs.python.org/3/library/ipaddress.html",
        None,
        f"the allowlist has two entries, {ALLOWED_DOMAINS}, and this is the second one.",
    ),
    _Case(
        "HTTPS://Example.COM/status",
        None,
        "schemes and hostnames are case-insensitive. Lowercase both before you "
        "compare, or let a URL parser hand them to you already lowered.",
    ),
    _Case(
        "http://example.com/plain",
        None,
        "http and https both pass rule 1. Refusing plain http is a different "
        "policy, and it would report 'scheme' for every private address below.",
    ),
)

_SCHEME: tuple[_Case, ...] = (
    _Case(
        "file:///etc/passwd",
        "scheme",
        "file:// reads the disk of whatever runs the server, and no host is "
        "involved at all. Rule 1 refuses every scheme that is not http or https.",
    ),
    _Case(
        "gopher://example.com:70/_",
        "scheme",
        "the host is on the allowlist and it is still refused: rule 1 runs first. "
        "gopher:// is the classic way to make a fetcher talk to a database port.",
    ),
    _Case(
        "ftp://example.com/pub/spec.json",
        "scheme",
        "an allowed host does not make a scheme allowed. Rule 1, again, first.",
    ),
)

_ADDRESS: tuple[_Case, ...] = (
    _Case(
        "http://10.0.0.7/internal",
        "not-public",
        "10.0.0.0/8 is private space: the neighbours of whatever machine runs "
        "this server, reachable from it and from nowhere else.",
    ),
    _Case(
        "http://192.168.1.10/admin",
        "not-public",
        "192.168.0.0/16 is private space, and this is the address of the router "
        "in most homes and offices.",
    ),
    _Case(
        "http://172.20.10.4/",
        "not-public",
        "172.16.0.0/12 runs from 172.16.0.0 to 172.31.255.255, so 172.20 is inside it.",
    ),
    _Case(
        "http://127.0.0.1:8000/debug",
        "not-public",
        "127.0.0.1 is the machine the server runs on, and a port on it is every "
        "admin interface somebody left unauthenticated because 'it is only local'.",
    ),
    _Case(
        "http://127.5.5.5/metrics",
        "not-public",
        "loopback is the whole of 127.0.0.0/8, not the one address people memorise.",
    ),
    _Case(
        "http://localhost:11434/api/tags",
        "not-public",
        "localhost is a name, and the name means this machine. A guard that only "
        "inspects IP literals never sees it.",
    ),
    _Case(
        "http://[::1]:3000/",
        "not-public",
        "::1 is loopback in IPv6. Half of a guard is no guard: the same machine "
        "answers on both stacks.",
    ),
    _Case(
        "http://169.254.1.1/",
        "not-public",
        "169.254.0.0/16 is link-local — addresses a host assigns itself, never routed.",
    ),
    _Case(
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        "not-public",
        "this is the cloud metadata address. It hands out the instance's "
        "credentials to anything that asks from inside the instance, which is "
        "exactly what a fetcher with no guard is.",
    ),
    _Case(
        "http://0.0.0.0:8080/",
        "not-public",
        "0.0.0.0 is the unspecified address, and most clients read it as this host.",
    ),
    _Case(
        "http://2130706433/",
        "not-public",
        "2130706433 is 127.0.0.1 written as one 32-bit number, and an HTTP client "
        "will dial it. A host that is all digits is an address: decode it, then judge it.",
    ),
    _Case(
        "http://0x7f000001/",
        "not-public",
        "the same address in hexadecimal. Decimal and hex forms are the oldest "
        "way past a guard that only recognises four numbers and three dots.",
    ),
)

_ALLOWLIST: tuple[_Case, ...] = (
    _Case(
        "https://evil-example.com/spec.json",
        "not-allowlisted",
        "evil-example.com ends with example.com and is a completely different "
        "domain, registered by somebody else. Compare whole labels: host == domain, "
        "or host ends with '.' + domain.",
    ),
    _Case(
        "https://example.com.attacker.net/spec.json",
        "not-allowlisted",
        "the allowed name is at the front here, and the domain is attacker.net. "
        "The labels at the END decide who owns a name.",
    ),
    _Case(
        "https://notexample.com/",
        "not-allowlisted",
        "another host that merely contains the allowed one.",
    ),
    _Case(
        "https://example.org/",
        "not-allowlisted",
        "a different top-level domain is a different domain.",
    ),
    _Case(
        "https://example.com@evil-example.net/spec.json",
        "not-allowlisted",
        "everything before the @ is userinfo, so the host is evil-example.net. "
        "Read the host with a URL parser; a host read off the string is the "
        "attacker's to write.",
    ),
    _Case(
        "http://172.32.0.1/",
        "not-allowlisted",
        "172.32.0.1 is public: 172.16.0.0/12 stops at 172.31.255.255. Rule 2 does "
        "not fire, rule 3 does, because no bare address is on the allowlist. A "
        "guard that answers 'not-public' here is matching a prefix, not a network.",
    ),
)

_MALFORMED: tuple[_Case, ...] = (
    _Case("", ANY_REASON, "a string that is not a URL still gets a verdict, and it is a refusal."),
    _Case("not a url", ANY_REASON, "no scheme and no host. Refuse it; do not raise on it."),
    _Case("https://", ANY_REASON, "a scheme and no host at all."),
    _Case("https:///spec.json", ANY_REASON, "a path where the host should be."),
    _Case("//example.com/spec.json", ANY_REASON, "no scheme, so rule 1 has nothing to allow."),
)

_CASES: tuple[_Case, ...] = _ALLOWED + _SCHEME + _ADDRESS + _ALLOWLIST + _MALFORMED


def _shape(result: Any, case: _Case) -> str | None:
    """The return contract, checked before anything is read out of the result."""
    if not isinstance(result, dict) or set(result) != {"allowed", "reason"}:
        return (
            f"{case.url!r}: the guard returned {result!r}; "
            "hint: return {'allowed': bool, 'reason': str} for every URL, so the caller "
            "reads one shape and never branches on a type"
        )
    if not isinstance(result["allowed"], bool):
        return (
            f"{case.url!r}: 'allowed' is {result['allowed']!r}; "
            "hint: True or False, not a value that happens to be truthy"
        )
    if not isinstance(result["reason"], str):
        return (
            f"{case.url!r}: 'reason' is {result['reason']!r}; "
            "hint: 'reason' is a string — a refusal nobody can read is a refusal nobody can fix"
        )
    return None


def _judge(guard: Any, case: _Case) -> str | None:
    """Drive the guard with one URL and read the verdict back."""
    try:
        result = guard(case.url)
    except Exception as error:  # noqa: BLE001 - a guard that raises is the bug under test
        return (
            f"{case.url!r}: the guard raised {type(error).__name__}: {error}; "
            "hint: every string gets a verdict. A guard that raises hands the decision "
            "back to a caller who has no rules to decide it with"
        )
    if problem := _shape(result, case):
        return problem
    allowed, reason = result["allowed"], result["reason"]
    if case.expect is None:
        if not allowed:
            return f"{case.url} was refused ({reason!r}), and it has to be allowed. {case.why}"
        return None
    if allowed:
        return f"{case.url} was allowed. {case.why}"
    code = reason.split(":", 1)[0].strip().lower()
    if code not in REASONS:
        return (
            f"{case.url} was refused with reason {reason!r}; "
            f"hint: start the reason with one of {list(REASONS)} and put your own detail "
            "after a colon. The code is what a caller branches on"
        )
    if case.expect != ANY_REASON and code != case.expect:
        return f"{case.url} was refused with {code!r}, and this one is {case.expect!r}. {case.why}"
    return None


@register("ch13-e4")
def _ch13_e4(fetch_guard: Any) -> str | None:
    """A guard that refuses the right URLs, and says which rule refused each one."""
    if not callable(fetch_guard):
        return "pass the fetch_guard function itself, not the result of calling it"
    for case in _CASES:
        if problem := _judge(fetch_guard, case):
            return problem
    return None
