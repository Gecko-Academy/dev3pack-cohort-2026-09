"""Render and verify Dev3Pack certificates.

New credential (publicly verifiable):
    uv run python final_assignment/certificate.py --receipt final_receipt.json \
      --public-key issuer.pub.pem --out certificate.svg
    uv run python final_assignment/certificate.py --verify certificate.svg \
      --receipt final_receipt.json --public-key issuer.pub.pem

Preview (never verified, even when a legacy secret is present):
    uv run python final_assignment/certificate.py --name "Ada" --score 85 --out preview.svg

Legacy v1 SVG verification remains available with CERT_SIGNING_SECRET. New issuance
from a caller-supplied name and score is deliberately impossible.
"""

from __future__ import annotations

import argparse
import base64
import hmac
import html
import json
import os
import re
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import receipt as final_receipt  # noqa: E402

COURSE = "Dev3Pack AI-Engineering Bootcamp"
COURSE_DATES = "September 14 – October 2, 2026"
SECRET_ENV = "CERT_SIGNING_SECRET"

_META_RE = re.compile(r"<!-- cert:name=(.*?);score=(\d+);date=(.*?);code=([0-9a-f]{16}) -->")
_V2_META_RE = re.compile(r"<!-- dev3pack-v2:([A-Za-z0-9+/=]+) -->")


def signing_code(secret: str, name: str, score: int, issued: str) -> str:
    """Legacy v1 HMAC retained only for already-issued record verification."""
    message = f"{name}|{score}|{issued}".encode()
    return hmac.new(secret.encode(), message, sha256).hexdigest()[:16]


def _score(score: int) -> int:
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise ValueError("score must be an integer from 0 to 100")
    return score


def render(name: str, score: int, issued: str, code: str | None) -> str:
    """Render a legacy v1 certificate or an unmistakable preview."""
    score = _score(score)
    safe_name = html.escape(name, quote=True)
    safe_issued = html.escape(issued, quote=True)
    verified_line = (
        f"Legacy verification code: {code}"
        if code
        else "PREVIEW — NOT VERIFIED (issued v2 credentials require a signed receipt)"
    )
    # Legacy metadata is preserved byte-for-byte for old certificate verification.
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
     aria-label="Certificate of completion — {safe_name}, {COURSE}, score {score}%">
  {meta}
  <defs><linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#19fb9b"/><stop offset="0.5" stop-color="#43b4ff"/><stop offset="1" stop-color="#9945ff"/></linearGradient></defs>
  <rect width="1123" height="794" fill="#fbfbfd"/>
  <rect x="18" y="18" width="1087" height="758" rx="16" fill="none" stroke="url(#edge)" stroke-width="5"/>
  <rect x="34" y="34" width="1055" height="726" rx="10" fill="none" stroke="#d8dce8" stroke-width="1.5"/>
  <g font-family="Segoe UI, Helvetica, Arial, sans-serif" text-anchor="middle">
    <text x="562" y="120" font-size="22" letter-spacing="6" fill="#7c87a3">DEV3PACK</text>
    <text x="562" y="185" font-size="44" font-weight="800" fill="#171b2b">Certificate of Completion</text>
    <text x="562" y="250" font-size="20" fill="#4a5470">This certifies that</text>
    <text x="562" y="325" font-size="52" font-weight="700" fill="#171b2b">{safe_name}</text>
    <rect x="380" y="352" width="364" height="4" rx="2" fill="url(#edge)"/>
    <text x="562" y="410" font-size="20" fill="#4a5470">has successfully completed the</text>
    <text x="562" y="452" font-size="30" font-weight="700" fill="#171b2b">{COURSE}</text>
    <text x="562" y="495" font-size="19" fill="#4a5470">{COURSE_DATES} · 15 sessions · capstone delivered and demonstrated</text>
    <text x="562" y="560" font-size="24" font-weight="700" fill="#171b2b">Final score: {score}%</text>
    <text x="562" y="595" font-size="16" fill="#7c87a3">Legacy v1 record; new credentials are backed by a signed private-evaluation receipt</text>
    <text x="300" y="700" font-size="16" fill="#4a5470">Issued: {safe_issued}</text>
    <text x="824" y="700" font-size="16" fill="#4a5470">Instructor, Dev3Pack</text>
    <rect x="704" y="672" width="240" height="1.5" fill="#9aa3ba"/>
    <text x="562" y="742" font-size="14" fill="#9aa3ba">{verified_line}</text>
  </g>
  {watermark}
