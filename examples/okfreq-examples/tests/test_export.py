"""Verification evidence for the okfreq traceability example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from export import export_rows  # noqa: E402


# This file verifies both nominal and boundary behavior for the requirement.
# @tests_req SwRS-CORE-001
def test_export_rows() -> None:
    assert export_rows([["name", "note"], ["Ada", "uses, commas"]]) == (
        'name,note\nAda,"uses, commas"\n'
    )


def test_export_rows_with_empty_selection() -> None:
    assert export_rows([]) == ""
