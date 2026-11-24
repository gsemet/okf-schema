"""Acceptance evidence: the export as a user runs it, in its own process."""

import csv
import json
import subprocess
import sys
from pathlib import Path

EXPORT = Path(__file__).parents[1] / "src/export.py"


# @accepts_req StRS-CORE-001#S1
def test_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    selected = [["name", "note"], ["Ada", "uses, commas"], ["Grace", "line\nbreak"]]
    (tmp_path / "rows.json").write_text(json.dumps(selected), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(EXPORT), "rows.json", "report.csv"], cwd=tmp_path, check=True
    )
    with (tmp_path / "report.csv").open(encoding="utf-8", newline="") as report:
        assert list(csv.reader(report)) == selected
