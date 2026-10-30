"""Execute the documented disposable requirements workflow as an acceptance test."""

import runpy
from pathlib import Path


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014
# @tests_req StRS-OKFSCHEMA-OKFREQ-001
def test_okfreq_showcase_runs_in_an_empty_project(tmp_path: Path) -> None:
    """A reader can exercise the complete workflow without mutating live requirements."""
    script = Path(__file__).parents[1] / "examples/okfreq-examples/showcase.py"
    namespace = runpy.run_path(str(script))
    outcomes = namespace["run_showcase"](tmp_path / "shipping")
    assert len(outcomes) == 12
    assert "okf_projection" in outcomes
    assert (tmp_path / "shipping/dist/requirements-report.json").is_file()
    assert not (tmp_path / "shipping/requirements/tiers/strs/broken.md").exists()
