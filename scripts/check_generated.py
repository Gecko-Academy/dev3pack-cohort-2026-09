"""Every generated file in the repository, checked in one command.

    uv run python scripts/check_generated.py

WHY THIS EXISTS. The generator checks used to be listed by hand in two workflow
files. They drifted: `dev3pack_entry` was in `test.yml` and not in
`publish.yml`, so a stale curriculum entry turned `test` red on every pull
request while `publish` stayed green and shipped. Three pull requests merged
over that red check on 23 September 2026 because the failure looked like
somebody else's.

One list, two callers. Adding a generator means adding it here, and
`tests/test_check_generated.py` fails if a script grows a `--check` flag that
nobody registered.

It runs every generator before reporting, rather than stopping at the first
stale one, because "regenerate and push" is one round trip and finding the
second stale file after the first fix is two.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The generators whose output is committed, and the check that proves it fresh.
GENERATORS: tuple[str, ...] = (
    "course_site.py",
    "instructor_pack.py",
    "dev3pack_entry.py",
    "notebook_index.py",
    "notebook_colab.py",
)

#: Scripts that take `--check` and are deliberately NOT run here, with the
#: reason. A script in neither list is a test failure, not a silent omission.
NOT_OURS: dict[str, str] = {
    "track.py": "reads the submissions repository, which CI does not check out",
}


def check(name: str) -> tuple[str, bool, str]:
    """Run one generator's `--check`. Returns its name, whether it passed, output."""
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    output = (done.stdout + done.stderr).strip()
    return name, done.returncode == 0, output


def main(argv: list[str] | None = None) -> int:
    stale: list[tuple[str, str]] = []
    for name in GENERATORS:
        generator, ok, output = check(name)
        print(f"{'ok   ' if ok else 'STALE'} {generator}")
        if not ok:
            stale.append((generator, output))

    if not stale:
        print(f"\n{len(GENERATORS)} generators, nothing stale")
        return 0

    print("\nRegenerate these, then commit what changes:")
    for generator, output in stale:
        print(f"\n  uv run python scripts/{generator}")
        for line in output.splitlines():
            print(f"    {line}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
