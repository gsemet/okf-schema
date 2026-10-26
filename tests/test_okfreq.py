"""Tests for the standalone okfreq requirements layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
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
    retire_requirement,
    supersede_requirement,
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
    assert "\n## Export reports\n" in strs_text
    assert "\n## Write CSV output\n" in swrs_text
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


# @tests_req StRS-OKFSCHEMA-OKFREQ-001
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

    base_schema = (root / "tiers" / "_schema" / "base.schema.yaml").read_text(encoding="utf-8")
    strs_schema = (root / "tiers" / "_schema" / "strs.schema.yaml").read_text(encoding="utf-8")
    swrs_schema = (root / "tiers" / "_schema" / "swrs.schema.yaml").read_text(encoding="utf-8")
    assert "description: Document type; selects which tier profile applies." in base_schema
    assert "description: Upstream requirement IDs this one is derived from." in base_schema
    assert "x-okf-link:" in base_schema
    assert "tooltip_shows_fields:" in base_schema
    assert "preview_shows_fields:" in base_schema
    assert "description: The stakeholder need this requirement formalizes." in strs_schema
    assert "description: Generated source paths." in swrs_schema
    assert "x-okf-link:" in swrs_schema
    assert "show_line_number: true" in swrs_schema

    guideline = (root / "guidelines" / "requirements.guidelines.md").read_text(encoding="utf-8")
    assert "## Generated navigation metadata" in guideline
    assert "x-okf-link" in guideline


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
            "generated_fields: [derived_by, supersedes, implemented_in_files, tested_in_files]",
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
    with pytest.raises(RequirementError, match="plain.md"):
        load_requirements(root)
    plain.unlink()
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
    assert runner.invoke(okfreq, ["update-coverage", str(root), "--check"]).exit_code == 1
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


@Parametrization.autodetect_parameters()
@Parametrization.case("no_frontmatter", text="# Broken\n")
@Parametrization.case("bad_yaml", text="---\ntitle: [\n---\n")
@Parametrization.case("non_mapping", text="---\n- value\n---\n")
@Parametrization.case("missing_id", text="---\ntype: StRS\n---\n")
@Parametrization.case("non_string_id", text="---\nid: 42\n---\n")
def test_unindexable_requirements_fail_validation_and_reporting(tmp_path: Path, text: str) -> None:
    """Invalid documents cannot disappear from validation, reports or generated updates."""
    root = make_bundle(tmp_path)
    broken = root / "tiers/strs/broken.md"
    broken.write_text(text, encoding="utf-8")
    for operation in (validate_requirements, report, update_coverage):
        with pytest.raises(RequirementError, match="broken.md"):
            operation(root)
    for command in ("validate", "lint", "status"):
        result = CliRunner().invoke(okfreq, [command, str(root)])
        assert result.exit_code != 0
        assert "broken.md" in result.output
        assert "Traceback" not in result.output
    assert broken.read_text(encoding="utf-8") == text


def test_coverage_check_detects_drift_without_writing_then_succeeds(tmp_path: Path) -> None:
    """CI can distinguish stale generated metadata from a synchronized bundle."""
    root = make_bundle(tmp_path)
    paths = add_requirements(root)
    before = {p: p.read_bytes() for p in paths}
    runner = CliRunner()
    result = runner.invoke(okfreq, ["update-coverage", str(root), "--check"])
    assert result.exit_code == 1
    assert {p: p.read_bytes() for p in paths} == before
    assert runner.invoke(okfreq, ["update-coverage", str(root), "--diff"]).exit_code == 0
    assert {p: p.read_bytes() for p in paths} == before
    assert runner.invoke(okfreq, ["update-coverage", str(root)]).exit_code == 0
    assert runner.invoke(okfreq, ["update-coverage", str(root), "--check"]).exit_code == 0


def test_overlapping_scope_paths_do_not_invent_duplicate_markers(tmp_path: Path) -> None:
    """Scanning the same file through two scopes is not a repeated marker in that file."""
    from okf_schema._internal.yaml import dump_yaml, make_yaml

    root = make_bundle(tmp_path)
    add_requirements(root)
    config = load_config(root)
    config["scopes"]["second"] = config["scopes"]["default"].copy()
    (root / "config.yml").write_text(
        dump_yaml(make_yaml().load(dump_yaml(config))), encoding="utf-8"
    )
    source = tmp_path / "src"
    tests = tmp_path / "tests"
    source.mkdir()
    tests.mkdir()
    marker = "# @implements_req SwRS-default-001\n"
    file = source / "implementation.py"
    file.write_text(marker, encoding="utf-8")
    scan = marker_scan(root)
    assert scan["implemented"]["SwRS-default-001"] == ["src/implementation.py"]
    assert scan["duplicates"] == []
    file.write_text(marker * 2, encoding="utf-8")
    assert marker_scan(root)["duplicates"] == ["SwRS-default-001"]


# @tests_req SwRS-OKFSCHEMA-CORE-008
def test_validate_reports_schema_file_diagnostics(tmp_path: Path) -> None:
    """Extra empty or broken schema files are reported without failing validation."""
    root = init_requirements(tmp_path)
    schemas = root / "tiers" / "_schema"
    (schemas / "extra.schema.yaml").write_text("# todo\n", encoding="utf-8")
    (schemas / "broken.schema.json").write_text("{", encoding="utf-8")

    findings = validate_requirements(root)
    result = CliRunner().invoke(okfreq, ["validate", str(root)])

    assert any(
        f.startswith("I1 ") and "extra.schema.yaml" in f and "is empty" in f for f in findings
    )
    assert any(f.startswith("W17 ") and "broken.schema.json" in f for f in findings)
    assert result.exit_code == 0, result.output
    assert "0 errors, 1 warnings" in result.output
    assert "I1 " in result.output


def test_missing_requirement_schema_names_the_cause(tmp_path: Path) -> None:
    """An empty required schema is explained in the error instead of vanishing."""
    root = init_requirements(tmp_path)
    (root / "tiers" / "_schema" / "swrs.schema.yaml").write_text("", encoding="utf-8")

    with pytest.raises(RequirementError, match=r"I1 .*swrs.schema.yaml.*is empty"):
        validate_requirements(root)


def test_status_and_report_do_not_count_schema_warnings_as_errors(tmp_path: Path) -> None:
    """W17 and I1 are listed by validate but are not errors in status or report."""
    root = init_requirements(tmp_path)
    (root / "tiers" / "_schema" / "broken.schema.json").write_text("{", encoding="utf-8")
    (root / "tiers" / "_schema" / "empty.schema.yaml").write_text("", encoding="utf-8")

    assert report(root)["legacy"]["schema_health"]["errors"] == 0
    assert '"errors": 0' in CliRunner().invoke(okfreq, ["status", str(root)]).output


def make_swrs(root: Path, title: str = "Write") -> Path:
    return create_requirement(
        root,
        "SwRS",
        title,
        "The service writes CSV output.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=["StRS-default-001"],
    )


def test_new_requirement_never_reuses_a_deleted_number(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    second = make_swrs(root, "Second")
    third = make_swrs(root, "Third")
    assert third.name == "SwRS-default-003.md"
    # A gap in the middle is not refilled, and the highest number moves on.
    second.unlink()
    assert make_swrs(root, "Fourth").name == "SwRS-default-004.md"
    # Deleting the highest number without retiring it is the documented limit.
    assert load_config(root)["retired_ids"] == []


def test_retire_records_id_deletes_file_and_logs(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-011
    root = make_bundle(tmp_path)
    add_requirements(root)
    draft = make_swrs(root, "Draft")
    before = (tiers_path(root) / "log.md").read_text(encoding="utf-8")

    assert retire_requirement(root, "SwRS-default-002", reason="merged into 001") == draft

    assert not draft.exists()
    assert load_config(root)["retired_ids"] == ["SwRS-default-002"]
    log = (tiers_path(root) / "log.md").read_text(encoding="utf-8")
    assert log.startswith(before.rstrip("\n"))
    assert "- Retired SwRS-default-002 (Draft); the number is never reused. Reason: merged" in log
    # The retired number was the highest, yet it is not handed out again.
    assert make_swrs(root, "Next").name == "SwRS-default-003.md"
    assert validate_requirements(root) == []


def test_retire_appends_to_todays_log_section_and_creates_missing_log(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    make_swrs(root, "First")
    make_swrs(root, "Second")
    retire_requirement(root, "SwRS-default-002")
    retire_requirement(root, "SwRS-default-003")
    lines = (tiers_path(root) / "log.md").read_text(encoding="utf-8").splitlines()
    assert sum(line.startswith("## ") for line in lines) == 1
    assert [line for line in lines if line.startswith("- ")] == [
        "- Retired SwRS-default-002 (First); the number is never reused.",
        "- Retired SwRS-default-003 (Second); the number is never reused.",
    ]
    (tiers_path(root) / "log.md").unlink()
    make_swrs(root, "Third")
    retire_requirement(root, "SwRS-default-004")
    assert (
        (tiers_path(root) / "log.md").read_text(encoding="utf-8").startswith("# Update Log\n\n## ")
    )


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="derives_from", field="derives_from", match="referenced by SwRS-default-002"
)
@Parametrization.case(name="depends_on", field="depends_on", match="referenced by SwRS-default-002")
def test_retire_refuses_a_referenced_requirement(tmp_path: Path, field: str, match: str) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    child = make_swrs(root, "Child")
    child.write_text(
        child.read_text(encoding="utf-8").replace(
            "derives_from:\n- StRS-default-001\n",
            "derives_from:\n- StRS-default-001\n"
            + (
                "- SwRS-default-001\n"
                if field == "derives_from"
                else "depends_on:\n- SwRS-default-001\n"
            ),
        ),
        encoding="utf-8",
    )
    # SwRS-default-001 is a draft with a referencing requirement.
    before = (root / "config.yml").read_text(encoding="utf-8")
    with pytest.raises(RequirementError, match=match):
        retire_requirement(root, "SwRS-default-001")
    assert (root / "config.yml").read_text(encoding="utf-8") == before
    assert "SwRS-default-001" in load_requirements(root)


def test_retire_refuses_unknown_published_and_marked_requirements(tmp_path: Path) -> None:
    project = tmp_path / "project"
    root = make_bundle(project)
    add_requirements(root)
    with pytest.raises(RequirementError, match="unknown requirement"):
        retire_requirement(root, "SwRS-default-099")
    approved = tiers_path(root) / "swrs" / "SwRS-default-001.md"
    approved.write_text(
        approved.read_text(encoding="utf-8").replace("lifecycle: draft", "lifecycle: approved"),
        encoding="utf-8",
    )
    with pytest.raises(RequirementError, match="use archive or supersede"):
        retire_requirement(root, "SwRS-default-001")
    approved.write_text(
        approved.read_text(encoding="utf-8").replace("lifecycle: approved", "lifecycle: draft"),
        encoding="utf-8",
    )
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    with pytest.raises(RequirementError, match=r"markers in src/app\.py"):
        retire_requirement(root, "SwRS-default-001")
    assert approved.exists()
    assert load_config(root)["retired_ids"] == []


def test_validation_flags_a_requirement_with_a_retired_id(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "retired_ids: []", "retired_ids: [SwRS-default-001]"
        )
    )
    findings = validate_requirements(root)
    assert any("SwRS-default-001 is listed in retired_ids" in finding for finding in findings)


@Parametrization.autodetect_parameters()
@Parametrization.case(name="not_a_list", value="retired_ids: SwRS-default-001")
@Parametrization.case(name="non_string_item", value="retired_ids: [1]")
def test_malformed_retired_ids_are_rejected(tmp_path: Path, value: str) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(config.read_text(encoding="utf-8").replace("retired_ids: []", value))
    with pytest.raises(RequirementError, match="invalid retired_ids"):
        load_config(root)


def test_scaffold_config_declares_empty_retired_ids_and_merge_unions_them(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    assert "retired_ids: []" in (root / "config.yml").read_text(encoding="utf-8")
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("retired_ids: []", "retired_ids: [A-1]")
    )
    source = tmp_path / "import.yml"
    source.write_text("retired_ids: [A-1, B-2]\ncustom: true\n", encoding="utf-8")
    assert merge_config(root, source) == []
    merged = load_config(root)
    assert merged["retired_ids"] == ["A-1", "B-2"]
    assert merged["custom"] is True


def test_cli_retire_requires_confirmation_and_reports_refusals(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    draft = make_swrs(root, "Draft")
    runner = CliRunner()
    refused = runner.invoke(okfreq, ["retire", "SwRS-default-002", "--path", str(root)])
    assert refused.exit_code != 0
    assert "pass --yes" in refused.output
    assert draft.exists()
    unknown = runner.invoke(okfreq, ["retire", "SwRS-default-099", "--path", str(root), "--yes"])
    assert unknown.exit_code != 0
    assert "unknown requirement" in unknown.output
    done = runner.invoke(
        okfreq,
        ["retire", "SwRS-default-002", "--path", str(root), "--reason", "duplicate", "--yes"],
    )
    assert done.exit_code == 0, done.output
    assert "Retired SwRS-default-002" in done.output
    assert not draft.exists()
    again = runner.invoke(
        okfreq,
        [
            "new",
            "swrs",
            "Next",
            "--description",
            "The service SHALL write.",
            "--project",
            "demo",
            "--derives-from",
            "StRS-default-001",
            "--path",
            str(root),
        ],
    )
    assert again.exit_code == 0
    assert "SwRS-default-003.md" in again.output


def test_retire_preserves_comments_and_formatting_of_an_existing_config(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)
    config = root / "config.yml"
    original = config.read_text(encoding="utf-8").replace("retired_ids: []\n", "")
    config.write_text("# project policy\n" + original, encoding="utf-8")
    retire_requirement(root, "SwRS-default-001")
    text = config.read_text(encoding="utf-8")
    assert text.startswith("# project policy\n" + original.rstrip("\n"))
    assert text.endswith("retired_ids:\n- SwRS-default-001\n")


def test_retired_numbers_of_other_scopes_and_wide_numbers_are_handled(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "retired_ids: []", "retired_ids: [StRS-other-900, StRS-default-1200, junk]"
        ),
        encoding="utf-8",
    )
    created = create_requirement(
        root, "StRS", "Wide", "A user can export.", project="demo", scope="default", origin="native"
    )
    assert created.name == "StRS-default-1201.md"


# --- supersession and relates_to ---------------------------------------------


def make_family(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    """Return a bundle with StRS-default-001 and SwRS-default-001..003."""
    root = make_bundle(tmp_path)
    add_requirements(root)
    make_swrs(root, "Second")
    make_swrs(root, "Third")
    paths = {path.stem: path for path in (tiers_path(root) / "swrs").glob("SwRS-*.md")}
    return root, paths


def set_fields(path: Path, **updates: object) -> None:
    """Rewrite frontmatter fields of one requirement, keeping the body."""
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    data = make_yaml().load(frontmatter)
    for key, value in updates.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def frontmatter_of(path: Path) -> dict:
    return load_requirements(path.parents[2])[path.stem][1]


def test_supersede_records_several_replacements_as_a_list(tmp_path: Path) -> None:
    # @tests_req SwRS-OKFSCHEMA-OKFREQ-012
    root, paths = make_family(tmp_path)
    old = paths["SwRS-default-001"]
    before = extract_frontmatter(old.read_text(encoding="utf-8"))[1]
    uuid = frontmatter_of(old)["uuid"]
    result = CliRunner().invoke(
        okfreq,
        ["supersede", "SwRS-default-001", "SwRS-default-002", "SwRS-default-003"]
        + ["--path", str(root), "--yes"],
    )
    assert result.exit_code == 0, result.output
    data = frontmatter_of(old)
    assert data["lifecycle"] == "superseded"
    assert data["superseded_by"] == ["SwRS-default-002", "SwRS-default-003"]
    assert data["uuid"] == uuid
    assert extract_frontmatter(old.read_text(encoding="utf-8"))[1] == before
    assert "superseded_by:\n- SwRS-default-002\n- SwRS-default-003\n" in old.read_text("utf-8")
    assert validate_requirements(root) == []


def test_supersede_with_one_replacement_writes_a_list_and_replaces_a_legacy_scalar(
    tmp_path: Path,
) -> None:
    root, paths = make_family(tmp_path)
    old = paths["SwRS-default-001"]
    set_fields(old, lifecycle="superseded", superseded_by="SwRS-default-002")
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-003"])
    assert frontmatter_of(old)["superseded_by"] == ["SwRS-default-003"]


@Parametrization.autodetect_parameters()
@Parametrization.case(name="itself", args=["SwRS-default-001"], match="cannot supersede itself")
@Parametrization.case(name="unknown", args=["SwRS-default-009"], match="unknown replacement")
@Parametrization.case(
    name="repeated",
    args=["SwRS-default-002", "SwRS-default-002"],
    match="duplicate replacement",
)
@Parametrization.case(name="none", args=[], match="at least one replacement")
def test_supersede_refuses_bad_replacements_without_writing(
    tmp_path: Path, args: list[str], match: str
) -> None:
    root, paths = make_family(tmp_path)
    before = paths["SwRS-default-001"].read_text(encoding="utf-8")
    with pytest.raises(RequirementError, match=match):
        supersede_requirement(root, "SwRS-default-001", args)
    assert paths["SwRS-default-001"].read_text(encoding="utf-8") == before


def test_supersede_refuses_a_cycle_and_an_unknown_target(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-002"])
    supersede_requirement(root, "SwRS-default-002", ["SwRS-default-003"])
    before = paths["SwRS-default-003"].read_text(encoding="utf-8")
    with pytest.raises(RequirementError, match="cycle: SwRS-default-001 -> SwRS-default-002"):
        supersede_requirement(root, "SwRS-default-003", ["SwRS-default-001"])
    assert paths["SwRS-default-003"].read_text(encoding="utf-8") == before
    with pytest.raises(RequirementError, match="unknown requirement"):
        supersede_requirement(root, "SwRS-default-009", ["SwRS-default-001"])
    runner = CliRunner()
    result = runner.invoke(okfreq, ["supersede", "SwRS-default-003", "--path", str(root), "--yes"])
    assert result.exit_code != 0


def test_cli_supersede_requires_a_replacement_and_confirmation(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    before = paths["SwRS-default-001"].read_text(encoding="utf-8")
    runner = CliRunner()
    assert runner.invoke(okfreq, ["supersede", "SwRS-default-001", "--path", str(root)]).exit_code
    result = runner.invoke(
        okfreq, ["supersede", "SwRS-default-001", "SwRS-default-002", "--path", str(root)]
    )
    assert result.exit_code != 0 and "--yes" in result.output
    assert paths["SwRS-default-001"].read_text(encoding="utf-8") == before


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="superseded_without_replacement",
    fields={"lifecycle": "superseded"},
    expected="lifecycle superseded requires a non-empty superseded_by",
)
@Parametrization.case(
    name="superseded_with_empty_list",
    fields={"lifecycle": "superseded", "superseded_by": []},
    expected="lifecycle superseded requires a non-empty superseded_by",
)
@Parametrization.case(
    name="replacement_on_an_active_requirement",
    fields={"superseded_by": ["SwRS-default-002"]},
    expected="superseded_by is only valid when lifecycle is superseded",
)
@Parametrization.case(
    name="unknown_replacement",
    fields={"lifecycle": "superseded", "superseded_by": ["SwRS-default-009"]},
    expected="unknown superseded_by target SwRS-default-009",
)
@Parametrization.case(
    name="self_replacement",
    fields={"lifecycle": "superseded", "superseded_by": ["SwRS-default-001"]},
    expected="superseded_by must not reference the requirement itself",
)
@Parametrization.case(
    name="repeated_replacement",
    fields={"lifecycle": "superseded", "superseded_by": ["SwRS-default-002"] * 2},
    expected="duplicate superseded_by target SwRS-default-002",
)
@Parametrization.case(
    name="not_a_list_of_ids",
    fields={"lifecycle": "superseded", "superseded_by": {"id": "SwRS-default-002"}},
    expected="superseded_by must be a list of requirement IDs",
)
@Parametrization.case(
    name="relates_to_unknown",
    fields={"relates_to": ["SwRS-default-009"]},
    expected="unknown relates_to target SwRS-default-009",
)
@Parametrization.case(
    name="relates_to_self",
    fields={"relates_to": ["SwRS-default-001"]},
    expected="relates_to must not reference the requirement itself",
)
@Parametrization.case(
    name="relates_to_scalar",
    fields={"relates_to": "SwRS-default-002"},
    expected="relates_to must be a list of requirement IDs",
)
@Parametrization.case(
    name="relates_to_repeated",
    fields={"relates_to": ["SwRS-default-002", "SwRS-default-002"]},
    expected="duplicate relates_to target SwRS-default-002",
)
def test_validation_rejects_inconsistent_relations(
    tmp_path: Path, fields: dict, expected: str
) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-001"], **fields)
    findings = validate_requirements(root)
    assert any(expected in finding for finding in findings), findings
    result = CliRunner().invoke(okfreq, ["validate", str(root)])
    assert result.exit_code == 1
    assert CliRunner().invoke(okfreq, ["lint", str(root)]).exit_code != 0


def test_validation_rejects_a_superseded_by_cycle(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    for old, new in (("001", "002"), ("002", "003"), ("003", "001")):
        set_fields(
            paths[f"SwRS-default-{old}"],
            lifecycle="superseded",
            superseded_by=[f"SwRS-default-{new}"],
        )
    cycles = [f for f in validate_requirements(root) if "superseded_by cycle" in f]
    assert len(cycles) == 1
    assert cycles[0].endswith(
        "SwRS-default-001 -> SwRS-default-002 -> SwRS-default-003 -> SwRS-default-001"
    )


def test_a_chain_of_replacements_is_valid(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    set_fields(
        paths["SwRS-default-001"], lifecycle="superseded", superseded_by=["SwRS-default-002"]
    )
    set_fields(
        paths["SwRS-default-002"], lifecycle="superseded", superseded_by=["SwRS-default-003"]
    )
    assert validate_requirements(root) == []


def test_legacy_scalar_superseded_by_is_accepted_with_an_informational_finding(
    tmp_path: Path,
) -> None:
    root, paths = make_family(tmp_path)
    old = paths["SwRS-default-001"]
    set_fields(old, lifecycle="superseded", superseded_by="SwRS-default-002")
    # The scaffold schema declares the list form; a bundle created by an earlier release
    # declares nothing for the field, which is what this scenario reproduces.
    findings = validate_requirements(root)
    assert any("is not of type 'array'" in f for f in findings)
    schema_file = tiers_path(root) / "_schema" / "base.schema.yaml"
    schema = make_yaml().load(schema_file.read_text(encoding="utf-8"))
    del schema["properties"]["superseded_by"]
    schema_file.write_text(dump_yaml(schema), encoding="utf-8")
    findings = validate_requirements(root)
    assert [f for f in findings if not f.startswith("I2 ")] == []
    assert any("write a list ([SwRS-default-002])" in f for f in findings)
    result = CliRunner().invoke(okfreq, ["validate", str(root)])
    assert result.exit_code == 0 and "I2 " in result.output
    assert CliRunner().invoke(okfreq, ["lint", str(root)]).exit_code == 0
    assert graph(root)["superseded_by"]["SwRS-default-001"] == ["SwRS-default-002"]
    assert graph(root)["supersedes"]["SwRS-default-002"] == ["SwRS-default-001"]
    assert update_coverage(root)  # supersedes is generated; the authored scalar is untouched
    assert "superseded_by: SwRS-default-002" in old.read_text(encoding="utf-8")
    record = next(r for r in report(root)["requirements"] if r["id"] == "SwRS-default-001")
    assert record["superseded_by"] == ["SwRS-default-002"]


def test_update_coverage_generates_supersedes_and_detects_stale_values(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    update_coverage(root)
    assert all("supersedes" not in path.read_text(encoding="utf-8") for path in paths.values())
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-002", "SwRS-default-003"])
    assert update_coverage(root, check=True)
    assert update_coverage(root)
    for replacement in ("SwRS-default-002", "SwRS-default-003"):
        assert frontmatter_of(paths[replacement])["supersedes"] == ["SwRS-default-001"]
    assert "supersedes" not in frontmatter_of(paths["SwRS-default-001"])
    assert update_coverage(root, check=True) == []
    result = CliRunner().invoke(okfreq, ["update-coverage", str(root), "--check"])
    assert result.exit_code == 0
    # A hand-edited value is stale, and is repaired.
    set_fields(paths["SwRS-default-002"], supersedes=["SwRS-default-009"])
    assert update_coverage(root, check=True) == [str(paths["SwRS-default-002"])]
    update_coverage(root)
    assert frontmatter_of(paths["SwRS-default-002"])["supersedes"] == ["SwRS-default-001"]
    # Re-targeting empties the old backlink instead of dropping the field.
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-003"])
    update_coverage(root)
    assert frontmatter_of(paths["SwRS-default-002"])["supersedes"] == []
    assert frontmatter_of(paths["SwRS-default-003"])["supersedes"] == ["SwRS-default-001"]


def test_supersedes_is_not_written_when_it_is_not_a_generated_field(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("derived_by, supersedes,", "derived_by,"),
        encoding="utf-8",
    )
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-002"])
    update_coverage(root)
    assert "supersedes" not in frontmatter_of(paths["SwRS-default-002"])
    assert graph(root)["supersedes"]["SwRS-default-002"] == ["SwRS-default-001"]


def test_graph_and_report_expose_the_new_relations(tmp_path: Path) -> None:
    from jsonschema import Draft202012Validator

    from okf_schema.okfreq.core import report_schema

    root, paths = make_family(tmp_path)
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-002", "SwRS-default-003"])
    set_fields(paths["SwRS-default-002"], relates_to=["StRS-default-001", "SwRS-default-003"])
    result = graph(root)
    assert result["errors"] == []
    assert result["superseded_by"]["SwRS-default-001"] == ["SwRS-default-002", "SwRS-default-003"]
    assert result["supersedes"]["SwRS-default-003"] == ["SwRS-default-001"]
    assert result["relates_to"]["SwRS-default-002"] == ["StRS-default-001", "SwRS-default-003"]
    assert result["relates_to"]["SwRS-default-003"] == []  # authored on one side only
    cli = CliRunner().invoke(okfreq, ["graph", str(root), "--json"])
    assert json.loads(cli.output)["supersedes"]["SwRS-default-002"] == ["SwRS-default-001"]
    payload = report(root)
    Draft202012Validator(report_schema()).validate(payload)
    records = {record["id"]: record for record in payload["requirements"]}
    assert records["SwRS-default-001"]["superseded_by"] == ["SwRS-default-002", "SwRS-default-003"]
    assert records["SwRS-default-002"]["supersedes"] == ["SwRS-default-001"]
    assert records["SwRS-default-002"]["relates_to"] == ["StRS-default-001", "SwRS-default-003"]
    assert records["StRS-default-001"]["relates_to"] == []


def test_graph_reports_unknown_relation_targets(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-001"], relates_to=["nope"])
    assert any("unknown relates_to target nope" in e for e in graph(root)["errors"])
    assert CliRunner().invoke(okfreq, ["graph", str(root)]).exit_code == 1


@Parametrization.autodetect_parameters()
@Parametrization.case(name="relates_to", fields={"relates_to": ["SwRS-default-001"]})
@Parametrization.case(
    name="superseded_by_list",
    fields={"lifecycle": "superseded", "superseded_by": ["SwRS-default-001"]},
)
@Parametrization.case(
    name="superseded_by_legacy_scalar",
    fields={"lifecycle": "superseded", "superseded_by": "SwRS-default-001"},
)
def test_retire_refuses_a_requirement_referenced_by_a_relation(
    tmp_path: Path, fields: dict
) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-002"], **fields)
    with pytest.raises(RequirementError, match="referenced by SwRS-default-002"):
        retire_requirement(root, "SwRS-default-001")
    assert paths["SwRS-default-001"].exists()


def test_scaffold_schema_annotates_the_relation_fields(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    base = make_yaml().load((tiers_path(root) / "_schema" / "base.schema.yaml").read_text("utf-8"))
    for field in ("superseded_by", "supersedes", "relates_to"):
        prop = base["properties"][field]
        assert prop["type"] == "array"
        assert prop["items"]["x-okf-link"]["resolution"] == "filename-stem"
    assert "supersedes" in load_config(root)["generated_fields"]
    assert "supersedes" in (root / "config.yml").read_text(encoding="utf-8")


def test_empty_scalar_superseded_by_counts_as_missing_without_a_list_hint(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-001"], lifecycle="superseded", superseded_by="")
    findings = validate_requirements(root)
    assert any("requires a non-empty superseded_by" in f for f in findings)
    assert not any(f.startswith("I2 ") for f in findings)
