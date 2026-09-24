"""Session 8's three figures: one loop against a graph, the RAG ladder, the indexes.

Each is drawn once and rendered twice -- light for the course page, dark for the
deck -- which is what `figure` is for."""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle

from .canvas import Canvas
from .theme import DECK_08, LIGHT, UNIT_08, figure, install, palette

# The active palette, kept in step by `use_theme`. Every primitive reads these
# as plain globals, which is what lets one drawing render under either theme;
# registering is what stops this module holding a stale copy of the other.
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


@figure(light=f"{UNIT_08}/loop-vs-graph.png", dark=f"{DECK_08}/01-loop-vs-graph.png")
def loop_vs_graph(target: Path) -> None:
    """One loop beside a graph of roles: the same task, and what each one spends."""
    c = Canvas(20, 13)
    c.title(
        0.4,
        12.35,
        "One loop, or a graph of roles",
        "The same task both ways: what each one is made of, and what each one spends",
    )

    # ---- left: one loop
    c.panel(0.4, 0.85, 9.3, 10.45, "One loop", BROWN, "ONE ROLE, ONE BUDGET", tab_w=3.0)
    c.node(1.75, 9.1, "target", BROWN, "Question", "one task", w=2.0, h=1.6)
    c.node(4.85, 9.1, "chip", BROWN, "agent", "one model, one prompt", w=2.6, h=1.9)
    c.node(8.1, 9.1, "gear", BROWN, "tool", "search_documents", w=2.2, h=1.7)
    c.arrow((2.8, 9.1), (3.5, 9.1))
    c.arrow((6.25, 9.1), (6.95, 9.1), "call")
    c.path(
        [(8.9, 8.25), (8.9, 7.55), (3.9, 7.55), (3.9, 8.15)],
        "and round again",
        text_at=(6.4, 7.63),
    )
    c.node(
        2.0,
        6.55,
        "checklist",
        BROWN,
        "step counter",
        "three tool calls, then it stops",
        w=2.6,
        h=1.7,
    )
    c.arrow((3.8, 7.68), (3.35, 7.45))
    c.node(
        7.1,
        5.9,
        "flag",
        BROWN,
        "Stop, with a receipt",
        "answered · budget · repeated_call",
        w=4.2,
        h=1.7,
    )
    c.arrow((3.35, 6.2), (4.85, 6.05), "the counter runs out")
    c.spend(5.05, 2.95, BROWN, ["1 model call", "2 with a corrective retry"])
    c.note(5.05, 1.8, "one role, one budget, one exit table")

    # ---- right: a graph of four roles
    c.panel(10.3, 0.85, 9.3, 10.45, "A graph", PURPLE, "FOUR NARROW ROLES", tab_w=3.0)
    c.ax.add_patch(
        FancyBboxPatch(
            (10.55, 4.25),
            8.9,
            5.9,
            boxstyle="round,pad=0,rounding_size=0.2",
            facecolor="none",
            edgecolor=PURPLE,
            linewidth=1.3,
            linestyle=(0, (4, 3)),
        )
    )
    c.ax.text(
        14.95,
        10.15,
        "ONE GRAPH: declared state, declared edges",
        fontsize=9.5,
        color=PURPLE,
        fontweight="bold",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=TINT[PURPLE], edgecolor=PURPLE),
    )
    roles = [
        ("coordinator", "picks the path"),
        ("researcher", "finds passages"),
        ("writer", "writes, cites"),
        ("critic", "checks, once"),
    ]
    for i, (name, what) in enumerate(roles):
        px = 11.52 + i * 2.32
        c.box(px, 9.1, 1.8, 1.7, PURPLE)
        c.chip(px, 9.45, PURPLE, s=0.55)
        c.ax.text(
            px,
            8.85,
            name,
            fontsize=9.5,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            family="monospace",
        )
        c.note(px, 8.62, what, size=8.5)
        if i:
            c.arrow((px - 1.42, 9.1), (px - 0.92, 9.1), color=PURPLE, solid=True)

    # the one edge back, and the cap that makes it one
    c.ax.plot([18.48, 18.48, 16.16], [8.25, 7.45, 7.45], color=PURPLE, linewidth=1.3, zorder=2)
    c.arrow((16.16, 7.45), (16.16, 8.25), color=PURPLE, solid=True)
    c.badge(17.32, 7.45, "×1")
    c.note(17.32, 7.12, "cap: one revision")

    c.node(
        14.95,
        5.6,
        "layers",
        PURPLE,
        "shared state",
        "one typed dict, and every role reads it and writes it",
        w=4.4,
        h=1.7,
    )
    c.arrow((13.3, 6.45), (11.8, 8.25), "reads")
    c.arrow((15.6, 8.25), (15.9, 6.45), "writes", dx=-0.55)
    c.spend(14.95, 2.95, PURPLE, ["2 model calls", "4 with a revision"])
    c.note(14.95, 1.8, "four roles, four instructions, and one edge you capped on purpose")

    c.ax.text(
        0.45,
        0.55,
        "More roles cost more calls. The table is how you find out what they bought.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(target)


@figure(light=f"{UNIT_08}/rag-family.png", dark=f"{DECK_08}/02-rag-family.png")
def rag_family(target: Path) -> None:
    """A ladder: each rung adds one thing to the rung below, and one new way to fail."""
    c = Canvas(18, 19.4)
    c.title(
        0.4,
        18.75,
        "The RAG family, rung by rung",
        "Read from the bottom up. Each rung adds one thing to the rung below it, "
        "and one new way to fail.",
    )

    rungs = [
        (
            0.3,
            "1",
            "A model\nalone",
            BLUE,
            "",
            "WHAT IT IS",
            True,
            [
                ("magnifier", "question", "as the reader asked it"),
                ("chip", "model", "answers from what\nit memorised"),
                ("bubbles", "answer", "fluent, and nothing\nto check it against"),
            ],
            "It answers from memory, and nothing\non the page says where that came from.",
        ),
        (
            3.85,
            "2",
            "Naive\nRAG",
            GREEN,
            "PROJECT 02, STEPS 5 TO 8",
            "WHAT IT ADDS",
            True,
            [
                ("document", "chunk", "split into pieces"),
                ("chip", "embed", "numbers per piece"),
                ("cylinder", "top k", "the nearest few"),
                ("bubbles", "answer", "from those passages"),
            ],
            "It retrieves a confidently wrong passage,\nand the answer reads just as well.",
        ),
        (
            7.4,
            "3",
            "Grounded\nand\nchecked",
            GREEN,
            "PROJECT 02, STEP 9",
            "WHAT IT ADDS",
            False,
            [
                ("document", "citations", "every claim carries\nthe id it came from"),
                ("shield", "a similarity floor", "below it, refuse\nrather than answer"),
                ("checklist", "a labelled set", "questions whose\nanswers you know"),
            ],
            "It scores well on the questions\nit was tuned on.",
        ),
        (
            10.95,
            "4",
            "Routed\nand\nhybrid",
            BROWN,
            "",
            "WHAT IT ADDS",
            True,
            [
                ("hub", "a router", "narrows before\nit searches"),
                ("magnifier", "hybrid search", "keyword and\nembeddings together"),
                ("layers", "one ranked list", "both scores, merged"),
            ],
            "The router picks wrong, and the answer\nstill looks right.",
        ),
        (
            14.5,
            "5",
            "A team\nin a\ngraph",
            PURPLE,
            "PROJECT 03",
            "WHAT IT ADDS",
            False,
            [
                ("chip", "narrow roles", "coordinator, researcher,\nwriter, critic"),
                ("hub", "declared edges", "written down, not\ndiscovered at run time"),
                ("layers", "shared state", "one typed dict,\nevery role reads it"),
            ],
            "It costs more, and it takes a transition\nnobody declared.",
        ),
    ]

    h = 3.3
    for y, number, label, color, where, tag, arrows, cards, fails in rungs:
        c.row(y, h, label, color, where)
        c.badge(0.58, y + h - 0.18, number)
        m = y + 1.75
        c.ax.text(
            2.95,
            y + 2.85,
            tag,
            fontsize=9,
            fontweight="bold",
            color=color,
            ha="left",
            va="center",
        )
        n = len(cards)
        w = 1.95 if n == 4 else 2.3
        xs = [3.6 + i * (6.8 / (n - 1)) for i in range(n)]
        for x, (icon, name, note) in zip(xs, cards, strict=True):
            c.node(x, m, icon, color, name, note, w=w, h=1.7)
        if arrows:
            for a, b in zip(xs, xs[1:], strict=False):
                c.arrow((a + w / 2 + 0.02, m), (b - w / 2 - 0.02, m))
        c.failure(14.55, m, fails)

    c.ax.text(
        0.45,
        -0.25,
        "Climb a rung when a measured failure justifies it, and not before.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(target)


@figure(light=f"{UNIT_08}/vector-indexes.png", dark=f"{DECK_08}/03-vector-indexes.png")
def vector_indexes(target: Path) -> None:
    """What sits under a vector database: four structures, and no measurements.

    Deliberately numberless. Speed, memory and recall belong in the table on the
    page, where a figure cannot strip the source off them.
    """
    c = Canvas(18, 14)
    c.title(
        0.4,
        13.35,
        "What sits under a vector database",
        "Four index structures, drawn as shapes. This figure carries no measurements.",
    )

    # ---- flat: compare against every vector
    c.panel(0.4, 7.0, 8.3, 5.5, "Flat", BLUE, "EXACT", tab_w=2.2)
    flat = [
        (3.3, 11.0),
        (4.4, 11.0),
        (5.5, 11.0),
        (6.6, 11.0),
        (7.7, 11.0),
        (3.1, 10.1),
        (4.2, 10.1),
        (5.3, 10.1),
        (6.4, 10.1),
        (7.5, 10.1),
        (8.2, 10.1),
        (3.4, 9.2),
        (4.5, 9.2),
        (5.6, 9.2),
        (6.7, 9.2),
        (7.8, 9.2),
        (3.2, 8.3),
        (4.3, 8.3),
        (5.4, 8.3),
        (6.5, 8.3),
        (7.6, 8.3),
    ]
    for px, py in flat:
        c.ax.plot([1.6, px], [9.5, py], color=LINE, linewidth=0.7, zorder=1)
    for px, py in flat:
        c.dot(px, py, BLUE, filled=(px, py) == (3.1, 10.1))
    c.query_dot(1.6, 9.5, BLUE)
    c.label(1.6, 9.12, "query", size=9.5)
    c.note(3.1, 10.52, "the nearest one", size=8.8)
    c.note(4.55, 7.62, "every vector compared, one by one, exactly")

    # ---- IVF: clusters around centroids, most of them skipped
    c.panel(9.3, 7.0, 8.3, 5.5, "IVF", GREEN, "CLUSTERED", tab_w=2.2)
    clusters = [
        (11.3, 10.5, 1.15, 0.80, True),
        (13.85, 10.5, 1.15, 0.80, False),
        (16.3, 10.4, 1.10, 0.80, False),
        (12.6, 8.75, 1.15, 0.82, True),
        (15.4, 8.7, 1.15, 0.80, False),
    ]
    for cx, cy, rx, ry, searched in clusters:
        c.ax.add_patch(
            Ellipse(
                (cx, cy),
                rx * 2,
                ry * 2,
                facecolor=TINT[GREEN] if searched else PAGE,
                edgecolor=GREEN if searched else LINE,
                linewidth=1.6 if searched else 1.3,
                linestyle="-" if searched else (0, (4, 3)),
                zorder=2,
            )
        )
        c.centroid(cx, cy + 0.18, GREEN if searched else DIM)
        for ox, oy in ((-0.6, -0.15), (-0.2, -0.45), (0.25, -0.42), (0.62, -0.1)):
            c.dot(cx + ox, cy + oy, GREEN)
        c.note(
            cx,
            cy + ry - 0.08,
            "searched" if searched else "skipped",
            color=GREEN if searched else DIM,
            size=8.8,
        )
    for cx, cy, _rx, _ry, searched in clusters:
        if searched:
            c.ax.plot([10.4, cx], [9.3, cy + 0.18], color=GREEN, linewidth=1.4, zorder=3)
    c.query_dot(10.4, 9.3, GREEN)
    c.label(10.4, 8.95, "query", size=9.5)
    c.note(13.45, 7.62, "the query searches its nearest clusters, and skips the rest")

    # ---- PQ: pieces, each replaced by a short code
    c.panel(0.4, 0.8, 8.3, 5.5, "PQ", BROWN, "COMPRESSED", tab_w=2.1)
    c.label(4.55, 5.08, "one long vector", size=10.5)
    c.ax.add_patch(
        Rectangle(
            (1.3, 4.25),
            6.5,
            0.45,
            facecolor=TINT[BROWN],
            edgecolor=INK,
            linewidth=1.4,
            zorder=3,
        )
    )
    edges = [1.3 + 6.5 * k / 4 for k in range(5)]
    for x in edges[1:-1]:
        c.ax.plot([x, x], [4.25, 4.70], color=INK, linewidth=1.3, zorder=4)
    codes = ["kq", "mv", "zt", "bd"]
    middles = [(edges[k] + edges[k + 1]) / 2 for k in range(4)]
    for sx, code in zip(middles, codes, strict=True):
        c.arrow((sx, 4.22), (sx, 3.80))
        c.ax.add_patch(
            FancyBboxPatch(
                (sx - 0.475, 3.2),
                0.95,
                0.6,
                boxstyle="round,pad=0,rounding_size=0.1",
                facecolor=TINT[BROWN],
                edgecolor=BROWN,
                linewidth=1.4,
                zorder=3,
            )
        )
        c.ax.text(
            sx,
            3.5,
            code,
            fontsize=10,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            family="monospace",
            zorder=4,
        )
    c.note(4.55, 3.05, "each piece becomes a short code")
    c.ax.add_patch(
        Rectangle(
            (3.53, 2.25),
            2.04,
            0.5,
            facecolor=TINT[BROWN],
            edgecolor=INK,
            linewidth=1.4,
            zorder=3,
        )
    )
    for k in range(1, 4):
        c.ax.plot([3.53 + 0.51 * k] * 2, [2.25, 2.75], color=INK, linewidth=1.1, zorder=4)
    for k, code in enumerate(codes):
        c.ax.text(
            3.785 + 0.51 * k,
            2.5,
            code,
            fontsize=8.5,
            color=INK,
            ha="center",
            va="center",
            family="monospace",
            zorder=4,
        )
    c.label(4.55, 2.10, "what gets stored", size=10.5)
    c.shield(6.85, 2.5, RED, s=0.8)
    c.ax.text(
        7.25,
        2.5,
        "the original\nis not\nrecoverable",
        fontsize=8.6,
        color=RED,
        ha="left",
        va="center",
        style="italic",
        linespacing=1.3,
    )
    c.note(4.55, 1.35, "small, and lossy")

    # ---- HNSW: sparse on top, dense at the bottom, a greedy descent
    c.panel(9.3, 0.8, 8.3, 5.5, "HNSW", PURPLE, "LAYERED", tab_w=2.4)
    bands = [(3.95, "sparse"), (2.85, "denser"), (1.75, "every vector")]
    for by, name in bands:
        c.ax.add_patch(
            FancyBboxPatch(
                (10.3, by),
                6.0,
                0.8,
                boxstyle="round,pad=0,rounding_size=0.15",
                facecolor="none",
                edgecolor=PURPLE,
                linewidth=1.3,
                linestyle=(0, (4, 3)),
                zorder=1,
            )
        )
        c.ax.text(
            16.5,
            by + 0.4,
            name,
            fontsize=9,
            color=DIM,
            ha="left",
            va="center",
            style="italic",
        )
    for px in (10.9, 12.6, 14.3, 15.8):
        c.dot(px, 4.35, PURPLE)
    for px in (10.8, 11.8, 12.9, 14.0, 15.1, 15.9):
        c.dot(px, 3.25, PURPLE)
    for px in (10.7, 11.25, 11.8, 12.35, 12.9, 13.45, 14.0, 14.55, 15.1, 15.65, 16.0):
        c.dot(px, 2.15, PURPLE)
    for p1, p2 in (
        ((11.2, 4.35), (12.35, 4.35)),
        ((12.6, 4.15), (12.9, 3.45)),
        ((13.15, 3.25), (13.75, 3.25)),
        ((14.0, 3.05), (13.6, 2.35)),
        ((13.65, 2.15), (14.4, 2.15)),
    ):
        c.arrow(p1, p2, color=PURPLE, solid=True)
    c.query_dot(10.9, 4.35, PURPLE, s=0.9)
    c.label(10.9, 5.02, "entry point", size=9.5)
    c.dot(14.55, 2.15, PURPLE, r=0.13, filled=True)
    c.note(14.55, 1.68, "nearest neighbour", size=8.8)
    c.note(13.45, 1.35, "an entry point at the top, and a greedy descent to the bottom")

    c.ax.text(
        0.45,
        0.45,
        "Structure only. Speed, memory and recall are measurements, and they live in the "
        "table on the page, where they carry a source.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(target)
