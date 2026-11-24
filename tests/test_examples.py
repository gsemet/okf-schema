"""Execute the documented disposable requirements workflow as an acceptance test."""

import json
import re
import runpy
import shutil
from pathlib import Path

from click.testing import CliRunner

from okf_schema._internal.yaml import extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import report

EXAMPLE = Path(__file__).parents[1] / "examples/okfreq-examples"
FAST_MARKER = re.compile(r"(?m)^# @accepts_req StRS-CORE-001#S1\n")
HEADING = re.compile(r"(?m)^#{3,4} (?:Path|Scenario) (S[0-9]+): (.+)$")


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S4
# @tests_req SwRS-OKFSCHEMA-OKFREQ-014#S1
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S1
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S2
# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S3
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
    bundle = tmp_path / "shipping/requirements/tiers"
    for name in ("strs/delivery/StRS-DELIVERY-001", "swrs/delivery/SwRS-DELIVERY-001"):
        text = (bundle / f"{name}.md").read_text(encoding="utf-8")
        frontmatter, body = extract_frontmatter(text)
        declared = [
            (item["id"], item["title"]) for item in make_yaml().load(frontmatter)["scenarios"]
        ]
        assert [identifier for identifier, _ in declared] == ["S1", "S2"]
        assert HEADING.findall(body) == declared


def test_checked_in_example_accepts_its_main_path() -> None:
    """The checked-in example runs in the new mode and its StRS is tested and accepted."""
    root = EXAMPLE / "requirements"
    assert "linked-swrs-and-acceptance-paths" in (root / "config.yml").read_text(encoding="utf-8")
    result = CliRunner().invoke(okfreq, ["validate", str(root), "--prose", "--json"])
    assert result.exit_code == 0, result.output
    findings = json.loads(result.output)
    assert findings["errors"] == [] and not [w for w in findings["warnings"] if "W00" in w[:4]]
    coverage = next(r for r in report(root)["requirements"] if r["id"] == "StRS-CORE-001")
    details = coverage["stakeholder_test_coverage"]
    assert details["status"] == "covered"
    assert details["paths"] == {"total": 1, "tested": 1, "accepted": 1}
    assert details["tests"]["files"] == ["tests/test_export.py"]
    assert details["acceptance_tests"]["files"] == ["tests/test_acceptance_export.py"]
    assert all(item["status"] == "covered" for item in details["linked_swrs"])
    assert all(
        record["transitions"]["missing"] == []
        for record in report(root)["requirements"]
        if record["id"].startswith("SwRS-")
    )


def test_commented_slow_acceptance_variant_is_not_evidence(tmp_path: Path) -> None:
    """Without the fast marker, the commented slow variant does not count and W004 returns."""
    shutil.copytree(EXAMPLE, tmp_path / "example", ignore=shutil.ignore_patterns("__pycache__"))
    acceptance = tmp_path / "example/tests/test_acceptance_export.py"
    text = acceptance.read_text(encoding="utf-8")
    assert len(FAST_MARKER.findall(text)) == 1
    assert "# # @accepts_req StRS-CORE-001#S1" in text
    acceptance.write_text(FAST_MARKER.sub("", text), encoding="utf-8")
    root = tmp_path / "example/requirements"

    result = CliRunner().invoke(okfreq, ["validate", str(root), "--json"])

    assert result.exit_code == 0, result.output
    warnings = json.loads(result.output)["warnings"]
    assert any(w.startswith("W004") and "StRS-CORE-001" in w for w in warnings)
    details = next(r for r in report(root)["requirements"] if r["id"] == "StRS-CORE-001")[
        "stakeholder_test_coverage"
    ]
    assert details["paths"] == {"total": 1, "tested": 1, "accepted": 0}
    assert details["acceptance_tests"] == {"status": "missing", "files": [], "count": 0}
    assert details["status"] == "missing"
