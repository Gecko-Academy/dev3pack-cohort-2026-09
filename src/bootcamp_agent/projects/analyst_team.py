"""Project 03: a team of narrow analysts over project 02's filings index.

Four roles, one state, declared transitions:

    coordinator  picks the company, with no model call at all
    researcher   fetches passages, and only that
    writer       writes ONE strict-JSON answer from those passages
    critic       approves it, or asks for one revision

WHAT THIS PROJECT IS FOR. Session 8 teaches a loop, a graph, and the price of
each hop: every role you add is a model call you pay for. The team here spends
two calls where session 5's loop spends one, and four when the critic sends the
draft back. `project-03-e3` makes you measure that rather than assume it.

TWO RUNNERS, ONE TEAM. `build_team` returns the same nodes either as a LangGraph
`StateGraph` or as a twelve-line Python walker. They are kept equal by
construction: both read `NEXT_NODE` for the transitions, both call the same node
functions, and both start from the same seeded state. A test asserts the two
finish in identical states. LangGraph is an optional extra (`uv sync --extra
projects --extra agents`, both of them, because uv sync uninstalls the extra you
leave out); without it the plain runner takes over and says so in `Team.why_not`.

THE ONE RULE THAT MAKES BOTH RUNNERS SIMPLE. A state with `stopped_because` set
is a finished state. Every edge asks that first, so "what happens after a parse
failure" is one line you can point at instead of a branch you have to find.

The checks at the bottom import nothing heavy: no chromadb, no numpy, no
langgraph. They read plain dicts, lists and strings, so they run on a base
install the way project 02's do.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any, TypedDict, cast

from ..bonus import register
from ..llm import LLMClient
from ..schema import (
    ANSWER_JSON_INSTRUCTIONS,
    AnswerParseError,
    ResearchAnswer,
    parse_research_answer,
)
from ..session_checks.ch05 import STOP_REASONS
from ..tools import MAX_SEARCH_RESULTS
from .sec_filings import questions, sources


class TeamError(Exception):
    """The team was asked for something it cannot give, with the fix in the message."""


#: One retrieved passage: (score, chunk_id, text). Higher score is better.
Passage = tuple[float, str, str]

#: The injected retrieval seam: (question, ticker or None, top_k) -> passages.
#: The notebook passes a Chroma-backed search; a test passes a list.
Searcher = Callable[[str, str | None, int], list[Passage]]

#: Passages below this score are treated as no passage at all. It is a floor,
#: not a relevance judgement: deciding what is relevant is the searcher's job.
SCORE_FLOOR = 0.05

#: The same cap the session-5 tools use, so one corpus answers to one number.
TOP_K = MAX_SEARCH_RESULTS

#: How much of a passage reaches the model. Untrusted text is always capped.
PASSAGE_CHARS = 900

#: node -> the node it goes to when the run is NOT finished. The whole map of
#: the team, in one place, read by both runners.
NEXT_NODE: dict[str, str] = {
    "coordinator": "researcher",
    "researcher": "writer",
    "writer": "critic",
    "critic": "writer",
}

#: Our own end marker. The LangGraph builder maps it onto `langgraph.graph.END`.
END_NODE = "end"

#: A walker that never ends is a bug, not a long run. LangGraph has the same
#: guard as `recursion_limit`; the plain runner needs its own.
MAX_STEPS = 32

CRITIC_RULES = (
    "You are a strict reviewer. Reply APPROVE if the answer is supported by the "
    "passages and cites them. Otherwise name one concrete fix in one sentence. "
    "Never rewrite the answer yourself."
)

#: The first line of each role's prompt. It is also the recorded-reply key, so a
#: recording made on one machine replays on another. See `reply_key`.
ROLE_MARKERS = {"writer": "Write the answer.", "critic": "Review the draft answer."}

#: The questions the notebook asks a model. ONE list, read by the notebook and by
#: `data/recorded/record.py`, because two copies drift and the drift is invisible:
#: a question the recording never covers replays as a refusal, and the notebook
#: still prints something that looks like an answer. A test asserts every one of
#: these has a recorded writer reply and a recorded critic reply.
DEMO_QUESTIONS: dict[str, str] = {
    "bottlers": "Which company says its bottling partners could hurt its business?",
    "sweet_drinks": "Who is exposed to taxes on sweet drinks?",
    "musk": "Which company depends on Elon Musk?",
    "azure": "Which company is exposed to risks in its Azure datacenters?",
    "hosts": "Which company depends on hosts listing their homes?",
    "gpus": "Who worries about export controls on its GPUs to China?",
    "batteries": "Who depends on suppliers of lithium-ion battery cells?",
    "foreign_attacks": "Who worries about attacks from foreign governments on its online services?",
}

_WORD = re.compile(r"[a-z0-9]+")

#: Words in a company name that name no company.
_SUFFIXES = frozenset({"inc", "corp", "co", "company", "ltd", "plc", "the", "and"})

#: Domain words that point at one of these eight filings. This is knowledge
#: about the companies, not about the labelled questions: sector nouns, brands
#: and products a reader would recognise. Deliberately thin. A word that fits
#: two of the eight (Airbnb and MercadoLibre are both marketplaces) belongs to
#: neither, and the question goes to every filing instead of the wrong one.
HINTS: dict[str, tuple[str, ...]] = {
    "aapl": ("iphone", "ipad", "macbook", "app store", "phone maker", "smartphone"),
    "msft": ("azure", "windows", "xbox", "office 365", "datacenter", "datacentre"),
    "nvda": ("gpu", "graphics card", "chip designer", "chipmaker", "semiconductor"),
    "tsla": ("musk", "carmaker", "car maker", "automaker", "electric vehicle", "lithium"),
    "ko": ("coke", "bottling", "bottler", "soda", "drinks", "beverage", "sparkling"),
    "nke": ("sneaker", "shoe", "footwear", "athlete", "endorser", "sportswear"),
    "meli": (
        "mercado pago",
        "mercadolibre",
        "argentine",
        "argentina",
        "peso",
        "latin america",
        "online marketplace",
    ),
    "abnb": ("airbnb", "host", "homes", "renting", "guests", "short-term rental"),
}


class TeamState(TypedDict, total=False):
    """The team's whole state, declared once and at module scope.

    Module scope is not a style choice: LangGraph resolves a routing function's
    hints with `get_type_hints`, which cannot see a class defined inside a
    function once `from __future__ import annotations` stringifies them.
    """

    question: str
    ticker: str | None
    routed_by: str
    passages: list[Passage]
    answer: Any
    critique: str
    approved: bool
    revisions: int
    max_revisions: int
    calls: list[str]
    stopped_because: str
    rejected: list[str]


def companies() -> dict[str, str]:
    """ticker -> company name, read from project 02's own sources file."""
    return {entry["ticker"].lower(): str(entry["company"]) for entry in sources()}


