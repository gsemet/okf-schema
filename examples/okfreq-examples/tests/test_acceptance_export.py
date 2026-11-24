"""Acceptance evidence for the example's declared main path.

``test_fast_export_selected_rows_for_offline_review`` runs the export as a user
does: a separate process, a JSON input on disk, and a report read back from
disk. It is deliberately cheap enough to run on every merge request; the slow
variant below shows where a full-pipeline acceptance test would live.

The slow variant is entirely commented out, so its marker cannot count as
acceptance evidence. ``test_commented_marker_does_not_count`` proves that.
"""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_SCRIPT = EXAMPLE_ROOT / "src" / "export.py"


# The acceptance test of main path S1. The export runs as a separate process so
# the test never imports the implementation: it exercises exactly what a user
# runs, and reads the report the way the user reads it.
# @accepts_req StRS-CORE-001#S1
def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    rows = [["name", "note"], ["Ada", "uses, commas"], ["Grace", "offline review"]]
    rows_path = tmp_path / "rows.json"
    report_path = tmp_path / "report.csv"
    rows_path.write_text(
        '[["name", "note"], ["Ada", "uses, commas"], ["Grace", "offline review"]]\n',
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), "rows.json", "report.csv"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    with report_path.open(newline="", encoding="utf-8") as handle:
        assert list(csv.reader(handle)) == rows


# A future slow acceptance variant (U5): the same main path, walked against the
# full pipeline instead of the library entry point. It has no implementation, so
# every line is commented out and the marker below must stay inactive.
#
# # @accepts_req StRS-CORE-001#S1
# def test_slow_export_selected_rows_through_the_pipeline(tmp_path):
#     deploy_review_pipeline(tmp_path)
#     write_rows(tmp_path / "rows.json", [["name", "note"], ["Ada", "uses, commas"]])
#     subprocess.run(
#         [*PIPELINE, "export", "rows.json", "report.csv"], cwd=tmp_path, check=True
#     )
#     with (tmp_path / "report.csv").open(newline="") as handle:
#         assert list(csv.reader(handle)) == [
#             ["name", "note"],
#             ["Ada", "uses, commas"],
#         ]


def test_commented_marker_does_not_count(tmp_path: Path) -> None:
    """The commented slow variant is not evidence; without the fast marker W004 returns."""
    from okf_schema.okfreq.core import bundle_path, marker_scan, validate_requirements

    project = tmp_path / "example"
    shutil.copytree(
        EXAMPLE_ROOT,
        project,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    acceptance = project / "tests" / "test_acceptance_export.py"
    active = "# @accepts_req StRS-CORE-001#S1"
    lines = acceptance.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if line.rstrip("\n") != active]
    assert len(kept) == len(lines) - 1, "the fast acceptance marker is not there"
    acceptance.write_text("".join(kept), encoding="utf-8")

    root = bundle_path(project / "requirements")
    commented = "# # @accepts_req StRS-CORE-001#S1"
    assert commented in acceptance.read_text(encoding="utf-8").splitlines()
    assert marker_scan(root)["accepted"].get("StRS-CORE-001", []) == [], (
        "the commented marker line must not be acceptance evidence"
    )

    findings = validate_requirements(root, project_root=project)
    assert not [finding for finding in findings if finding.startswith("error")], findings
    assert [finding for finding in findings if finding.startswith("W004")], findings
