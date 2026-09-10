"""Create and verify signed final-assessment receipts.

The private grader writes a v2 report.  This issuer validates its hard gates,
removes private plaintext, binds all artifact/question/evaluator hashes, and signs
the canonical JSON with Ed25519.  The public key can verify the receipt without
revealing the private key or private question set.

Examples:
    uv run python final_assignment/receipt.py keygen --private issuer.pem --public issuer.pub.pem
    uv run python final_assignment/receipt.py sign --report private-report.json \
      --private-key issuer.pem --demo-evidence demo.json \
      --credential-id dev3pack-2026-0001 --out receipt.json
    uv run python final_assignment/receipt.py verify --receipt receipt.json \
      --public-key issuer.pub.pem
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ModuleNotFoundError as error:  # pragma: no cover - an install message, not logic
    raise SystemExit(
        "signing needs the certificate extra:\n"
        "  uv sync --extra certificate\n"
        "It is not in the default install because nothing on a learner's path signs anything."
    ) from error

SCHEMA = "dev3pack.final-receipt.v2"
REPORT_SCHEMA = "dev3pack.final-report.v2"
_CREDENTIAL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{7,63}$")


class ReceiptError(ValueError):
    """A report, key, or signed receipt failed closed."""


def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_payload(payload: dict) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return "ed25519-" + hashlib.sha256(raw).hexdigest()[:16]


def generate_keys(private_path: Path, public_path: Path) -> None:
    if private_path.exists() or public_path.exists():
        raise ReceiptError("refusing to overwrite an existing key")
    private_key = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    os.chmod(private_path, 0o600)
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def _load_private(path: Path) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as error:
        raise ReceiptError(f"could not load private key: {error}") from error
    if not isinstance(key, Ed25519PrivateKey):
        raise ReceiptError("private key is not Ed25519")
    return key


def _load_public(path: Path) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise ReceiptError(f"could not load public key: {error}") from error
    if not isinstance(key, Ed25519PublicKey):
        raise ReceiptError("public key is not Ed25519")
    return key


def build_unsigned(
    report: dict,
    credential_id: str,
    *,
    demo_evidence: dict | None = None,
    subject_id: str = "",
    issued_at: str | None = None,
) -> dict:
    if report.get("schema") != REPORT_SCHEMA:
        raise ReceiptError(f"report schema must be {REPORT_SCHEMA!r}")
    if report.get("mode") != "private":
        raise ReceiptError("practice reports are not credential evidence")
    if not report.get("credential_eligible") or not report.get("passed"):
        raise ReceiptError("report is not credential eligible")
    gates = report.get("gates")
    if (
        not isinstance(gates, dict)
        or not gates
        or not all(value is True for value in gates.values())
    ):
        raise ReceiptError("every signed hard gate must be true")
    if not _CREDENTIAL_ID.fullmatch(credential_id):
        raise ReceiptError("credential_id must be 8-64 lowercase letters, digits, or hyphens")
    display_name = report.get("name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise ReceiptError("report needs a student display name")
    score = report.get("score", {})
    percent = score.get("percent")
    if not isinstance(percent, int) or isinstance(percent, bool) or not 0 <= percent <= 100:
        raise ReceiptError("report score percent must be an integer from 0 to 100")
    demo = demo_evidence or {}
    if demo.get("completed") is not True:
        raise ReceiptError("Demo Day evidence must record completed=true")
    if not isinstance(demo.get("reviewer"), str) or not demo["reviewer"].strip():
        raise ReceiptError("Demo Day evidence needs an instructor reviewer")
    artifact_hash = demo.get("artifact_sha256")
    if not isinstance(artifact_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", artifact_hash):
        raise ReceiptError("Demo Day evidence needs a lowercase SHA-256 artifact hash")

    stamp = issued_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "credential_id": credential_id,
        "subject": {"id": subject_id or credential_id, "display_name": display_name.strip()},
        "issued_at": stamp,
        "course_release": report.get("course_release"),
        "score": score,
        "gates": gates,
        "demo": {
            "completed": True,
            "reviewer": demo["reviewer"].strip(),
            "artifact_sha256": artifact_hash,
        },
        "run": {
            "grader": report.get("grader"),
            "question_set": report.get("question_set"),
            "artifacts": report.get("artifacts"),
            "report_sha256": sha256_payload(report),
        },
        "cases": [
            {
                "task_id": result.get("task_id"),
                "category": result.get("category"),
                "critical": result.get("critical"),
                "question_sha256": result.get("question_sha256"),
                "answer_sha256": result.get("answer_sha256"),
                "passed": result.get("passed"),
                "dimensions": result.get("dimensions"),
            }
            for result in report.get("results", [])
        ],
    }


def sign(unsigned: dict, private_key: Ed25519PrivateKey) -> dict:
    if "signature" in unsigned:
        raise ReceiptError("unsigned payload already contains a signature")
    signature = private_key.sign(canonical_bytes(unsigned))
    receipt = dict(unsigned)
    receipt["signature"] = {
        "algorithm": "Ed25519",
        "key_id": key_id(private_key.public_key()),
        "value": base64.b64encode(signature).decode("ascii"),
    }
    receipt["receipt_sha256"] = sha256_payload(unsigned)
    return receipt


def verify(receipt: object, public_key: Ed25519PublicKey) -> tuple[bool, str]:
    if not isinstance(receipt, dict):
        return False, "receipt is not a JSON object"
    if receipt.get("schema") != SCHEMA:
        return False, f"unsupported receipt schema {receipt.get('schema')!r}"
    signature = receipt.get("signature")
    if not isinstance(signature, dict) or signature.get("algorithm") != "Ed25519":
        return False, "missing Ed25519 signature"
    if signature.get("key_id") != key_id(public_key):
        return False, "receipt key id does not match the supplied public key"
    unsigned = dict(receipt)
    unsigned.pop("signature", None)
    recorded_hash = unsigned.pop("receipt_sha256", None)
    expected_hash = sha256_payload(unsigned)
    if recorded_hash != expected_hash:
        return False, "receipt hash does not match its contents"
    try:
        value = base64.b64decode(signature.get("value", ""), validate=True)
        public_key.verify(value, canonical_bytes(unsigned))
    except (InvalidSignature, ValueError, TypeError):
        return False, "signature does not verify"
    if not all(value is True for value in receipt.get("gates", {}).values()):
        return False, "a signed hard gate is false"

    # TWO KINDS OF RECEIPT, and conflating them was a real interoperability bug.
    #
    # The course platform signs one when a learner passes the final assessment:
    # both gates held, and that is the whole claim. Demo day has not happened
    # and it cannot invent evidence for it.
    #
    # The instructor signs the stronger one at demo day, which carries who
    # reviewed the artifact and its hash.
    #
    # Absent evidence is therefore honest and is reported as the lesser claim.
    # HALF-PRESENT evidence is not: a receipt asserting a reviewed demo without
    # naming the reviewer is worse than one making no such assertion.
    demo = receipt.get("demo")
    if demo is None:
        return True, "valid signed final-assessment receipt (no Demo Day evidence)"
    if not isinstance(demo, dict):
        return False, "the demo field is not an object"
    if (
        demo.get("completed") is not True
        or not isinstance(demo.get("reviewer"), str)
        or not demo.get("reviewer", "").strip()
        or not isinstance(demo.get("artifact_sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", demo.get("artifact_sha256", ""))
    ):
        return False, "signed Demo Day evidence is incomplete"
    return True, "valid signed credential receipt (final assessment and Demo Day)"


def read_receipt(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReceiptError(f"could not read receipt: {error}") from error
    if not isinstance(payload, dict):
        raise ReceiptError("receipt must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    keygen = commands.add_parser("keygen", help="generate an Ed25519 issuer key pair")
    keygen.add_argument("--private", type=Path, required=True)
    keygen.add_argument("--public", type=Path, required=True)

    signer = commands.add_parser("sign", help="sign a credential-eligible private report")
    signer.add_argument("--report", type=Path, required=True)
    signer.add_argument("--private-key", type=Path, required=True)
    signer.add_argument("--credential-id", required=True)
    signer.add_argument("--subject-id", default="")
    signer.add_argument(
        "--demo-evidence",
        type=Path,
        required=True,
        help="JSON with completed=true, reviewer, and artifact_sha256",
    )
    signer.add_argument("--out", type=Path, required=True)

    verifier = commands.add_parser("verify", help="verify a signed receipt")
    verifier.add_argument("--receipt", type=Path, required=True)
    verifier.add_argument("--public-key", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "keygen":
            generate_keys(args.private, args.public)
            print(f"private key written: {args.private}")
            print(f"public key written: {args.public}")
            return 0
        if args.command == "sign":
            report = json.loads(args.report.read_text(encoding="utf-8"))
            demo = json.loads(args.demo_evidence.read_text(encoding="utf-8"))
            unsigned = build_unsigned(
                report,
                args.credential_id,
                demo_evidence=demo,
                subject_id=args.subject_id,
            )
            receipt = sign(unsigned, _load_private(args.private_key))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            print(f"signed receipt written: {args.out}")
            return 0
        receipt = read_receipt(args.receipt)
        valid, reason = verify(receipt, _load_public(args.public_key))
        print(("VALID: " if valid else "INVALID: ") + reason)
        return 0 if valid else 1
    except (ReceiptError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