def reply_key(role: str, question: str) -> str:
    """The recorded-reply key for one role and one question.

    It is the FIRST LINE of the prompt that role sends, so `FakeLLM` finds it in
    the user message by construction: record under this key and the replay is
    exact. The two roles start differently, so a critic's reply can never be
    returned to the writer.
    """
    if role not in ROLE_MARKERS:
        raise TeamError(f"unknown role {role!r}; the roles that call a model are writer and critic")
    return f"{ROLE_MARKERS[role]}\nQuestion: {question}"


def route_company(question: str, tickers: Mapping[str, str]) -> tuple[str | None, str]:
    """Pick the company a question is about. Deterministic, and no model call.

    Three rungs, tried in order: the ticker itself, a word of the company name,
    then a domain word from `HINTS`. Returns the ticker and which rung decided,
    or `(None, "unrouted")`, which is an answer too: search every filing.
    """
    known = {ticker.lower(): name for ticker, name in tickers.items()}
    lowered = question.lower()
    words = set(_WORD.findall(lowered))
    for ticker in known:
        if ticker in words:
            return ticker, "ticker"
    for ticker, name in known.items():
        if any(word in words for word in _name_words(name)):
            return ticker, "company name"
    for ticker, hints in HINTS.items():
        if ticker in known and any(hint in lowered for hint in hints):
            return ticker, "word"
    return None, "unrouted"


