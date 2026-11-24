"""Acceptance evidence for the main path of ``StRS-CORE-001``.

The test runs the export the way a user does: ``src/export.py`` in a separate
process, with the report written to and read back from disk.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

EXPORT_SCRIPT = Path(__file__).parents[1] / "src/export.py"


# Fast acceptance test of main path S1: cheap enough to run on every pull or merge request.
# @accepts_req StRS-CORE-001#S1
def test_fast_export_selected_rows_for_offline_review(tmp_path: Path) -> None:
    selected = [["name", "note"], ["Ada", "uses, commas"], ["Grace", "plain"]]
    (tmp_path / "rows.json").write_text(json.dumps(selected), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT), "rows.json", "report.csv"],
        cwd=tmp_path,
        check=True,
    )

    with (tmp_path / "report.csv").open(newline="", encoding="utf-8") as report:
        assert list(csv.reader(report)) == selected


# Slow acceptance variant of the same main path, shown only as a future example. It is
# entirely commented out: it has no implementation, is not collected as a test, and its
# inactive marker below is not counted, so it is not acceptance evidence. A project would
# write it against its installed product in the main-branch pipeline, where a long run
# is affordable.
#
# # @accepts_req StRS-CORE-001#S1
# def test_slow_export_selected_rows_from_the_installed_product(tmp_path: Path) -> None:
#     ...
