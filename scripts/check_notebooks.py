"""Notebook validity + execution checker.

Run:  uv run python scripts/check_notebooks.py [paths...]

For every .ipynb under the given paths (default: modules/ and cookbook/):
- validate the notebook format with nbformat;
- execute it top to bottom with nbclient (timeout 120s per cell, cwd = the
  notebook's directory), UNLESS its first cell contains a line starting with
  `# manual-run:` — those are session notebooks that need a human, an
  assistant, or an instructor-hosted surface, and are reported as SKIP.

The convention this enforces: every notebook must run offline on the FakeLLM
by default. Cells that touch a provider, an external CLI, or a hosted surface
must guard themselves (env var / shutil.which checks) and print a graceful
skip message instead of raising.

Exit code: non-zero if any notebook FAILs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

MANUAL_MARKER = "# manual-run:"
STRICT_ENV = "BOOTCAMP_CHECKS_STRICT"


def check_notebook(path: Path) -> str:
    """Return 'PASS', 'SKIP: <reason>', or raise on failure."""
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            for line in cell.source.splitlines():
                if line.strip().startswith(MANUAL_MARKER):
                    return "SKIP: " + line.strip().removeprefix(MANUAL_MARKER).strip()
            break  # only the first code cell can carry the marker
    # Solutions must pass their own exercise checks; exercise notebooks only
    # have to run (an unfilled TODO prints a ❌ and the notebook continues).
    previous = os.environ.get(STRICT_ENV)
    os.environ[STRICT_ENV] = "1" if "solutions" in path.parts else "0"
    try:
        client = NotebookClient(
            notebook,
            timeout=120,
            kernel_name="python3",
            resources={"metadata": {"path": str(path.parent)}},
        )
        client.execute()
    finally:
        if previous is None:
            os.environ.pop(STRICT_ENV, None)
        else:
            os.environ[STRICT_ENV] = previous
    return "PASS"


def main(argv: list[str]) -> int:
    roots = [Path(arg) for arg in argv] or [Path("modules"), Path("cookbook")]
    notebooks: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".ipynb":
            notebooks.append(root)
        elif root.is_dir():
            notebooks.extend(sorted(root.rglob("*.ipynb")))
    if not notebooks:
        print("No notebooks found.")
        return 0
    failures = 0
    for path in notebooks:
        if ".ipynb_checkpoints" in path.parts:
            continue
        try:
            status = check_notebook(path)
        except Exception as error:  # noqa: BLE001 - report every failure kind uniformly
            status = f"FAIL: {type(error).__name__}: {str(error)[:200]}"
            failures += 1
        print(f"{status.split(':')[0]:>4}  {path}" + (f"  ({status})" if "FAIL" in status else ""))
    if failures:
        print(f"\n{failures} notebook(s) failed.")
        return 1
    print(f"\nAll {len(notebooks)} notebook(s) OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