def _name_words(company: str) -> set[str]:
    """The words of a company name that actually name it: no 'Inc', no 'Corp'."""
    return {
        word for word in _WORD.findall(company.lower()) if word not in _SUFFIXES and len(word) > 2
    }


class Team:
    """A built team. `run` answers one question; `framework` says what ran it."""

    def __init__(
        self,
        nodes: dict[str, Callable[[TeamState], TeamState]],
        framework: str,
        why_not: str,
        max_revisions: int,
        graph: Any | None = None,
    ) -> None:
        self.framework = framework
        self.why_not = why_not
        self._nodes = nodes
        self._max_revisions = max_revisions
        self._graph = graph

    @property
    def graph(self) -> Any | None:
        """The compiled LangGraph graph, or None when the plain runner is in charge.

        Public because a graph you cannot draw or stream is a graph you have to take
        on trust. The notebook draws it and streams one run through it.
        """
        return self._graph

    def seed_state(self, question: str) -> TeamState:
        """The state every run starts from. Public so a caller can stream it itself."""
        return TeamState(
            question=question,
            passages=[],
            calls=[],
            revisions=0,
            max_revisions=self._max_revisions,
            rejected=[],
        )

    def run(self, question: str) -> TeamState:
        """Answer one question and return the finished state, receipt included."""
        state = self.seed_state(question)
        if self._graph is not None:
            return cast(TeamState, dict(self._graph.invoke(state)))
        return _walk(self._nodes, state)


def build_team(
    search: Searcher,
    model: LLMClient,
    *,
    max_revisions: int = 1,
    budget: int = 6,
    framework: str = "auto",
) -> Team:
    """Build the analyst team over an injected search and an injected model.

    `budget` counts MODEL CALLS, the way session 5's loop counts tool calls: the
    writer and the critic both refuse to start one past it. `max_revisions` caps
    the critic's send-backs. `framework` is "auto" (LangGraph when installed),
    "langgraph" (insist, and say how to install it) or "plain" (never import it).
    """
    if framework not in ("auto", "langgraph", "plain"):
        raise TeamError(f"framework must be 'auto', 'langgraph' or 'plain', not {framework!r}")
    if max_revisions < 0:
        raise TeamError("max_revisions cannot be negative")
    if budget < 1:
        raise TeamError("budget counts model calls; it must be at least 1")
    nodes = _build_nodes(search, model, budget=budget, max_revisions=max_revisions)
    if framework == "plain":
        return Team(nodes, "plain", "", max_revisions)
    try:
        graph = _compile(nodes)
    except ImportError as error:
        if framework == "langgraph":
            raise TeamError(
                "framework='langgraph' needs the optional extra. Install it with: "
                "uv sync --extra projects --extra agents"
            ) from error
        why_not = (
            "langgraph is not installed, so the plain runner ran: "
            "uv sync --extra projects --extra agents"
        )
        return Team(nodes, "plain", why_not, max_revisions)
    return Team(nodes, "langgraph", "", max_revisions, graph=graph)


