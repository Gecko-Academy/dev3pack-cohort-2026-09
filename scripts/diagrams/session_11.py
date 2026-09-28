"""Session 11's figures: short-term against long-term memory, and what the store does.

Dark only, like sessions 4 to 10. The diagrams take their ideas from LangChain's memory
concepts page (docs.langchain.com/oss/python/concepts/memory) and redraw them in this
course's own terms: ana and bruno, the owner, the expiry, the cap of five.

The terminal cards print code and output that were RUN, on langgraph 1.2.12 and
chromadb 1.5.9, on 28 September 2026. A card is a claim about what the code does, so
change the code and the output together, by running it, or not at all.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .terminal import Terminal
from .theme import DECK_11, LIGHT, figure, install, palette

(
    INK,
    DIM,
    LINE,
    PAGE,
    PANEL,
    BLUE,
    GREEN,
    BROWN,
    PURPLE,
    RED,
    TINT,
    TAB_INK,
    BADGE_FACE,
    BADGE_EDGE,
) = palette(LIGHT)
install(globals())


def _card(s: Slide, box: tuple[float, float, float, float], accent: str) -> None:
    left, top, right, bottom = box
    s.ax.add_patch(
        FancyBboxPatch(
            (left, top),
            right - left,
            bottom - top,
            boxstyle=f"round,pad=0,rounding_size={SLIDE_ROUND}",
            facecolor=PANEL,
            edgecolor=accent,
            linewidth=SLIDE_EDGE,
        )
    )


def _pill(s: Slide, x: float, y: float, w: float, text: str, accent: str, size: float = 14) -> None:
    """A message or a step: a small outlined box with its label centred."""
    s.ax.add_patch(
        FancyBboxPatch(
            (x, y - 17),
            w,
            34,
            boxstyle="round,pad=0,rounding_size=8",
            facecolor=PAGE,
            edgecolor=accent,
            linewidth=1.8,
        )
    )
    s.text(x + w / 2, y, text, accent, size=size, ha="center")


def _rule(s: Slide, left: float, right: float, y: float) -> None:
    s.ax.plot([left, right], [y, y], color=LINE, linewidth=1.4)


@figure(dark=f"{DECK_11}/01-short-vs-long.png")
def short_vs_long(target: Path) -> None:
    """Two memories with different lifetimes, both ending in the same prompt."""
    s = Slide(1430, 700)
    s.text(34, 44, "Short-term and long-term memory", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "One lives as long as the conversation. The other outlives it, and that is why "
        "it needs an owner and an expiry.",
        DIM,
        size=17,
    )

    _card(s, (29, 132, 689, 478), BLUE)
    s.text(53, 166, "SHORT-TERM: THIS CONVERSATION", BLUE, size=16, bold=True)
    _rule(s, 53, 665, 192)
    for i, (who, text) in enumerate(
        (
            ("ana ›", "answer briefly, please"),
            ("bot ›", "Sure."),
            ("ana ›", "how does chunking work?"),
            ("bot ›", "It splits pages into passages."),
        )
    ):
        colour = RED if who.startswith("ana") else GREEN
        _pill(s, 53 + (40 if i % 2 else 0), 222 + i * 44, 400, f"{who} {text}", colour)
    s.text(
        53, 408, "Ours: SessionState   ·   LangGraph: a checkpointer, per thread_id", INK, size=14
    )
    s.text(53, 446, "Capped at five. Gone with the thread.", BLUE, size=16, bold=True)

    _card(s, (741, 132, 1401, 478), PURPLE)
    s.text(765, 166, "LONG-TERM: THE STORE", PURPLE, size=16, bold=True)
    _rule(s, 765, 1377, 192)
    rows = (
        ('("ana", "memories")', "locale = pt-BR", "expires 2026-10-28"),
        ('("ana", "memories")', "answer_style = short", "expires end of term"),
        ('("bruno", "memories")', "locale = en-GB", "expires None"),
    )
    for i, (space, value, expiry) in enumerate(rows):
        y = 226 + i * 54
        s.text(765, y, space, PURPLE, size=14, bold=True)
        s.text(1060, y, value, INK, size=14)
        s.text(1060, y + 22, expiry, RED if "None" in expiry else DIM, size=12)
    s.text(765, 408, "Ours: MemoryStore   ·   LangGraph: a store, per namespace", INK, size=14)
    s.text(765, 446, "Outlives the thread. Reads name the owner.", PURPLE, size=16, bold=True)

    s.arrow((359, 482), (640, 556), BLUE)
    s.arrow((1071, 482), (790, 556), PURPLE)
    _card(s, (455, 560, 975, 618), GREEN)
    s.text(715, 589, "the prompt the model actually sees", GREEN, size=16, bold=True, ha="center")

    s.text(
        34,
        664,
        "A memory the prompt never carries is decoration, whichever box it lives in. "
        "bruno's row with no expiry is the one to worry about.",
        BROWN,
        size=15,
    )
    s.save(target)


@figure(dark=f"{DECK_11}/02-the-cap.png")
def the_cap(target: Path) -> None:
    """Short-term memory is trimmed on purpose: the cap of five is an expiry."""
    s = Slide(1430, 560)
    s.text(34, 44, "The cap is an expiry", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Short-term memory is trimmed on purpose. Keep the last five questions, and the "
        "sixth pushes the first one out.",
        DIM,
        size=17,
    )
    questions = [f"Q{i}: question {i}" for i in range(1, 8)]
    for i, q in enumerate(questions):
        _pill(s, 60, 150 + i * 46, 330, q, RED if i < 2 else BLUE, size=15)
    s.text(225, 486, "seven asked", DIM, size=14, ha="center")

    s.arrow((430, 334), (700, 334), GREEN, scale=30, width=3)
    s.text(565, 306, "episodes[-5:]", GREEN, size=18, bold=True, ha="center")
    s.text(565, 366, "two lines of code", DIM, size=14, ha="center")

    for i, q in enumerate(questions[2:]):
        _pill(s, 740, 196 + i * 46, 330, q, BLUE, size=15)
    s.text(905, 440, "five kept", DIM, size=14, ha="center")

    s.text(1110, 196, "Q1 and Q2 are gone:", RED, size=16, bold=True)
    s.text(1110, 228, "not deleted by anyone,", INK, size=15)
    s.text(1110, 256, "expired by the rule.", INK, size=15)
    s.text(1110, 312, "LangGraph calls this", DIM, size=14)
    s.text(1110, 338, "trimming or filtering", DIM, size=14)
    s.text(1110, 364, "messages. Same idea.", DIM, size=14)
    s.text(
        34,
        530,
        "ch11-e1 judges it by running it: the cap holds, and reset clears.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_11}/03-three-shapes.png")
def three_shapes(target: Path) -> None:
    """Long-term memory comes in three shapes, and each one is corrected differently."""
    s = Slide(1430, 660)
    s.text(34, 44, "Three shapes of long-term memory", INK, size=26, bold=True)
    s.text(
        34,
        86,
        'Each one answers "how is it corrected?" differently. Pick the shape before you '
        "write the first memory.",
        DIM,
        size=17,
    )
    panels = (
        (
            "A PROFILE",
            "semantic memory",
            BLUE,
            ("{ locale: pt-BR,", "  answer_style: short }"),
            ("{ locale: en-GB,", "  answer_style: short }"),
            "one record, overwritten",
            "Easy to correct. One bad write",
            "and the old value is gone.",
        ),
        (
            "A COLLECTION",
            "episodic memory",
            PURPLE,
            ("[ asked about chunking,", "  asked about BM25 ]"),
            ("[ asked about chunking,", "  asked about BM25,", "  asked about HNSW ]"),
            "a list that grows",
            "Nothing lost, so it needs",
            "a cap and an expiry.",
        ),
        (
            "INSTRUCTIONS",
            "procedural memory",
            GREEN,
            ("You answer from the", "course pages."),
            ("You answer from the", "course pages. Short", "answers for ana."),
            "the prompt or skill, rewritten",
            "Your session 10 skill. It goes",
            "stale when the API changes.",
        ),
    )
    for i, (name, kind, accent, before, after, how, risk1, risk2) in enumerate(panels):
        left = 29 + i * 468
        right = left + 440
        _card(s, (left, 132, right, 600), accent)
        s.text(left + 24, 166, name, accent, size=17, bold=True)
        s.text(right - 24, 166, kind, DIM, size=13, ha="right")
        _rule(s, left + 24, right - 24, 192)
        s.text(left + 24, 218, "before", DIM, size=13)
        for j, line in enumerate(before):
            s.text(left + 24, 246 + j * 24, line, INK, size=14)
        s.arrow((left + 220, 312), (left + 220, 344), accent, scale=18)
        s.text(left + 24, 362, "after", DIM, size=13)
        for j, line in enumerate(after):
            s.text(left + 24, 390 + j * 24, line, accent, size=14)
        s.text(left + 24, 486, how, INK, size=15, bold=True)
        s.text(left + 24, 530, risk1, DIM, size=14)
        s.text(left + 24, 556, risk2, DIM, size=14)
    s.text(
        34,
        634,
        "Today's MemoryStore is a profile: one value per (owner, key). "
        "The episodes list is a collection.",
        BROWN,
        size=15,
    )
    s.save(target)


@figure(dark=f"{DECK_11}/04-hot-path-vs-background.png")
def hot_path_vs_background(target: Path) -> None:
    """When the memory is written: before the reply, or later, by something else."""
    s = Slide(1430, 640)
    s.text(34, 44, "When is the memory written?", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "In the hot path the user waits for the write. In the background they do not, and "
        "the next turn may not see it yet.",
        DIM,
        size=17,
    )
    _card(s, (29, 132, 629, 560), BLUE)
    s.text(53, 166, "IN THE HOT PATH", BLUE, size=16, bold=True)
    _rule(s, 53, 605, 192)
    steps = (
        ("ana's message", RED, 0),
        ("update memory", BLUE, 40),
        ("reply", GREEN, 40),
        ("ana's message", RED, 0),
        ("update memory", BLUE, 40),
        ("reply", GREEN, 40),
    )
    for i, (text, accent, indent) in enumerate(steps):
        _pill(s, 60 + indent, 228 + i * 50, 260, text, accent)
    s.text(380, 262, "fresh on the", INK, size=15)
    s.text(380, 288, "very next turn", INK, size=15)
    s.text(380, 420, "slower reply,", DIM, size=15)
    s.text(380, 446, "one more thing", DIM, size=15)
    s.text(380, 472, "that can fail", DIM, size=15)

    _card(s, (665, 132, 1401, 560), PURPLE)
    s.text(689, 166, "IN THE BACKGROUND", PURPLE, size=16, bold=True)
    _rule(s, 689, 1377, 192)
    s.text(800, 214, "the conversation", DIM, size=13, ha="center")
    s.text(1210, 214, "a job, later", DIM, size=13, ha="center")
    s.ax.plot([1030, 1030], [200, 540], color=LINE, linewidth=1.6, linestyle=(0, (2, 4)))
    for i, (text, accent, indent) in enumerate(
        (
            ("ana's message", RED, 0),
            ("reply", GREEN, 40),
            ("ana's message", RED, 0),
            ("reply", GREEN, 40),
        )
    ):
        _pill(s, 690 + indent, 246 + i * 50, 260, text, accent)
    _pill(s, 900, 454, 250, "30 minutes later...", INK)
    _pill(s, 1090, 510, 260, "update memory", BLUE)

    s.text(
        34,
        600,
        "Everything today writes in the hot path, inside the call that answers. Simple and "
        "right for a class; a busy app moves it out.",
        BROWN,
        size=15,
    )
    s.save(target)


@figure(dark=f"{DECK_11}/05-the-owner-is-the-namespace.png")
def owner_is_the_namespace(target: Path) -> None:
    """In LangGraph's store the owner is the namespace, and a search can forget it."""
    s = Slide(1430, 600)
    s.text(34, 44, "The owner is the namespace", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "The same rule as MemoryStore: the first part of the namespace is whose memory it is.",
        DIM,
        size=17,
    )
    _card(s, (29, 132, 589, 470), PURPLE)
    s.text(53, 166, "THE STORE", PURPLE, size=16, bold=True)
    _rule(s, 53, 565, 192)
    s.text(53, 228, '("ana", "memories")', PURPLE, size=16, bold=True)
    s.text(83, 262, "locale  ->  pt-BR", INK, size=15)
    s.text(53, 330, '("bruno", "memories")', PURPLE, size=16, bold=True)
    s.text(83, 364, "locale  ->  en-GB", INK, size=15)
    s.text(53, 430, "Two owners, the same key, never the same memory.", DIM, size=14)

    reads = (
        ('store.search(("ana",))', "ana's memories, nobody else's", GREEN),
        ('store.get(("ana", "memories"), "plan")', "None: a miss is an answer", GREEN),
        ("store.search(())", "ana's AND bruno's: no owner named", RED),
    )
    for i, (call, result, accent) in enumerate(reads):
        top = 132 + i * 116
        _card(s, (629, top, 1401, top + 96), accent)
        s.text(653, top + 32, call, INK, size=16, bold=True)
        s.text(653, top + 66, result, accent, size=16)
    s.text(
        34,
        530,
        "The third read is part 3's bug with a library name: a search that does not say "
        "whose memory it wants",
        BROWN,
        size=16,
    )
    s.text(
        34, 562, "gets everybody's. The store will not stop you. Your code has to.", BROWN, size=16
    )
    s.save(target)