</svg>
"""


def _who(receipt: dict) -> str:
    """Whose certificate this is.

    A receipt signed at demo day carries a display name the instructor entered.
    One signed by the course platform when a learner passes the final carries
    their GitHub login, which is the only identity that flow ever has, and is
    the identity the whole course uses. Either is enough to name a certificate;
    neither is invented when absent.
    """
    subject = receipt.get("subject")
    if isinstance(subject, dict) and str(subject.get("display_name", "")).strip():
        return str(subject["display_name"])
    if str(receipt.get("github", "")).strip():
        return str(receipt["github"])
    raise final_receipt.ReceiptError(
        "the receipt names nobody: no subject.display_name and no github"
    )


def render_v2(receipt: dict) -> str:
    name = html.escape(_who(receipt), quote=True)
    score = _score(receipt["score"]["percent"])
    issued = html.escape(str(receipt["issued_at"]), quote=True)
    credential_id = html.escape(str(receipt["credential_id"]), quote=True)
    receipt_hash = str(receipt["receipt_sha256"])
    # Say what was actually earned. A certificate rendered from a receipt with no
    # Demo Day evidence must not claim a Demo Day contract: the signature would
    # verify and the sentence would still be false, which is the worse failure.
    earned = (
        "completed the private assessment and the Demo Day contract"
        if isinstance(receipt.get("demo"), dict)
        else "passed the private final assessment, including every safety gate"
    )
    meta_payload = {
        "schema": "dev3pack.certificate.v2",
        "credential_id": receipt["credential_id"],
        "receipt_sha256": receipt_hash,
        "key_id": receipt["signature"]["key_id"],
        "score": score,
    }
    encoded = base64.b64encode(
        json.dumps(meta_payload, sort_keys=True, separators=(",", ":")).encode()
    ).decode("ascii")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1123 794" role="img" aria-label="Verified certificate of completion — {name}, score {score}%">
  <!-- dev3pack-v2:{encoded} -->
  <defs><linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#19fb9b"/><stop offset="0.5" stop-color="#43b4ff"/><stop offset="1" stop-color="#9945ff"/></linearGradient></defs>
  <rect width="1123" height="794" fill="#fbfbfd"/>
  <rect x="18" y="18" width="1087" height="758" rx="16" fill="none" stroke="url(#edge)" stroke-width="5"/>
  <g font-family="Segoe UI, Helvetica, Arial, sans-serif" text-anchor="middle">
    <text x="562" y="120" font-size="22" letter-spacing="6" fill="#7c87a3">DEV3PACK</text>
    <text x="562" y="185" font-size="44" font-weight="800" fill="#171b2b">Verified Certificate of Completion</text>
    <text x="562" y="250" font-size="20" fill="#4a5470">This certifies that</text>
    <text x="562" y="325" font-size="52" font-weight="700" fill="#171b2b">{name}</text>
    <rect x="380" y="352" width="364" height="4" rx="2" fill="url(#edge)"/>
    <text x="562" y="410" font-size="20" fill="#4a5470">{earned}</text>
    <text x="562" y="452" font-size="30" font-weight="700" fill="#171b2b">{COURSE}</text>
    <text x="562" y="520" font-size="24" font-weight="700" fill="#171b2b">Final score: {score}%</text>
    <text x="562" y="560" font-size="16" fill="#4a5470">All signed hard gates passed · Course release {html.escape(str(receipt["course_release"]))}</text>
    <text x="300" y="700" font-size="16" fill="#4a5470">Issued: {issued}</text>
    <text x="824" y="700" font-size="16" fill="#4a5470">Credential: {credential_id}</text>
    <text x="562" y="742" font-size="14" fill="#9aa3ba">Receipt SHA-256: {receipt_hash}</text>
  </g>
</svg>
"""


