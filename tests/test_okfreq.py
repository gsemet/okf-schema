"""Tests for the standalone okfreq requirements layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    RequirementError,
    bundle_path,
    create_requirement,
    graph,
    init_requirements,
    load_config,
    load_requirements,
    marker_scan,
    merge_config,
    report,
    tiers_path,
    update_coverage,
    validate_requirements,
    write_markdown_report,
)


def make_bundle(tmp_path: Path) -> Path:
    root = init_requirements(tmp_path)
    assert isinstance(root, Path)
    return root


def add_requirements(root: Path) -> tuple[Path, Path]:
    strs = create_requirement(
        root,
        "StRS",
        "Export",
        "A user can export a report.",
        project="demo",
        scope="default",
        origin="native",
    )
    swrs = create_requirement(
        root,
        "SwRS",
        "Write",
        "The service writes CSV output.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=["StRS-default-001"],
    )
    return strs, swrs


def test_init_and_new_requirements(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    strs, swrs = add_requirements(root)
    assert strs.name == "StRS-default-001.md"
    assert swrs.name == "SwRS-default-001.md"
    assert validate_requirements(root) == []
    assert graph(root)["derived_by"]["StRS-default-001"] == ["SwRS-default-001"]
    assert load_config(root)["levels"]["SwRS"]["prefix"] == "SwRS"
    assert load_config(root)["strs_test_coverage_mode"] == "linked-swrs"


def test_new_requirement_bodies_use_distinct_tier_templates(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    stakeholder_behavior = "The reporting capability SHALL let users export a report."
    user_need = "Users need a portable report for offline review."
    strs = create_requirement(
        root,
        "StRS",
        "Export reports",
        stakeholder_behavior,
        project="demo",
        scope="default",
        origin="native",
        user_need=user_need,
    )
    software_behavior = (
        "When export is requested, the service SHALL write the report as CSV output."
    )
    swrs = create_requirement(
        root,
        "SwRS",
        "Write CSV output",
        software_behavior,
        project="demo",
        scope="default",
        origin="native",
        derives_from=["StRS-default-001"],
    )

    strs_text = strs.read_text(encoding="utf-8")
    swrs_text = swrs.read_text(encoding="utf-8")
    assert stakeholder_behavior in strs_text
    assert "## User Need\n\n" + user_need in strs_text
    assert "### Rationale and constraints" in strs_text
    assert "### Scenario:" not in strs_text
    assert "### Verification notes" not in strs_text
    assert software_behavior in swrs_text
    assert "### Scenario: <nominal behavior>" in swrs_text
    assert "### Scenario: <boundary or failure behavior>" in swrs_text
    assert "### Verification notes" in swrs_text
    assert "## User Need" not in swrs_text
    assert "### Rationale and constraints" not in swrs_text


def test_strs_keeps_missing_user_need_explicit(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    requirement = create_requirement(
        root,
        "StRS",
        "Export reports",
        "The reporting capability SHALL let users export a report.",
        project="demo",
        scope="default",
        origin="native",
    )

    text = requirement.read_text(encoding="utf-8")
    placeholder = "<stakeholder need in the stakeholder's language>"
    assert f"user_need: {placeholder}" in text
    assert f"## User Need\n\n{placeholder}" in text
    assert any(finding.startswith("W002 ") for finding in validate_requirements(root, prose=True))


def test_swrs_requires_parent_and_invalid_level(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    with pytest.raises(RequirementError, match="derives_from"):
        create_requirement(
            root,
            "SwRS",
            "Write",
            "The service writes output.",
            project="demo",
            scope="default",
            origin="native",
        )
    with pytest.raises(RequirementError, match="not configured"):
        create_requirement(
            root,
            "Foo",
            "Nope",
            "A valid description.",
            project="demo",
            scope="default",
            origin="native",
        )
    parent = create_requirement(
        root,
        "StRS",
        "Export reports",
        "The reporting capability SHALL let users export a report.",
        project="demo",
        scope="default",
        origin="native",
        user_need="Users need a portable report.",
    )
    with pytest.raises(RequirementError, match="SwRS does not accept user_need"):
        create_requirement(
            root,
            "SwRS",
            "Write CSV",
            "When export is requested, the service SHALL write CSV output.",
            project="demo",
            scope="default",
            origin="native",
            derives_from=[parent.stem],
            user_need="This field belongs only on StRS.",
        )


def test_preserves_body_and_updates_only_generated_coverage(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    requirement, _ = add_requirements(root)
    original = requirement.read_text(encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "export.py").write_text(
        "# @implements_req StRS-default-001\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_export.py").write_text(
        "# @tests_req StRS-default-001\n", encoding="utf-8"
    )
    assert marker_scan(root)["missing_ids"] == []
    assert update_coverage(root)
    content = requirement.read_text(encoding="utf-8")
    assert "implemented_in_files" not in content
    swrs_content = (tiers_path(root) / "swrs" / "SwRS-default-001.md").read_text(encoding="utf-8")
    assert "implemented_in_files" in swrs_content
    assert "A user can export a report." in content
    assert update_coverage(root) == []
    requirement.write_text(original, encoding="utf-8")
    assert update_coverage(root, check=True)
    assert requirement.read_text(encoding="utf-8") == original
    assert update_coverage(root, show_diff=True)


def test_validation_reports_structural_and_graph_errors(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-005
    root = make_bundle(tmp_path)
    requirement, _ = add_requirements(root)
    content = requirement.read_text(encoding="utf-8").replace("uuid:", "uuid: bad-")
    requirement.write_text(content, encoding="utf-8")
    errors = validate_requirements(root, prose=True)
    assert any("invalid UUID" in error for error in errors)
    swrs = tiers_path(root) / "swrs" / "SwRS-default-001.md"
    swrs.write_text(
        swrs.read_text(encoding="utf-8").replace("StRS-default-001", "missing"), encoding="utf-8"
    )
    assert any("unknown derives_from" in error for error in validate_requirements(root))


def test_marker_scan_warns_for_missing_scope_dirs_and_unknown_ids(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text("# @implements_req Unknown-1\n", encoding="utf-8")
    result = marker_scan(root)
    assert result["missing_ids"] == ["Unknown-1"]
    assert any("missing directory" in warning for warning in result["warnings"])


def test_marker_scan_handles_scope_files(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "feature.py").write_text(
        "# @implements_req SwRS-okfkb-001\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_feature.py").write_text(
        "# @tests_req SwRS-okfkb-001\n", encoding="utf-8"
    )
    config = (root / "config.yml").read_text(encoding="utf-8")
    config = config.replace(
        "default: {source_dirs: [src], test_dirs: [tests]}",
        "okfkb: {source_dirs: [src/feature.py], test_dirs: [tests/test_feature.py]}",
    )
    (root / "config.yml").write_text(config, encoding="utf-8")

    result = marker_scan(root)

    assert result["implemented"] == {}
    assert result["tested"] == {}
    assert result["missing_ids"] == ["SwRS-okfkb-001"]


def test_marker_scan_ignores_markers_inside_source_strings_and_cache_files(
    tmp_path: Path,
) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    source = tmp_path / "src"
    source.mkdir()
    (source / "feature.py").write_text(
        'message = "# @implements_req Unknown-1"\n# @implements_req SwRS-OKFSCHEMA-OKFREQ-001\n',
        encoding="utf-8",
    )
    cache = source / "__pycache__"
    cache.mkdir()
    (cache / "feature.pyc").write_bytes(b"# @implements_req Unknown-2")
    result = marker_scan(root)

    assert result["implemented"] == {}
    assert "Unknown-1" not in result["missing_ids"]
    assert "SwRS-OKFSCHEMA-OKFREQ-001" in result["missing_ids"]
    assert "Unknown-2" not in result["missing_ids"]


def test_report_and_cli_surface(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-004
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-001
    root = make_bundle(tmp_path)
    add_requirements(root)
    assert report(root)["totals"]["requirements"] == 2
    runner = CliRunner()
    commands = (
        "init",
        "new",
        "validate",
        "lint",
        "index",
        "trace",
        "status",
        "scope",
        "update-coverage",
        "archive",
        "supersede",
        "graph",
        "generate-report",
        "search",
    )
    result = runner.invoke(okfreq, ["--help"])
    assert result.exit_code == 0
    for command in commands:
        assert command in result.output
    for command in ("index", "trace", "status", "scope", "graph"):
        result = runner.invoke(okfreq, [command, str(root)])
        assert result.exit_code == 0, result.output
    assert (
        runner.invoke(okfreq, ["search", "Export", str(root)]).output.strip() == "StRS-default-001"
    )
    assert runner.invoke(okfreq, ["validate", str(root), "--json"]).exit_code == 0
    assert runner.invoke(okfreq, ["lint", str(root)]).exit_code == 0
    file_path = tiers_path(root) / "strs" / "StRS-default-001.md"
    assert runner.invoke(okfreq, ["in-file", str(file_path)]).exit_code == 0
    assert runner.invoke(okfreq, ["generate-report", str(root)]).exit_code == 0
    output = tmp_path / "report.json"
    assert (
        runner.invoke(
            okfreq, ["generate-report", str(root), "--output-json", str(output)]
        ).exit_code
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["totals"]["requirements"] == 2
    schema = tmp_path / "report.schema.json"
    assert schema.is_file()
    schema_data = json.loads(schema.read_text(encoding="utf-8"))
    assert schema_data["$defs"]["requirement"]["properties"]["text"]["type"] == "string"
    assert "bundle_path" not in schema_data["required"]
    assert "bundle_path" not in schema_data["properties"]
    markdown = tmp_path / "report.md"
    assert (
        runner.invoke(
            okfreq,
            ["generate-report", str(root), "--output-summary-md", str(markdown)],
        ).exit_code
        == 0
    )
    assert "Requirements report" in markdown.read_text(encoding="utf-8")


def test_report_defines_marker_coverage_and_preserves_requirement_text(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, swrs = add_requirements(root)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_export.py").write_text(
        "# @tests_req SwRS-default-001\n", encoding="utf-8"
    )

    result = report(root)
    assert "bundle_path" not in result
    assert "project_root" not in result["scan"]
    assert result["totals"]["source_coverage_percent"] == 100.0
    assert result["totals"]["test_coverage_percent"] == 100.0
    assert result["totals"]["combined_coverage_percent"] == 100.0
    record = next(item for item in result["requirements"] if item["id"] == swrs.stem)
    assert "The service writes CSV output." in record["text"]
    assert record["tests"]["status"] == "covered"
    assert record["execution"]["status"] == "not_collected"

    destination = tmp_path / "summary.md"
    write_markdown_report(root, destination)
    summary = destination.read_text(encoding="utf-8")
    assert "Combined traceability: 100.0%" in summary
    assert "## By stakeholder requirement" in summary
    assert "| Scope | Tier | ID | Name | Tests |" in summary
    assert "| default | StRS | StRS-default-001 | Export | ✅ covered |" in summary
    assert (
        "*Note: current configuration is that an StRS is considered as covered when it "
        "is linked to at least one SwRS and every linked SwRS has at least one test "
        "marker.*"
    ) in summary
    assert "### StRS test coverage" not in summary
    assert "## By software requirement" in summary
    assert "| Scope | Tier | ID | Name | Source | Tests |" in summary
    assert "| default | SwRS | SwRS-default-001 | Write | ✅ covered | ✅ covered |" in summary
    assert "Execution" not in summary


def test_report_computes_configured_stakeholder_test_coverage(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    strs, first_swrs = add_requirements(root)
    second_swrs = create_requirement(
        root,
        "SwRS",
        "Format",
        "The service SHALL format the exported report.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=[strs.stem],
    )
    source = tmp_path / "src"
    tests = tmp_path / "tests"
    source.mkdir()
    tests.mkdir()
    for requirement in (first_swrs, second_swrs):
        (source / f"{requirement.stem}.py").write_text(
            f"# @implements_req {requirement.stem}\n", encoding="utf-8"
        )
        (tests / f"test_{requirement.stem}.py").write_text(
            f"# @tests_req {requirement.stem}\n", encoding="utf-8"
        )

    data = report(root)
    stakeholder = next(item for item in data["requirements"] if item["id"] == strs.stem)
    assert stakeholder["implementation"] == {"status": "not_applicable", "files": [], "count": 0}
    assert stakeholder["tests"]["status"] == "covered"
    assert stakeholder["stakeholder_test_coverage"]["linked_swrs"] == [
        {"id": first_swrs.stem, "status": "covered"},
        {"id": second_swrs.stem, "status": "covered"},
    ]
    assert data["stakeholder_test_coverage"] == {
        "mode": "linked-swrs",
        "requirements": 1,
        "covered": 1,
        "coverage_percent": 100.0,
    }

    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: linked-swrs-and-validation-test",
        ),
        encoding="utf-8",
    )
    strict_data = report(root)
    strict_stakeholder = next(
        item for item in strict_data["requirements"] if item["id"] == strs.stem
    )
    assert strict_stakeholder["tests"]["status"] == "missing"
    assert strict_stakeholder["stakeholder_test_coverage"]["validation_tests"] == {
        "status": "missing",
        "files": [],
        "count": 0,
    }

    (tests / "test_stakeholder_validation.py").write_text(
        f"# @tests_req {strs.stem}\n", encoding="utf-8"
    )
    covered_data = report(root)
    covered_stakeholder = next(
        item for item in covered_data["requirements"] if item["id"] == strs.stem
    )
    assert covered_stakeholder["tests"]["status"] == "covered"
    assert marker_scan(root)["validation_tests"][strs.stem] == [
        "tests/test_stakeholder_validation.py"
    ]


def test_cli_lifecycle_and_new(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-002
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-007
    project = tmp_path / "project"
    project.mkdir()
    runner = CliRunner()
    assert runner.invoke(okfreq, ["init", str(project)]).exit_code == 0
    strs_result = runner.invoke(
        okfreq,
        [
            "new",
            "strs",
            "Export",
            "--description",
            "When export is requested, the reporting capability SHALL provide a report.",
            "--user-need",
            "Users need a portable report for offline review.",
            "--project",
            "demo",
            "--path",
            str(project),
        ],
    )
    assert strs_result.exit_code == 0
    assert "stakeholder need and constraint gaps" in strs_result.output
    swrs_result = runner.invoke(
        okfreq,
        [
            "new",
            "swrs",
            "Write",
            "--description",
            "When export is requested, the service SHALL write CSV output.",
            "--project",
            "demo",
            "--derives-from",
            "StRS-default-001",
            "--path",
            str(project),
        ],
    )
    assert swrs_result.exit_code == 0
    assert "scenarios and verification gaps" in swrs_result.output
    root = project / ".agents" / "requirements"
    assert (
        runner.invoke(okfreq, ["archive", "StRS-default-001", "--path", str(root)]).exit_code != 0
    )
    assert (
        runner.invoke(
            okfreq, ["archive", "StRS-default-001", "--path", str(root), "--yes"]
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            okfreq,
            ["supersede", "SwRS-default-001", "StRS-default-001", "--path", str(root), "--yes"],
        ).exit_code
        == 0
    )
    assert "deprecated" in (tiers_path(root) / "strs" / "StRS-default-001.md").read_text(
        encoding="utf-8"
    )


def test_init_refuses_non_empty_and_preserves_config(tmp_path: Path) -> None:
    root = tmp_path / ".agents" / "requirements"
    root.mkdir(parents=True)
    (root / "config.yml").write_text("version: 99\n", encoding="utf-8")
    with pytest.raises(RequirementError, match="not empty"):
        init_requirements(tmp_path)
    init_requirements(tmp_path, force=True)
    assert "version: 99" in (root / "config.yml").read_text(encoding="utf-8")


def test_legacy_config_under_tiers_resolves_to_tiers(tmp_path: Path) -> None:
    tiers = tmp_path / "requirements" / "tiers"
    tiers.mkdir(parents=True)
    (tiers / "config.yml").write_text("version: 1\n", encoding="utf-8")

    assert bundle_path(tmp_path / "requirements") == tiers
    assert tiers_path(tiers) == tiers


def test_split_bundle_layout_is_resolved_from_the_project_root(tmp_path: Path) -> None:
    root = tmp_path / "requirements"
    (root / "tiers").mkdir(parents=True)
    (root / "config.yml").write_text("version: 1\n", encoding="utf-8")

    assert bundle_path(tmp_path) == root
    assert tiers_path(root) == root / "tiers"


def test_init_creates_split_layout_with_guideline(tmp_path: Path) -> None:
    root = init_requirements(tmp_path)

    assert (root / "config.yml").is_file()
    assert (root / "guidelines" / "requirements.guidelines.md").is_file()
    assert (root / "tiers" / "_schema" / "base.schema.yaml").is_file()
    assert (root / "tiers" / "_schema" / "strs.schema.yaml").is_file()
    assert (root / "tiers" / "_schema" / "swrs.schema.yaml").is_file()
    assert (root / "tiers" / "index.md").is_file()
    assert (root / "tiers" / "log.md").is_file()
    assert (root / "tiers" / "strs").is_dir()
    assert (root / "tiers" / "swrs").is_dir()
    assert not (root / "strs").exists()


def test_guidelines_are_not_loaded_as_requirements(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)

    assert set(load_requirements(root)) == {"StRS-default-001", "SwRS-default-001"}


def test_missing_schema_is_reported_explicitly(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    (root / "tiers" / "_schema" / "base.schema.yaml").unlink()

    with pytest.raises(RequirementError, match="missing requirement schema"):
        validate_requirements(root)


def test_invalid_config_and_missing_parent_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "requirements"
    root.mkdir()
    (root / "config.yml").write_text("[invalid", encoding="utf-8")
    with pytest.raises(RequirementError, match="invalid configuration"):
        load_config(root)
    valid = make_bundle(tmp_path / "other")
    requirement = tiers_path(valid) / "strs" / "broken.md"
    requirement.write_text("---\ntype: StRS\nid: broken\n---\n", encoding="utf-8")
    assert validate_requirements(valid)


def test_invalid_stakeholder_test_coverage_mode_is_rejected(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: unsupported",
        ),
        encoding="utf-8",
    )

    with pytest.raises(RequirementError, match="unsupported strs_test_coverage_mode"):
        load_config(root)


def test_custom_markers_and_missing_directories(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-003
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8")
        .replace("@implements_req", "@impl")
        .replace("@tests_req", "@verify"),
        encoding="utf-8",
    )
    create_requirement(
        root,
        "StRS",
        "Export",
        "A user can export a report.",
        project="demo",
        scope="default",
        origin="native",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text(
        "# @impl StRS-default-001\n# @verify Unknown\n", encoding="utf-8"
    )
    result = marker_scan(root)
    assert result["implemented"] == {}
    assert result["non_leaf"] == ["StRS-default-001"]
    assert result["missing_ids"] == []
    assert result["warnings"]


def test_marker_scan_handles_non_mapping_and_non_list_scopes(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "default: {source_dirs: [src], test_dirs: [tests]}",
            "default: bad\n  other: {source_dirs: bad, test_dirs: bad}",
        ),
        encoding="utf-8",
    )
    assert marker_scan(root)["warnings"] == []


def test_marker_scan_reports_duplicate_and_non_leaf_markers(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    create_requirement(
        root,
        "StRS",
        "Export",
        "A user can export a report.",
        project="demo",
        scope="default",
        origin="native",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    marker = "@implements_req StRS-default-001\n"
    (tmp_path / "src" / "a.py").write_text(marker, encoding="utf-8")
    (tmp_path / "src" / "b.py").write_text(marker, encoding="utf-8")
    result = marker_scan(root)
    # The same ID in two distinct files is legitimate multi-file coverage.
    assert result["duplicates"] == []
    assert result["implemented"] == {}
    assert result["non_leaf"] == ["StRS-default-001"]

    (tmp_path / "src" / "a.py").write_text(marker * 2, encoding="utf-8")
    assert marker_scan(root)["duplicates"] == ["StRS-default-001"]


def test_marker_scan_uses_configured_id_pattern(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, requirement = add_requirements(root)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("[A-Za-z][A-Za-z0-9_-]*", "SwRS-[A-Za-z0-9_-]+"),
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "feature.py").write_text(
        f"# @implements_req {requirement.stem}\n", encoding="utf-8"
    )

    assert marker_scan(root)["implemented"][requirement.stem] == ["src/feature.py"]


def test_report_exempts_leaf_requirement_with_reason(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, requirement = add_requirements(root)
    text = requirement.read_text(encoding="utf-8").replace(
        "annotation_exemption: false\nexemption_reason:",
        "annotation_exemption: true\nexemption_reason: Generated code is verified externally",
    )
    requirement.write_text(text, encoding="utf-8")

    coverage = report(root)["marker_coverage"]

    assert coverage["missing_implementation"] == []
    assert coverage["missing_tests"] == []
    assert coverage["exemptions"] == [
        {"id": requirement.stem, "reason": "Generated code is verified externally"}
    ]


def test_validation_rejects_exemption_without_reason(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, requirement = add_requirements(root)
    requirement.write_text(
        requirement.read_text(encoding="utf-8").replace(
            "annotation_exemption: false", "annotation_exemption: true"
        ),
        encoding="utf-8",
    )

    assert any("requires exemption_reason" in error for error in validate_requirements(root))


def test_schema_requires_non_empty_exemption_reason(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, swrs = add_requirements(root)
    content = swrs.read_text(encoding="utf-8").replace(
        "annotation_exemption: false\nexemption_reason:",
        "annotation_exemption: true\nexemption_reason:",
    )
    swrs.write_text(content, encoding="utf-8")

    assert any("exemption_reason" in error for error in validate_requirements(root))


def test_update_coverage_rejects_unknown_generated_field(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "generated_fields: [derived_by, implemented_in_files, tested_in_files]",
            "generated_fields: [unknown]",
        ),
        encoding="utf-8",
    )

    with pytest.raises(RequirementError, match="unsupported generated_fields"):
        update_coverage(root)


def test_unsupported_id_policy_is_rejected(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "id_policy: scope-prefix-sequence", "id_policy: random"
        ),
        encoding="utf-8",
    )

    with pytest.raises(RequirementError, match="unsupported id_policy"):
        create_requirement(
            root,
            "StRS",
            "Export",
            "The reporting capability SHALL export a report.",
            project="demo",
            scope="default",
            origin="native",
        )


def test_missing_frontmatter_and_missing_graph_target(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    plain = tiers_path(root) / "strs" / "plain.md"
    plain.write_text("plain body", encoding="utf-8")
    assert "strs" in str(plain)
    create_requirement(
        root,
        "StRS",
        "Export",
        "A user can export a report.",
        project="demo",
        scope="default",
        origin="native",
    )
    swrs = create_requirement(
        root,
        "SwRS",
        "Write",
        "The service writes CSV output.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=["StRS-default-001"],
    )
    swrs.write_text(
        swrs.read_text(encoding="utf-8").replace("StRS-default-001", "missing"), encoding="utf-8"
    )
    result = graph(root)
    assert result["errors"]


def test_generated_field_rendering_rejects_bad_documents(tmp_path: Path) -> None:
    from okf_schema.okfreq.core import _render_frontmatter

    with pytest.raises(RequirementError, match="no frontmatter"):
        _render_frontmatter("body", {})
    with pytest.raises(RequirementError, match="not a mapping"):
        _render_frontmatter("---\n- list\n---\nbody", {})
    root = make_bundle(tmp_path / "empty")
    assert update_coverage(root) == []


def test_id_allocation_skips_existing_numbers(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    create_requirement(
        root,
        "StRS",
        "One",
        "A first useful requirement.",
        project="demo",
        scope="default",
        origin="native",
    )
    create_requirement(
        root,
        "StRS",
        "Two",
        "A second useful requirement.",
        project="demo",
        scope="default",
        origin="native",
    )
    assert (
        create_requirement(
            root,
            "StRS",
            "Three",
            "A third useful requirement.",
            project="demo",
            scope="default",
            origin="native",
        ).name
        == "StRS-default-003.md"
    )


def test_cli_error_and_preview_paths(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(okfreq, ["init", str(tmp_path)]).exit_code == 0
    root = tmp_path / ".agents" / "requirements"
    assert (
        runner.invoke(
            okfreq,
            [
                "new",
                "swrs",
                "Write",
                "--description",
                "A service writes output.",
                "--project",
                "demo",
                "--path",
                str(root),
            ],
        ).exit_code
        != 0
    )
    assert (
        runner.invoke(okfreq, ["archive", "missing", "--path", str(root), "--yes"]).exit_code != 0
    )
    assert (
        runner.invoke(
            okfreq, ["supersede", "missing", "replacement", "--path", str(root), "--yes"]
        ).exit_code
        != 0
    )
    assert runner.invoke(okfreq, ["archive", "missing", "--path", str(root)]).exit_code != 0
    assert (
        runner.invoke(
            okfreq, ["supersede", "missing", "replacement", "--path", str(root)]
        ).exit_code
        != 0
    )


def test_supersede_rejects_unknown_replacement_without_writing(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, requirement = add_requirements(root)
    before = requirement.read_text(encoding="utf-8")

    result = CliRunner().invoke(
        okfreq,
        ["supersede", requirement.stem, "missing", "--path", str(root), "--yes"],
    )

    assert result.exit_code != 0
    assert "unknown replacement requirement" in result.output
    assert requirement.read_text(encoding="utf-8") == before


def test_cli_validation_and_graph_failures(tmp_path: Path) -> None:
    runner = CliRunner()
    root = make_bundle(tmp_path)
    invalid = tiers_path(root) / "strs" / "invalid.md"
    invalid.write_text("---\ntype: StRS\nid: bad\n---\n", encoding="utf-8")
    result = runner.invoke(okfreq, ["validate", str(root)])
    assert result.exit_code == 1
    assert runner.invoke(okfreq, ["validate", str(root), "--json"]).exit_code == 1
    assert runner.invoke(okfreq, ["lint", str(root)]).exit_code == 1
    assert runner.invoke(okfreq, ["graph", str(root)]).exit_code == 0
    assert runner.invoke(okfreq, ["graph", str(root), "--json"]).exit_code == 0
    assert runner.invoke(okfreq, ["update-coverage", str(root), "--check"]).exit_code == 0
    assert runner.invoke(okfreq, ["update-coverage", str(root), "--diff"]).exit_code == 0
    assert runner.invoke(okfreq, ["init", str(root)]).exit_code != 0
    assert (
        runner.invoke(okfreq, ["archive", "missing", "--path", str(root), "--yes"]).exit_code != 0
    )
    assert (
        runner.invoke(
            okfreq, ["supersede", "missing", "replacement", "--path", str(root), "--yes"]
        ).exit_code
        != 0
    )

    broken = tiers_path(root) / "swrs" / "broken.md"
    broken.write_text(
        "---\n"
        "type: SwRS\n"
        "id: SwRS-default-001\n"
        "uuid: 00000000-0000-0000-0000-000000000001\n"
        "title: Broken\n"
        "description: A broken requirement.\n"
        "project: demo\n"
        "scope: default\n"
        "lifecycle: draft\n"
        "origin: native\n"
        "tier: SwRS\n"
        "derives_from: [unknown]\n"
        "---\n",
        encoding="utf-8",
    )
    assert runner.invoke(okfreq, ["graph", str(root)]).exit_code == 1
    (root / "config.yml").write_text("[broken", encoding="utf-8")
    assert runner.invoke(okfreq, ["validate", str(root)]).exit_code != 0


def test_custom_level_and_scope_config(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    text = """version: 1
levels:
  StRS: {folder: stakeholder, prefix: Stake, derives_from: []}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS]}
