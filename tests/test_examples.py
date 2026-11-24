"""Execute the documented disposable requirements workflow as an acceptance test."""

import runpy
from pathlib import Path

from okf_schema._internal.yaml import extract_frontmatter, make_yaml


# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S1
def test_okfreq_showcase_runs_in_an_empty_project(tmp_path: Path) -> None:
    """A reader can exercise the complete workflow without mutating live requirements."""
    script = Path(__file__).parents[1] / "examples/okfreq-examples/showcase.py"
    namespace = runpy.run_path(str(script))
    outcomes = namespace["run_showcase"](tmp_path / "shipping")
    assert len(outcomes) == 13
    assert "okf_projection" in outcomes
    assert "acceptance_paths" in outcomes
    assert (tmp_path / "shipping/dist/requirements-report.json").is_file()
    assert not (tmp_path / "shipping/requirements/tiers/strs/broken.md").exists()
    tiers = tmp_path / "shipping/requirements/tiers"
    for relative in (
        "strs/delivery/StRS-DELIVERY-001.md",
        "swrs/delivery/SwRS-DELIVERY-001.md",
    ):
        document = (tiers / relative).read_text(encoding="utf-8")
        declared = make_yaml().load(extract_frontmatter(document)[0])["scenarios"]
        for scenario in declared:
            assert f"Scenario {scenario['id']}: {scenario['title']}" in document or (
                f"Path {scenario['id']}: {scenario['title']}" in document
            ), (relative, scenario)
