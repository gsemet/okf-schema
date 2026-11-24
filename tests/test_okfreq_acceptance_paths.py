"""Regression coverage for okfreq acceptance paths and declared scenarios."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from okf_schema._internal.yaml import make_yaml
from okf_schema.okfreq.core import (
    RequirementError,
    create_requirement,
    initialize_bundle,
    load_config,
    load_requirements,
    marker_scan,
    report,
    report_schema,
    update_coverage,
    validate_requirements,
)


def _bundle(tmp_path: Path) -> Path:
    root, _ = initialize_bundle(tmp_path / "requirements")
    path = root / "config.yml"
    path.write_text(
        path.read_text().replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
        )
    )
    return root


def _set_frontmatter(path: Path, **updates: object) -> None:
    yaml = make_yaml()
    text = path.read_text()
    frontmatter, body = text.split("---", 2)[1:]
    data = yaml.load(frontmatter)
    data.update(updates)
    output = io.StringIO()
    yaml.dump(data, output)
    path.write_text(f"---\n{output.getvalue()}---{body}")


def _requirements(root: Path) -> tuple[Path, Path]:
    stakeholder = create_requirement(
        root,
        "StRS",
        "Export rows",
        "The stakeholder SHALL export selected rows.",
        project="demo",
        scope="default",
        origin="native",
        user_need="Review the rows offline.",
        lifecycle="proposed",
    )
    software = create_requirement(
        root,
        "SwRS",
        "Write rows",
        "The writer SHALL emit selected rows.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=[next(iter(load_requirements(root)))],
        lifecycle="proposed",
    )
    _set_frontmatter(
        stakeholder,
        scenarios=[
            {"id": "S1", "title": "Export selected rows"},
            {"id": "S2", "title": "Export an empty selection"},
        ],
    )
    _set_frontmatter(
        software,
        scenarios=[
            {"id": "S1", "title": "Write selected rows"},
            {"id": "S2", "title": "Write no rows"},
        ],
    )
    return stakeholder, software


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_acceptance_paths_classify_independent_counters_and_report(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    stakeholder, software = _requirements(root)
    tests = root.parent / "tests"
    tests.mkdir()
    (root.parent / "src").mkdir()
    stakeholder_id = load_requirements(root)[next(iter(load_requirements(root)))][1]["id"]
    (tests / "flow.py").write_text(
        f"# @tests_req {stakeholder_id}#S1\n"
        f"# @accepts_req {stakeholder_id}#S2\n"
        "# @tests_req SwRS-default-001#S1\n"
    )
    (root.parent / "src" / "flow.py").write_text("# @implements_req SwRS-default-001\n")

    assert validate_requirements(root) == []
    data = report(root)
    stakeholder_data = data["requirements"][0]["stakeholder_test_coverage"]
    assert stakeholder_data["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert stakeholder_data["tested"] is False
    assert stakeholder_data["accepted"] is False
    assert data["requirements"][1]["transitions"] == {"tested": ["S1"], "missing": ["S2"]}
    Draft202012Validator(report_schema()).validate(data)

    update_coverage(root)
    assert "tested_in_files" in stakeholder.read_text()
    assert "accepted_in_files" in stakeholder.read_text()
    assert "tested_in_files" in software.read_text()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_invalid_fragments_do_not_count(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    _requirements(root)
    (root.parent / "tests").mkdir()
    (root.parent / "tests" / "flow.py").write_text(
        "# @tests_req StRS-default-001\n"
        "# @accepts_req StRS-default-001#S9\n"
        "# @tests_req SwRS-default-001#S9\n"
    )

    scan = marker_scan(root)
    findings = validate_requirements(root)
    assert len(scan["scenario_markers"]) == 3
    assert any("has no scenario fragment" in item for item in findings)
    assert sum("names no declared scenario" in item for item in findings) == 2
    assert scan["warnings"] == ["scope default: missing directory src"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_old_mode_accepts_suffixes_and_removes_stakeholder_files(tmp_path: Path) -> None:
    root, _ = initialize_bundle(tmp_path / "requirements")
    stakeholder, software = _requirements(root)
    (root.parent / "tests").mkdir()
    (root.parent / "tests" / "flow.py").write_text(
        "# @tests_req StRS-default-001#S9\n"
        "# @accepts_req StRS-default-001\n"
        "# @tests_req SwRS-default-001#S9\n"
    )
    _set_frontmatter(stakeholder, tested_in_files=["keep/no"], accepted_in_files=["keep/no"])

    assert validate_requirements(root) == []
    update_coverage(root)
    text = stakeholder.read_text()
    assert "tested_in_files" not in text
    assert "accepted_in_files" not in text
    assert "S9" not in software.read_text()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_duplicate_marker_keywords_are_refused(tmp_path: Path) -> None:
    root, _ = initialize_bundle(tmp_path / "requirements")
    config = root / "config.yml"
    config.write_text(
        config.read_text().replace("accepts: '@accepts_req'", "accepts: '@tests_req'")
    )
    with pytest.raises(RequirementError, match="same keyword"):
        load_config(root)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_old_swrs_schema_and_whitespace_waiver_are_refused(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    stakeholder, software = _requirements(root)
    schema = root / "tiers/_schema/swrs.schema.yaml"
    schema.write_text(schema.read_text().replace("maxItems: 0", "maxItems: 1"))
    _set_frontmatter(
        stakeholder,
        acceptance_exemption=True,
        acceptance_exemption_reason="   ",
    )
    findings = validate_requirements(root)
    assert any("accepted_in_files is not refused" in item for item in findings)
    assert any("acceptance exemption requires" in item for item in findings)
    assert software.exists()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_w003_suggests_numbered_legacy_paths_and_waiver_suppresses_only_w004(
    tmp_path: Path,
) -> None:
    root = _bundle(tmp_path)
    stakeholder, _ = _requirements(root)
    _set_frontmatter(
        stakeholder,
        scenarios=None,
        acceptance_exemption=True,
        acceptance_exemption_reason="Human review is the only possible acceptance.",
    )
    text = stakeholder.read_text().replace("scenarios:", "discarded_scenarios:", 1)
    stakeholder.write_text(text)
    findings = validate_requirements(root)
    assert any("W003" in item and '"####"' not in item for item in findings)
    assert not any("W004" in item for item in findings)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_unconfigured_generated_acceptance_field_is_preserved(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    stakeholder, _ = _requirements(root)
    config = root / "config.yml"
    config.write_text(
        config.read_text().replace("accepted_in_files, default_owner_email", "default_owner_email")
    )
    _set_frontmatter(stakeholder, accepted_in_files=["hand-authored/keep.txt"])
    update_coverage(root)
    assert "hand-authored/keep.txt" in stakeholder.read_text()
