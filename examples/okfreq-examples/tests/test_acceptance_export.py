"""Acceptance evidence for the export path."""

import csv
import json
import subprocess
import sys
from pathlib import Path


# @accepts_req StRS-CORE-001#S1
def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    source = tmp_path / "rows.json"
    destination = tmp_path / "report.csv"
    rows = [["name", "note"], ["Ada", "uses, commas"]]
    source.write_text(json.dumps(rows), encoding="utf-8")
    export = Path(__file__).parents[1] / "src" / "export.py"

    completed = subprocess.run(
        [sys.executable, str(export), str(source), str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    with destination.open(newline="", encoding="utf-8") as stream:
        assert list(csv.reader(stream)) == rows


# A future end-to-end browser import could be run separately:
# # @accepts_req StRS-CORE-001#S1
# def test_slow_export_selected_rows_for_offline_review():
#     ...