@figure(dark=f"{DECK_11}/06-store-commands.png")
def store_commands(target: Path) -> None:
    """put, get, a miss, and search, with the output they printed."""
    t = Terminal("long-term memory: LangGraph's InMemoryStore")
    t.line(">>> from langgraph.store.memory import InMemoryStore", "blue")
    t.line(">>> store = InMemoryStore()", "blue")
    t.line(
        '>>> store.put(("ana", "memories"), "locale", {"value": "pt-BR", "expires": "2026-10-28"})',
        "blue",
    )
    t.line(
        '>>> store.put(("bruno", "memories"), "locale", {"value": "en-GB", "expires": None})',
        "blue",
    )
    t.blank()
    t.line('>>> store.get(("ana", "memories"), "locale").value', "blue")
    t.line("{'value': 'pt-BR', 'expires': '2026-10-28'}", "green")
    t.line('>>> store.get(("ana", "memories"), "plan")', "blue")
    t.line("None", "green")
    t.line('>>> [i.value for i in store.search(("ana",))]', "blue")
    t.line("[{'value': 'pt-BR', 'expires': '2026-10-28'}]", "green")
    t.save(target)


@figure(dark=f"{DECK_11}/07-store-leak.png")
def store_leak(target: Path) -> None:
    """The one read that returns everybody's memory."""
    t = Terminal("the same store, searched without an owner")
    t.line(">>> [i.namespace for i in store.search(())]", "blue")
    t.line("[('ana', 'memories'), ('bruno', 'memories')]", "red")
    t.blank()
    t.line(">>> store.list_namespaces()", "blue")
    t.line("[('ana', 'memories'), ('bruno', 'memories')]", "ink")
    t.blank()
    t.line("# No error, no warning. An empty namespace means everyone.", "amber")
    t.save(target)


