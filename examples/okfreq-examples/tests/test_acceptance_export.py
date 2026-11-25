"""End-to-end acceptance tests for the okfreq CSV export example."""

import csv
import json
import subprocess
import sys
from pathlib import Path

EXPORT_SCRIPT = Path(__file__).parents[1] / "src" / "export.py"


# @accepts_req StRS-CORE-001#S1
def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    """Run the export script in a separate process and read back the CSV from disk."""
    expected_rows = [["name", "note"], ["Ada", "uses, commas"], ["Grace", "offline"]]
    rows_file = tmp_path / "rows.json"
    report_file = tmp_path / "report.csv"
    rows_file.write_text(json.dumps(expected_rows), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), str(rows_file), str(report_file)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0

    with report_file.open(encoding="utf-8", newline="") as handle:
        actual_rows = list(csv.reader(handle))
    assert actual_rows == expected_rows


# Illustrative slow acceptance variant (not collected, not evidence).
# A nightly job could exercise the same path S1 with a large dataset or external
# spreadsheet reader, so its marker stays commented out and inactive:
# # @accepts_req StRS-CORE-001#S1
# def test_slow_export_large_report_for_offline_review(tmp_path: Path) -> None:
#     ...
