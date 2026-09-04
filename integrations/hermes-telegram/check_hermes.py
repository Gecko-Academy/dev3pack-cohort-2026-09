"""Hermes × Telegram setup checker — ✅/⚠️ with the exact next command.

Run:  uv run python integrations/hermes-telegram/check_hermes.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

OK = "✅"
WARN = "⚠️ "


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    hermes_bin = shutil.which("hermes")
    hermes_repo = (Path.home() / "hermes-agent").is_dir() or (Path.home() / ".hermes").is_dir()
    if hermes_bin:
        version = subprocess.run(
            [hermes_bin, "--version"], capture_output=True, text=True, timeout=30
        ).stdout.strip()
        print(f"{OK} hermes on PATH ({version or 'version unknown'})")
    elif hermes_repo:
        print(f"{OK} hermes-agent checkout found (run it via its own uv env)")
    else:
        print(f"{WARN} Hermes not found")
        print(
            "   -> curl -fsSL https://raw.githubusercontent.com/NousResearch/"
            "hermes-agent/main/scripts/install.sh | bash"
        )

    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        print(f"{OK} TELEGRAM_BOT_TOKEN present (value not printed — it's a secret)")
    else:
        print(f"{WARN} TELEGRAM_BOT_TOKEN not set")
        print("   -> talk to @BotFather in Telegram, then add the token to .env")

    provider = any(os.environ.get(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"))
    if provider:
        print(f"{OK} an LLM provider key is present for Hermes to use")
    else:
        print(f"{WARN} no provider key found (OPENAI_API_KEY / ANTHROPIC_API_KEY)")
        print("   -> Hermes needs one; your OpenRouter key from SETUP.md works")

    print(
        "\nAll green? Start the gateway per "
        "https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram "
        "and message your bot."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