lifecycle:
  values: [draft, proposed, approved, deprecated, superseded]
markers:
  implements: '@implements_req'
  tests: '@tests_req'
generated_fields: [derived_by, implemented_in_files, tested_in_files]
scopes:
    custom: {id_token: CUSTOM, folder: custom, source_dirs: [missing-src], test_dirs: bad}
"""
    config.write_text(text, encoding="utf-8")
    requirement = create_requirement(
        root,
        "StRS",
        "Custom",
        "A custom requirement exists.",
        project="demo",
        scope="custom",
        origin="imported",
    )
    assert requirement.name == "Stake-CUSTOM-001.md"
    assert requirement.parent == tiers_path(root) / "stakeholder" / "custom"
    assert load_requirements(root)["Stake-CUSTOM-001"][1]["scope"] == "custom"
    uppercase_scope = create_requirement(
        root,
        "StRS",
        "Another custom requirement",
        "Another custom requirement exists.",
        project="demo",
        scope="CUSTOM",
        origin="native",
    )
    assert uppercase_scope.name == "Stake-CUSTOM-002.md"
    assert uppercase_scope.parent == requirement.parent
    assert load_requirements(root)["Stake-CUSTOM-002"][1]["scope"] == "custom"
    result = marker_scan(root)
    assert result["warnings"]


def test_explicit_config_merge_preserves_unknown_keys_and_reports_conflicts(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-006
    root = make_bundle(tmp_path)
    source = tmp_path / "import.yml"
    source.write_text("version: 2\nexternal_key: preserved\n", encoding="utf-8")
    assert merge_config(root, source) == ["version"]
    config = load_config(root)
    assert config["external_key"] == "preserved"
    assert runner_config_merge(root, source) == 0
    imported = CliRunner().invoke(okfreq, ["import", str(source), "--path", str(root)])
    assert imported.exit_code == 0, imported.output


def runner_config_merge(root: Path, source: Path) -> int:
    result = CliRunner().invoke(okfreq, ["config-merge", str(source), "--path", str(root)])
    assert result.exit_code == 0, result.output
    return result.exit_code


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    first = create_requirement(
        root,
        "StRS",
        "One",
        "A first useful requirement.",
        project="demo",
        scope="default",
        origin="native",
    )
    (tiers_path(root) / "swrs" / "duplicate.md").write_text(
        first.read_text(encoding="utf-8"), encoding="utf-8"
    )
    with pytest.raises(RequirementError, match="duplicate"):
        load_requirements(root)
