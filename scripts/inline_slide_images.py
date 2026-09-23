"""Build a session's self-contained deck: the slides we present, images inlined.

    uv run python scripts/inline_slide_images.py \
        docs/instructor/sessions/session-08-loops-and-graphs

`slides.mdx` holds two things: a generated spine that follows the session's own
concept pages, and the slides we actually stand up and present, written after
`<!-- generated:end -->`. This writes the second one out as `slides-standalone.mdx`
with every `![](img/x.png)` replaced by a `data:image/png;base64,...` URI, so the
file travels alone — it is what the designer generates the deck from.

Re-run it after re-rendering a figure; it is idempotent and reads nothing but
`slides.mdx` and the PNGs beside it.

Sessions 3, 4, 5 and 7 have standalone decks that interleave the generated spine,
assembled by hand before this existed. This does not rebuild those: pass it a
session directory, never a glob.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
END = "<!-- generated:end -->"
IMAGE = re.compile(r"!\[([^\]]*)\]\((?!data:|https?:)([^)]+)\)")

HEADER = """<!-- Presentation order, and the deck we stand up and present. These are the
slides after `generated:end` in slides.mdx, in the order they are taught; the
generated spine above that marker follows the session's concept pages and is
read, not presented. Every image is inlined as a data URI, so this one file is
self-contained: it is what the designer generates from, and the only file to
send. Rebuild it with scripts/inline_slide_images.py, never by hand. -->"""


class DeckError(Exception):
    """The deck cannot be assembled from what is on disk."""


def inline_images(text: str, base: Path) -> str:
    """Replace every relative image reference with a data URI read from `base`."""

    def swap(match: re.Match[str]) -> str:
        alt, reference = match.group(1), match.group(2).strip()
        source = (base / reference).resolve()
        if not source.is_file():
            raise DeckError(f"{reference} is referenced by the deck and is not on disk")
        kind, _ = mimetypes.guess_type(source.name)
        if kind is None:
            raise DeckError(f"{reference} has no recognisable image type")
        payload = base64.b64encode(source.read_bytes()).decode("ascii")
        return f"![{alt}](data:{kind};base64,{payload})"

    return IMAGE.sub(swap, text)


def standalone(slides: Path) -> str:
    """The frontmatter, the title slide, the header note, then the presented slides."""
    text = slides.read_text()
    if END not in text:
        raise DeckError(f"{slides} has no {END} marker")
    spine, presented = text.split(END, 1)
    presented = presented.strip("\n")
    if not presented:
        raise DeckError(f"{slides} has no slides after {END} — nothing to present")

    # the generated spine opens with the marp frontmatter and the title slide,
    # and both belong to every rendering of this deck
    head = spine.split("<!-- generated:start -->", 1)[-1].lstrip("\n")
    opening = re.match(r"(---\n.*?\n---\n)\n(.*?)\n\n---\n", head, flags=re.S)
    if opening is None:
        raise DeckError(f"{slides} has no marp frontmatter and title slide to open with")
    frontmatter, title = opening.group(1), opening.group(2)

    # the note rides on the title slide, as a presenter comment, so it never
    # renders as a blank slide of its own
    deck = f"{frontmatter}\n{title}\n\n{HEADER}\n\n---\n\n{presented}\n"
    return inline_images(deck, slides.parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path, help="a docs/instructor/sessions/<session> directory")
    args = parser.parse_args(argv)

    session = args.session if args.session.is_absolute() else Path.cwd() / args.session
    slides = session / "slides.mdx"
    if not slides.is_file():
        raise DeckError(f"no slides.mdx in {session}")
    target = session / "slides-standalone.mdx"
    target.write_text(standalone(slides))
    print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
