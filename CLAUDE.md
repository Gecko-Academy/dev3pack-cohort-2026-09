# Claude Code instructions

@AGENTS.md

The line above is an IMPORT, not a link: Claude Code reads `CLAUDE.md` and
follows `@path` references, so the policy is actually loaded rather than merely
pointed at. A Markdown link is a link — Claude does not open it. `AGENTS.md`
stays canonical; only Claude-specific differences belong below.

Claude-specific notes:

- Verify with the commands this copy actually has: `uv run bootcamp check chNN`
  for an exercise, `uv run ruff check .`, and
  `uv run python scripts/check_setup.py`. `tests/` is not published, so pytest
  is not a verification step here (AGENTS.md says the same).
- When asked to add a feature, present the plan and wait for approval before
  editing (this repo teaches the inspect → plan → implement → test → review loop —
  model it).
- For notebook edits, verify with
  `uv run python scripts/check_notebooks.py <path>` afterwards.
