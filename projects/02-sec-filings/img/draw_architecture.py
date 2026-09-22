"""Project 02 architecture: the offline lane and the online lane, in the road diagram's style."""

import matplotlib  # noqa: I001

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

BG, INK, DIM = "#0b1120", "#e6edf3", "#9aa5b8"
CYAN, GREEN, YELLOW, RED = "#22c3e6", "#2ecc71", "#f5c518", "#f0645a"
fig, ax = plt.subplots(figsize=(22, 10.5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 22)
ax.set_ylim(0, 10.5)
ax.axis("off")


def box(x, y, w, h, label, caption, color, fill=False, dashed=False, badge=None, lfs=12):
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.2",
            linewidth=2.2,
            edgecolor=color,
            facecolor=color if fill else BG,
            linestyle="--" if dashed else "-",
        )
    )
    ax.text(
        x,
        y + 0.22,
        label,
        ha="center",
        va="center",
        fontsize=lfs,
        fontweight="bold",
        color=BG if fill else color,
    )
    ax.text(x, y - 0.26, caption, ha="center", va="center", fontsize=8.2, color=BG if fill else INK)
    if badge:
        ax.add_patch(
            Circle(
                (x + w / 2, y - h / 2),
                0.21,
                facecolor=YELLOW,
                edgecolor=BG,
                linewidth=1.5,
                zorder=5,
            )
        )
        ax.text(
            x + w / 2,
            y - h / 2,
            badge,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=BG,
            zorder=6,
        )


def arrow(p1, p2, color=DIM, thin=False, dashed=False, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            p1,
            p2,
            arrowstyle="-|>",
            mutation_scale=12 if thin else 16,
            linewidth=1.1 if thin else 1.8,
            color=color,
            linestyle="--" if dashed else "-",
            connectionstyle=f"arc3,rad={rad}",
            zorder=3,
        )
    )


def lane(y, text, color):
    ax.text(0.4, y + 0.3, text, fontsize=13, fontweight="bold", color=color, va="center")
    ax.plot([0.4, 21.6], [y, y], color=color, linewidth=2.5)


# ---------------- offline lane
lane(9.6, "OFFLINE  ·  once per document set  ·  steps 2 to 6", CYAN)
oy, OW, OH = 8.1, 2.5, 1.25
ox = [1.9 + i * 3.64 for i in range(6)]
off = [
    ("Raw filings", "8 HTML files from EDGAR,\nItem 1A only", None),
    ("Clean", "HTML parser for tags,\nregex for page furniture", "e1"),
    ("Load documents", "one Document per company:\nid, text, tags", None),
    ("Chunk", "sentence-aware, max 800\ncharacters, nothing lost", "e2"),
    ("Embed", "nomic-embed-text,\n768 numbers each", None),
    ("Vector store", "ChromaDB: id, vector, text,\ncompany. 1,401 records", "e3"),
]
for x, (label, caption, badge) in zip(ox, off, strict=True):
    box(x, oy, OW, OH, label, caption, CYAN, badge=badge)
for i, t in enumerate(
    [
        "HTML text",
        "plain text, paragraphs",
        "8 Documents",
        "1,401 chunk texts, id = ticker#position",
        "1,401 vectors + texts + metadata",
    ]
):
    arrow((ox[i] + OW / 2, oy), (ox[i + 1] - OW / 2, oy))
    ax.text(
        (ox[i] + ox[i + 1]) / 2,
        oy + OH / 2 + 0.12,
        t,
        ha="center",
        va="bottom",
        fontsize=7.8,
        color=DIM,
    )

# ---------------- online lane
lane(5.55, "ONLINE  ·  once per question  ·  steps 7 and 8", GREEN)
ny, NW, NH = 4.0, 1.95, 1.25
nx = [1.35 + i * 2.41 for i in range(9)]
on = [
    ("Question", "the analyst's text,\nas typed", False),
    ("Embed question", "same model,\n768 numbers", False),
    ("Nearest k chunks", "cosine search in\nthe store, k = 4", False),
    ("Floor 0.58", "keep hits at or above;\nnone left = stop", False),
    ("Build prompt", "system = rules + shape\nuser = [id] passages + Q", False),
    ("MODEL", "qwen2.5:7b, one chat call;\nthe reply is the answer", True),
    ("Parse JSON", "answer, citations,\nconfidence, review flag", False),
    ("Check citations", "keep only ids the\nsearch returned", False),
    ("Answer + paragraph", "shown next to the\ncited chunk's text", False),
]
for x, (label, caption, fill) in zip(nx, on, strict=True):
    box(x, ny, NW, NH, label, caption, GREEN, fill=fill, lfs=9.4)
for i, t in enumerate(
    [
        "text",
        "1 vector",
        "4 × (score, id)",
        "hits above the floor",
        "2 messages",
        "1 JSON string",
        "ResearchAnswer",
        "answer + kept ids",
    ]
):
    arrow((nx[i] + NW / 2, ny), (nx[i + 1] - NW / 2, ny))
    ax.text(
        (nx[i] + nx[i + 1]) / 2,
        ny + NH / 2 + 0.12,
        t,
        ha="center",
        va="bottom",
        fontsize=7.8,
        color=DIM,
    )

