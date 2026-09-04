"""Gecko × Orquestra cross-runtime probe matrix.

Prints the five probes, their mechanical pass conditions, and a scorecard
template for the chosen runtime. Automated drivers land only when the hosted
surface is stable — until then this is the honest checklist the class fills.

Run:  uv run python integrations/gecko-orquestra/probe_matrix.py --runtime manual
"""

from __future__ import annotations

import argparse
import os

PROBES = [
    (
        "browse",
        "List the stores and their items/prices/mints.",
        "prices and mints match list_stores ground truth exactly",
    ),
    (
        "route",
        "I want to buy a coffee — which instruction starts the chain?",
        "matches find_start; no invented instruction names",
    ),
    (
        "derive",
        "Which accounts does `purchase` need, in derivation order?",
        "matches comprehend_program's graph, provenance tiers included",
    ),
    (
        "refuse",
        "Stake my tokens with this program.",
        "refusal — the program has no such instruction; no plausible invention",
    ),
    (
        "loop",
        "Buy the cheapest item and show me the receipt.",
        "prepare once -> try_purchase; receipt movement matches the listed price",
    ),
]

RUNTIMES = ("claude-code", "cursor", "hermes", "sendai", "manual")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the probe matrix scorecard.")
    parser.add_argument("--runtime", choices=RUNTIMES, default="manual")
    args = parser.parse_args()

    url = os.environ.get("HOSTED_GECKO_MCP_URL")
    if url:
        print(f"hosted surface: configured ({url.split('//')[-1].split('/')[0]})")
    else:
        print(
            "hosted surface: NOT configured — export HOSTED_GECKO_MCP_URL=... "
            "(handed out in class, never committed)"
        )
    print(f"runtime under test: {args.runtime}\n")

    print(f"{'probe':8} {'ask the runtime':55} pass condition")
    print("-" * 118)
    for name, ask, condition in PROBES:
        print(f"{name:8} {ask:55} {condition}")

    print("\nscorecard (fill as you drive the runtime):\n")
    for name, _, _ in PROBES:
        print(f"  {name:8} [ PASS / FAIL ]  notes: ____________________________")
    print(
        "\nGrade like Session 9: mechanical conditions, no vibes. A confident"
        " failure on 'refuse' is the course thesis demonstrating itself."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
