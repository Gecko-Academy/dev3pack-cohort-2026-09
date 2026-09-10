"""Exercise checks: one function per exercise id, called from the notebooks.

`check("ch02-e1", value)` prints one line (✅ or ❌ with the reason and a
hint) and returns a bool. It never raises, so an unfinished exercise does
not stop the notebook. In strict mode (`BOOTCAMP_CHECKS_STRICT=1`, set by
the notebook checker for `solutions/` notebooks) a failed check raises, so
CI proves every solution passes its own check.

A checker takes the participant's value and returns None on pass or a
message on failure. Checks are exact on the FakeLLM and tolerant on a real
model: they judge shape and behaviour, not the exact words a model chose.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bootcamp_agent.documents import load_corpus
from bootcamp_agent.evals import load_cases, run_evals
from bootcamp_agent.llm import FakeLLM
from bootcamp_agent.retrieval import retrieve
from bootcamp_agent.schema import AnswerParseError, ResearchAnswer, parse_research_answer
from bootcamp_agent.tools import ToolError

STRICT_ENV = "BOOTCAMP_CHECKS_STRICT"
REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "data" / "corpus"

Checker = Callable[[Any], str | None]
CHECKS: dict[str, Checker] = {}
# The latest verdict per exercise id in this kernel; `review()` reads it.
RESULTS: dict[str, str | None] = {}


class ExerciseCheckFailed(AssertionError):
    """Raised in strict mode when a check fails."""


class UnknownCheck(KeyError):
    """Raised for an exercise id that has no checker."""


def register(exercise_id: str) -> Callable[[Checker], Checker]:
    def wrap(function: Checker) -> Checker:
        CHECKS[exercise_id] = function
        return function

    return wrap


def _ensure_registered() -> None:
    """Import the per-session check modules, once, so a notebook needs no extra import.

    The registry is filled by side effect of importing. Week 0 asks for its own
    package explicitly; the sessions authored after the re-sequence live in
    `session_checks`, and a learner should not have to know that.
    """
    import bootcamp_agent.session_checks  # noqa: F401 - importing is what registers them


def check(exercise_id: str, value: Any) -> bool:
    """Run the checker for `exercise_id` on `value`, print the verdict, return pass/fail."""
    _ensure_registered()
    if exercise_id not in CHECKS:
        raise UnknownCheck(f"no check registered for {exercise_id!r}; known: {sorted(CHECKS)}")
    try:
        problem = CHECKS[exercise_id](value)
    except Exception as error:  # noqa: BLE001 - a crashing answer is a failed check, not a crash
        problem = f"your code raised {type(error).__name__}: {error}"
    RESULTS[exercise_id] = problem
    _record_quietly(exercise_id, passed=problem is None)
    if problem is None:
        print(f"✅ {exercise_id} passed")
        return True
    print(f"❌ {exercise_id}: {problem}")
    if os.environ.get(STRICT_ENV) == "1":
        raise ExerciseCheckFailed(f"{exercise_id}: {problem}")
    return False


def _record_quietly(exercise_id: str, *, passed: bool) -> None:
    """Note the attempt, and never let the notebook fail because of it.

    A read-only home directory or a corrupt progress file is an inconvenience.
    An exercise that crashes because bookkeeping failed is a blocker, and the
    bookkeeping is the least important thing in this function.
    """
    try:
        from bootcamp_agent.hints import record

        record(exercise_id, passed=passed)
    except Exception:  # noqa: BLE001 - progress is optional, the exercise is not
        pass


def _marks(ids: list[str]) -> str:
    """`  ·  240/300 marks`, or nothing at all if progress is unavailable."""
    try:
        from bootcamp_agent.hints import FULL_MARKS, attempt

        earned = sum(attempt(exercise_id).score for exercise_id in ids)
    except Exception:  # noqa: BLE001
        return ""
    return f"  ·  {earned}/{len(ids) * FULL_MARKS} marks"


def review(chapter: str) -> bool:
    """Print the chapter scorecard from the checks run so far. Returns True when all passed."""
    _ensure_registered()
    ids = sorted(exercise_id for exercise_id in CHECKS if exercise_id.startswith(f"{chapter}-"))
    passed = [exercise_id for exercise_id in ids if RESULTS.get(exercise_id, "") is None]
    print(f"{chapter}: {len(passed)}/{len(ids)} passed{_marks(ids)}")
    for exercise_id in ids:
        if exercise_id not in RESULTS:
            print(f"   {exercise_id}: not checked yet; run its check cell")
        elif RESULTS[exercise_id] is not None:
            print(f"❌ {exercise_id}: {RESULTS[exercise_id]}")
    return len(passed) == len(ids)


def _corpus():  # noqa: ANN202 - small local helper
    return load_corpus(CORPUS_DIR)


# ---------------------------------------------------------------- chapter 01


@register("ch02-e1")
def _ch02_e1(replies: Any) -> str | None:
    """Three FakeLLM replies: one per canned keyword, one default."""
    if not isinstance(replies, (list, tuple)) or len(replies) != 3:
        return "expected a list of exactly three replies; hint: one call per question"
    if any(not isinstance(reply, str) or not reply.strip() for reply in replies):
        return "every reply must be a non-empty string; hint: print what complete() returns"
    joined = " ".join(replies)
    wanted = {
        "agent": "An agent is a loop",
        "hello": "Hello!",
        "default": "no canned answer",
    }
    missing = [name for name, needle in wanted.items() if needle not in joined]
    if missing:
        return f"no reply matched the {missing} case(s); hint: read the keys of hello_llm.responses"
    return None


@register("ch02-e2")
def _ch02_e2(runs: Any) -> str | None:
    """Two lanes, two calls each: the fake pair is identical; the live pair is two answers."""
    if not isinstance(runs, dict) or set(runs) != {"fake", "live"}:
        return "expected a dict with keys 'fake' and 'live'"
    for lane in ("fake", "live"):
        pair = runs[lane]
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return f"runs[{lane!r}] must hold exactly two replies"
        if any(not isinstance(reply, str) or not reply.strip() for reply in pair):
            return f"runs[{lane!r}] has an empty reply"
    if runs["fake"][0] != runs["fake"][1]:
        return "the two FakeLLM replies differ; hint: same question, same fake, same answer"
    return None


@register("ch02-e3")
def _ch02_e3(bar: Any) -> str | None:
    """The reliability bar: three sentences, each written by the participant."""
    keys = ("reliable_when", "review_when", "never_unreviewed")
    if not isinstance(bar, dict) or set(bar) != set(keys):
        return f"expected a dict with keys {keys}"
    for key in keys:
        text = bar[key]
        if not isinstance(text, str) or len(text.strip()) < 20 or text.strip().startswith("..."):
            return f"{key!r} needs one full sentence (20+ characters); hint: be concrete"
    return None


# ---------------------------------------------------------------- chapter 02


@register("ch06-e2")
def _ch06_e2(load_mini: Any) -> str | None:
    """A loader with both failure modes, judged on a temp directory."""
    import tempfile

    if not callable(load_mini):
        return "pass the load_mini function itself, not a call to it"
    tmp = Path(tempfile.mkdtemp())
    (tmp / "good.md").write_text("# A Title\nBody text.\nMore.", encoding="utf-8")
    (tmp / "bad.md").write_text("no title here\n# late title", encoding="utf-8")
    doc = load_mini(tmp / "good.md")
    if getattr(doc, "doc_id", None) != "good":
        return "doc_id must be the file stem ('good'); hint: path.stem"
    if getattr(doc, "title", None) != "A Title":
        return "title must be the first line without '# '; hint: lines[0][2:].strip()"
    if "Body text." not in getattr(doc, "text", ""):
        return "text must hold the lines after the title"
    for bad in (tmp / "bad.md", tmp / "missing.md"):
        try:
            load_mini(bad)
        except ValueError as error:
            if not str(error).strip():
                return f"the ValueError for {bad.name} has no message; hint: name the file"
        except Exception as error:  # noqa: BLE001
            return f"{bad.name} raised {type(error).__name__}, expected ValueError"
        else:
            return f"{bad.name} did not raise; hint: errors are part of the contract"
    return None


@register("ch06-e3")
def _ch06_e3(index: Any) -> str | None:
    """A tag index over the real corpus: tag -> sorted doc_ids."""
    expected: dict[str, list[str]] = {}
    for doc in _corpus():
        for tag in doc.tags:
            expected.setdefault(tag, []).append(doc.doc_id)
    expected = {tag: sorted(ids) for tag, ids in expected.items()}
    if not isinstance(index, dict):
        return "expected a dict of tag -> list of doc_ids"
    if set(index) != set(expected):
        missing = sorted(set(expected) - set(index))
        extra = sorted(set(index) - set(expected))
        return f"tag set is wrong: missing={missing} extra={extra}; hint: loop over doc.tags"
    for tag, ids in expected.items():
        if list(index[tag]) != ids:
            return f"tag {tag!r} maps to {list(index[tag])}, expected {ids} (sorted)"
    return None


# ---------------------------------------------------------------- chapter 03


@register("ch03-e1")
def _ch03_e1(attempts: Any) -> str | None:
    """Three distinct payloads the strict parser must reject."""
    if not isinstance(attempts, (list, tuple)) or len(attempts) != 3:
        return "expected a list of three strings"
    if len({str(attempt) for attempt in attempts}) != 3:
        return "the three attempts must be different strings"
    for attempt in attempts:
        try:
            parse_research_answer(str(attempt))
        except AnswerParseError:
            continue
        return (
            f"the parser accepted {str(attempt)[:60]!r}; hint: break a field, a type, or the JSON"
        )
    return None


@register("ch03-e2")
def _ch03_e2(golden: Any) -> str | None:
    """Three golden questions whose retrieval behaviour matches their kind."""
    kinds = ("answerable", "ambiguous", "unsupported")
    if not isinstance(golden, (list, tuple)) or [case.get("kind") for case in golden] != list(
        kinds
    ):
        return f"expected three cases with kinds {kinds}, in that order"
    documents = _corpus()
    for case in golden:
        question = str(case.get("question", "")).strip()
        behavior = str(case.get("expected_behavior", "")).strip()
        if not question or not behavior:
            return f"the {case.get('kind')} case needs both a question and an expected_behavior"
        hits = {scored.chunk.doc_id for scored in retrieve(question, documents, top_k=5)}
        if case["kind"] == "answerable" and not hits:
            return "the answerable question retrieves nothing; hint: use words from a corpus doc"
        if case["kind"] == "ambiguous" and len(hits) < 2:
            return "the ambiguous question retrieves under two documents; hint: overlap two topics"
        if case["kind"] == "unsupported" and hits:
            return (
                f"the unsupported question still retrieves {sorted(hits)}; hint: leave the corpus"
            )
    return None


@register("ch03-e3")
def _ch03_e3(answer: Any) -> str | None:
    """A ResearchAnswer that came through the parser, on any lane."""
    if not isinstance(answer, ResearchAnswer):
        return "expected result.answer (a ResearchAnswer); hint: answer_question(...).answer"
    if not 0.0 <= answer.confidence <= 1.0:
        return "confidence is out of range; the parser should have refused this"
    if answer.needs_human_review and answer.citations:
        return "a flagged refusal must carry no citations"
    return None


# ---------------------------------------------------------------- chapter 05


@register("ch04-e1")
def _ch04_e1(list_documents: Any) -> str | None:
    """The four-clause contract of list_documents(tag=None)."""
    if not callable(list_documents):
        return "pass the list_documents function itself"
    documents = _corpus()
    all_ids = sorted(doc.doc_id for doc in documents)
    if sorted(str(list_documents()).splitlines()) != all_ids:
        return "no tag must list every doc_id, one per line"
    if str(list_documents(tag="retrieval")).splitlines() != ["rag-basics"]:
        return "tag='retrieval' must list only rag-basics; hint: `tag in doc.tags`"
    for bad in ("", "nonexistent-tag"):
        try:
            list_documents(tag=bad)
        except ToolError as error:
            if bad and "retrieval" not in str(error):
                return "the unknown-tag ToolError must name the valid tags"
        except Exception as error:  # noqa: BLE001
            return f"tag={bad!r} raised {type(error).__name__}, expected ToolError"
        else:
            return f"tag={bad!r} did not raise ToolError; hint: validate at the boundary"
    return None


@register("ch04-e2")
def _ch04_e2(convert_currency: Any) -> str | None:
    """A currency tool judged with an injected, offline rate table."""
    if not callable(convert_currency):
        return "pass the convert_currency function itself"

    def fake_fetch(base: str) -> dict[str, float]:
        table = {"USD": {"EUR": 0.5, "BRL": 5.0}, "EUR": {"USD": 2.0}}
        if base not in table:
            raise ToolError(f"unknown base currency {base!r}")
        return table[base]

    result = convert_currency(100, "USD", "EUR", fetch=fake_fetch)
    if not isinstance(result, str) or "50.00" not in result:
        return f"100 USD at rate 0.5 must read '50.00 EUR' somewhere; got {result!r}"
    for amount, source, target in ((-1, "USD", "EUR"), (10, "usd", "EUR"), (10, "USD", "XXX")):
        try:
            convert_currency(amount, source, target, fetch=fake_fetch)
        except ToolError:
            continue
        except Exception as error:  # noqa: BLE001
            return (
                f"({amount}, {source!r}, {target!r}) raised {type(error).__name__}, want ToolError"
            )
        return f"({amount}, {source!r}, {target!r}) was accepted; hint: validate before fetching"
    return None


@register("ch05-e1")
def _ch05_e1(traces: Any) -> str | None:
    """Trace kinds at two budgets: both visible, budget never exceeded."""
    if not isinstance(traces, dict) or set(traces) != {1, 3}:
        return "expected a dict {1: [...kinds...], 3: [...kinds...]}"
    for budget, kinds in traces.items():
        if not isinstance(kinds, (list, tuple)) or not kinds:
            return f"traces[{budget}] must be a non-empty list of trace kinds"
        if sum(kind == "tool_call" for kind in kinds) > budget:
            return f"budget {budget} was exceeded; hint: pass max_tool_calls"
        if "decision" not in kinds:
            return f"traces[{budget}] shows no 'decision'; hint: [e.kind for e in result.trace]"
    return None


# ---------------------------------------------------------------- week 2 helpers

#: Words that mean the participant left the line unwritten. A check that accepts
#: these accepts nothing, which is the failure mode this whole module exists to stop.
_PLACEHOLDERS = ("", "...", "todo", "tbd", "n/a", "na", "none", "-", "?")


def _unwritten(text: object, minimum: int = 20) -> bool:
    """True when `text` is missing, a placeholder, or too short to be an answer."""
    if not isinstance(text, str):
        return True
    stripped = text.strip()
    return stripped.lower() in _PLACEHOLDERS or len(stripped) < minimum


def _retrieved_ids(query: str, top_k: int = 3) -> list[str]:
    return [scored.chunk.doc_id for scored in retrieve(query, _corpus(), top_k=top_k)]


# ---------------------------------------------------------------- chapter 06

#: The three queries the failure table classifies, and what retrieval really does with
#: each one (measured, not asserted): the middle query retrieves NOTHING, so its only
#: correct verdict is "missed"; the other two retrieve their topic and cannot be "missed".
CH06_QUERIES = (
    "what should an agent do when it cannot answer",
    "vector embeddings cosine similarity",
    "citations",
)
_CH06_VERDICTS = ("good", "missed", "irrelevant", "duplicated")


@register("ch06-e1")
def _ch06_e1(table: object) -> str | None:
    """The failure table: a verdict per query, judged against what retrieval did."""
    if not isinstance(table, (list, tuple)) or len(table) != 3:
        return "expected a list of exactly three rows, one per query"
    for row, query in zip(table, CH06_QUERIES, strict=True):
        if not isinstance(row, dict) or "verdict" not in row:
            return "every row needs a 'verdict' key"
        verdict = str(row["verdict"]).strip()
        word = verdict.split()[0].strip("—-:,").lower() if verdict else ""
        if word not in _CH06_VERDICTS:
            return f"verdict for {query[:34]!r} must start with one of {_CH06_VERDICTS}"
        if _unwritten(verdict, minimum=14):
            return f"the verdict for {query[:34]!r} needs a reason, not just the word"
        retrieved = _retrieved_ids(query)
        if not retrieved and word != "missed":
            return (
                f"{query[:34]!r} retrieves NOTHING, so its verdict is 'missed'; "
                "hint: run the cell above and read the output"
            )
        if retrieved and word == "missed":
            return f"{query[:34]!r} did retrieve {retrieved}, so it is not 'missed'"
    return None


# ---------------------------------------------------------------- chapter 07


@register("ch07-e1")
def _ch07_e1(finding: object) -> str | None:
    """A paraphrase that really misses its expected doc, and why."""
    keys = ("breaking_query", "expected_doc", "why_it_misses")
    if not isinstance(finding, dict) or set(finding) != set(keys):
        return f"expected a dict with keys {keys}"
    query, expected, why = (str(finding[k]).strip() for k in keys)
    if _unwritten(query, minimum=10):
        return "'breaking_query' needs a real paraphrase"
    if expected not in {doc.doc_id for doc in _corpus()}:
        return f"'expected_doc' must be a corpus doc_id, got {expected!r}"
    if _unwritten(why, minimum=40):
        return "'why_it_misses' needs one full sentence about word overlap"
    retrieved = _retrieved_ids(query)
    if expected in retrieved:
        return (
            f"that query DOES retrieve {expected} at top_k=3 ({retrieved}); "
            "hint: replace the doc's own words with everyday ones"
        )
    return None


@register("ch07-e2")
def _ch07_e2(report: object) -> str | None:
    """The honest report: an improvement AND a regression or risk."""
    keys = ("improvement", "regression_or_risk")
    if not isinstance(report, dict) or set(report) != set(keys):
        return f"expected a dict with keys {keys}"
    if _unwritten(report["improvement"], minimum=25):
        return "'improvement' needs a sentence naming what got better"
    risk = str(report["regression_or_risk"]).strip()
    if _unwritten(risk, minimum=25):
        return "'regression_or_risk' needs a sentence; 'none' is almost never true"
    return None


# ---------------------------------------------------------------- chapter 08

#: Measured on the seeded fake: the chain always spends exactly one model call and
#: cannot refuse before it, because retrieval's result flows straight into the prompt.
_CH08_TRUTH = {
    "chain": {"llm_calls": 1, "can_refuse_early": False},
    "tool_loop": {"can_refuse_early": True},
    "reflection": {"can_refuse_early": True},
}


@register("ch08-e1")
def _ch08_e1(comparison: object) -> str | None:
    """The comparison table, judged on the two columns that are facts."""
    if not isinstance(comparison, dict) or set(comparison) != set(_CH08_TRUTH):
        return f"expected a dict with keys {tuple(_CH08_TRUTH)}"
    for name, truth in _CH08_TRUTH.items():
        row = comparison[name]
        if not isinstance(row, dict) or not {
            "llm_calls",
            "can_refuse_early",
            "failure_modes",
        } <= set(row):
            return f"row {name!r} needs llm_calls, can_refuse_early and failure_modes"
        if row["llm_calls"] is None:
            return f"row {name!r} has no llm_calls; count them on the cells above"
        if "llm_calls" in truth and str(row["llm_calls"]).strip() not in {"1", "1 (+retry)"}:
            return f"the {name} spends exactly 1 model call (measured); got {row['llm_calls']!r}"
        if row["can_refuse_early"] is not truth["can_refuse_early"]:
            because = (
                "it always prompts the model with whatever retrieval returned"
                if name == "chain"
                else "it can refuse before any model call when retrieval is empty"
            )
            return f"can_refuse_early for {name} is {truth['can_refuse_early']}: {because}"
        if _unwritten(row["failure_modes"], minimum=20):
            return f"row {name!r} needs a real failure_modes sentence"
    return None


# ---------------------------------------------------------------- chapter 09


@register("ch09-e1")
def _ch09_e1(buckets: object) -> str | None:
    """The failure bucket for the plain fake: the generation side, not retrieval."""
    key = "grounded cases with plain FakeLLM"
    if not isinstance(buckets, dict) or key not in buckets:
        return f"expected a dict with the key {key!r}"
    answer = str(buckets[key]).strip()
    if _unwritten(answer, minimum=40):
        return "name the bucket AND why, in one sentence"
    lowered = answer.lower()
    if "instruction_following" not in lowered:
        return (
            "the bucket is instruction_following; hint: read a trace, retrieval "
            "returned the right chunks and the model ignored them"
        )
    if lowered.startswith("retrieval"):
        return "retrieval WORKED here; the trace shows the chunks it returned"
    return None


@register("ch07-e3")
def _ch07_e3(finding: object) -> str | None:
    """The cite-everything fake: the rate it really scores, and what that proves."""
    keys = ("pass_rate", "weakness")
    if not isinstance(finding, dict) or set(finding) != set(keys):
        return f"expected a dict with keys {keys}"
    try:
        reported = float(finding["pass_rate"])
    except (TypeError, ValueError):
        return "'pass_rate' must be the number run_evals reported (report.pass_rate)"
    cases = load_cases(REPO_ROOT / "data" / "evals" / "golden.jsonl")
    cite_all = FakeLLM(
        default=json.dumps(
            {
                "answer": "Everything is in rag-basics, trust me.",
                "citations": ["rag-basics"],
                "confidence": 0.9,
                "needs_human_review": False,
            }
        )
    )
    truth = run_evals(cases, _corpus(), cite_all).pass_rate
    if abs(reported - truth) > 0.005:
        return (
            f"the cite-everything fake scores {truth:.0%}, not {reported:.0%}; "
            "hint: report report.pass_rate from YOUR run"
        )
    if _unwritten(finding["weakness"], minimum=60):
        return "'weakness' needs a sentence about what the pass condition does not check"
    return None


# ---------------------------------------------------------------- chapter 10


@register("ch10-e1")
def _ch10_e1(skill: object) -> str | None:
    """The second skill: five sections written, and a before/after actually run."""
    sections = ("when_to_use", "workflow", "output_format", "failure_rules", "safety_boundary")
    evidence = ("without_skill", "with_skill", "improved_instruction")
    if not isinstance(skill, dict) or set(skill) != set(sections + evidence):
        return f"expected a dict with keys {sections + evidence}"
    for key in sections:
        if _unwritten(skill[key], minimum=25):
            return f"section {key!r} is not written yet"
    for key in ("without_skill", "with_skill"):
        if _unwritten(skill[key], minimum=30):
            return f"{key!r} needs an excerpt from the run you saved"
    if str(skill["without_skill"]).strip() == str(skill["with_skill"]).strip():
        return "the two runs are identical; the point of the exercise is the difference"
    if _unwritten(skill["improved_instruction"], minimum=25):
        return "'improved_instruction' names the line you fixed after seeing a failure"
    return None


# ---------------------------------------------------------------- chapter 11


@register("ch11-e1")
def _ch11_e1(memory: object) -> str | None:
    """The state wrapper, judged by running it: preference applied, reset clears, cap holds."""
    if not isinstance(memory, dict) or set(memory) != {"state_cls", "answer_fn"}:
        return "expected {'state_cls': SessionState, 'answer_fn': answer_with_state}"
    state_cls, answer_fn = memory["state_cls"], memory["answer_fn"]
    if not callable(state_cls) or not callable(answer_fn):
        return "pass the class and the function themselves, not instances or calls"
    probe = FakeLLM()
    state = state_cls()
    if not hasattr(state, "preferences") or not hasattr(state, "episodes"):
        return "SessionState needs 'preferences' and 'episodes'"
    state.preferences["answer_style"] = "short"
    answer_fn("How does chunking work in RAG?", state, probe)
    if not probe.calls:
        return "answer_fn never called the client; hint: it must run answer_question"
    if "(answer briefly)" not in probe.calls[-1][1]:
        return "(a) the 'short' preference did not reach the prompt the model saw"
    if not hasattr(state, "reset"):
        return "(b) SessionState needs a reset() method"
    state.reset()
    if state.preferences or state.episodes:
        return "(b) reset() left something behind"
    for index in range(7):
        answer_fn(f"question number {index} about chunking", state, FakeLLM())
    if len(state.episodes) != 5:
        return f"(c) episodes should cap at 5, got {len(state.episodes)} after 7 questions"
    return None


@register("ch11-e2")
def _ch11_e2(policy: object) -> str | None:
    """The storage policy: five lines answered, and a refuse-to-remember list."""
    if not isinstance(policy, str):
        return "expected the storage_policy string"
    text = policy.strip()
    if len(text) < 120:
        return "the policy needs every line filled, not just the labels"
    for label in ("STORED", "WHY", "CORRECTED BY", "EXPIRES", "WE REFUSE TO REMEMBER"):
        head, _, rest = text.partition(f"{label}:")
        if not head and not rest:
            return f"the policy has no {label}: line"
        answer = rest.split("\n")[0].strip() if rest else ""
        if label == "WE REFUSE TO REMEMBER":
            answer = rest.strip()
        if _unwritten(answer, minimum=12):
            return f"the {label}: line is not answered yet"
    return None


# ---------------------------------------------------------------- chapter 12


@register("cap01-e1")
def _cap01_e1(result: object) -> str | None:
    """Checkpoint 1: a supported question answered with the citation verified."""
    answer = getattr(result, "answer", None)
    if not isinstance(answer, ResearchAnswer):
        return "expected the AgentResult from answer_question, not its text"
    if answer.citations != ("rag-basics",):
        return f"citations should be ('rag-basics',) and are {answer.citations}"
    if answer.needs_human_review:
        return "a supported, cited answer must not be flagged for review"
    return None


@register("cap01-e2")
def _cap01_e2(refusal: object) -> str | None:
    """Checkpoint 2: an unsupported question refused BEFORE any model call."""
    if not isinstance(refusal, dict) or set(refusal) != {"result", "probe_calls"}:
        return "expected {'result': AgentResult, 'probe_calls': len(probe.calls)}"
    answer = getattr(refusal["result"], "answer", None)
    if not isinstance(answer, ResearchAnswer):
        return "'result' must be the AgentResult"
    if not answer.needs_human_review:
        return "an unsupported question must be flagged for review"
    if answer.citations:
        return f"a refusal cites nothing, and this one cites {answer.citations}"
    if refusal["probe_calls"] != 0:
        return (
            f"the model was called {refusal['probe_calls']} time(s); the refusal must "
            "happen before any model call, so probe.calls is empty"
        )
    return None


@register("cap01-e3")
def _cap01_e3(kinds: object) -> str | None:
    """Checkpoint 3: a trace a reviewer can follow."""
    if not isinstance(kinds, (list, tuple, set)):
        return "expected the trace kinds: [e.kind for e in result.trace]"
    missing = {"retrieve", "llm_call", "decision"} - set(kinds)
    if missing:
        return f"the trace is missing {sorted(missing)}"
    return None


@register("cap01-e4")
def _cap01_e4(report: object) -> str | None:
    """Checkpoint 4: the eval gate. v1 is done when every case passes."""
    rate = getattr(report, "pass_rate", None)
    if rate is None:
        return "expected the EvalReport from run_evals"
    if rate < 0.999:
        return f"the gate is green at 100% and this run scored {rate:.0%}"
    return None


@register("cap01-e5")
def _cap01_e5(issues: object) -> str | None:
    """The ranked issue list: Thursday's backlog, and demo day's honest limitation."""
    if not isinstance(issues, (list, tuple)) or len(issues) < 3:
        return "expected at least three ranked issues"
    ranks = []
    for row in issues:
        if not isinstance(row, dict) or not {"rank", "issue", "impact"} <= set(row):
            return "every row needs rank, issue and impact"
        if _unwritten(row["issue"], minimum=15):
            return "every issue needs a sentence, not a placeholder"
        if _unwritten(row["impact"], minimum=15):
            return "every issue needs its impact written; that is what ranks it"
        ranks.append(row["rank"])
    if sorted(ranks) != list(range(1, len(ranks) + 1)):
        return f"ranks must be 1..{len(ranks)} with no gaps or ties, got {ranks}"
    return None


# ---------------------------------------------------------------- chapter 13


@register("ch13-e1")
def _ch13_e1(checklist: object) -> str | None:
    """The safety checklist. Self-attested by design, and explicit rather than implied.

    Lane-aware since the session split into three. The fork line only applies if
    you actually ran the fork, and claiming it when you did not is exactly the
    kind of unearned attestation the session is about.
    """
    boxes = (
        "no_credentials_entered",
        "url_not_committed",
        "provenance_tier_named",
        "mode_for_an_unknown_api",
    )
    expected = {*boxes, "ran_the_fork_lane", "why_nothing_could_spend"}
    if not isinstance(checklist, dict) or set(checklist) != expected:
        return (
            f"expected a dict with {boxes} plus 'ran_the_fork_lane' and 'why_nothing_could_spend'"
        )
    unticked = [box for box in boxes if checklist[box] is not True]
    if unticked:
        return f"these are not ticked: {unticked}; do not leave the room until they are"
    if not isinstance(checklist["ran_the_fork_lane"], bool):
        return (
            "'ran_the_fork_lane' is True or False. Most people will answer False, and that is fine"
        )
    if _unwritten(checklist["why_nothing_could_spend"], minimum=40):
        return (
            "say in your own words why nothing you ran could have spent real money. "
            "If you stayed in the recorded and read-only lanes, that is the answer"
        )
    return None


@register("ch13-e2")
def _ch13_e2(lanes: object) -> str | None:
    """Which lane is the lowest one that can do each thing. 'never' is an answer."""
    truth = {
        "read the 16 tool names": "recorded",
        "derive the accounts one instruction needs": "recorded",
        "see the price a store charges today": "public-read-only",
        "sign anything": "fork",
        "spend real money on mainnet": "never",
    }
    allowed = {"recorded", "public-read-only", "fork", "never"}
    if not isinstance(lanes, dict) or set(lanes) != set(truth):
        return f"expected a lane for each of {sorted(truth)}"
    for activity, expected in truth.items():
        got = str(lanes[activity]).strip().lower()
        if got not in allowed:
            return f"{activity!r}: pick one of {sorted(allowed)}"
        if got != expected:
            why = {
                "recorded": "a fixture already holds this; the network adds nothing",
                "public-read-only": "a fixture goes stale, and this one is about today",
                "fork": "signing needs a key, and a key may only exist off mainnet",
                "never": "no lane in this course spends real money, and that is the point",
            }[expected]
            return f"{activity!r} is {expected!r}: {why}"
    return None


@register("ch12-e1")
def _ch12_e1(classified: object) -> str | None:
    """Of sixteen tools, two can change state. Knowing which two is the session."""
    changes_state = {"try_purchase", "submit_transaction"}
    builds_unsigned = {"prepare_purchase", "prepare_instruction", "plan_payment", "plan_swap"}
    problem = _keys_are_ch13(classified)
    if problem:
        return problem
    assert isinstance(classified, dict)
    got_changes = {str(name).strip() for name in classified["changes_state"]}
    got_builds = {str(name).strip() for name in classified["builds_unsigned"]}

    if got_changes != changes_state:
        extra = sorted(got_changes - changes_state)
        if "prepare_purchase" in extra:
            return (
                "prepare_purchase does not change state. It returns UNSIGNED bytes and a "
                "receipt; nothing moves until something signs them and submits"
            )
        if "verify_signed_transaction" in extra:
            return "verify_signed_transaction only checks bytes against a binding. It sends nothing"
        return f"changes_state should be {sorted(changes_state)}, got {sorted(got_changes)}"
    if got_builds != builds_unsigned:
        return f"builds_unsigned should be {sorted(builds_unsigned)}, got {sorted(got_builds)}"
    return None


def _keys_are_ch13(value: object) -> str | None:
    if not isinstance(value, dict) or set(value) != {"changes_state", "builds_unsigned"}:
        return (
            "expected a dict with 'changes_state' and 'builds_unsigned', each a list of tool names"
        )
    for key in ("changes_state", "builds_unsigned"):
        if not isinstance(value[key], list):
            return f"{key!r} is a list of tool names"
    return None


# ---------------------------------------------------------------- chapter 14


@register("ch02-e4")
def _ch02_e4(answer_with_timeout: object) -> str | None:
    """A hanging provider must become a defined refusal, judged by calling it."""
    if not callable(answer_with_timeout):
        return "pass the answer_with_timeout function itself"
    try:
        result = answer_with_timeout("How does chunking work in RAG?")
    except TimeoutError:
        return "the TimeoutError escaped; catch it and return a flagged refusal instead"
    answer = getattr(result, "answer", None)
    if not isinstance(answer, ResearchAnswer):
        return "return an AgentResult, so the caller handles one shape either way"
    if not answer.needs_human_review:
        return "a timeout is not an answer: set needs_human_review"
    if answer.citations:
        return "a timeout cites nothing"
    return None


@register("ch08-e2")
def _ch08_e2(comparison: object) -> str | None:
    """The graph appendix: it ran and was compared, or it was skipped for a stated reason."""
    keys = ("ran", "skipped_because", "framework_free_calls", "graph_calls", "difference")
    if not isinstance(comparison, dict) or set(comparison) != set(keys):
        return f"expected a dict with keys {keys}"
    if comparison["ran"] is not True:
        if _unwritten(comparison["skipped_because"], minimum=20):
            return (
                "if the appendix did not run, say why (no langgraph installed, no "
                "provider, model too small) — a blank is not a reason"
            )
        return None
    for key in ("framework_free_calls", "graph_calls"):
        if not isinstance(comparison[key], int) or comparison[key] < 1:
            return f"{key!r} must be the model-call count you measured"
    if _unwritten(comparison["difference"], minimum=40):
        return "'difference' names what the traces showed, in one sentence"
    return None


# ---------------------------------------------------------------- chapter 04


@register("ch01-e1")
def _ch01_e1(loop: object) -> str | None:
    """The task loop, evidenced. The rejection is the one that cannot be skipped."""
    keys = ("plan_approved", "diff_inspected", "rejected_change", "why_rejected", "risks")
    if not isinstance(loop, dict) or set(loop) != set(keys):
        return f"expected a dict with keys {keys}"
    if _unwritten(loop["plan_approved"], minimum=30):
        return "'plan_approved' quotes the plan you approved before any edit"
    if _unwritten(loop["diff_inspected"], minimum=30):
        return "'diff_inspected' names what you actually read in the diff"
    if _unwritten(loop["rejected_change"], minimum=20):
        return (
            "'rejected_change' names one change you refused. If you rejected "
            "nothing, you were not reviewing — that is the lesson, not a formality"
        )
    if _unwritten(loop["why_rejected"], minimum=25):
        return "'why_rejected' gives the reason: unsafe, unnecessary, or out of scope"
    if _unwritten(loop["risks"], minimum=25):
        return "'risks' records the remaining-risk summary you asked the assistant for"
    return None
