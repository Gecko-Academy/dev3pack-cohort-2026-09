"""Render the course as the static site a learner reads.

    uv run --extra site python scripts/course_html.py            # build into site/
    uv run --extra site python scripts/course_html.py --serve     # build, then serve it

WHY THIS EXISTS. The pages are MDX carrying `<Question>` blocks, which is the
Hugging Face course format, and nothing renders that by reading the file. GitHub's
preview shows the headings and then prints

    <Question choices={[{ text: "An AI model that can reason...", explain: ...

as a paragraph — the same on Hugging Face's own repository, so it is the format,
not our authoring. The explanations are the teaching, and that is exactly what is
lost. So the pages get rendered rather than read raw.

TRANSPORT ONLY, like every other generator here. `units/en/_toctree.yml` is the
single ordering source, and this file reads it rather than recomputing the order:
a second opinion about what comes after what is how a table of contents starts
disagreeing with the course. Whatever the toctree says, the sidebar says.

The output is `site/`, which is generated and NOT committed — there is no honest
`--check` for a tree of HTML, and a stale committed site that looks current is
worse than no site. Rebuild it; it takes under a second.
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import shutil
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.read import (  # noqa: E402
    Entry,
    Page,
    ReadError,
    render,
    toctree,
)

OUT = ROOT / "site"


# The page model -- parsing `<Question>`, rendering markdown, reading the
# toctree -- lives in `bootcamp_agent.read`, because it is what a page IS and
# three surfaces need it: the notebook, this site, and whatever comes later.
# What stays here is the site AROUND a page: the shell, the sidebar, the files.


# --------------------------------------------------------------------------
# The page shell
# --------------------------------------------------------------------------

STYLE = """
:root{--bg:#fff;--fg:#1b1b1f;--muted:#6b6b76;--line:#e3e3e8;--accent:#2f6f4f;
--side:#fafafa;--code:#f4f4f6;--ok:#1d7a4c;--okbg:#eaf6ef}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e6e6ea;--muted:#9a9aa6;
--line:#24262e;--accent:#7fd1a5;--side:#12141a;--code:#181b22;--ok:#7fd1a5;--okbg:#16241d}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.layout{display:grid;grid-template-columns:290px minmax(0,1fr) 230px;min-height:100vh}
nav.side{background:var(--side);border-right:1px solid var(--line);padding:22px 16px;
overflow-y:auto;max-height:100vh;position:sticky;top:0}
nav.side h1{font-size:15px;margin:0 0 18px}
nav.side h1 a{color:var(--fg);text-decoration:none}
nav.side .group{font-size:11px;letter-spacing:.08em;text-transform:uppercase;
color:var(--muted);margin:20px 0 7px}
nav.side a.page{display:block;padding:5px 9px;border-radius:6px;color:var(--fg);
text-decoration:none;font-size:14px}
nav.side a.page:hover{background:var(--line)}
nav.side a.page[aria-current]{background:var(--line);font-weight:600}
main{padding:40px 52px 90px;max-width:860px}
aside.onthispage{padding:40px 18px;font-size:13px;position:sticky;top:0;
max-height:100vh;overflow-y:auto}
aside.onthispage a{display:block;color:var(--muted);text-decoration:none;padding:3px 0}
aside.onthispage a:hover{color:var(--accent)}
aside.onthispage a.h3{padding-left:12px}
h1,h2,h3{line-height:1.25}
h2{margin-top:2.2em;padding-top:.3em;border-top:1px solid var(--line)}
code{background:var(--code);padding:.12em .35em;border-radius:4px;font-size:.9em}
pre{background:var(--code);padding:14px 16px;border-radius:8px;overflow-x:auto}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left}
blockquote{margin:1em 0;padding:.4em 1em;border-left:3px solid var(--line);color:var(--muted)}
img{max-width:100%}
.question{margin:1.1em 0 1.8em}
.choices{list-style:none;margin:0;padding:0}
.choice{margin:7px 0}
.choice summary{padding:10px 13px;border:1px solid var(--line);border-radius:8px;
cursor:pointer;font-size:15px;list-style:none}
.choice summary::-webkit-details-marker{display:none}
.choice summary:hover{border-color:var(--accent)}
.choice details[open] summary{border-color:var(--accent);border-bottom-left-radius:0;
border-bottom-right-radius:0}
.choice .explain{margin:0;padding:9px 13px;font-size:14px;color:var(--muted);
border:1px solid var(--line);border-top:0;border-radius:0 0 8px 8px}
.tick{color:var(--ok);font-weight:700}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:64px;
padding-top:20px;border-top:1px solid var(--line);font-size:14px}
.pager a{text-decoration:none}
.crumb{color:var(--muted);font-size:13px;margin-bottom:6px}
@media(max-width:1100px){.layout{grid-template-columns:260px minmax(0,1fr)}
aside.onthispage{display:none}}
@media(max-width:760px){.layout{grid-template-columns:1fr}
nav.side{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line)}
main{padding:26px 20px 70px}}
"""

SCRIPT = """
// PURE ENHANCEMENT. The quiz is <details>, so it already works with this file
// blocked, with JavaScript off, and inside a notebook -- where a <script>
// inserted through innerHTML never runs at all. All this adds is closing the
// other choices when one opens, so the page does not become a wall of answers.
document.addEventListener('toggle', function (event) {
  var opened = event.target;
  if (!opened.open || !opened.closest('.choices')) return;
  opened.closest('.choices').querySelectorAll('details').forEach(function (other) {
    if (other !== opened) { other.open = false; }
  });
}, true);
"""


def _depth(local: str) -> str:
    """The `../` prefix that reaches the site root from this page."""
    return "../" * local.count("/")


def _sidebar(groups: list[tuple[str, list[Entry]]], here: str) -> str:
    up = _depth(here)
    out = [f'<h1><a href="{up}index.html">Dev3Pack AI-Engineering Bootcamp</a></h1>']
    for title, entries in groups:
        if not entries:
            continue
        out.append(f'<p class="group">{html.escape(title)}</p>')
        for entry in entries:
            current = ' aria-current="page"' if entry.local == here else ""
            out.append(
                f'<a class="page" href="{up}{entry.local}.html"{current}>'
                f"{html.escape(entry.title)}</a>"
            )
    return "\n".join(out)


def _onthispage(page: Page) -> str:
    links = [
        f'<a class="h{level}" href="#{anchor}">{html.escape(shown)}</a>'
        for level, shown, anchor in page.headings
        if 2 <= level <= 3
    ]
    if not links:
        return ""
    return '<p class="group">On this page</p>' + "".join(links)


def _pager(entries: list[Entry], position: int) -> str:
    here = entries[position]
    up = _depth(here.local)
    left = right = ""
    if position > 0:
        previous = entries[position - 1]
        left = f'<a href="{up}{previous.local}.html">← {html.escape(previous.title)}</a>'
    if position + 1 < len(entries):
        following = entries[position + 1]
        right = f'<a href="{up}{following.local}.html">{html.escape(following.title)} →</a>'
    return f'<div class="pager"><span>{left}</span><span>{right}</span></div>'


def shell(page: Page, entry: Entry, sidebar: str, pager: str) -> str:
    up = _depth(entry.local)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(page.title)} — Dev3Pack</title>
<link rel="stylesheet" href="{up}style.css">
</head><body>
<div class="layout">
<nav class="side">{sidebar}</nav>
<main>
<p class="crumb">{html.escape(entry.group)}</p>
{page.body}
{pager}
</main>
<aside class="onthispage">{_onthispage(page)}</aside>
</div>
<script src="{up}course.js"></script>
</body></html>
"""


