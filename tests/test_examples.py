"""Execute the documented disposable requirements workflow as an acceptance test."""

import runpy
import shutil
from pathlib import Path

from okf_schema.okfreq.core import report, validate_requirements


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S1
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_okfreq_showcase_runs_in_an_empty_project(tmp_path: Path) -> None:
    """A reader can exercise the complete workflow without mutating live requirements."""
    script = Path(__file__).parents[1] / "examples/okfreq-examples/showcase.py"
    namespace = runpy.run_path(str(script))
    outcomes = namespace["run_showcase"](tmp_path / "shipping")
    assert len(outcomes) == 13
    assert "acceptance_paths" in outcomes
    assert "okf_projection" in outcomes
    assert (tmp_path / "shipping/dist/requirements-report.json").is_file()
    assert not (tmp_path / "shipping/requirements/tiers/strs/broken.md").exists()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_okfreq_example_commented_slow_variant_does_not_count(tmp_path: Path) -> None:
    """Removing the active fast acceptance marker leaves StRS-CORE-001 unaccepted with W004."""
    src_example = Path(__file__).parents[1] / "examples/okfreq-examples"
    dst_example = tmp_path / "okfreq-examples"
    shutil.copytree(src_example, dst_example)

    acceptance_test = dst_example / "tests/test_acceptance_export.py"
    original = acceptance_test.read_text(encoding="utf-8")
    assert "# # @accepts_req StRS-CORE-001#S1" in original
    updated = original.replace("# @accepts_req StRS-CORE-001#S1", "# fast marker removed", 1)
    assert updated != original
    acceptance_test.write_text(updated, encoding="utf-8")

    rep = report(dst_example / "requirements")
    strs_entry = next(r for r in rep["requirements"] if r["id"] == "StRS-CORE-001")
    cov = strs_entry["stakeholder_test_coverage"]
    assert cov["paths"] == {"total": 1, "tested": 1, "accepted": 0}
    assert cov["accepted"] is False
    assert cov["tested"] is True
    assert cov["status"] == "missing"

    findings = validate_requirements(dst_example / "requirements")
    assert any("W004" in msg and "StRS-CORE-001" in msg for msg in findings), findings