# the store is shared: thin cyan arrows from the store down into the online lane
store = (ox[5], oy - OH / 2)
for target, rad, label, lx, ly in (
    ((nx[2] + 0.4, ny + NH / 2), -0.22, "ids + texts + metadata", 12.6, 5.85),
    ((nx[4] + 0.4, ny + NH / 2), -0.12, "chunk texts (collection.get)", 16.6, 6.45),
    ((nx[8] - 0.4, ny + NH / 2), 0.08, "the cited paragraph", 19.2, 6.3),
):
    arrow(store, target, color=CYAN, thin=True, rad=rad)
    ax.text(lx, ly, label, fontsize=7.8, color=CYAN, ha="center")

# return paths below the lane: retrieved ids reach the citation check; retrieval feeds the measure
arrow((nx[2] + 0.5, ny - NH / 2), (nx[7], ny - NH / 2), thin=True, rad=0.16)
ax.text(
    (nx[2] + nx[7]) / 2,
    2.02,
    "the set of retrieved ids, for the citation check",
    ha="center",
    fontsize=7.8,
    color=DIM,
)

# refusal exit
box(
    nx[3],
    1.35,
    2.35,
    1.05,
    "Refused, no call",
    "nothing above the floor;\nthe model is never asked",
    RED,
    dashed=True,
    lfs=11,
)
arrow((nx[3], ny - NH / 2), (nx[3], 1.35 + 0.55), color=RED, dashed=True)
ax.text(nx[3] + 0.18, 2.75, "no hits", fontsize=8, color=RED, va="center")
ax.text(
    nx[3] - 1.3,
    1.35,
    "nonsense scored 0.51 or less on this data;\nreal questions 0.64 or more",
    fontsize=7.8,
    color=DIM,
    va="center",
    ha="right",
)

# measure
box(
    nx[5],
    1.35,
    2.45,
    1.05,
    "Measure",
    "20 labelled questions, hit rate\nat 3, keyword vs embeddings",
    YELLOW,
    badge="e4",
    lfs=11,
)
arrow((nx[2] - 0.5, ny - NH / 2), (nx[5] - 1.22, 1.35), thin=True, rad=0.3)
ax.text(
    nx[5] + 1.35,
    1.35,
    "top-3 ids per question:\nthe measure reads retrieval only",
    fontsize=7.8,
    color=DIM,
    va="center",
)

# annotations
ax.text(
    nx[5],
    ny - NH / 2 - 0.2,
    "the ONLY place a model writes;\neverything else is your code",
    ha="center",
    va="top",
    fontsize=8.2,
    color=GREEN,
    fontweight="bold",
)
ax.text(
    nx[4],
    ny - NH / 2 - 0.2,
    "78% of the prompt\nis the passages",
    ha="center",
    va="top",
    fontsize=7.8,
    color=DIM,
)
ax.text(
    nx[7],
    ny - NH / 2 - 0.2,
    "parser checks shape · app checks against retrieval\n· only a human checks the paragraph",
    ha="center",
    va="top",
    fontsize=7.6,
    color=DIM,
)

# legend
lx, ly = 0.5, 0.3
ax.add_patch(
    FancyBboxPatch(
        (lx, ly),
        0.55,
        0.3,
        boxstyle="round,pad=0.01,rounding_size=0.06",
        facecolor=GREEN,
        edgecolor=GREEN,
    )
)
ax.text(lx + 0.7, ly + 0.15, "filled = model call", va="center", fontsize=8, color=INK)
ax.add_patch(
    FancyBboxPatch(
        (lx + 2.9, ly),
        0.55,
        0.3,
        boxstyle="round,pad=0.01,rounding_size=0.06",
        facecolor=BG,
        edgecolor=RED,
        linestyle="--",
    )
)
ax.text(lx + 3.6, ly + 0.15, "dashed = exit without a call", va="center", fontsize=8, color=INK)
ax.add_patch(Circle((lx + 7.0, ly + 0.15), 0.15, facecolor=YELLOW))
ax.text(lx + 7.3, ly + 0.15, "e1 to e4 = a project-02 check", va="center", fontsize=8, color=INK)
ax.plot([lx + 10.6, lx + 11.3], [ly + 0.15, ly + 0.15], color=CYAN, linewidth=1.2)
ax.text(
    lx + 11.45,
    ly + 0.15,
    "thin cyan = read back from the store",
    va="center",
    fontsize=8,
    color=INK,
)
ax.text(
    21.6,
    0.45,
    "Project 02 · RAG on SEC filings · every arrow carries something you can print",
    ha="right",
    fontsize=8.5,
    color=DIM,
)

fig.savefig("projects/02-sec-filings/img/architecture.png", facecolor=BG, bbox_inches="tight")
print("saved")