# --------------------------------------------------------------------------
# Building
# --------------------------------------------------------------------------


def build(out: Path = OUT) -> tuple[int, list[str]]:
    """Write the whole site. Returns how many pages, and what was missing."""
    groups = toctree()
    flat = [entry for _, entries in groups for entry in entries]
    missing = [entry.local for entry in flat if not entry.source.is_file()]
    present = [entry for entry in flat if entry.source.is_file()]

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "style.css").write_text(STYLE, encoding="utf-8")
    (out / "course.js").write_text(SCRIPT, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    # Only pages that exist go in the sidebar: a week that has not been
    # published yet has no file, and a link to it would 404 rather than teach.
    shown = [(title, [e for e in entries if e.source.is_file()]) for title, entries in groups]

    for position, entry in enumerate(present):
        page = render(entry.source)
        destination = out / f"{entry.local}.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            shell(page, entry, _sidebar(shown, entry.local), _pager(present, position)),
            encoding="utf-8",
        )

    if present:
        first = present[0]
        (out / "index.html").write_text(
            f'<!doctype html><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={first.local}.html">'
            f'<a href="{first.local}.html">Start the course</a>',
            encoding="utf-8",
        )
    (out / "pages.json").write_text(
        json.dumps([{"local": e.local, "title": e.title} for e in present], indent=2),
        encoding="utf-8",
    )
    return len(present), missing


def serve(out: Path, port: int) -> int:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(out), **kwargs)  # type: ignore[arg-type]

        def log_message(self, *args: object) -> None:  # keep the console quiet
            return

    with socketserver.TCPServer(("127.0.0.1", port), Handler) as server:
        print(f"the course is at http://127.0.0.1:{port}/  (ctrl-c to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(OUT), help="where to write the site")
    parser.add_argument("--serve", action="store_true", help="serve it after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    out = Path(args.out)
    try:
        count, missing = build(out)
    except ReadError as error:
        print(f"{error}", file=sys.stderr)
        return 1

    print(f"built {count} pages -> {out}")
    if missing:
        print(
            f"  {len(missing)} not published yet: {', '.join(missing[:4])}"
            + (" ..." if len(missing) > 4 else "")
        )
    if args.serve:
        return serve(out, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
