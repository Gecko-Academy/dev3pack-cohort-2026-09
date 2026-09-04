"""Generate and verify the bootcamp certificate (SVG).

Issue (instructor — CERT_SIGNING_SECRET set, report must be a pass):
    uv run python final_assignment/certificate.py --report final_assignment/score_report.json --out certificate.svg

Preview (anyone, no secret — watermarked, carries no verification code):
    uv run python final_assignment/certificate.py --name "Ada Lovelace" --score 85 --out preview.svg

Verify (requires the same secret):
    uv run python final_assignment/certificate.py --verify certificate.svg

The verification code is HMAC-SHA256(secret, "name|score|date") truncated to 16
hex chars and embedded both visibly and in a machine-readable comment. Only a
holder of the course secret can issue or verify — students cannot self-issue.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path

COURSE = "Dev3Pack AI-Engineering Bootcamp"
COURSE_DATES = "September 14 – October 2, 2026"
SECRET_ENV = "CERT_SIGNING_SECRET"

_META_RE = re.compile(r"<!-- cert:name=(.*?);score=(\d+);date=(.*?);code=([0-9a-f]{16}) -->")


def signing_code(secret: str, name: str, score: int, issued: str) -> str:
    message = f"{name}|{score}|{issued}".encode()
    return hmac.new(secret.encode(), message, sha256).hexdigest()[:16]


def render(name: str, score: int, issued: str, code: str | None) -> str:
    """Render the certificate SVG. code=None -> watermarked preview."""
    verified_line = (
        f"Verification code: {code}"
        if code
        else "PREVIEW — NOT VERIFIED (issued certificates carry a signed code)"
    )
    meta = f"<!-- cert:name={name};score={score};date={issued};code={code} -->" if code else ""
    watermark = (
        ""
        if code
        else (
            '<text x="562" y="420" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
            'font-size="90" font-weight="800" fill="#c33" opacity="0.13" text-anchor="middle" '
            'transform="rotate(-18 562 420)">PREVIEW — NOT VERIFIED</text>'
        )
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1123 794" role="img"
     aria-label="Certificate of completion — {name}, {COURSE}, score {score}%">
  {meta}
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#19fb9b"/>
      <stop offset="0.5" stop-color="#43b4ff"/>
      <stop offset="1" stop-color="#9945ff"/>
    </linearGradient>
  </defs>
  <rect width="1123" height="794" fill="#fbfbfd"/>
  <rect x="18" y="18" width="1087" height="758" rx="16" fill="none" stroke="url(#edge)" stroke-width="5"/>
  <rect x="34" y="34" width="1055" height="726" rx="10" fill="none" stroke="#d8dce8" stroke-width="1.5"/>

  <g font-family="Segoe UI, Helvetica, Arial, sans-serif" text-anchor="middle">
    <text x="562" y="120" font-size="22" letter-spacing="6" fill="#7c87a3">DEV3PACK</text>
    <text x="562" y="185" font-size="44" font-weight="800" fill="#171b2b">Certificate of Completion</text>
    <text x="562" y="250" font-size="20" fill="#4a5470">This certifies that</text>
    <text x="562" y="325" font-size="52" font-weight="700" fill="#171b2b">{name}</text>
    <rect x="380" y="352" width="364" height="4" rx="2" fill="url(#edge)"/>
    <text x="562" y="410" font-size="20" fill="#4a5470">has successfully completed the</text>
    <text x="562" y="452" font-size="30" font-weight="700" fill="#171b2b">{COURSE}</text>
    <text x="562" y="495" font-size="19" fill="#4a5470">{COURSE_DATES} · 15 sessions · capstone delivered and demonstrated</text>
    <text x="562" y="560" font-size="24" font-weight="700" fill="#171b2b">Final score: {score}%</text>
    <text x="562" y="595" font-size="16" fill="#7c87a3">graded on the private question set — grounded answers with verified citations,</text>
    <text x="562" y="618" font-size="16" fill="#7c87a3">refusal on unsupported questions, injection defended</text>

    <text x="300" y="700" font-size="16" fill="#4a5470">Issued: {issued}</text>
    <text x="824" y="700" font-size="16" fill="#4a5470">Instructor, Dev3Pack</text>
    <rect x="704" y="672" width="240" height="1.5" fill="#9aa3ba"/>
    <text x="562" y="742" font-size="14" fill="#9aa3ba">{verified_line}</text>
  </g>
  {watermark}
</svg>
"""


def verify(path: Path, secret: str) -> int:
    match = _META_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        print("INVALID: no signed metadata found (a PREVIEW certificate, or not ours)")
        return 1
    name, score, issued, code = match.group(1), int(match.group(2)), match.group(3), match.group(4)
    expected = signing_code(secret, name, score, issued)
    if hmac.compare_digest(code, expected):
        print(f"VALID: {name} — {score}% — issued {issued}")
        return 0
    print("INVALID: verification code does not match the certificate contents")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify a bootcamp certificate.")
    parser.add_argument("--report", type=Path, help="score_report.json from grade.py")
    parser.add_argument("--name", default="", help="Student name (overrides the report)")
    parser.add_argument(
        "--score", type=int, default=None, help="Score percent (overrides the report)"
    )
    parser.add_argument("--date", default="", help="Issue date YYYY-MM-DD (default: today)")
    parser.add_argument("--out", type=Path, default=Path("certificate.svg"))
    parser.add_argument("--verify", type=Path, help="Verify an issued certificate SVG and exit")
    args = parser.parse_args(argv)

    secret = os.environ.get(SECRET_ENV, "")

    if args.verify:
        if not secret:
            print(f"error: --verify needs {SECRET_ENV} (verification requires the course secret)")
            return 2
        return verify(args.verify, secret)

    name, score, passed = args.name, args.score, None
    if args.report:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        name = name or report.get("name", "")
        score = score if score is not None else report.get("score_percent")
        passed = report.get("passed")
    if not name or score is None:
        print("error: need --report, or both --name and --score")
        return 2
    issued = args.date or date.today().isoformat()

    code: str | None = None
    if secret:
        if passed is False or score < 70:
            print(f"refusing to issue a verified certificate for a non-passing score ({score}%)")
            return 1
        code = signing_code(secret, name, score, issued)
    args.out.write_text(render(name, score, issued, code), encoding="utf-8")
    kind = "VERIFIED certificate" if code else "preview (unverified)"
    print(f"{kind} written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
