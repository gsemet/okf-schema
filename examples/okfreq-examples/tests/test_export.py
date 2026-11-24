"""Verification evidence for the okfreq traceability example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from export import export_rows  # noqa: E402


# Each test names the SwRS transition it verifies with a #S<n> fragment.
# This cheap in-process test also walks the StRS main path, so it carries a
# StRS marker; the acceptance test in test_acceptance_export.py proves it.
# @tests_req SwRS-CORE-001#S1
# @tests_req StRS-CORE-001#S1
def test_export_rows() -> None:
    assert export_rows([["name", "note"], ["Ada", "uses, commas"]]) == (
        'name,note\nAda,"uses, commas"\n'
    )


# @tests_req SwRS-CORE-001#S2
def test_export_rows_with_empty_selection() -> None:
    assert export_rows([]) == ""