def _build_nodes(
    search: Searcher, model: LLMClient, *, budget: int, max_revisions: int
) -> dict[str, Callable[[TeamState], TeamState]]:
    """The four roles, as four functions over the state. Both runners use these."""

    def coordinator(state: TeamState) -> TeamState:
        """Route the question. No model call: a router you can read is cheaper."""
        ticker, how = route_company(state["question"], companies())
        return TeamState(ticker=ticker, routed_by=how)

    def researcher(state: TeamState) -> TeamState:
        """Fetch passages, and only that. Nothing found is an exit, not a crash."""
        found = search(state["question"], state.get("ticker"), TOP_K)
        kept = [passage for passage in found if passage[0] >= SCORE_FLOOR]
        if not kept:
            return TeamState(
                passages=[],
                answer=_refusal(
                    "The index returned no passage for this question, so there is "
                    "nothing to answer from."
                ),
                approved=False,
                stopped_because="answered",
            )
        return TeamState(passages=kept)

    def writer(state: TeamState) -> TeamState:
        """ONE model call, strict JSON, and citations only for what came back."""
        calls = list(state.get("calls", []))
        if len(calls) >= budget:
            return _out_of_budget("writer")
        revisions = state.get("revisions", 0) + (1 if state.get("critique") else 0)
        raw = model.complete(system=ANSWER_JSON_INSTRUCTIONS, user=_writer_prompt(state))
        calls.append("writer")
        try:
            answer = parse_research_answer(raw)
        except AnswerParseError as error:
            # The writer's output contract was broken, so the step failed the way
            # a tool does. The run ends flagged rather than passing prose on.
            return TeamState(
                calls=calls,
                revisions=revisions,
                approved=False,
                answer=_refusal(f"The writer's reply did not parse: {error}"),
                stopped_because="tool_error",
            )
        retrieved = {chunk_id for _, chunk_id, _ in state.get("passages", [])}
        kept = tuple(cited for cited in answer.citations if cited in retrieved)
        dropped = [cited for cited in answer.citations if cited not in retrieved]
        return TeamState(
            calls=calls,
            revisions=revisions,
            # A citation retrieval never returned is the failure mode this whole
            # project exists to catch, so it is dropped AND the answer is flagged.
            answer=replace(
                answer,
                citations=kept,
                needs_human_review=answer.needs_human_review or bool(dropped),
            ),
            rejected=[*state.get("rejected", []), *dropped],
        )

    def critic(state: TeamState) -> TeamState:
        """ONE model call: approve, or ask for one revision. The cap lives here."""
        calls = list(state.get("calls", []))
        if len(calls) >= budget:
            return _out_of_budget("critic", answer=state.get("answer"))
        verdict = model.complete(system=CRITIC_RULES, user=_critic_prompt(state)).strip()
        calls.append("critic")
        approved = verdict.upper().startswith("APPROVE")
        patch = TeamState(calls=calls, critique=verdict, approved=approved)
        if approved:
            patch["stopped_because"] = "answered"
        elif state.get("revisions", 0) >= max_revisions:
            # The revision cap is a budget, and a draft that was never approved
            # leaves flagged. Anything else would ship an unreviewed answer.
            patch["stopped_because"] = "budget"
            patch["answer"] = _flag(state.get("answer"))
        return patch

    return {
        "coordinator": coordinator,
        "researcher": researcher,
        "writer": writer,
        "critic": critic,
    }


def _refusal(reason: str) -> ResearchAnswer:
    """The one shape every exit that is not an answer takes: flagged, uncited."""
    return ResearchAnswer(answer=reason, citations=(), confidence=0.0, needs_human_review=True)


def _flag(answer: Any) -> Any:
    """Mark an answer for a human. Anything that is not one is left alone."""
    if isinstance(answer, ResearchAnswer):
        return replace(answer, needs_human_review=True)
    return answer


def _out_of_budget(role: str, answer: Any = None) -> TeamState:
    """Stop before the call, not after it. A draft already written leaves flagged."""
    stopped = _refusal(f"The budget ran out before the {role} could call the model.")
    return TeamState(
        approved=False,
        stopped_because="budget",
        answer=_flag(answer) if answer is not None else stopped,
    )


def _passages_block(state: TeamState) -> str:
    return "\n\n".join(
        f"[{chunk_id}] (score {score:.2f})\n{text[:PASSAGE_CHARS]}"
        for score, chunk_id, text in state.get("passages", [])
    )


def _writer_prompt(state: TeamState) -> str:
    """The key line first, then the passages, then any fix the critic asked for."""
    prompt = f"{reply_key('writer', state['question'])}\n\nPassages:\n{_passages_block(state)}"
    critique = state.get("critique", "")
    if critique:
        prompt = f"{prompt}\n\nOne fix the reviewer asked for: {critique[:300]}"
    return prompt


def _critic_prompt(state: TeamState) -> str:
    answer = state.get("answer")
    draft = getattr(answer, "answer", answer)
    cited = ", ".join(getattr(answer, "citations", ()) or ()) or "nothing"
    return (
        f"{reply_key('critic', state['question'])}\n\n"
        f"Draft: {str(draft)[:1200]}\nCited: {cited}\n\n"
        f"Passages:\n{_passages_block(state)}"
    )


