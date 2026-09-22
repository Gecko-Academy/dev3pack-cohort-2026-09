"""Fetch the Project 02 corpus: Item 1A of each company's latest 10-K, as raw HTML.

Instructor-only. Learners never run this: the files it writes are committed, so
the project works offline and every learner reads the same bytes.

    SEC_CONTACT="you@example.com" uv run python projects/02-sec-filings/fetch.py

WHY SEC_CONTACT. EDGAR's fair-access policy refuses (HTTP 403) any request whose
User-Agent does not carry a contact email. The address goes in the header of
this one run and nowhere else: it is read from the environment, never written
to disk, never committed.

WHY RAW HTML, AND WHY ONLY ITEM 1A. The project teaches cleaning, so the input
has to be dirty for real: inline styles, entities, page footers, a table of
contents that repeats every heading. Item 1A is "Risk Factors", which is exactly
the project's question: what are these companies worried about? Taking only
that item keeps the corpus near a megabyte instead of twenty.

WHY A TEXT-TO-HTML OFFSET MAP. Headings in these files are split across tags
(`<span>Item</span><span> 1A.</span>`), so a regex over raw HTML misses them.
The parser records where each piece of text came from in the raw file; the
heading search runs on text, and the cut is made in the HTML at the matching
offsets.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
SOURCES = HERE / "data" / "sources.json"

COMPANIES = {
    "AAPL": 320193,
    "MSFT": 789019,
    "NVDA": 1045810,
    "TSLA": 1318605,
    "KO": 21344,
    "NKE": 320187,
    "MELI": 1099590,
    "ABNB": 1559720,
}

START = re.compile(r"item\s*1a\s*\.?\s*[:\-–—]?\s*risk\s+factors", re.IGNORECASE)
END = re.compile(
    r"item\s*1b\s*\.?\s*[:\-–—]?\s*unresolved|item\s*1c\s*\.?\s*[:\-–—]?\s*cybersecurity"
    r"|item\s*1b\s*,\s*1c|item\s*2\s*\.?\s*[:\-–—]?\s*properties",
    re.IGNORECASE,
)


class FetchError(Exception):
    pass


def _get(url: str, contact: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": f"Dev3Pack bootcamp course data {contact}"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - pinned sec.gov hosts
        return response.read()


class _TextMap(HTMLParser):
    """Collect visible text, and the raw-HTML offset each text piece started at."""

    def __init__(self, raw: str) -> None:
        super().__init__(convert_charrefs=True)
        self.line_starts = [0]
        for match in re.finditer("\n", raw):
            self.line_starts.append(match.end())
        self.text: list[str] = []
        self.offsets: list[tuple[int, int]] = []  # (text position, raw position)
        self._length = 0

    def handle_data(self, data: str) -> None:
        line, column = self.getpos()
        self.offsets.append((self._length, self.line_starts[line - 1] + column))
        self.text.append(data)
        self._length += len(data)


def _raw_offset(offsets: list[tuple[int, int]], text_position: int) -> int:
    """The raw offset of the text piece that contains `text_position`."""
    best = offsets[0][1]
    for text_at, raw_at in offsets:
        if text_at > text_position:
            break
        best = raw_at
    return best


def _is_heading(text: str, chunk_starts: list[int], position: int) -> bool:
    """A heading opens its own text block; a cross-reference sits mid-sentence."""
    block = max((c for c in chunk_starts if c <= position), default=0)
    return not text[block:position].strip()


def item_1a(raw: str) -> str:
    """The raw HTML of Item 1A, from its heading to the next item's heading.

    Only matches that open a text block count as headings, and each start heading
    pairs with the NEAREST end heading after it. Pairing more loosely lets a
    table-of-contents entry reach the real Item 2 (swallowing Item 1 whole), or
    the real heading run on past 1B into 1C. Of the pairs left, the longest wins:
    the contents page's pair is a line long.
    """
    mapper = _TextMap(raw)
    mapper.feed(raw)
    # The parser already decoded entities (convert_charrefs), so text positions
    # line up with the offset map. The patterns tolerate any whitespace.
    text = "".join(mapper.text)
    chunk_starts = [text_at for text_at, _ in mapper.offsets]
    starts = [m.start() for m in START.finditer(text) if _is_heading(text, chunk_starts, m.start())]
    ends = [m.start() for m in END.finditer(text) if _is_heading(text, chunk_starts, m.start())]
    best: tuple[int, int] = (0, 0)
    for start in starts:
        after = [end for end in ends if end > start]
        if after and after[0] - start > best[1] - best[0]:
            best = (start, after[0])
    if best == (0, 0):
        raise FetchError("no Item 1A span found")
    if best[1] - best[0] < 5_000:
        raise FetchError(f"Item 1A span is only {best[1] - best[0]} characters")
    return raw[_raw_offset(mapper.offsets, best[0]) : _raw_offset(mapper.offsets, best[1])]


def main() -> int:
    contact = os.environ.get("SEC_CONTACT", "").strip()
    if "@" not in contact:
        print("Set SEC_CONTACT to an email address. EDGAR refuses requests without one.")
        return 2
    RAW.mkdir(parents=True, exist_ok=True)
    sources = []
    for ticker, cik in COMPANIES.items():
        meta = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", contact))
        recent = meta["filings"]["recent"]
        index = recent["form"].index("10-K")
        accession = recent["accessionNumber"][index]
        document = recent["primaryDocument"][index]
        folder = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{document}"
        time.sleep(0.2)  # EDGAR asks for at most ten requests a second
        raw = _get(url, contact).decode("utf-8", errors="replace")
        section = item_1a(raw)
        target = RAW / f"{ticker.lower()}-10k-item1a.html"
        target.write_text(section, encoding="utf-8")
        sources.append(
            {
                "ticker": ticker,
                "company": meta["name"],
                "cik": cik,
                "form": "10-K",
                "accession": accession,
                "period_of_report": recent["reportDate"][index],
                "filed": recent["filingDate"][index],
                "url": url,
                "section": "Item 1A. Risk Factors",
                "file": f"raw/{target.name}",
                "bytes": len(section.encode("utf-8")),
            }
        )
        print(f"{ticker:5} {recent['reportDate'][index]}  {len(section) / 1024:7.0f} KB  {url}")
        time.sleep(0.2)
    SOURCES.write_text(
        json.dumps({"fetched": date.today().isoformat(), "filings": sources}, indent=1) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
