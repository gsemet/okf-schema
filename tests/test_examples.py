"""Execute the documented disposable requirements workflow as an acceptance test."""

import runpy
import shutil
from pathlib import Path

from okf_schema.okfreq.core import marker_scan, validate_requirements


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S6
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S2
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


def test_commented_slow_acceptance_test_counts_as_no_evidence(tmp_path: Path) -> None:
    """Only the fast acceptance test accepts the path; the planned slow one is a comment."""
    example = Path(__file__).parents[1] / "examples/okfreq-examples"
    root = tmp_path / "requirements"
    shutil.copytree(example / "requirements", root)
    (tmp_path / "tests").mkdir()
    acceptance = (example / "tests/test_acceptance_export.py").read_text(encoding="utf-8")
    fast_marker = "# @accepts_req StRS-CORE-001#S1\ndef test_fast_"
    assert fast_marker in acceptance
    assert "# # @accepts_req StRS-CORE-001#S1\n# def test_slow_" in acceptance
    test_file = tmp_path / "tests/test_acceptance_export.py"
    test_file.write_text(acceptance, encoding="utf-8")
    assert marker_scan(root)["accepted"]["StRS-CORE-001"] == ["tests/test_acceptance_export.py"]

    test_file.write_text(acceptance.replace(fast_marker, "def test_fast_", 1), encoding="utf-8")

    assert "StRS-CORE-001" not in marker_scan(root)["accepted"]
    assert any(
        finding.startswith("W004") and "StRS-CORE-001" in finding
        for finding in validate_requirements(root)
    )
