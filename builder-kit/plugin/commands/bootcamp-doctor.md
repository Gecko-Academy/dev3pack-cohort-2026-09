---
description: Verify the Dev3Pack bootcamp environment — runs the setup doctor, the test suite, and reports what to fix.
---

Run the bootcamp environment checks and report the results honestly:

1. `uv run python scripts/check_setup.py` — the doctor. If it fails, show the
   ❌ lines and the fix each one names; stop here until they're green.
2. `uv run pytest -q` — the deterministic suite (no keys, no network). On
   failure, show the failing test names and read one failure before proposing
   anything.
3. `uv run python scripts/check_notebooks.py modules cookbook workspaces` —
   only when notebooks were touched (it executes them; it takes minutes).

Report: what's green, what's red, and the exact next command for each red
item. Never claim a check passed without running it.