@figure(dark=f"{DECK_11}/08-checkpointer-threads.png")
def checkpointer_threads(target: Path) -> None:
    """Short-term memory per thread: one thread keeps five, a new thread starts empty."""
    t = Terminal("short-term memory: a checkpointer, per thread")
    t.line(">>> from langgraph.checkpoint.memory import InMemorySaver", "blue")
    t.line(">>> app = graph.compile(checkpointer=InMemorySaver())", "blue")
    t.line('>>> t1 = {"configurable": {"thread_id": "t1"}}', "blue")
    t.line(">>> # seven questions on thread t1, the node keeps episodes[-5:]", "dim")
    t.line('>>> len(app.get_state(t1).values["episodes"])', "blue")
    t.line("5", "green")
    t.line('>>> app.get_state({"configurable": {"thread_id": "t2"}}).values', "blue")
    t.line("{}", "green")
    t.blank()
    t.line("# A new thread starts empty. What should survive it goes in the store.", "amber")
    t.save(target)


@figure(dark=f"{DECK_11}/09-demo-11-run.png")
def demo_11_run(target: Path) -> None:
    """One real run of demo 11: the trade, and the setting that lies."""
    t = Terminal("demos/11_memory_at_scale.ipynb, one run")
    t.line("exact, 20,000 memories:  0.61 ms per question", "ink")
    t.line("exact, 100,000 memories: 2.58 ms per question", "ink")
    t.blank()
    t.line("links  candidates   recall   ms/question", "dim")
    for row, colour in (
        ("    4          10     0.33      0.095", "red"),
        ("    4          50     0.86      0.099", "amber"),
        ("    4         200     0.95      0.148", "ink"),
        ("   16          10     0.92      0.080", "ink"),
        ("   16          50     1.00      0.109", "green"),
        ("   16         200     1.00      0.205", "green"),
    ):
        t.line(row, colour)
    t.blank()
    t.line("recall before the change: 0.39", "ink")
    t.line("the collection reports:   ef_search = 200", "amber")
    t.line("recall after the change:  0.39", "red")
    t.save(target)


SESSION_11 = (
    short_vs_long,
    the_cap,
    three_shapes,
    hot_path_vs_background,
    owner_is_the_namespace,
    store_commands,
    store_leak,
    checkpointer_threads,
    demo_11_run,
)