def verify_legacy(path: Path, secret: str) -> int:
    match = _META_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        print("INVALID: no legacy signed metadata found")
        return 1
    name, score, issued, code = match.group(1), int(match.group(2)), match.group(3), match.group(4)
    expected = signing_code(secret, name, score, issued)
    if hmac.compare_digest(code, expected):
        print(f"VALID LEGACY HMAC: {name} — {score}% — issued {issued}")
        return 0
    print("INVALID: legacy verification code does not match")
    return 1


def verify_v2(path: Path, receipt_path: Path, public_key_path: Path) -> int:
    match = _V2_META_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        print("INVALID: no v2 certificate metadata")
        return 1
    try:
        meta = json.loads(base64.b64decode(match.group(1), validate=True))
        receipt = final_receipt.read_receipt(receipt_path)
        public_key = final_receipt._load_public(public_key_path)
    except (ValueError, json.JSONDecodeError, final_receipt.ReceiptError) as error:
        print(f"INVALID: {error}")
        return 1
    valid, reason = final_receipt.verify(receipt, public_key)
    if not valid:
        print(f"INVALID: {reason}")
        return 1
    expected = {
        "schema": "dev3pack.certificate.v2",
        "credential_id": receipt["credential_id"],
        "receipt_sha256": receipt["receipt_sha256"],
        "key_id": receipt["signature"]["key_id"],
        "score": receipt["score"]["percent"],
    }
    if meta != expected:
        print("INVALID: certificate metadata does not match the signed receipt")
        return 1
    print(
        f"VALID V2: {_who(receipt)} — {receipt['score']['percent']}% — {receipt['credential_id']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, help="report used only to prefill an unverified preview"
    )
    parser.add_argument("--receipt", type=Path, help="signed v2 final receipt")
    parser.add_argument("--public-key", type=Path, help="Ed25519 issuer public key")
    parser.add_argument("--name", default="", help="preview display name")
    parser.add_argument("--score", type=int, default=None, help="preview score")
    parser.add_argument("--date", default="", help="preview issue date")
    parser.add_argument("--out", type=Path, default=Path("certificate.svg"))
    parser.add_argument("--verify", type=Path, help="verify a certificate and exit")
    args = parser.parse_args(argv)

    if args.verify:
        text = args.verify.read_text(encoding="utf-8")
        if _V2_META_RE.search(text):
            if not args.receipt or not args.public_key:
                print("error: v2 verification needs --receipt and --public-key")
                return 2
            return verify_v2(args.verify, args.receipt, args.public_key)
        secret = os.environ.get(SECRET_ENV, "")
        if not secret:
            print(f"error: legacy verification needs {SECRET_ENV}")
            return 2
        return verify_legacy(args.verify, secret)

    if args.receipt:
        if not args.public_key:
            print("error: v2 issuance needs --public-key")
            return 2
        receipt = final_receipt.read_receipt(args.receipt)
        valid, reason = final_receipt.verify(receipt, final_receipt._load_public(args.public_key))
        if not valid:
            print(f"refusing to issue: {reason}")
            return 1
        args.out.write_text(render_v2(receipt), encoding="utf-8")
        print(f"verified v2 certificate written: {args.out}")
        return 0

    name, score = args.name, args.score
    if args.report:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        name = name or report.get("name", "")
        report_score = report.get("score", {})
        score = (
            score if score is not None else report_score.get("percent", report.get("score_percent"))
        )
    if not name or score is None:
        print("error: preview needs --report, or both --name and --score")
        return 2
    try:
        svg = render(name, score, args.date or date.today().isoformat(), code=None)
    except ValueError as error:
        print(f"error: {error}")
        return 2
    args.out.write_text(svg, encoding="utf-8")
    print(f"preview (unverified) written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
