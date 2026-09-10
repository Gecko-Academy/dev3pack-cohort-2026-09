"""Checks added per session after the 2026-09-09 re-sequence, one module each.

WHY A PACKAGE RATHER THAN MORE OF `checks.py`. Five sessions were authored in
parallel in the week before the cohort, and a single registry file is the one
place five authors collide. Each session's new checks live in their own module
here, register themselves with :func:`bootcamp_agent.checks.register` on
import, and are tested in their own `tests/test_session_checks_chNN.py`.

Importing this package is what registers them, exactly as `week0_checks` does.
`curriculum.exercise_ids` imports it before reading the registry.
"""

from __future__ import annotations

import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
