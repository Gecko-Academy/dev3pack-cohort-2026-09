# Claude Code instructions

Follow the canonical assistant policy in [`AGENTS.md`](AGENTS.md) — mission,
commands, coding rules, and the non-negotiable safety section all live there.

Claude-specific notes:

- Prefer targeted `uv run pytest tests/test_<module>.py` runs over full sweeps
  while iterating; run the full suite before claiming done.
- When asked to add a feature, present the plan and wait for approval before
  editing (this repo teaches the inspect → plan → implement → test → review loop —
  model it).
- For notebook edits, verify with
  `uv run python scripts/check_notebooks.py <path>` afterwards.
