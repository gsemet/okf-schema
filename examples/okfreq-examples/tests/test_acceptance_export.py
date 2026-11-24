"""Verify an offline export through the executable example."""

import csv
import json
import subprocess
import sys
from pathlib import Path


# @accepts_req StRS-CORE-001#S1
def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    rows = [["name", "note"], ["Ada", "uses, commas"]]
    source = tmp_path / "rows.json"
    destination = tmp_path / "report.csv"
    source.write_text(json.dumps(rows), encoding="utf-8")
    script = Path(__file__).parents[1] / "src" / "export.py"
    subprocess.run(
        [sys.executable, str(script), str(source), str(destination)], cwd=tmp_path, check=True
    )
    with destination.open(encoding="utf-8", newline="") as stream:
        assert list(csv.reader(stream)) == rows


# Planned slow acceptance test; the nested marker is inactive until implemented.
# # @accepts_req StRS-CORE-001#S1
# def test_slow_export_large_report_for_offline_review(tmp_path: Path) -> None:
#     raise NotImplementedError("Export a large report and read it offline")