def _next_node(node: str, state: TeamState) -> str:
    """The only transition rule: a state with `stopped_because` is finished."""
    return END_NODE if state.get("stopped_because") else NEXT_NODE[node]


def _decide(node: str) -> Callable[[TeamState], str]:
    def route(state: TeamState) -> str:
        return _next_node(node, state)

    return route


def _walk(nodes: dict[str, Callable[[TeamState], TeamState]], state: TeamState) -> TeamState:
    """The plain runner: the same nodes, the same edges, no framework."""
    node = "coordinator"
    for _ in range(MAX_STEPS):
        if node == END_NODE:
            return state
        state.update(nodes[node](state))
        node = _next_node(node, state)
    raise TeamError(f"the team ran {MAX_STEPS} steps without finishing; check NEXT_NODE")


def _compile(nodes: dict[str, Callable[[TeamState], TeamState]]) -> Any:
    """The same nodes and the same edges, as a LangGraph graph. Raises ImportError."""
    from langgraph.graph import END, StateGraph

    builder = StateGraph(TeamState)
    for name, node in nodes.items():
        builder.add_node(name, node)
    builder.set_entry_point("coordinator")
    for name, target in NEXT_NODE.items():
        builder.add_conditional_edges(name, _decide(name), {target: target, END_NODE: END})
    return builder.compile()


# --------------------------------------------------------------------------- #
# The checks. Uncounted, and they import nothing the base install lacks.
# --------------------------------------------------------------------------- #

_ANSWER_FIELDS = ("answer", "citations", "confidence", "needs_human_review")


def _as_state(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


@register("project-03-e1")
def _receipt(team_state: Any) -> str | None:
    """The receipt: a named exit, the calls it took, and citations it can prove."""
    state = _as_state(team_state)
    if state is None:
        return "pass one finished TeamState: team.run(question)"
    stopped = state.get("stopped_because")
    if stopped not in STOP_REASONS:
        return f"stopped_because={stopped!r}; it must be one of {STOP_REASONS}"
    calls = state.get("calls")
    if not isinstance(calls, list) or not all(isinstance(call, str) for call in calls):
        return "'calls' must be a list of role names, one per model call"
    answer = state.get("answer")
    if any(not hasattr(answer, field) for field in _ANSWER_FIELDS):
        return "'answer' must be a ResearchAnswer, on every exit including the refusals"
    citations = tuple(answer.citations)
    passages = state.get("passages") or []
    retrieved = {passage[1] for passage in passages if isinstance(passage, (list, tuple))}
    if not passages and citations:
        return (
            f"nothing was retrieved but the answer cites {list(citations)}: a refusal cites nothing"
        )
    invented = [cited for cited in citations if cited not in retrieved]
    if invented:
        return f"the answer cites {invented}, which retrieval never returned"
    if stopped != "answered" and not answer.needs_human_review:
        return f"the run stopped on {stopped!r}, so the answer must set needs_human_review"
    revisions, cap = state.get("revisions", 0), state.get("max_revisions", 0)
    if isinstance(revisions, int) and isinstance(cap, int) and revisions > cap:
        return f"{revisions} revisions under a cap of {cap}"
    return None


@register("project-03-e2")
def _routing(routing: Any) -> str | None:
    """The deterministic router, on every labelled question, with its accuracy."""
    if not isinstance(routing, Sequence) or isinstance(routing, str) or not routing:
        return "expected a list of rows: {'question', 'expected', 'routed', 'how'}"
    labelled = {item["question"]: item["company"] for item in questions()}
    tickers = set(companies())
    seen: dict[str, dict[str, Any]] = {}
    for row in routing:
        if not isinstance(row, dict) or not {"question", "expected", "routed", "how"} <= set(row):
            return "every row needs 'question', 'expected', 'routed' and 'how'"
        question = row["question"]
        if question not in labelled:
            return f"{question!r} is not one of the labelled questions"
        if row["expected"] not in tickers:
            return f"{question!r}: expected={row['expected']!r} is not one of {sorted(tickers)}"
        if row["expected"] != labelled[question]:
            return (
                f"{question!r}: the label says {labelled[question]!r}, "
                f"the row says {row['expected']!r}"
            )
        if row["routed"] is not None and row["routed"] not in tickers:
            return f"{question!r}: routed={row['routed']!r} is neither None nor a real ticker"
        if not isinstance(row["how"], str) or not row["how"].strip():
            return f"{question!r}: 'how' must say which rung decided it"
        seen[question] = row
    missing = sorted(set(labelled) - set(seen))
    if missing:
        return f"{len(missing)} labelled questions have no row, starting with {missing[0]!r}"
    hits = sum(1 for row in seen.values() if row["routed"] == row["expected"])
    wrong = sum(1 for row in seen.values() if row["routed"] not in (None, row["expected"]))
    print(
        f"   routing: {hits}/{len(seen)} right, {wrong} sent to the wrong company, "
        f"{len(seen) - hits - wrong} left to every filing"
    )
    return None


@register("project-03-e3")
def _comparison(comparison: Any) -> str | None:
    """The team against one loop, on the same questions: what the roles cost."""
    if not isinstance(comparison, dict) or not {"team", "loop"} <= set(comparison):
        return "expected {'team': {...}, 'loop': {...}} and a written 'difference'"
    totals = []
    for side in ("team", "loop"):
        run = comparison[side]
        if not isinstance(run, dict) or not {"llm_calls", "answered", "refused"} <= set(run):
            return f"{side!r} needs 'llm_calls', 'answered' and 'refused'"
        calls = run["llm_calls"]
        if not isinstance(calls, int) or isinstance(calls, bool) or calls < 1:
            return f"{side!r}: llm_calls={calls!r}; count the model calls you actually made"
        counts = [run["answered"], run["refused"]]
        if any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in counts):
            return f"{side!r}: 'answered' and 'refused' are counts of questions"
        totals.append(sum(counts))
    if totals[0] != totals[1]:
        return (
            f"the team answered or refused {totals[0]} questions and the loop {totals[1]}; "
            "run both on the SAME questions or the call counts compare nothing"
        )
    if totals[0] < 1:
        return "no questions were run"
    written = [
        comparison.get("difference"),
        *(comparison[s].get("difference") for s in ("team", "loop")),
    ]
    difference = next((text for text in written if isinstance(text, str) and text.strip()), "")
    if len(difference.strip()) < 40:
        return (
            "add 'difference': one or two sentences on what the extra calls bought, "
            "at the top level or on either side. Say it in your own words"
        )
    return None


