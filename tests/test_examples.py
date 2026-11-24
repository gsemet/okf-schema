"""Execute the documented disposable requirements workflow as an acceptance test."""

import runpy
from pathlib import Path

from okf_schema.okfreq.core import marker_scan, report


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S4
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S4
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S5
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S6
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S3
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S1
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S2
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_okfreq_showcase_runs_in_an_empty_project(tmp_path: Path) -> None:
    """A reader can exercise the complete workflow without mutating live requirements."""
    script = Path(__file__).parents[1] / "examples/okfreq-examples/showcase.py"
    namespace = runpy.run_path(str(script))
    outcomes = namespace["run_showcase"](tmp_path / "shipping")
    assert len(outcomes) == 13
    assert "okf_projection" in outcomes
    assert (tmp_path / "shipping/dist/requirements-report.json").is_file()
    assert not (tmp_path / "shipping/requirements/tiers/strs/broken.md").exists()


def test_checked_in_example_slow_acceptance_comment_is_not_evidence() -> None:
    """The illustrative slow acceptance variant cannot create a marker link."""
    root = Path(__file__).parents[1] / "examples/okfreq-examples/requirements"
    scan = marker_scan(root)
    acceptance = [
        item
        for item in scan["scenario_markers"]
        if item["id"] == "StRS-CORE-001" and item["marker"] == "accepted"
    ]
    assert acceptance == [
        {
            "marker": "accepted",
            "id": "StRS-CORE-001",
            "fragment": "S1",
            "file": "tests/test_acceptance_export.py",
            "line": 8,
        }
    ]
    stakeholder = report(root)["requirements"][0]["stakeholder_test_coverage"]
    assert stakeholder["paths"] == {"total": 1, "tested": 1, "accepted": 1}
