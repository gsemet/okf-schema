"""Tests for the OKF projection of okfreq requirements."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    create_requirement,
    init_requirements,
    load_requirements,
    project_requirements,
    supersede_requirement,
    tiers_path,
    update_coverage,
    validate_requirements,
)
from okf_schema.projection import LINKS_START
from okf_schema.validator import validate_bundle

# @tests_req SwRS-OKFSCHEMA-OKFREQ-014


def _family(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    root = init_requirements(tmp_path)
    common = {"project": "demo", "scope": "default", "origin": "native"}
    paths = {
        "StRS-default-001": create_requirement(
            root, "StRS", "Export", "The tool SHALL export.", user_need="Export.", **common
        )
    }
    for title in ("First", "Second"):
        path = create_requirement(
            root,
            "SwRS",
            title,
            f"The tool SHALL {title.lower()}.",
            derives_from=["StRS-default-001"],
            lifecycle="proposed",
            **common,
        )
        paths[path.stem] = path
    update_coverage(root)
    return root, paths


def _edit(path: Path, **fields: object) -> None:
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    data = make_yaml().load(frontmatter)
    data.update(fields)
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def test_new_and_update_coverage_project_status_and_links(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    requirements = load_requirements(root)

    assert requirements["StRS-default-001"][1]["status"] == "draft"
    assert requirements["SwRS-default-001"][1]["status"] == "stable"
    parent = paths["StRS-default-001"].read_text(encoding="utf-8")
    assert "- Derived by:\n  - [SwRS-default-001](../swrs/SwRS-default-001.md): First\n" in parent
    child = paths["SwRS-default-001"].read_text(encoding="utf-8")
    assert "- Derives from:\n  - [StRS-default-001](../strs/StRS-default-001.md): Export\n" in child
    assert update_coverage(root, check=True) == []
    assert project_requirements(root, check=True) == []
    assert validate_requirements(root) == []


def test_okf_validator_finds_no_orphan_and_no_error_in_the_tiers(tmp_path: Path) -> None:
    root, _ = _family(tmp_path)
    CliRunner().invoke(okfreq, ["lint", str(root)])

    report = validate_bundle(tiers_path(root))

    assert report.errors == []
    assert {finding.code for finding in report.warnings} <= {"W3", "W6", "W7"}


def test_approval_becomes_a_human_verified_event(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    strs = paths["StRS-default-001"]
    _edit(strs, req_lifecycle="approved", status="stable", approved_by="po@x.org")
    text = strs.read_text(encoding="utf-8").replace(
        "approved_by: po@x.org\n", "approved_by: po@x.org\napproved_at: 2026-10-28T09:00:00+01:00\n"
    )
    strs.write_text(text, encoding="utf-8")

    assert update_coverage(root) == [str(strs)]

    assert (
        "approved_at: 2026-10-28T09:00:00+01:00\n"
        "verified:\n  by: human:po@x.org\n  at: 2026-10-28T09:00:00+01:00\n"
    ) in strs.read_text(encoding="utf-8")
    assert validate_requirements(root) == []
    _edit(strs, approved_by=None)
    update_coverage(root)
    assert "verified" not in load_requirements(root)["StRS-default-001"][1]


def test_lifecycle_commands_write_the_status(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    runner = CliRunner()

    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-002"])
    archived = runner.invoke(okfreq, ["archive", "SwRS-default-002", "--path", str(root), "--yes"])

    assert archived.exit_code == 0, archived.output
    requirements = load_requirements(root)
    assert requirements["SwRS-default-001"][1]["status"] == "deprecated"
    assert requirements["SwRS-default-002"][1]["status"] == "deprecated"
    assert "- Superseded by:\n  - [SwRS-default-002](SwRS-default-002.md): Second\n" in (
        paths["SwRS-default-001"].read_text(encoding="utf-8")
    )


def test_validate_reports_a_status_that_disagrees_with_the_lifecycle(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    _edit(paths["SwRS-default-001"], req_lifecycle="deprecated")

    findings = validate_requirements(root)

    assert len(findings) == 1
    assert (
        "status stable does not match req_lifecycle deprecated (expected deprecated)"
        in (findings[0])
    )
    update_coverage(root)
    assert validate_requirements(root) == []


def test_validate_reports_malformed_projection_annotations(tmp_path: Path) -> None:
    root = init_requirements(tmp_path)
    schema = tiers_path(root) / "_schema" / "base.schema.yaml"
    text = schema.read_text(encoding="utf-8")
    schema.write_text(
        text.replace("      superseded: deprecated\n  status:", "  status:").replace(
            "  derives_from:\n    type: array\n    items:\n      type: string\n      x-okf-link:\n"
            "        resolution: filename-stem\n",
            "  derives_from:\n    type: array\n    items:\n      type: string\n      x-okf-link:\n"
            "        resolution: project-relative\n",
        ),
        encoding="utf-8",
    )

    findings = validate_requirements(root)

    assert len(findings) == 2
    assert any(
        "derives_from: x-okf-link link-projection needs a resolution inside the bundle" in item
        for item in findings
    )
    assert any(
        "req_lifecycle: x-okf-status-projection has no OKF status for superseded" in item
        for item in findings
    )


def test_lint_check_fails_on_a_stale_links_section_and_a_log_heading(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    runner = CliRunner()
    assert runner.invoke(okfreq, ["lint", str(root)]).exit_code == 0
    assert runner.invoke(okfreq, ["lint", str(root), "--check"]).exit_code == 0

    child = paths["SwRS-default-001"]
    child.write_text(child.read_text(encoding="utf-8").replace(": Export\n", ": Stale\n"), "utf-8")
    stale = runner.invoke(okfreq, ["lint", str(root), "--check"])
    assert stale.exit_code == 1
    assert "1 requirement OKF projections would change" in stale.output
    assert runner.invoke(okfreq, ["lint", str(root)]).exit_code == 0
    assert ": Export\n" in child.read_text(encoding="utf-8")

    log = tiers_path(root) / "log.md"
    log.write_text(log.read_text(encoding="utf-8") + "\n## 2020-01-01 (topic)\n", "utf-8")
    bad_log = runner.invoke(okfreq, ["lint", str(root), "--check"])
    assert bad_log.exit_code == 1
    assert "W5 " in bad_log.output


def test_a_malformed_links_section_is_a_domain_error(tmp_path: Path) -> None:
    root, paths = _family(tmp_path)
    child = paths["SwRS-default-001"]
    child.write_text(child.read_text(encoding="utf-8") + f"\n{LINKS_START}\n", "utf-8")

    result = CliRunner().invoke(okfreq, ["update-coverage", str(root)])

    assert result.exit_code == 1
    assert "one complete generated Links section" in result.output


def test_okf_errors_are_okfreq_errors(tmp_path: Path) -> None:
    root, _ = _family(tmp_path)
    (tiers_path(root) / "strs" / "log.md").write_text("# Log\n", encoding="utf-8")

    assert any(finding.startswith("E6 ") for finding in validate_requirements(root))