@register("project-03-e4")
def _revisions(revisions: Any) -> str | None:
    """The critic's cap: one send-back, one rerun of the writer, then it stops."""
    runs = [revisions] if isinstance(revisions, dict) else revisions
    if not isinstance(runs, Sequence) or isinstance(runs, str) or not runs:
        return "pass the finished states you ran: one TeamState, or a list of them"
    revised = 0
    for run in runs:
        state = _as_state(run)
        if state is None:
            return "every item must be a finished TeamState"
        count, cap = state.get("revisions"), state.get("max_revisions")
        if not isinstance(count, int) or not isinstance(cap, int):
            return "every run carries 'revisions' and 'max_revisions'"
        if count > cap:
            return f"{count} revisions under a cap of {cap}: the cap is not holding"
        if state.get("stopped_because") not in STOP_REASONS:
            return f"a run stopped_because={state.get('stopped_because')!r}, which is not a reason"
        if count:
            revised += 1
            writes = sum(1 for call in state.get("calls", []) if call == "writer")
            if writes < count + 1:
                return (
                    f"a run records {count} revision(s) but called the writer {writes} time(s); "
                    "a revision the writer never reran is a revision in name only"
                )
    if not revised:
        return "no run here was ever sent back. Show the critic asking for one revision"
    return None


__all__ = [
    "CRITIC_RULES",
    "DEMO_QUESTIONS",
    "END_NODE",
    "HINTS",
    "NEXT_NODE",
    "Passage",
    "ROLE_MARKERS",
    "Searcher",
    "Team",
    "TeamError",
    "TeamState",
    "build_team",
    "companies",
    "reply_key",
    "route_company",
]
