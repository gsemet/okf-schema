"""Tests for the standalone okfreq requirements layer."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from jsonschema import Draft202012Validator
from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    ACCEPTANCE_PATHS_MODE,
    STATUS_PROJECTION,
    STRS_TEST_COVERAGE_DESCRIPTIONS,
    STRS_TEST_COVERAGE_MODES,
    RequirementError,
    bundle_path,
    create_requirement,
    ears_body,
    graph,
    init_requirements,
    lifecycle_values,
    load_config,
    load_requirements,
    marker_scan,
    merge_config,
    owner_policy,
    project_path,
    report,
    report_schema,
    retire_requirement,
    supersede_requirement,
    tiers_path,
    update_coverage,
    validate_requirements,
    write_markdown_report,
)
from okf_schema.projection import strip_links_section


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


MAIN_PATHS_BODY = """## Export

### Normative behavior

The tool SHALL export a report.

### Main paths

#### Path 1: Choose a format

1. Choose the format.

#### Path 2: Write the file

1. Write the file.

## User Need

Users need reports.
"""

SCENARIO_BODY = """## Write

### Normative behavior

The tool SHALL write the file.

### Scenario S1: Write succeeds

- GIVEN a writable file

### Scenario S2: The disk is full

- GIVEN a full disk
"""


def set_frontmatter(path: Path, *, drop: tuple[str, ...] = (), **values: Any) -> None:
    """Rewrite a requirement's frontmatter, keeping its body."""
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    for key in drop:
        data.pop(key, None)
    data.update(values)
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def set_body(path: Path, body: str) -> None:
    """Replace a requirement's body, keeping its frontmatter."""
    head, separator, _ = path.read_text(encoding="utf-8").partition("\n---\n")
    path.write_text(head + separator + "\n" + body, encoding="utf-8")


def set_mode(root: Path, mode: str) -> None:
    """Select a stakeholder test-coverage mode in an initialized bundle."""
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    assert "strs_test_coverage_mode: linked-swrs\n" in text
    config.write_text(
        text.replace(
            "strs_test_coverage_mode: linked-swrs\n", f"strs_test_coverage_mode: {mode}\n"
        ),
        encoding="utf-8",
    )


def declare_scenarios(path: Path, *ids: str) -> None:
    """Declare ``scenarios:`` entries whose titles match ``S<n>`` ids."""
    set_frontmatter(path, scenarios=[{"id": item, "title": f"Scenario {item}"} for item in ids])


def make_scanned_bundle(tmp_path: Path, mode: str = "linked-swrs") -> Path:
    """Init a bundle whose project root is ``tmp_path``, so ``tests/`` is private to it."""
    root = init_requirements(tmp_path / "requirements")
    assert isinstance(root, Path)
    set_mode(root, mode)
    return root


def write_test_file(root: Path, name: str, markers: list[str]) -> Path:
    """Write a test file under the project's scanned ``tests`` directory."""
    source: Path = project_path(root) / "tests" / name
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("".join(f"{marker}\n" for marker in markers), encoding="utf-8")
    return source


def make_acceptance_bundle(tmp_path: Path, mode: str) -> dict[str, Path]:
    """Build the shared fixture of the default/configured-value matrix.

    StRS-A declares S1/S2 and has two ``#### Path`` headings; StRS-B declares no
    ``scenarios:``; SwRS-A derives from StRS-A and declares S1/S2; StRS-C is a
    plain draft. One test file carries the matrix's markers.
    """
    root = init_requirements(tmp_path / "requirements")
    set_mode(root, mode)
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    stunter = create_requirement(
        root,
        "StRS",
        "Export",
        "The tool SHALL export a report.",
        user_need="Users need reports.",
        **common,
    )
    silent = create_requirement(
        root,
        "StRS",
        "Import",
        "The tool SHALL import a report.",
        user_need="Users need imports.",
        **common,
    )
    software = create_requirement(
        root,
        "SwRS",
        "Write",
        "The tool SHALL write the file.",
        derives_from=[stunter.stem],
        **common,
    )
    draft = create_requirement(
        root,
        "StRS",
        "Archive",
        "The tool SHALL archive a report.",
        user_need="Users need archives.",
        **common,
    )
    declare_scenarios(stunter, "S1", "S2")
    set_body(stunter, MAIN_PATHS_BODY)
    set_frontmatter(silent, drop=("scenarios",))
    set_body(
        silent,
        "## Import\n\n### Normative behavior\n\nThe tool SHALL import a report.\n\n"
        "## User Need\n\nUsers need imports.\n",
    )
    declare_scenarios(software, "S1", "S2")
    set_body(software, SCENARIO_BODY)
    set_frontmatter(draft, drop=("scenarios",))
    set_body(
        draft,
        "## Archive\n\n### Normative behavior\n\nThe tool SHALL archive a report.\n\n"
        "## User Need\n\nUsers need archives.\n",
    )
    project = root.parent
    (project / "src").mkdir()
    (project / "src" / "implementation.py").write_text(
        f"# @implements_req {software.stem}\n", encoding="utf-8"
    )
    write_test_file(
        root,
        "test_flow.py",
        [
            f"# @accepts_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @tests_req {stunter.stem}",
            f"# @tests_req {silent.stem}",
            f"# @tests_req {software.stem}",
            f"# @tests_req {software.stem}#S9",
            f"# @accepts_req {software.stem}",
            f"# @accepts_req {draft.stem}",
        ],
    )
    return {
        "root": root,
        "stunter": stunter,
        "silent": silent,
        "software": software,
        "draft": draft,
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-002#S1
def test_init_and_new_requirements(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    strs, swrs = add_requirements(root)
    assert strs.name == "StRS-default-001.md"
    assert swrs.name == "SwRS-default-001.md"
    assert validate_requirements(root) == []
    assert graph(root)["derived_by"]["StRS-default-001"] == ["SwRS-default-001"]
    assert load_config(root)["tiers"]["SwRS"]["prefix"] == "SwRS"
    assert load_config(root)["strs_test_coverage_mode"] == "linked-swrs"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-002#S3
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-002#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S3
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-002#S2
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


# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S3
def test_validation_reports_structural_and_graph_errors(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-003#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S2
def test_marker_scan_warns_for_missing_scope_dirs_and_unknown_ids(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text("# @implements_req Unknown-1\n", encoding="utf-8")
    result = marker_scan(root)
    assert result["missing_ids"] == ["Unknown-1"]
    assert any("missing directory" in warning for warning in result["warnings"])


# @tests_req SwRS-OKFSCHEMA-OKFREQ-003#S1
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


# @tests_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_report_and_cli_surface(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-004#S1
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-007#S1
def test_cli_lifecycle_and_new(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S2
def test_init_refuses_non_empty_and_preserves_config(tmp_path: Path) -> None:
    root = tmp_path / ".agents" / "requirements"
    root.mkdir(parents=True)
    (root / "config.yml").write_text("version: 99\n", encoding="utf-8")
    with pytest.raises(RequirementError, match="not empty"):
        init_requirements(tmp_path)
    init_requirements(tmp_path, force=True)
    assert "version: 99" in (root / "config.yml").read_text(encoding="utf-8")


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S1
def test_legacy_config_under_tiers_resolves_to_tiers(tmp_path: Path) -> None:
    tiers = tmp_path / "requirements" / "tiers"
    tiers.mkdir(parents=True)
    (tiers / "config.yml").write_text("version: 1\n", encoding="utf-8")

    assert bundle_path(tmp_path / "requirements") == tiers
    assert tiers_path(tiers) == tiers


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S1
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
    assert "The same requirement ID may appear more than once in a file" in guideline


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S4
def test_init_force_replaces_only_the_installed_guideline(tmp_path: Path) -> None:
    """`init` keeps an edited guideline; `init --force` replaces it and spares project files."""
    root = tmp_path / "requirements"
    runner = CliRunner()
    first = runner.invoke(okfreq, ["init", str(root)])
    assert first.exit_code == 0
    assert "Guideline installed:" in first.output
    guideline = root / "guidelines" / "requirements.guidelines.md"
    shipped = guideline.read_text(encoding="utf-8")
    project = root / "guidelines" / "project.guidelines.md"
    project.write_text("Project rules\n", encoding="utf-8")
    config = root / "config.yml"
    config.write_text(config.read_text(encoding="utf-8") + "# local\n", encoding="utf-8")

    guideline.write_text("edited\n", encoding="utf-8")
    assert runner.invoke(okfreq, ["init", str(root)]).exit_code != 0
    assert guideline.read_text(encoding="utf-8") == "edited\n"

    replaced = runner.invoke(okfreq, ["init", str(root), "--force"])
    assert replaced.exit_code == 0
    assert "Guideline replaced:" in replaced.output
    assert guideline.read_text(encoding="utf-8") == shipped
    assert project.read_text(encoding="utf-8") == "Project rules\n"
    assert config.read_text(encoding="utf-8").endswith("# local\n")

    again = runner.invoke(okfreq, ["init", str(root), "--force"])
    assert "Guideline up to date:" in again.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S4
def test_init_without_force_never_overwrites_the_guideline(tmp_path: Path) -> None:
    """Without --force the initializer reports an existing guideline as kept."""
    from okf_schema.okfreq.core import _install_guideline, initialize_bundle

    root = tmp_path / "requirements"
    initialize_bundle(root)
    guideline = root / "guidelines" / "requirements.guidelines.md"
    guideline.write_text("edited\n", encoding="utf-8")
    assert initialize_bundle(root, force=True)[1] == "replaced"
    guideline.write_text("edited\n", encoding="utf-8")
    assert _install_guideline(root) == "kept"
    assert guideline.read_text(encoding="utf-8") == "edited\n"


def test_installed_guideline_carries_no_okf_schema_marker(tmp_path: Path) -> None:
    """The packaged guideline is evidence for okf-schema; the installed copy has no marker."""
    from okf_schema.okfreq.core import GUIDELINE_NAME

    shipped = (
        Path(__file__).parents[1] / "src/okf_schema/data/requirements/guidelines" / GUIDELINE_NAME
    ).read_text(encoding="utf-8")
    assert "<!-- @implements_req SwRS-OKFSCHEMA-OKFREQ-002 -->" in shipped
    root = tmp_path / "requirements"
    init_requirements(root)
    for forced in (False, True):
        if forced:
            init_requirements(root, force=True)
        installed = (root / "guidelines" / GUIDELINE_NAME).read_text(encoding="utf-8")
        assert "SwRS-OKFSCHEMA" not in installed
        assert installed.startswith(shipped.split("<!--", 1)[0])
        assert "`@implements_req <ID>`" in installed


def test_guidelines_are_not_loaded_as_requirements(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    add_requirements(root)

    assert set(load_requirements(root)) == {"StRS-default-001", "SwRS-default-001"}


def test_missing_schema_is_reported_explicitly(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    (root / "tiers" / "_schema" / "base.schema.yaml").unlink()

    with pytest.raises(RequirementError, match="missing requirement schema"):
        validate_requirements(root)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-003#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-003#S2
def test_marker_scan_reports_non_leaf_and_accepts_repeated_markers(tmp_path: Path) -> None:
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
    repeated = marker_scan(root)
    assert repeated["duplicates"] == []
    assert repeated["non_leaf"] == ["StRS-default-001"]


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
        re.sub(
            r"generated_fields: \[.*?\](?=\n)",
            "generated_fields: [unknown]",
            config.read_text(encoding="utf-8"),
            flags=re.DOTALL,
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S2
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
        "req_lifecycle: draft\n"
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-006#S1
def test_explicit_config_merge_preserves_unknown_keys_and_reports_conflicts(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-004#S3
# @tests_req SwRS-OKFSCHEMA-OKFREQ-005#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-003#S3
def test_overlapping_scope_paths_list_a_file_once(tmp_path: Path) -> None:
    """Scanning the same file through two scopes lists it once; repeated markers are accepted."""
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
    repeated = marker_scan(root)
    assert repeated["duplicates"] == []
    assert repeated["implemented"]["SwRS-default-001"] == ["src/implementation.py"]


# @tests_req SwRS-OKFSCHEMA-CORE-008#S1
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-002#S4
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
def test_retire_records_id_deletes_file_and_logs(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S1
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S2
def test_retire_refuses_unknown_published_and_marked_requirements(tmp_path: Path) -> None:
    project = tmp_path / "project"
    root = make_bundle(project)
    add_requirements(root)
    with pytest.raises(RequirementError, match="unknown requirement"):
        retire_requirement(root, "SwRS-default-099")
    approved = tiers_path(root) / "swrs" / "SwRS-default-001.md"
    approved.write_text(
        approved.read_text(encoding="utf-8").replace(
            "req_lifecycle: draft", "req_lifecycle: approved"
        ),
        encoding="utf-8",
    )
    with pytest.raises(RequirementError, match="use archive or supersede"):
        retire_requirement(root, "SwRS-default-001")
    approved.write_text(
        approved.read_text(encoding="utf-8").replace(
            "req_lifecycle: approved", "req_lifecycle: draft"
        ),
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-011#S3
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
    """Rewrite frontmatter fields of one requirement, keeping the body and its status."""
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    data = make_yaml().load(frontmatter)
    for key, value in updates.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    if "req_lifecycle" in updates and "status" in data:
        data["status"] = STATUS_PROJECTION.get(str(data["req_lifecycle"]), data["status"])
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def frontmatter_of(path: Path) -> dict[str, Any]:
    """Return a requirement file's parsed frontmatter."""
    data: dict[str, Any] = load_requirements(path.parents[2])[path.stem][1]
    return data


# @tests_req SwRS-OKFSCHEMA-OKFREQ-007#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S1
def test_supersede_records_several_replacements_as_a_list(tmp_path: Path) -> None:
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
    assert data["req_lifecycle"] == "superseded"
    assert data["superseded_by"] == ["SwRS-default-002", "SwRS-default-003"]
    assert data["uuid"] == uuid
    after = extract_frontmatter(old.read_text(encoding="utf-8"))[1]
    assert strip_links_section(after) == strip_links_section(before)
    assert "- Superseded by:\n  - [SwRS-default-002](SwRS-default-002.md)" in after
    assert "superseded_by:\n- SwRS-default-002\n- SwRS-default-003\n" in old.read_text("utf-8")
    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S5
def test_supersede_with_one_replacement_writes_a_list_and_replaces_a_legacy_scalar(
    tmp_path: Path,
) -> None:
    root, paths = make_family(tmp_path)
    old = paths["SwRS-default-001"]
    set_fields(old, req_lifecycle="superseded", superseded_by="SwRS-default-002")
    supersede_requirement(root, "SwRS-default-001", ["SwRS-default-003"])
    assert frontmatter_of(old)["superseded_by"] == ["SwRS-default-003"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-007#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S4
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-007#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S4
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S3
@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="superseded_without_replacement",
    fields={"req_lifecycle": "superseded"},
    expected="lifecycle superseded requires a non-empty superseded_by",
)
@Parametrization.case(
    name="superseded_with_empty_list",
    fields={"req_lifecycle": "superseded", "superseded_by": []},
    expected="lifecycle superseded requires a non-empty superseded_by",
)
@Parametrization.case(
    name="replacement_on_an_active_requirement",
    fields={"superseded_by": ["SwRS-default-002"]},
    expected="superseded_by is only valid when lifecycle is superseded",
)
@Parametrization.case(
    name="unknown_replacement",
    fields={"req_lifecycle": "superseded", "superseded_by": ["SwRS-default-009"]},
    expected="unknown superseded_by target SwRS-default-009",
)
@Parametrization.case(
    name="self_replacement",
    fields={"req_lifecycle": "superseded", "superseded_by": ["SwRS-default-001"]},
    expected="superseded_by must not reference the requirement itself",
)
@Parametrization.case(
    name="repeated_replacement",
    fields={"req_lifecycle": "superseded", "superseded_by": ["SwRS-default-002"] * 2},
    expected="duplicate superseded_by target SwRS-default-002",
)
@Parametrization.case(
    name="not_a_list_of_ids",
    fields={"req_lifecycle": "superseded", "superseded_by": {"id": "SwRS-default-002"}},
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S4
def test_validation_rejects_a_superseded_by_cycle(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    for old, new in (("001", "002"), ("002", "003"), ("003", "001")):
        set_fields(
            paths[f"SwRS-default-{old}"],
            req_lifecycle="superseded",
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
        paths["SwRS-default-001"], req_lifecycle="superseded", superseded_by=["SwRS-default-002"]
    )
    set_fields(
        paths["SwRS-default-002"], req_lifecycle="superseded", superseded_by=["SwRS-default-003"]
    )
    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S5
def test_legacy_scalar_superseded_by_is_accepted_with_an_informational_finding(
    tmp_path: Path,
) -> None:
    root, paths = make_family(tmp_path)
    old = paths["SwRS-default-001"]
    set_fields(old, req_lifecycle="superseded", superseded_by="SwRS-default-002")
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S2
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-004#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S6
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S6
def test_graph_reports_unknown_relation_targets(tmp_path: Path) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-001"], relates_to=["nope"])
    assert any("unknown relates_to target nope" in e for e in graph(root)["errors"])
    assert CliRunner().invoke(okfreq, ["graph", str(root)]).exit_code == 1


# @tests_req SwRS-OKFSCHEMA-OKFREQ-012#S6
@Parametrization.autodetect_parameters()
@Parametrization.case(name="relates_to", fields={"relates_to": ["SwRS-default-001"]})
@Parametrization.case(
    name="superseded_by_list",
    fields={"req_lifecycle": "superseded", "superseded_by": ["SwRS-default-001"]},
)
@Parametrization.case(
    name="superseded_by_legacy_scalar",
    fields={"req_lifecycle": "superseded", "superseded_by": "SwRS-default-001"},
)
def test_retire_refuses_a_requirement_referenced_by_a_relation(
    tmp_path: Path, fields: dict
) -> None:
    root, paths = make_family(tmp_path)
    set_fields(paths["SwRS-default-002"], **fields)
    with pytest.raises(RequirementError, match="referenced by SwRS-default-002"):
        retire_requirement(root, "SwRS-default-001")
    assert paths["SwRS-default-001"].exists()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-001#S3
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
    set_fields(paths["SwRS-default-001"], req_lifecycle="superseded", superseded_by="")
    findings = validate_requirements(root)
    assert any("requires a non-empty superseded_by" in f for f in findings)
    assert not any(f.startswith("I2 ") for f in findings)


def _set_fields(document: Path, **fields: object) -> None:
    """Rewrite authored frontmatter fields of one requirement document."""
    frontmatter, body = extract_frontmatter(document.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    data.update(fields)
    if "req_lifecycle" in fields and "status" in data:
        data["status"] = STATUS_PROJECTION[str(data["req_lifecycle"])]
    document.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def _edit_config(root: Path, old: str, new: str) -> None:
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    assert old in text
    config.write_text(text.replace(old, new), encoding="utf-8")


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S1
def test_generated_config_states_tiers_lock_and_lifecycle_field(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    config = load_config(root)

    assert config["tiers"]["StRS"]["approval_lock"] is True
    assert config["tiers"]["SwRS"]["approval_lock"] is False
    assert config["lifecycle"] == {"field": "req_lifecycle"}
    assert "levels" not in config
    assert lifecycle_values(root, config) == [
        "draft",
        "proposed",
        "approved",
        "deprecated",
        "superseded",
    ]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S4
def test_lifecycle_values_come_from_the_schema_enum_unless_legacy_values_are_set(
    tmp_path: Path,
) -> None:
    root = make_bundle(tmp_path)
    schema = tiers_path(root) / "_schema" / "base.schema.yaml"
    schema.write_text(
        schema.read_text(encoding="utf-8").replace(
            "    - superseded\n", "    - superseded\n    - retired\n"
        ),
        encoding="utf-8",
    )
    assert lifecycle_values(root, load_config(root))[-1] == "retired"

    _edit_config(root, "  field: req_lifecycle\n", "  values: [draft, proposed]\n")
    assert lifecycle_values(root, load_config(root)) == ["draft", "proposed"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S1
def test_legacy_levels_key_is_read_and_cannot_be_mixed_with_tiers(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _edit_config(root, "tiers:\n", "levels:\n")
    add_requirements(root)
    assert validate_requirements(root) == []

    _edit_config(root, "levels:\n", "tiers: {}\nlevels:\n")
    with pytest.raises(RequirementError, match="both tiers and the legacy levels"):
        load_config(root)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S5
@Parametrization.autodetect_parameters()
@Parametrization.case(name="tier_default", scope="other", expected=(False, "tier@x.org"))
@Parametrization.case(name="scope_owner", scope="ui", expected=(False, "scope@x.org"))
@Parametrization.case(name="scope_tier", scope="api", expected=(True, "api@x.org"))
def test_owner_policy_prefers_scope_tier_then_scope_then_tier(
    scope: str, expected: tuple[bool, str]
) -> None:
    config = {
        "tiers": {
            "SwRS": {"derives_from": ["StRS"], "approval_lock": False, "owner_email": "tier@x.org"}
        },
        "scopes": {
            "ui": {"owner_email": "scope@x.org"},
            "api": {
                "owner_email": "scope@x.org",
                "tiers": {"SwRS": {"approval_lock": True, "owner_email": "api@x.org"}},
            },
        },
    }

    assert owner_policy(config, "SwRS", scope) == expected


def test_lock_defaults_to_top_tiers_when_unset() -> None:
    config = {"tiers": {"StRS": {"derives_from": []}, "SwRS": {"derives_from": ["StRS"]}}}

    assert owner_policy(config, "StRS", "default") == (True, None)
    assert owner_policy(config, "SwRS", "default") == (False, None)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S5
def test_default_owner_email_is_generated_and_removed_with_the_config(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    strs, swrs = add_requirements(root)
    _edit_config(root, "approval_lock: true}", "approval_lock: true, owner_email: po@x.org}")

    update_coverage(root)
    assert load_requirements(root)["StRS-default-001"][1]["default_owner_email"] == "po@x.org"
    assert "default_owner_email" not in load_requirements(root)["SwRS-default-001"][1]

    _edit_config(root, ", owner_email: po@x.org}", "}")
    assert update_coverage(root) == [str(strs)]
    assert "default_owner_email" not in load_requirements(root)["StRS-default-001"][1]
    assert swrs.is_file()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S6
def test_approved_requirement_needs_the_owner_agreement_fields(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    strs, _ = add_requirements(root)
    _set_fields(strs, req_lifecycle="approved", owner_email="po@x.org")

    findings = validate_requirements(root)
    assert len(findings) == 1
    assert "requires approved_by and approved_at" in findings[0]
    assert "(po@x.org)" in findings[0]
    assert "a coding agent never decides it alone" in findings[0]
    assert "request the owner's review" in findings[0]

    _set_fields(strs, approved_by="po@x.org", approved_at="2026-10-28")
    findings = validate_requirements(root)
    assert len(findings) == 1
    assert "approved_at must be an ISO 8601 datetime" in findings[0]

    _set_fields(strs, approved_at="2026-10-28T09:00:00+01:00")
    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S6
def test_approved_is_refused_where_approval_lock_is_false(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _, swrs = add_requirements(root)
    _set_fields(
        swrs,
        req_lifecycle="approved",
        approved_by="po@x.org",
        approved_at="2026-10-28T09:00:00+01:00",
    )

    findings = validate_requirements(root)
    assert len(findings) == 1
    assert "approval_lock is false" in findings[0]

    _edit_config(
        root,
        "  default: {source_dirs: [src], test_dirs: [tests]}",
        "  default: {source_dirs: [src], test_dirs: [tests], tiers: {SwRS: {approval_lock: true}}}",
    )
    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S7
@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="lock", setting="approval_lock: yes-please", match="approval_lock must be true or false"
)
@Parametrization.case(
    name="owner", setting="owner_email: nobody", match="owner_email is not an email address"
)
def test_malformed_ownership_settings_are_reported(
    tmp_path: Path, setting: str, match: str
) -> None:
    root = make_bundle(tmp_path)
    _edit_config(root, "approval_lock: false}", f"approval_lock: false}}\n  SwRT: {{{setting}}}")

    assert any(match in finding for finding in validate_requirements(root))


def test_new_can_start_a_requirement_as_proposed(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    result = CliRunner().invoke(
        okfreq,
        [
            "new",
            "strs",
            "Export",
            "--description",
            "The tool SHALL export.",
            "--project",
            "p",
            "--lifecycle",
            "proposed",
            "--path",
            str(root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert load_requirements(root)["StRS-default-001"][1]["req_lifecycle"] == "proposed"
    with pytest.raises(RequirementError, match="starts as draft or proposed"):
        create_requirement(
            root,
            "StRS",
            "X",
            "The tool SHALL x.",
            project="p",
            scope="default",
            origin="native",
            lifecycle="approved",
        )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S2
@Parametrization.autodetect_parameters()
@Parametrization.case(name="legacy_import", destination="tiers", incoming="levels")
@Parametrization.case(name="legacy_destination", destination="levels", incoming="tiers")
def test_config_merge_normalizes_legacy_levels_to_tiers(
    tmp_path: Path, destination: str, incoming: str
) -> None:
    root = make_bundle(tmp_path)
    _edit_config(root, "tiers:\n", f"{destination}:\n")
    source = tmp_path / "import.yml"
    source.write_text(
        f"{incoming}:\n  SwRT: {{folder: swrt, prefix: SwRT, derives_from: [SwRS]}}\n",
        encoding="utf-8",
    )

    assert merge_config(root, source) == []
    text = (root / "config.yml").read_text(encoding="utf-8")
    assert "levels:" not in text
    config = load_config(root)
    assert list(config["tiers"]) == ["StRS", "SwRS", "SwRT"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-006#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S2
def test_config_merge_refuses_a_legacy_lifecycle_values_list_over_a_field(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    source = tmp_path / "import.yml"
    source.write_text("lifecycle:\n  values: [draft, done]\n", encoding="utf-8")

    assert merge_config(root, source) == ["lifecycle.values"]
    assert load_config(root)["lifecycle"] == {"field": "req_lifecycle"}

    source.write_text("tiers: {}\nlevels: {}\n", encoding="utf-8")
    with pytest.raises(RequirementError, match="both tiers and the legacy levels"):
        merge_config(root, source)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S5
@Parametrization.autodetect_parameters()
@Parametrization.case(name="case_insensitive_scope", scope="API", expected=(True, "api@x.org"))
@Parametrization.case(name="unknown_scope", scope="nowhere", expected=(False, "tier@x.org"))
@Parametrization.case(
    name="null_scope_lock_falls_back", scope="web", expected=(False, "tier@x.org")
)
def test_owner_policy_scope_matching_and_null_lock(scope: str, expected: tuple[bool, str]) -> None:
    config = {
        "tiers": {
            "SwRS": {"derives_from": ["StRS"], "approval_lock": False, "owner_email": "tier@x.org"}
        },
        "scopes": {
            "api": {"tiers": {"SwRS": {"approval_lock": True, "owner_email": "api@x.org"}}},
            "web": {"tiers": {"SwRS": {"approval_lock": None}}},
        },
    }

    assert owner_policy(config, "SwRS", scope) == expected


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S5
def test_null_lock_everywhere_and_custom_top_tier_default_to_lockable() -> None:
    config = {
        "tiers": {"Need": {"folder": "need", "approval_lock": None}},
        "scopes": {"default": {"tiers": {"Need": {"approval_lock": None}}}},
    }

    assert owner_policy(config, "Need", "default") == (True, None)
    assert owner_policy({"tiers": {"Goal": {"folder": "goal"}}}, "Goal", "x") == (True, None)


def test_new_rejects_an_unknown_initial_lifecycle(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    result = CliRunner().invoke(
        okfreq,
        ["new", "strs", "Export", "--description", "The tool SHALL export.", "--project", "p"]
        + ["--lifecycle", "bogus", "--path", str(root)],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--lifecycle'" in result.output
    assert load_requirements(root) == {}


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S6
@Parametrization.autodetect_parameters()
@Parametrization.case(name="deprecated", lifecycle="deprecated", extra={})
@Parametrization.case(
    name="superseded", lifecycle="superseded", extra={"superseded_by": ["SwRS-default-002"]}
)
def test_retired_requirement_may_keep_its_approval_record(
    tmp_path: Path, lifecycle: str, extra: dict
) -> None:
    root, paths = make_family(tmp_path)
    set_fields(
        paths["SwRS-default-001"],
        req_lifecycle=lifecycle,
        approved_by="po@x.org",
        approved_at="2026-10-28T09:00:00+01:00",
        **extra,
    )

    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-013#S3
def test_lifecycle_field_names_a_custom_frontmatter_field(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _edit_config(root, "  field: req_lifecycle\n", "  field: state\n")
    schema = tiers_path(root) / "_schema" / "base.schema.yaml"
    text = schema.read_text(encoding="utf-8")
    assert "\n  req_lifecycle:\n" in text and "\n- req_lifecycle\n" in text
    schema.write_text(
        text.replace("\n  req_lifecycle:\n", "\n  state:\n").replace(
            "\n- req_lifecycle\n", "\n- state\n"
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    for title in ("Export", "Import"):
        result = runner.invoke(
            okfreq,
            ["new", "strs", title, "--description", "The tool SHALL move data.", "--project", "p"]
            + ["--user-need", "Users move data.", "--lifecycle", "proposed", "--path", str(root)],
        )
        assert result.exit_code == 0, result.output
    created = load_requirements(root)["StRS-default-001"][1]
    assert (created["state"], created["status"]) == ("proposed", "stable")
    assert "req_lifecycle" not in created
    assert validate_requirements(root) == []

    supersede_requirement(root, "StRS-default-001", ["StRS-default-002"])
    archived = runner.invoke(okfreq, ["archive", "StRS-default-002", "--path", str(root), "--yes"])
    assert archived.exit_code == 0, archived.output
    requirements = load_requirements(root)
    assert requirements["StRS-default-001"][1]["state"] == "superseded"
    assert requirements["StRS-default-002"][1]["state"] == "deprecated"
    assert requirements["StRS-default-002"][1]["status"] == "deprecated"
    assert "req_lifecycle" not in requirements["StRS-default-002"][1]
    assert validate_requirements(root) == []


def findings_of(root: Path) -> tuple[list[str], list[str]]:
    """Split validation findings into structural errors and W003/W004 advisories."""
    findings = validate_requirements(root)
    advisories = [item for item in findings if item.startswith(("W003 ", "W004 "))]
    return [item for item in findings if item not in advisories], advisories


def requirement_of(root: Path, identifier: str) -> dict[str, Any]:
    """Return one requirement record of the generated report."""
    return next(item for item in report(root)["requirements"] if item["id"] == identifier)


def stakeholder_of(root: Path, identifier: str) -> dict[str, Any]:
    """Return one StRS's ``stakeholder_test_coverage`` report entry."""
    coverage: dict[str, Any] = requirement_of(root, identifier)["stakeholder_test_coverage"]
    return coverage


def make_paths_bundle(
    tmp_path: Path, *, paths: int = 3, mode: str = ACCEPTANCE_PATHS_MODE
) -> dict[str, Path]:
    """Return an StRS declaring ``paths`` scenarios, its SwRS and its implementation."""
    root = init_requirements(tmp_path / "requirements")
    set_mode(root, mode)
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    stunter = create_requirement(
        root,
        "StRS",
        "Export",
        "The tool SHALL export a report.",
        user_need="Users need reports.",
        **common,
    )
    declare_scenarios(stunter, *(f"S{number}" for number in range(1, paths + 1)))
    software = create_requirement(
        root,
        "SwRS",
        "Write",
        "The tool SHALL write the file.",
        derives_from=[stunter.stem],
        **common,
    )
    (project_path(root) / "src").mkdir(exist_ok=True)
    (project_path(root) / "src" / "implementation.py").write_text(
        f"# @implements_req {software.stem}\n", encoding="utf-8"
    )
    return {"root": root, "stunter": stunter, "software": software}


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_load_config_accepts_the_acceptance_paths_mode(tmp_path: Path) -> None:
    assert STRS_TEST_COVERAGE_MODES == (
        "linked-swrs",
        "linked-swrs-and-validation-test",
        ACCEPTANCE_PATHS_MODE,
    )
    root = make_bundle(tmp_path)
    assert load_config(root)["strs_test_coverage_mode"] == "linked-swrs"
    set_mode(root, ACCEPTANCE_PATHS_MODE)
    config = load_config(root)

    assert config["strs_test_coverage_mode"] == ACCEPTANCE_PATHS_MODE
    assert config["markers"]["accepts"] == "@accepts_req"
    assert "accepted_in_files" in config["generated_fields"]
    assert ACCEPTANCE_PATHS_MODE in STRS_TEST_COVERAGE_DESCRIPTIONS


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_the_mode_refusal_lists_the_three_modes(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    _edit_config(
        root,
        "strs_test_coverage_mode: linked-swrs\n",
        "strs_test_coverage_mode: unsupported\n",
    )

    with pytest.raises(RequirementError) as raised:
        load_config(root)
    assert str(raised.value) == (
        "unsupported strs_test_coverage_mode: unsupported; expected one of: "
        "linked-swrs, linked-swrs-and-validation-test, linked-swrs-and-acceptance-paths"
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
@pytest.mark.parametrize("mode", STRS_TEST_COVERAGE_MODES)
def test_duplicate_marker_keywords_fail_in_every_mode(tmp_path: Path, mode: str) -> None:
    root = make_bundle(tmp_path)
    set_mode(root, mode)
    _edit_config(root, "  accepts: '@accepts_req'\n", "  accepts: '@tests_req'\n")

    with pytest.raises(
        RequirementError,
        match="markers.tests and markers.accepts use the same keyword @tests_req",
    ):
        load_config(root)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_an_old_config_without_accepts_gets_the_default_keyword(tmp_path: Path) -> None:
    paths = make_paths_bundle(tmp_path, paths=2)
    root = paths["root"]
    _edit_config(root, "  accepts: '@accepts_req'\n", "")
    assert "accepts" not in (root / "config.yml").read_text(encoding="utf-8")
    assert load_config(root)["markers"]["accepts"] == "@accepts_req"
    write_test_file(
        root,
        "test_paths.py",
        [f"# @accepts_req {paths['stunter'].stem}#S1", f"# @tests_req {paths['software'].stem}#S1"],
    )
    assert marker_scan(root)["accepted"] == {paths["stunter"].stem: ["tests/test_paths.py"]}
    assert stakeholder_of(root, paths["stunter"].stem)["paths"] == {
        "total": 2,
        "tested": 0,
        "accepted": 1,
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_accepted_in_files_is_a_supported_generated_field(tmp_path: Path) -> None:
    paths = make_paths_bundle(tmp_path, paths=2)
    root = paths["root"]
    write_test_file(
        root,
        "test_paths.py",
        [f"# @accepts_req {paths['stunter'].stem}#S1", f"# @tests_req {paths['software'].stem}#S1"],
    )
    update_coverage(root)
    data = load_requirements(root)[paths["stunter"].stem][1]

    assert data["tested_in_files"] == []
    assert data["accepted_in_files"] == ["tests/test_paths.py"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_init_writes_the_scenarios_and_acceptance_declarations(tmp_path: Path) -> None:
    root = make_bundle(tmp_path)
    schemas = tiers_path(root) / "_schema"
    yaml = make_yaml()
    base = yaml.load((schemas / "base.schema.yaml").read_text(encoding="utf-8"))
    stakhold = yaml.load((schemas / "strs.schema.yaml").read_text(encoding="utf-8"))
    software = yaml.load((schemas / "swrs.schema.yaml").read_text(encoding="utf-8"))
    config_text = (root / "config.yml").read_text(encoding="utf-8")

    scenarios = base["properties"]["scenarios"]
    assert (scenarios["type"], scenarios["minItems"]) == ("array", 1)
    assert "#S<n>" in scenarios["description"]
    assert scenarios["items"]["required"] == ["id", "title"]
    assert scenarios["items"]["additionalProperties"] is False
    assert scenarios["items"]["properties"]["id"]["pattern"] == "^S[1-9][0-9]*$"
    assert scenarios["items"]["properties"]["title"]["minLength"] == 1
    assert (
        "adds declared scenarios (the scenarios frontmatter field, body intact)"
        in (base["properties"]["req_lifecycle"]["description"])
    )

    profile = next(part for part in stakhold["allOf"] if "properties" in part)
    properties = profile["properties"]
    assert properties["tested_in_files"]["description"] == "Generated test paths."
    assert properties["tested_in_files"]["items"]["x-okf-link"]["basename_marker"] == "@tests_req"
    accepted = properties["accepted_in_files"]
    assert accepted["items"]["x-okf-link"]["basename_marker"] == "@accepts_req"
    assert ACCEPTANCE_PATHS_MODE in accepted["description"]
    assert properties["acceptance_exemption"]["type"] == "boolean"
    assert properties["acceptance_exemption_reason"]["minLength"] == 1
    conditional = next(part for part in profile["allOf"] if "if" in part)
    assert conditional["if"]["properties"]["acceptance_exemption"]["const"] is True
    assert conditional["then"]["required"] == ["acceptance_exemption_reason"]

    swrs_profile = next(part for part in software["allOf"] if "properties" in part)
    refusal = swrs_profile["properties"]["accepted_in_files"]
    assert refusal["maxItems"] == 0
    assert refusal["description"].startswith("Never present. @accepts_req names a StRS main path")

    assert "  accepts: '@accepts_req'\n" in config_text
    assert "accepted_in_files" in config_text


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_marker_scan_reads_accepts_markers_lines_and_fragments(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path)
    add_requirements(root)
    write_test_file(
        root,
        "test_fragments.py",
        [
            "# @accepts_req StRS-default-001#S1",
            "# @tests_req StRS-default-001#S1",
            "# @tests_req StRS-default-001#S2",
            "# @tests_req StRS-default-001#path1",
            "# @tests_req StRS-default-001#S1a",
            "# @tests_req StRS-default-001#",
            "# @accepts_req StRS-default-001#S0",
            "# @tests_req Ghost-001",
            "# @accepts_req Ghost-002",
        ],
    )
    (project_path(root) / "src").mkdir(exist_ok=True)
    (project_path(root) / "src" / "implementation.py").write_text(
        "# @accepts_req StRS-default-001\n# @tests_req SwRS-default-001\n", encoding="utf-8"
    )
    scan = marker_scan(root)

    assert sorted(scan)[0] == "accepted"
    assert sorted(scan)[-1] == "warnings"
    assert "scenario_markers" in scan
    assert [
        (item["marker"], item["id"], item["fragment"], item["line"])
        for item in scan["scenario_markers"]
    ] == [
        ("accepts", "StRS-default-001", "S1", 1),
        ("tests", "StRS-default-001", "S1", 2),
        ("tests", "StRS-default-001", "S2", 3),
        ("tests", "StRS-default-001", None, 4),
        ("tests", "StRS-default-001", None, 5),
        ("tests", "StRS-default-001", None, 6),
        ("accepts", "StRS-default-001", "S0", 7),
        ("tests", "Ghost-001", None, 8),
        ("accepts", "Ghost-002", None, 9),
    ]
    assert {item["file"] for item in scan["scenario_markers"]} == {"tests/test_fragments.py"}
    assert scan["accepted"] == {"StRS-default-001": ["tests/test_fragments.py"] * 2}
    assert scan["missing_ids"] == ["Ghost-001", "Ghost-002"]
    # ``validation_tests`` keeps the raw ``@tests_req`` files on a StRS in every mode,
    # once per distinct fragment.
    assert scan["validation_tests"]["StRS-default-001"] == ["tests/test_fragments.py"] * 3
    assert "SwRS-default-001" not in scan["tested"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_marker_scan_uses_the_configured_test_keywords(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path)
    add_requirements(root)
    _edit_config(root, "  tests: '@tests_req'\n", "  tests: '@verifies'\n")
    _edit_config(root, "  accepts: '@accepts_req'\n", "  accepts: '@accepts'\n")
    write_test_file(
        root,
        "test_keywords.py",
        [
            "# @verifies StRS-default-001#S1",
            "# @accepts StRS-default-001#S1",
            "# @tests_req StRS-default-002",
        ],
    )
    scan = marker_scan(root)

    assert [(item["marker"], item["fragment"]) for item in scan["scenario_markers"]] == [
        ("tests", "S1"),
        ("accepts", "S1"),
    ]
    # A StRS keeps its ``@tests_req`` markers as validation tests, in every mode.
    assert scan["tested"] == {}
    assert scan["validation_tests"] == {"StRS-default-001": ["tests/test_keywords.py"]}
    assert scan["accepted"] == {"StRS-default-001": ["tests/test_keywords.py"]}
    assert "StRS-default-002" not in scan["validation_tests"]


def transitions_bundle(
    tmp_path: Path, *, paths: int = 2, transitions: int = 2, mode: str = ACCEPTANCE_PATHS_MODE
) -> dict[str, Path]:
    """Return an StRS with ``paths`` scenarios and a SwRS with ``transitions`` of them."""
    bundle = make_paths_bundle(tmp_path, paths=paths, mode=mode)
    declare_scenarios(bundle["software"], *(f"S{number}" for number in range(1, transitions + 1)))
    return bundle


def silent_bundle(tmp_path: Path, *, paths: int = 2) -> dict[str, Path]:
    """Return a bundle whose SwRS declares no transitions."""
    bundle = make_paths_bundle(tmp_path, paths=paths)
    set_frontmatter(bundle["software"], drop=("scenarios",))
    return bundle


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_declared_fragment_tests_and_accepts_its_path(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @accepts_req {stunter.stem}#S1",
            f"# @accepts_req {stunter.stem}#S2",
        ],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert errors == []
    assert advisories == []
    assert coverage["paths"] == {"total": 2, "tested": 2, "accepted": 2}
    assert (coverage["tested"], coverage["accepted"]) == (True, True)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_an_undeclared_fragment_is_an_error_on_a_declared_statement(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @accepts_req {stunter.stem}#S4"],
    )
    errors, _ = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert errors == [
        f"tests/test_paths.py:1: @accepts_req {stunter.stem}#S4 names no declared scenario "
        f"of {stunter.stem} (declared: S1, S2)"
    ]
    assert coverage["paths"] == {"total": 2, "tested": 0, "accepted": 0}
    assert coverage["accepted"] is False


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_fragmentless_test_marker_is_an_error_when_paths_are_declared(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @tests_req {stunter.stem}"])
    errors, _ = findings_of(bundle["root"])

    expected = f"tests/test_paths.py:1: @tests_req {stunter.stem} has no scenario fragment; "
    assert expected in errors[0]
    assert errors[0].endswith(
        f"{stunter.stem} declares scenarios S1, S2: write @tests_req {stunter.stem}#S<n> "
        "(this marker does not count)"
    )
    assert stakeholder_of(bundle["root"], stunter.stem)["paths"] == {
        "total": 2,
        "tested": 0,
        "accepted": 0,
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_fragmentless_accepts_marker_is_an_error_when_paths_are_declared(
    tmp_path: Path,
) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @accepts_req {stunter.stem}"])
    errors, _ = findings_of(bundle["root"])

    assert errors[0].endswith(
        f"{stunter.stem} declares scenarios S1, S2: write @accepts_req {stunter.stem}#S<n> "
        "(this marker does not count)"
    )
    assert stakeholder_of(bundle["root"], stunter.stem)["accepted"] is False


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_declared_fragment_tests_a_swrs_transition(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {software.stem}#S1", f"# @tests_req {software.stem}#S2"],
    )
    errors, _ = findings_of(bundle["root"])
    record = requirement_of(bundle["root"], software.stem)

    assert errors == []
    assert record["transitions"] == {"tested": ["S1", "S2"], "missing": []}
    assert record["tests"]["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_an_undeclared_fragment_is_an_error_on_a_swrs(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @tests_req {software.stem}#S9"])
    errors, _ = findings_of(bundle["root"])

    assert errors == [
        f"tests/test_paths.py:1: @tests_req {software.stem}#S9 names no declared scenario "
        f"of {software.stem} (declared: S1, S2)"
    ]
    assert requirement_of(bundle["root"], software.stem)["tests"]["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_fragmentless_swrs_marker_is_an_error_when_transitions_are_declared(
    tmp_path: Path,
) -> None:
    bundle = transitions_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @tests_req {software.stem}"])
    errors, _ = findings_of(bundle["root"])

    assert errors[0].endswith(
        f"{software.stem} declares scenarios S1, S2: write @tests_req {software.stem}#S<n> "
        "(this marker does not count)"
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_fragmentless_swrs_marker_covers_the_whole_statement(tmp_path: Path) -> None:
    bundle = silent_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @tests_req {software.stem}"])
    errors, _ = findings_of(bundle["root"])
    record = requirement_of(bundle["root"], software.stem)

    assert errors == []
    assert "transitions" not in record
    assert record["tests"] == {"status": "covered", "files": ["tests/test_paths.py"], "count": 1}


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_an_undeclared_fragment_is_an_error_when_nothing_is_declared(tmp_path: Path) -> None:
    bundle = silent_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @tests_req {software.stem}#S1"])
    errors, _ = findings_of(bundle["root"])

    assert errors == [
        f"tests/test_paths.py:1: @tests_req {software.stem}#S1 names no declared scenario "
        f"of {software.stem} ({software.stem} declares no scenarios:)"
    ]


def add_tier(root: Path, name: str, *, derives_from: list[str]) -> None:
    """Add a project tier, with a minimal schema built on the bundle's base schema."""
    _edit_config(
        root,
        "  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}\n",
        "  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}\n"
        f"  {name}: {{folder: {name.casefold()}, prefix: {name}, "
        f"derives_from: [{', '.join(derives_from)}], approval_lock: false}}\n",
    )
    (tiers_path(root) / "_schema" / f"{name.casefold()}.schema.yaml").write_text(
        "$schema: https://json-schema.org/draft/2020-12/schema\n"
        f"$id: {name.casefold()}.schema.yaml\n"
        f"title: okfreq {name} profile\n"
        "allOf:\n"
        "  - $ref: base.schema.yaml\n"
        "  - type: object\n"
        "    properties:\n"
        f"      type: {{const: {name}}}\n"
        f"      tier: {{const: {name}}}\n",
        encoding="utf-8",
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_a_marker_on_a_project_added_parent_tier_keeps_todays_handling(
    tmp_path: Path,
) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    root = bundle["root"]
    add_tier(root, "USec", derives_from=[])
    _edit_config(
        root,
        "  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}",
        "  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS, USec], approval_lock: false}",
    )
    software = bundle["software"]
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    detail = create_requirement(
        root,
        "USec",
        "Detail",
        "The tool SHALL detail the file.",
        user_need="Users need details.",
        **common,
    )
    set_frontmatter(detail, scenarios=[{"id": "S1", "title": "Detail"}])
    _set_fields(
        software,
        derives_from=[bundle["stunter"].stem, detail.stem],
    )
    write_test_file(
        root,
        "test_paths.py",
        [f"# @tests_req {detail.stem}#S1"],
    )
    scan = marker_scan(root)
    errors, _ = findings_of(root)

    # Today's handling: the parent tier is a ``non_leaf`` entry, its fragment is not
    # checked and Rule 4's counters ignore it.
    assert scan["non_leaf"] == [detail.stem]
    assert detail.stem not in scan["tested"]
    assert [error for error in errors if detail.stem in error] == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_no_marker_leaves_every_path_counter_at_zero(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=3)
    coverage = stakeholder_of(bundle["root"], bundle["stunter"].stem)

    assert coverage["paths"] == {"total": 3, "tested": 0, "accepted": 0}
    assert (coverage["tested"], coverage["accepted"]) == (False, False)
    assert coverage["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_two_of_three_paths_tested_and_one_accepted(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=3)
    stunter = bundle["stunter"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @accepts_req {stunter.stem}#S3",
        ],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert errors == []
    assert coverage["paths"] == {"total": 3, "tested": 2, "accepted": 1}
    # S3 is accepted and not tested; S1 and S2 are tested and not accepted.
    assert (coverage["tested"], coverage["accepted"]) == (False, False)
    # One counting ``@accepts_req`` is enough to suppress W004.
    assert advisories == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_the_counters_are_independent_of_each_other(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {stunter.stem}#S1", f"# @accepts_req {stunter.stem}#S2"],
    )
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert coverage["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert (coverage["tested"], coverage["accepted"]) == (False, False)
    assert coverage["tests"]["files"] == ["tests/test_paths.py"]
    assert coverage["acceptance_tests"]["files"] == ["tests/test_paths.py"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_every_path_tested_and_accepted_covers_the_statement(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @accepts_req {stunter.stem}#S1",
            f"# @accepts_req {stunter.stem}#S2",
            f"# @tests_req {software.stem}#S1",
            f"# @tests_req {software.stem}#S2",
        ],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert (errors, advisories) == ([], [])
    assert coverage["paths"] == {"total": 2, "tested": 2, "accepted": 2}
    assert (coverage["tested"], coverage["accepted"]) == (True, True)
    assert coverage["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_statement_without_linked_swrs_never_gets_covered(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    stunter = bundle["stunter"]
    (tiers_path(bundle["root"]) / "swrs" / f"{bundle['software'].stem}.md").unlink()
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {stunter.stem}#S1", f"# @accepts_req {stunter.stem}#S1"],
    )
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert coverage["paths"] == {"total": 1, "tested": 1, "accepted": 1}
    assert coverage["linked_swrs"] == []
    assert coverage["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_missing_linked_swrs_keeps_the_statement_missing(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @accepts_req {stunter.stem}#S1",
            f"# @accepts_req {stunter.stem}#S2",
            f"# @tests_req {software.stem}#S1",
        ],
    )
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert coverage["accepted"] is True
    assert coverage["linked_swrs"] == [{"id": software.stem, "status": "missing"}]
    assert coverage["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_statement_without_scenarios_is_tested_by_a_fragmentless_marker(
    tmp_path: Path,
) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    set_frontmatter(stunter, drop=("scenarios",))
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {stunter.stem}", f"# @accepts_req {stunter.stem}"],
    )
    errors, _ = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert coverage["paths"] == {"total": 0, "tested": 0, "accepted": 0}
    assert (coverage["tested"], coverage["accepted"]) == (True, True)
    assert any(error.startswith("W003 ") for error in errors) is False


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_update_coverage_writes_the_counting_statement_fields(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @accepts_req {stunter.stem}#S1",
            f"# @tests_req {software.stem}#S1",
            f"# @tests_req {software.stem}",
            f"# @accepts_req {software.stem}",
        ],
    )
    update_coverage(bundle["root"])
    requirements = load_requirements(bundle["root"])

    assert requirements[stunter.stem][1]["tested_in_files"] == ["tests/test_paths.py"]
    assert requirements[stunter.stem][1]["accepted_in_files"] == ["tests/test_paths.py"]
    # The SwRS frontmatter is the raw scan (see the divergence test below); the report
    # lists only its counting markers.
    assert requirement_of(bundle["root"], software.stem)["tests"] == {
        "status": "covered",
        "files": ["tests/test_paths.py"],
        "count": 1,
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_update_coverage_lists_only_counting_swrs_marker_files(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_counting.py", [f"# @tests_req {software.stem}#S1"])
    write_test_file(
        bundle["root"],
        "test_rejected.py",
        [f"# @tests_req {software.stem}", f"# @accepts_req {software.stem}"],
    )
    update_coverage(bundle["root"])

    assert load_requirements(bundle["root"])[software.stem][1]["tested_in_files"] == [
        "tests/test_counting.py"
    ]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_update_coverage_leaves_an_unlisted_generated_field_untouched(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    root, stunter = bundle["root"], bundle["stunter"]
    _edit_config(root, "  accepted_in_files, ", "  ")
    set_frontmatter(stunter, accepted_in_files=["hand/placed.py"])
    write_test_file(
        root,
        "test_paths.py",
        [f"# @tests_req {stunter.stem}#S1", f"# @accepts_req {stunter.stem}#S1"],
    )
    update_coverage(root)
    data = load_requirements(root)[stunter.stem][1]

    assert data["tested_in_files"] == ["tests/test_paths.py"]
    assert data["accepted_in_files"] == ["hand/placed.py"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_update_coverage_adds_no_unlisted_field(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    root, stunter = bundle["root"], bundle["stunter"]
    _edit_config(root, "  accepted_in_files, ", "  ")
    write_test_file(root, "test_paths.py", [f"# @accepts_req {stunter.stem}#S1"])
    update_coverage(root)

    assert "accepted_in_files" not in load_requirements(root)[stunter.stem][1]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
@pytest.mark.parametrize("mode", ["linked-swrs", "linked-swrs-and-validation-test"])
def test_old_modes_remove_the_test_fields_from_a_statement(tmp_path: Path, mode: str) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1, mode=mode)
    root, stunter = bundle["root"], bundle["stunter"]
    set_frontmatter(stunter, tested_in_files=["hand/t.py"], accepted_in_files=["hand/a.py"])
    update_coverage(root)
    data = load_requirements(root)[stunter.stem][1]

    assert "tested_in_files" not in data
    assert "accepted_in_files" not in data


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_justified_waiver_covers_the_statement_and_keeps_honest_counts(
    tmp_path: Path,
) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    set_frontmatter(
        stunter,
        acceptance_exemption=True,
        acceptance_exemption_reason="Interactive consolidation cannot be automated.",
    )
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [
            f"# @tests_req {stunter.stem}#S1",
            f"# @accepts_req {stunter.stem}#S1",
            f"# @tests_req {software.stem}#S1",
            f"# @tests_req {software.stem}#S2",
        ],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert errors == []
    # W004 is suppressed, the actual acceptance is not invented.
    assert advisories == []
    assert coverage["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert coverage["accepted"] is False
    assert coverage["status"] == "covered"
    assert coverage["acceptance_exemption"] == {
        "reason": "Interactive consolidation cannot be automated."
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_an_entirely_unaccepted_waived_statement_is_covered_without_acceptance(
    tmp_path: Path,
) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    set_frontmatter(
        stunter,
        acceptance_exemption=True,
        acceptance_exemption_reason="No automated acceptance possible.",
    )
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {software.stem}#S1", f"# @tests_req {software.stem}#S2"],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert errors == []
    assert advisories == []
    assert coverage["paths"] == {"total": 2, "tested": 0, "accepted": 0}
    assert (coverage["tested"], coverage["accepted"]) == (False, False)
    assert coverage["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_waiver_without_a_reason_is_invalid_and_never_covers(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    stunter = bundle["stunter"]
    set_frontmatter(stunter, acceptance_exemption=True)
    errors, _ = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert any("acceptance exemption requires a non-empty" in error for error in errors)
    assert "acceptance_exemption" not in coverage
    assert coverage["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_blank_waiver_reason_is_invalid_in_the_new_mode(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    stunter = bundle["stunter"]
    set_frontmatter(stunter, acceptance_exemption=True, acceptance_exemption_reason="   ")
    errors, _ = findings_of(bundle["root"])

    assert any(
        error.endswith(
            f"{stunter}: acceptance exemption requires a non-empty acceptance_exemption_reason"
        )
        for error in errors
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_an_exempt_swrs_satisfies_the_linked_condition_and_stays_out_of_fields(
    tmp_path: Path,
) -> None:
    bundle = transitions_bundle(tmp_path)
    stunter, software = bundle["stunter"], bundle["software"]
    set_frontmatter(
        software,
        annotation_exemption=True,
        exemption_reason="Delivered by an external generator.",
    )
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @accepts_req {stunter.stem}#S1", f"# @accepts_req {stunter.stem}#S2"],
    )
    errors, advisories = findings_of(bundle["root"])
    coverage = stakeholder_of(bundle["root"], stunter.stem)
    generated = report(bundle["root"])["marker_coverage"]

    assert errors == []
    assert advisories == []
    assert coverage["linked_swrs"] == [{"id": software.stem, "status": "exempt"}]
    assert coverage["status"] == "covered"
    assert generated["missing_tests"] == []
    assert generated["exemptions"] == [
        {"id": software.stem, "reason": "Delivered by an external generator."}
    ]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_a_justified_waiver_writes_neither_markers_nor_counters(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    stunter = bundle["stunter"]
    set_frontmatter(
        stunter, acceptance_exemption=True, acceptance_exemption_reason="Manual review."
    )
    update_coverage(bundle["root"])
    data = load_requirements(bundle["root"])[stunter.stem][1]
    coverage = stakeholder_of(bundle["root"], stunter.stem)

    assert data["acceptance_exemption"] is True
    assert data["acceptance_exemption_reason"] == "Manual review."
    assert data["accepted_in_files"] == []
    assert coverage["paths"] == {"total": 2, "tested": 0, "accepted": 0}
    assert coverage["accepted"] is False


def weaken_swrs_schema(schema: Path, *, drop: bool = True) -> bool:
    """Make a bundle's SwRS schema accept ``accepted_in_files``.

    With ``drop`` the whole property goes (a pre-0.18.0 bundle); without it only
    the ``maxItems: 0`` refusal goes, leaving a declaration that accepts a path.
    """
    yaml = make_yaml()
    data = yaml.load(schema.read_text(encoding="utf-8"))
    for part in data["allOf"]:
        properties = part.get("properties") if isinstance(part, dict) else None
        if properties and "accepted_in_files" in properties:
            if drop:
                properties.pop("accepted_in_files")
            else:
                properties["accepted_in_files"].pop("maxItems", None)
            buffer = io.StringIO()
            yaml.dump(data, buffer)
            schema.write_text(buffer.getvalue(), encoding="utf-8")
            return True
    return False


SCENARIOS_DOC_LINK = (
    "https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html"
    "#okfreq-declared-scenarios"
)
EXECUTION_COST_LINK = (
    "https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html"
    "#okfreq-execution-cost"
)


def w003_of(root: Path, identifier: str) -> str:
    """Return the single W003 finding addressed to one statement."""
    found = [
        finding
        for finding in validate_requirements(root)
        if finding.startswith("W003 ") and f"/{identifier}.md: {identifier} " in finding
    ]
    assert len(found) == 1, found
    return str(found[0])


def w004_of(root: Path, identifier: str) -> str:
    """Return the single W004 finding addressed to one statement."""
    found = [
        finding
        for finding in validate_requirements(root)
        if finding.startswith("W004 ") and f"/{identifier}.md: {identifier} " in finding
    ]
    assert len(found) == 1, found
    return str(found[0])


def w003_bundle(tmp_path: Path) -> Path:
    """Return a new-mode bundle whose StRS declares no ``scenarios:`` (so W003 fires)."""
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    set_frontmatter(tiers_path(root) / "strs" / "StRS-default-001.md", drop=("scenarios",))
    return root


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_quotes_the_path_headings_and_gives_the_block_to_paste(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)
    set_body(
        tiers_path(root) / "strs" / "StRS-default-001.md",
        "## Export\n\n### Normative behavior\n\nThe tool SHALL export.\n\n"
        "### Main paths\n\n#### Path 1: Choose a format\n\n1. Choose.\n\n"
        "#### Path 2: Write the file\n\n1. Write.\n\n## User Need\n\nUsers need exports.\n",
    )
    finding = w003_of(root, "StRS-default-001")

    assert finding.endswith(SCENARIOS_DOC_LINK)
    # The quote keeps the heading text without its leading hashes.
    assert 'headings found:\n  - "Path 1: Choose a format"\n  - "Path 2: Write the file"' in finding
    assert (
        "Add this block to the frontmatter (body intact), then add a #S<n> fragment to "
        "each test marker:\nscenarios:\n  - id: S1\n    title: Choose a format\n"
        "  - id: S2\n    title: Write the file\n"
    ) in finding
    assert "On an approved StRS, log the change in the bundle's tiers/log.md." in finding


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_reads_scenario_headings_of_any_kind(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)
    set_body(
        tiers_path(root) / "strs" / "StRS-default-001.md",
        "## Export\n\n### Scenario: Wait for a render\n\n1. Wait.\n\n"
        "### Scenario S7: The source is gone\n\n1. Recover.\n",
    )
    finding = w003_of(root, "StRS-default-001")

    assert '  - "Scenario: Wait for a render"' in finding
    assert '  - "Scenario S7: The source is gone"' in finding
    # The legacy heading keeps its whole text; the explicit id is preserved.
    assert '  - id: S1\n    title: "Scenario: Wait for a render"\n' in finding
    assert "  - id: S7\n    title: The source is gone\n" in finding


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_gives_a_placeholder_block_without_a_heading(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)
    set_body(
        tiers_path(root) / "strs" / "StRS-default-001.md",
        "## Export\n\n### Normative behavior\n\nThe tool SHALL export.\n",
    )
    finding = w003_of(root, "StRS-default-001")

    assert "declares no scenarios:; no path or scenario heading was found in the body\n" in finding
    assert "scenarios:\n  - id: S1\n    title: <main path title>\n" in finding


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_stops_at_the_next_section_and_at_the_links_block(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)
    set_body(
        tiers_path(root) / "strs" / "StRS-default-001.md",
        "## Export\n\n### Main paths\n\n#### Path 1: Keep\n\n1. Keep.\n\n"
        "## User Need\n\n#### Path 9: Ignored\n\n1. Ignored.\n\n"
        "<!-- okf:links:start -->\n\n#### Path 8: Also ignored\n",
    )
    finding = w003_of(root, "StRS-default-001")

    assert "Keep" in finding
    assert "Ignored" not in finding
    assert "Also ignored" not in finding


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_skips_retired_statements_and_flags_a_draft(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)
    draft = w003_of(root, "StRS-default-001")

    assert draft.startswith("W003 ")

    for lifecycle in ("deprecated", "superseded"):
        set_frontmatter(
            tiers_path(root) / "strs" / "StRS-default-001.md",
            req_lifecycle=lifecycle,
            superseded_by="",
        )
        assert not any(
            finding.startswith("W003 ") and "StRS-default-001" in finding
            for finding in validate_requirements(root)
        )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w003_is_printed_without_the_prose_flag(tmp_path: Path) -> None:
    root = w003_bundle(tmp_path)

    assert any(finding.startswith("W003 ") for finding in validate_requirements(root, prose=False))
    assert any(finding.startswith("W003 ") for finding in validate_requirements(root, prose=True))


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_no_w003_for_a_swrs_without_scenarios(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    _, swrs = add_requirements(root)
    set_frontmatter(tiers_path(root) / "swrs" / swrs.name, drop=("scenarios",))
    set_body(
        tiers_path(root) / "swrs" / swrs.name,
        "## Write\n\n### Scenario: Write succeeds\n\n1. Write.\n",
    )
    findings = validate_requirements(root)

    assert not any(finding.startswith("W003 ") and swrs.stem in finding for finding in findings)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w004_names_the_statement_and_the_execution_cost(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    finding = w004_of(root, "StRS-default-001")

    assert finding == (
        f"W004 {tiers_path(root) / 'strs' / 'StRS-default-001.md'}: StRS-default-001 has no "
        "acceptance test: no @accepts_req marker that counts names it. Mark the test closest "
        "to the final product that walks each main path with @accepts_req StRS-default-001#S<n> "
        "(@accepts_req StRS-default-001 while it declares no scenarios:). That test may be "
        "costly and run in the main-branch pipeline, beside cheaper @tests_req tests run on "
        f"every pull or merge request. See {EXECUTION_COST_LINK}"
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w004_counts_only_acceptance_markers_that_count(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    write_test_file(root, "test_flow.py", ["# @accepts_req StRS-default-001"])
    assert w004_of(root, "StRS-default-001")

    write_test_file(root, "test_flow.py", ["# @accepts_req StRS-default-001#S1"])
    assert not any(
        finding.startswith("W004 ") and "StRS-default-001" in finding
        for finding in validate_requirements(root)
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w004_is_independent_of_w003_and_suppressed_by_a_waiver(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    stunter = tiers_path(root) / "strs" / "StRS-default-001.md"
    set_frontmatter(stunter, drop=("scenarios",))
    findings = validate_requirements(root)

    assert any(
        finding.startswith("W003 ") and "StRS-default-001" in finding for finding in findings
    )
    assert any(
        finding.startswith("W004 ") and "StRS-default-001" in finding for finding in findings
    )

    set_frontmatter(
        stunter, acceptance_exemption=True, acceptance_exemption_reason="Manual review only."
    )
    waived = validate_requirements(root)

    # A justified waiver suppresses W004, never W003.
    assert any(finding.startswith("W003 ") and "StRS-default-001" in finding for finding in waived)
    assert not any(
        finding.startswith("W004 ") and "StRS-default-001" in finding for finding in waived
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w004_skips_retired_statements(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    for lifecycle in ("deprecated", "superseded"):
        set_frontmatter(
            tiers_path(root) / "strs" / "StRS-default-001.md",
            req_lifecycle=lifecycle,
            superseded_by="",
        )
        assert not any(
            finding.startswith("W004 ") and "StRS-default-001" in finding
            for finding in validate_requirements(root)
        )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_w004_is_printed_without_the_prose_flag(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)

    assert any(finding.startswith("W004 ") for finding in validate_requirements(root))


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_update_coverage_preserves_the_waiver_fields(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    stunter = tiers_path(root) / "strs" / "StRS-default-001.md"
    set_frontmatter(
        stunter, acceptance_exemption=True, acceptance_exemption_reason="Manual review only."
    )
    original = stunter.read_text(encoding="utf-8")
    update_coverage(root)
    data = load_requirements(root)["StRS-default-001"][1]

    assert data["acceptance_exemption"] is True
    assert data["acceptance_exemption_reason"] == "Manual review only."
    # Only generated fields and the generated links block are added; the authored
    # waiver and the body stay.
    body = strip_links_section(stunter.read_text(encoding="utf-8"))
    assert extract_frontmatter(body)[1].rstrip() == extract_frontmatter(original)[1].rstrip()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_an_approved_statement_may_gain_only_its_scenarios(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    stunter = tiers_path(root) / "strs" / "StRS-default-001.md"
    body = extract_frontmatter(stunter.read_text(encoding="utf-8"))[1]
    set_frontmatter(
        stunter,
        drop=("scenarios",),
        req_lifecycle="approved",
        status="stable",
        approved_by="owner@example.com",
        approved_at="2026-01-01T09:00:00+00:00",
    )
    assert body == extract_frontmatter(stunter.read_text(encoding="utf-8"))[1]
    declare_scenarios(stunter, "S1", "S2")

    errors, _ = findings_of(root)

    assert errors == []
    assert body == extract_frontmatter(stunter.read_text(encoding="utf-8"))[1]


SCENARIO_REFUSALS = [
    (
        "kind",
        [{"id": "S1", "title": "Go", "kind": "path"}],
        "Additional properties are not allowed ('kind' was unexpected)",
        "scenarios: unexpected keys: kind",
    ),
    (
        "P1",
        [{"id": "P1", "title": "Go"}],
        "'P1' does not match '^S[1-9][0-9]*$'",
        "scenarios: invalid id 'P1'; expected S<n>",
    ),
    (
        "empty title",
        [{"id": "S1", "title": ""}],
        "'' should be non-empty",
        "scenarios: scenario 'S1' needs a non-empty title",
    ),
    (
        "empty list",
        [],
        "[] should be non-empty",
        "scenarios: expected a non-empty list",
    ),
]
SCENARIO_SUFFIX = "(each entry is {id: S<n>, title: <text>}, ids unique)"


def _scenarios_block(text: str) -> str:
    """Return the literal ``scenarios:`` block of a document's frontmatter."""
    frontmatter, _, _ = text.partition("\n---\n")
    match = re.search(r"(?m)^scenarios:\n(?:[- ][^\n]*(?:\n|$))*", frontmatter)
    assert match is not None, frontmatter
    return match.group(0)


@pytest.mark.parametrize(("label", "value", "schema_message", "code_message"), SCENARIO_REFUSALS)
# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_the_scenarios_field_is_refused_in_every_mode(
    tmp_path: Path,
    label: str,
    value: list[dict[str, str]],
    schema_message: str,
    code_message: str,
) -> None:
    for mode in STRS_TEST_COVERAGE_MODES:
        root = make_scanned_bundle(tmp_path / mode.replace("-", "_"), mode)
        stunter = create_requirement(
            root,
            "StRS",
            "Export",
            "The tool SHALL export a report.",
            project="demo",
            scope="default",
            origin="native",
            user_need="Users need reports.",
        )
        set_frontmatter(stunter, scenarios=value)
        errors, _ = findings_of(root)

        assert any(error.endswith(f": {schema_message}") for error in errors), label
        assert bool([error for error in errors if code_message in error]) is (
            mode == ACCEPTANCE_PATHS_MODE
        )

        if mode == ACCEPTANCE_PATHS_MODE:
            assert any(error.endswith(f"{code_message} {SCENARIO_SUFFIX}") for error in errors)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_duplicate_scenario_ids_are_refused_in_the_new_mode_only(tmp_path: Path) -> None:
    duplicate = [{"id": "S1", "title": "One"}, {"id": "S1", "title": "Two"}]
    results: dict[str, list[str]] = {}
    for mode in STRS_TEST_COVERAGE_MODES:
        root = make_scanned_bundle(tmp_path / mode.replace("-", "_"), mode)
        stunter = create_requirement(
            root,
            "StRS",
            "Export",
            "The tool SHALL export a report.",
            project="demo",
            scope="default",
            origin="native",
            user_need="Users need reports.",
        )
        set_frontmatter(stunter, scenarios=duplicate)
        results[mode] = findings_of(root)[0]

    assert not any("ids must be unique" in error for error in results["linked-swrs"])
    assert not any(
        "ids must be unique" in error for error in results["linked-swrs-and-validation-test"]
    )
    assert any(
        error.endswith(f"scenarios: ids must be unique {SCENARIO_SUFFIX}")
        for error in results[ACCEPTANCE_PATHS_MODE]
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_update_coverage_preserves_the_scenarios_block_byte_for_byte(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path, paths=3, transitions=2)
    stunter, software = bundle["stunter"], bundle["software"]
    before = {
        path: _scenarios_block(path.read_text(encoding="utf-8")) for path in (stunter, software)
    }
    write_test_file(
        bundle["root"],
        "test_paths.py",
        [f"# @tests_req {stunter.stem}#S1", f"# @accepts_req {stunter.stem}#S1"],
    )
    update_coverage(bundle["root"])

    for path, block in before.items():
        assert _scenarios_block(path.read_text(encoding="utf-8")).rstrip("\n") == (
            block.rstrip("\n")
        )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_accepts_on_a_swrs_is_refused_with_the_schema_description(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    software = bundle["software"]
    write_test_file(bundle["root"], "test_paths.py", [f"# @accepts_req {software.stem}#S1"])
    errors, _ = findings_of(bundle["root"])

    assert errors == [
        f"tests/test_paths.py:1: @accepts_req {software.stem}: Never present. @accepts_req "
        f"names a StRS main path; mark a SwRS test with @tests_req <SwRS-ID>#S<n>."
    ]
    # It counts toward nothing.
    assert requirement_of(bundle["root"], software.stem)["tests"]["status"] == "missing"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
@pytest.mark.parametrize("drop", [True, False], ids=["not-declared", "not-refusing"])
def test_a_weak_swrs_schema_fails_validation(tmp_path: Path, drop: bool) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    add_requirements(root)
    schema = tiers_path(root) / "_schema" / "swrs.schema.yaml"
    assert weaken_swrs_schema(schema, drop=drop) is True
    errors, _ = findings_of(root)

    named = [error for error in errors if "accepted_in_files is not refused" in error]
    assert len(named) == 1
    assert named[0].startswith(f"{tiers_path(root) / '_schema' / 'swrs.schema.yaml'}: ")
    assert f"mode {ACCEPTANCE_PATHS_MODE} needs the okf-schema 0.18.0 declaration" in named[0]
    assert "accepted_in_files:\n    type: array\n    maxItems: 0" in named[0]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
@pytest.mark.parametrize("mode", ["linked-swrs", "linked-swrs-and-validation-test"])
def test_a_weak_swrs_schema_passes_in_the_old_modes(tmp_path: Path, mode: str) -> None:
    root = make_scanned_bundle(tmp_path, mode)
    add_requirements(root)
    assert weaken_swrs_schema(tiers_path(root) / "_schema" / "swrs.schema.yaml")
    errors, _ = findings_of(root)

    assert not any("accepted_in_files" in error for error in errors)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
@pytest.mark.parametrize(
    "mode",
    ["linked-swrs", "linked-swrs-and-validation-test", ACCEPTANCE_PATHS_MODE],
)
def test_every_mode_reports_format_version_two(tmp_path: Path, mode: str) -> None:
    bundle = make_acceptance_bundle(tmp_path, mode)
    data = report(bundle["root"])

    assert data["format_version"] == 2
    assert data["report_format"] == "okfreq-requirements-report"
    Draft202012Validator(report_schema()).validate(data)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_the_new_report_fields_appear_only_in_the_new_mode(tmp_path: Path) -> None:
    old = report(make_acceptance_bundle(tmp_path / "old", "linked-swrs")["root"])
    new = report(make_acceptance_bundle(tmp_path / "new", ACCEPTANCE_PATHS_MODE)["root"])

    assert sorted(old["stakeholder_test_coverage"]) == [
        "coverage_percent",
        "covered",
        "mode",
        "requirements",
    ]
    assert "paths" in new["stakeholder_test_coverage"]
    assert new["coverage_definition"]["tests"] == (
        "every declared transition has a test marker with its fragment, or at least one "
        "test marker when none is declared"
    )
    assert old["coverage_definition"]["tests"] == (
        "at least one @tests_req marker for each SwRS coverage target"
    )
    assert (
        new["coverage_definition"]["stakeholder_tests"]
        == (STRS_TEST_COVERAGE_DESCRIPTIONS[ACCEPTANCE_PATHS_MODE])
    )
    assert (
        old["legacy"]["marker_coverage"]["validation_tests"]
        == (old["marker_coverage"]["validation_tests"])
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_a_statement_reports_acceptance_as_its_validation_tests(tmp_path: Path) -> None:
    bundle = make_acceptance_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    stunter = bundle["stunter"].stem
    stakeholder = stakeholder_of(bundle["root"], stunter)
    record = next(item for item in report(bundle["root"])["requirements"] if item["id"] == stunter)

    assert stakeholder["validation_tests"] == stakeholder["acceptance_tests"]
    assert stakeholder["tests"]["files"] == ["tests/test_flow.py"]
    # The record's own `tests` follow the acceptance side's files (Q62), while its
    # status is the statement's own covered/missing status.
    assert record["tests"]["files"] == stakeholder["validation_tests"]["files"]
    assert record["tests"]["count"] == stakeholder["validation_tests"]["count"]
    assert record["tests"]["status"] == stakeholder["status"]
    assert record["stakeholder_test_coverage"]["tests"] == stakeholder["tests"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_rejected_markers_stay_out_of_every_coverage_section(tmp_path: Path) -> None:
    bundle = make_acceptance_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    root = bundle["root"]
    software = bundle["software"].stem
    data = report(root)
    record = next(item for item in data["requirements"] if item["id"] == software)

    # The SwRS carries a fragmentless @tests_req and one with an undeclared fragment.
    assert record["tests"]["files"] == []
    assert record["transitions"] == {"tested": [], "missing": ["S1", "S2"]}
    assert data["totals"]["tested"] == 0
    assert software in data["marker_coverage"]["missing_tests"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_a_partly_marked_swrs_counts_as_a_link_but_not_as_covered(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path)
    root = bundle["root"]
    software = bundle["software"]
    write_test_file(root, "test_half.py", [f"# @tests_req {software.stem}#S1"])
    data = report(root)
    record = next(item for item in data["requirements"] if item["id"] == software.stem)

    # One link is counted, but a half-marked SwRS stays a missing coverage target.
    assert data["marker_coverage"]["tested"] == 1
    assert software.stem in data["marker_coverage"]["missing_tests"]
    assert data["totals"]["tested"] == 0
    assert record["transitions"] == {"tested": ["S1"], "missing": ["S2"]}
    assert record["tests"]["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_the_old_modes_keep_their_link_counting(tmp_path: Path) -> None:
    bundle = transitions_bundle(tmp_path, mode="linked-swrs")
    root = bundle["root"]
    software = bundle["software"]
    write_test_file(root, "test_half.py", [f"# @tests_req {software.stem}"])
    data = report(root)

    assert data["totals"]["tested"] == 1
    assert data["marker_coverage"]["tested"] == 1
    assert data["marker_coverage"]["missing_tests"] == []
    records = {item["id"]: item for item in data["requirements"]}
    assert "transitions" not in records[software.stem]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_the_markdown_report_carries_the_path_columns(tmp_path: Path) -> None:
    bundle = make_acceptance_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    destination = tmp_path / "report.md"
    write_markdown_report(bundle["root"], destination)
    text = destination.read_text(encoding="utf-8")

    assert "| Scope | Tier | ID | Name | Tests | Tested | Accepted |" in text
    assert "| Scope | Tier | ID | Name | Source | Tests | Missing transitions |" in text
    assert "- StRS paths: tested 1/2, accepted 1/2" in text
    assert "| default | StRS | StRS-default-001 | Export | ❌ missing | 1/2 | 1/2 |" in text
    # A StRS without `scenarios:` shows whether its fragmentless marker counts.
    assert (
        "| default | StRS | StRS-default-002 | Import | ❌ missing | ✅ no paths |"
        " ❌ no paths |" in text
    )
    assert (
        "| default | StRS | StRS-default-003 | Archive | ❌ missing | ❌ no paths |"
        " ✅ no paths |" in text
    )
    assert (
        "| default | SwRS | SwRS-default-001 | Write | ✅ covered | ❌ missing | S1, S2 |" in text
    )
    description = STRS_TEST_COVERAGE_DESCRIPTIONS[ACCEPTANCE_PATHS_MODE]
    note = f"*Note: current configuration is that {description[0].lower()}{description[1:]}*"
    assert note in text


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_the_old_markdown_report_has_no_path_columns(tmp_path: Path) -> None:
    bundle = make_acceptance_bundle(tmp_path, "linked-swrs")
    destination = tmp_path / "report.md"
    write_markdown_report(bundle["root"], destination)
    text = destination.read_text(encoding="utf-8")

    assert "Tested |" not in text
    assert "Missing transitions" not in text
    assert "StRS paths" not in text
    assert "| default | StRS | StRS-default-001 | Export | ✅ covered |" in text


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_a_waived_statement_reports_its_reason_and_an_exempt_cell(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=2)
    root = bundle["root"]
    stunter = bundle["stunter"]
    write_test_file(
        root,
        "test_paths.py",
        [
            f"# @tests_req {bundle['software'].stem}#S1",
            f"# @tests_req {bundle['software'].stem}#S2",
        ],
    )
    set_frontmatter(
        stunter,
        acceptance_exemption=True,
        acceptance_exemption_reason="Judged by inspection; no automated run exists.",
    )
    data = report(root)
    stakeholder = stakeholder_of(root, stunter.stem)
    destination = tmp_path / "report.md"
    write_markdown_report(root, destination)

    assert stakeholder["acceptance_exemption"] == {
        "reason": "Judged by inspection; no automated run exists."
    }
    assert stakeholder["accepted"] is False
    assert stakeholder["status"] == "covered"
    assert stakeholder["paths"] == {"total": 2, "tested": 0, "accepted": 0}
    waived_row = "| default | StRS | StRS-default-001 | Export | ✅ covered | 0/2 | exempt |"
    assert waived_row in destination.read_text(encoding="utf-8")
    Draft202012Validator(report_schema()).validate(data)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_an_individually_exempt_swrs_reports_as_exempt(tmp_path: Path) -> None:
    bundle = make_paths_bundle(tmp_path, paths=1)
    root = bundle["root"]
    stunter = bundle["stunter"]
    software = bundle["software"]
    set_frontmatter(software, annotation_exemption=True, exemption_reason="Consolidated.")
    write_test_file(root, "test_paths.py", [f"# @accepts_req {stunter.stem}#S1"])
    data = report(root)

    assert stakeholder_of(root, stunter.stem)["linked_swrs"] == [
        {"id": software.stem, "status": "exempt"}
    ]
    assert software.stem not in data["marker_coverage"]["missing_tests"]
    assert data["marker_coverage"]["exemptions"] == [
        {"id": software.stem, "reason": "Consolidated."}
    ]
    assert stakeholder_of(root, stunter.stem)["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_a_new_swrs_pre_fills_its_scenarios_from_its_headings(tmp_path: Path) -> None:
    root = make_scanned_bundle(tmp_path, ACCEPTANCE_PATHS_MODE)
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    stunter = create_requirement(
        root, "StRS", "Export", "The tool SHALL export.", user_need="Users need reports.", **common
    )
    software = create_requirement(
        root, "SwRS", "Write", "The tool SHALL write.", derives_from=[stunter.stem], **common
    )
    body = software.read_text(encoding="utf-8")

    assert frontmatter_of(software)["scenarios"] == [
        {"id": "S1", "title": "<nominal behavior>"},
        {"id": "S2", "title": "<boundary or failure behavior>"},
    ]
    assert "### Scenario S1: <nominal behavior>" in body
    assert "### Scenario S2: <boundary or failure behavior>" in body
    assert frontmatter_of(stunter)["scenarios"] == [{"id": "S1", "title": "<main path title>"}]
    assert "### Main paths" in stunter.read_text(encoding="utf-8")
    assert "#### Path S1: <main path title>" in stunter.read_text(encoding="utf-8")
    errors, advisories = findings_of(root)
    # The scaffold is valid; W004 is the expected reminder that no test accepts it yet.
    assert errors == []
    assert [advisory.split(" ")[0] for advisory in advisories] == ["W004"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
@pytest.mark.parametrize("mode", ["linked-swrs", "linked-swrs-and-validation-test"])
def test_the_old_modes_pre_fill_nothing(tmp_path: Path, mode: str) -> None:
    root = make_scanned_bundle(tmp_path, mode)
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    stunter = create_requirement(
        root, "StRS", "Export", "The tool SHALL export.", user_need="Users need reports.", **common
    )
    software = create_requirement(
        root, "SwRS", "Write", "The tool SHALL write.", derives_from=[stunter.stem], **common
    )
    st_body = extract_frontmatter(stunter.read_text(encoding="utf-8"))[1]
    sw_body = extract_frontmatter(software.read_text(encoding="utf-8"))[1]

    assert "scenarios" not in frontmatter_of(stunter)
    assert "scenarios" not in frontmatter_of(software)
    assert st_body.lstrip("\n") == ears_body(
        "StRS", "The tool SHALL export.", title="Export", user_need="Users need reports."
    )
    assert "### Main paths" not in st_body
    assert "### Scenario: <nominal behavior>" in sw_body


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_the_new_scaffold_differs_from_the_old_one_only_by_the_paths(tmp_path: Path) -> None:
    old = ears_body("StRS", "The tool SHALL export.", title="Export")
    new = ears_body("StRS", "The tool SHALL export.", title="Export", acceptance_paths=True)
    old_swrs = ears_body("SwRS", "The tool SHALL write.", title="Write")
    new_swrs = ears_body("SwRS", "The tool SHALL write.", title="Write", acceptance_paths=True)

    assert new == old.replace(
        "### Preserved stakeholder intent",
        "### Main paths\n\n#### Path S1: <main path title>\n\n"
        "1. <first step the stakeholder observes>\n"
        "2. <next step, up to the observable outcome>\n\n"
        "### Preserved stakeholder intent",
    )
    assert new_swrs == old_swrs.replace(
        "### Scenario: <nominal behavior>", "### Scenario S1: <nominal behavior>"
    ).replace(
        "### Scenario: <boundary or failure behavior>",
        "### Scenario S2: <boundary or failure behavior>",
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
@pytest.mark.parametrize(
    "mode", ["linked-swrs", "linked-swrs-and-validation-test", ACCEPTANCE_PATHS_MODE]
)
def test_retire_refuses_a_draft_named_only_by_an_acceptance_marker(
    tmp_path: Path, mode: str
) -> None:
    root = make_scanned_bundle(tmp_path, mode)
    stunter = create_requirement(
        root,
        "StRS",
        "Export",
        "The tool SHALL export.",
        user_need="Users need reports.",
        project="demo",
        scope="default",
        origin="native",
    )
    write_test_file(root, "test_accepts.py", [f"# @accepts_req {stunter.stem}"])
    before = stunter.read_text(encoding="utf-8")

    with pytest.raises(RequirementError) as caught:
        retire_requirement(root, stunter.stem, reason="nothing uses it")

    assert "referenced by markers in tests/test_accepts.py" in str(caught.value)
    assert stunter.read_text(encoding="utf-8") == before
    assert [path.name for path in stunter.parent.iterdir()] == [stunter.name]


def _d1(tmp_path: Path) -> None:
    """D1: the shipped default ignores every acceptance suffix and marker."""
    bundle = make_acceptance_bundle(tmp_path / "d1", "linked-swrs")
    root = bundle["root"]
    errors, advisories = findings_of(root)
    assert (errors, advisories) == ([], [])
    data = report(root)
    assert data["format_version"] == 2
    assert "paths" not in data["stakeholder_test_coverage"]

    # The same bundle without the suffixes and the @accepts_req lines covers the same.
    plain = make_acceptance_bundle(tmp_path / "plain", "linked-swrs")
    stunter, silent, software = (plain[key].stem for key in ("stunter", "silent", "software"))
    write_test_file(
        plain["root"],
        "test_flow.py",
        [
            f"# @tests_req {stunter}",
            f"# @tests_req {stunter}",
            f"# @tests_req {silent}",
            f"# @tests_req {software}",
            f"# @tests_req {software}",
        ],
    )
    clean = report(plain["root"])
    for section in ("totals", "stakeholder_test_coverage", "scopes"):
        assert data[section] == clean[section]
    assert data["marker_coverage"]["tested"] == clean["marker_coverage"]["tested"]
    assert data["marker_coverage"]["missing_tests"] == clean["marker_coverage"]["missing_tests"]
    # The acceptance marker is scanned, yet it decides nothing in this mode.
    assert marker_scan(root)["accepted"]
    assert stakeholder_of(root, bundle["draft"].stem)["status"] == "missing"

    set_frontmatter(bundle["stunter"], tested_in_files=["hand.py"], accepted_in_files=["hand.py"])
    update_coverage(root)
    assert "tested_in_files" not in frontmatter_of(bundle["stunter"])
    assert "accepted_in_files" not in frontmatter_of(bundle["stunter"])


def _d2(tmp_path: Path) -> None:
    """D2: the validation-test mode reads suffixes as decoration and stays as today."""
    bundle = make_acceptance_bundle(tmp_path / "d2", "linked-swrs-and-validation-test")
    root = bundle["root"]
    errors, advisories = findings_of(root)
    assert (errors, advisories) == ([], [])
    scan = marker_scan(root)
    data = report(root)
    assert "paths" not in data["stakeholder_test_coverage"]
    assert scan["validation_tests"] == {
        bundle["stunter"].stem: ["tests/test_flow.py", "tests/test_flow.py"],
        bundle["silent"].stem: ["tests/test_flow.py"],
    }
    # Both SwRS markers count as one link, the suffix included.
    assert scan["tested"] == {bundle["software"].stem: ["tests/test_flow.py"] * 2}
    assert data["totals"]["tested"] == 1
    assert data["totals"]["fully_traceable"] == 1
    assert data["stakeholder_test_coverage"] == {
        "mode": "linked-swrs-and-validation-test",
        "requirements": 3,
        "covered": 1,
        "coverage_percent": 33.33,
    }


def _d3(tmp_path: Path) -> None:
    """D3: the new mode refuses the fixture's markers and reports its paths."""
    bundle = make_acceptance_bundle(tmp_path / "d3", ACCEPTANCE_PATHS_MODE)
    root = bundle["root"]
    stunter, silent, draft = bundle["stunter"].stem, bundle["silent"].stem, bundle["draft"].stem
    errors, advisories = findings_of(root)
    assert [error.split(":")[1] for error in errors] == ["3", "5", "6", "7"]
    assert f"@tests_req {stunter} has no scenario fragment" in errors[0]
    assert f"@tests_req {bundle['software'].stem} has no scenario fragment" in errors[1]
    assert f"@tests_req {bundle['software'].stem}#S9 names no declared scenario" in errors[2]
    assert errors[3].endswith(
        "Never present. @accepts_req names a StRS main path; mark a SwRS test with "
        "@tests_req <SwRS-ID>#S<n>."
    )
    assert sorted(advisory.split(" ")[0] for advisory in advisories) == ["W003", "W003", "W004"]
    named = [
        advisory.split(" ")[1].rsplit("/", 1)[-1].removesuffix(".md:") for advisory in advisories
    ]
    assert sorted(named) == sorted([silent, silent, draft])

    assert stakeholder_of(root, stunter)["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    silent_coverage = stakeholder_of(root, silent)
    assert (silent_coverage["tested"], silent_coverage["accepted"]) == (True, False)
    assert stakeholder_of(root, draft)["accepted"] is True
    data = report(root)
    record = next(item for item in data["requirements"] if item["id"] == bundle["software"].stem)
    assert record["transitions"] == {"tested": [], "missing": ["S1", "S2"]}

    update_coverage(root)
    assert frontmatter_of(bundle["stunter"])["tested_in_files"] == ["tests/test_flow.py"]
    assert frontmatter_of(bundle["stunter"])["accepted_in_files"] == ["tests/test_flow.py"]

    destination = tmp_path / "report.md"
    write_markdown_report(root, destination)
    text = destination.read_text(encoding="utf-8")
    assert f"| default | StRS | {stunter} | Export | ❌ missing | 1/2 | 1/2 |" in text
    # StRS-B is tested by its fragmentless @tests_req, and is not accepted.
    silent_row = f"| default | StRS | {silent} | Import | ❌ missing | ✅ no paths | ❌ no paths |"
    assert silent_row in text


def _d5(tmp_path: Path) -> None:
    """D5: a config.yml written before this change keeps the default keyword."""
    bundle = make_acceptance_bundle(tmp_path / "d5", ACCEPTANCE_PATHS_MODE)
    root = bundle["root"]
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    config.write_text(
        text.replace("  accepts: '@accepts_req'\n", "").replace(
            "tested_in_files,\n  accepted_in_files,", "tested_in_files,"
        ),
        encoding="utf-8",
    )
    loaded = load_config(root)
    assert loaded["markers"]["accepts"] == "@accepts_req"
    assert "accepted_in_files" not in loaded["generated_fields"]

    errors, advisories = findings_of(root)
    assert [error.split(":")[1] for error in errors] == ["3", "5", "6", "7"]
    assert [advisory.split(" ")[0] for advisory in advisories] == ["W003", "W004", "W003"]
    assert stakeholder_of(root, bundle["stunter"].stem)["paths"] == {
        "total": 2,
        "tested": 1,
        "accepted": 1,
    }

    set_frontmatter(bundle["stunter"], accepted_in_files=["hand.py"])
    update_coverage(root)
    # Not a configured generated field: the hand-placed value stays, none is added.
    assert frontmatter_of(bundle["stunter"])["accepted_in_files"] == ["hand.py"]
    assert frontmatter_of(bundle["stunter"])["tested_in_files"] == ["tests/test_flow.py"]
    assert frontmatter_of(bundle["silent"]).get("accepted_in_files") in (None, [])
    assert frontmatter_of(bundle["silent"])["tested_in_files"] == ["tests/test_flow.py"]


def _d7(tmp_path: Path) -> None:
    """D7: an unsupported mode is refused, naming the three supported ones."""
    root = make_scanned_bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs", "strs_test_coverage_mode: unsupported"
        ),
        encoding="utf-8",
    )

    with pytest.raises(RequirementError) as caught:
        load_config(root)

    message = str(caught.value)
    assert "unsupported strs_test_coverage_mode: unsupported" in message
    for mode in STRS_TEST_COVERAGE_MODES:
        assert mode in message


def _d8(tmp_path: Path) -> None:
    """D8: a justified whole-StRS waiver covers a statement with an unaccepted path."""
    bundle = make_acceptance_bundle(tmp_path / "d8", ACCEPTANCE_PATHS_MODE)
    root = bundle["root"]
    stunter, software = bundle["stunter"], bundle["software"]
    write_test_file(
        root,
        "test_flow.py",
        [
            f"# @accepts_req {stunter.stem}#S1",
            f"# @tests_req {stunter.stem}#S2",
            f"# @tests_req {software.stem}#S1",
            f"# @tests_req {software.stem}#S2",
            f"# @accepts_req {bundle['draft'].stem}",
        ],
    )
    set_frontmatter(
        stunter,
        acceptance_exemption=True,
        acceptance_exemption_reason="Walked by hand with the product owner.",
    )
    errors, advisories = findings_of(root)
    assert errors == []
    assert [advisory.split(" ")[0] for advisory in advisories] == ["W003", "W004", "W003"]

    coverage = stakeholder_of(root, stunter.stem)
    assert coverage["status"] == "covered"
    assert coverage["accepted"] is False
    assert coverage["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert coverage["acceptance_exemption"] == {"reason": "Walked by hand with the product owner."}

    destination = tmp_path / "report.md"
    write_markdown_report(root, destination)
    assert f"| default | StRS | {stunter.stem} | Export | ✅ covered | 1/2 | exempt |" in (
        destination.read_text(encoding="utf-8")
    )
    Draft202012Validator(report_schema()).validate(report(root))

    # With no acceptance marker naming it at all, the waiver still suppresses W004
    # and its coverage stays what its paths say.
    write_test_file(
        root,
        "test_flow.py",
        [
            f"# @tests_req {stunter.stem}#S2",
            f"# @tests_req {software.stem}#S1",
            f"# @tests_req {software.stem}#S2",
        ],
    )
    errors, advisories = findings_of(root)
    assert errors == []
    assert [advisory.split(" ")[0] for advisory in advisories] == ["W003", "W004", "W003", "W004"]
    still = stakeholder_of(root, stunter.stem)
    assert (still["status"], still["accepted"]) == ("covered", False)
    assert still["paths"] == {"total": 2, "tested": 1, "accepted": 0}


def _d9(tmp_path: Path) -> None:
    """D9: the linked-SwRS condition still decides, waived StRS or not."""
    bundle = make_acceptance_bundle(tmp_path / "d9", ACCEPTANCE_PATHS_MODE)
    root = bundle["root"]
    stunter, software = bundle["stunter"], bundle["software"]
    write_test_file(root, "test_flow.py", [f"# @tests_req {software.stem}#S1"])
    set_frontmatter(
        stunter, acceptance_exemption=True, acceptance_exemption_reason="Judged by hand."
    )

    assert stakeholder_of(root, stunter.stem)["status"] == "missing"
    set_frontmatter(software, annotation_exemption=True, exemption_reason="Consolidated.")
    coverage = stakeholder_of(root, stunter.stem)
    assert coverage["linked_swrs"] == [{"id": software.stem, "status": "exempt"}]
    assert coverage["status"] == "covered"

    # A blank or absent reason is reported as an error and no longer satisfies the
    # linked-SwRS condition, so the statement is missing again.
    set_frontmatter(software, exemption_reason="")
    errors, _ = findings_of(root)
    assert len(errors) == 1
    assert errors[0].endswith("annotation exemption requires exemption_reason")
    assert stakeholder_of(root, stunter.stem)["status"] == "missing"
    set_frontmatter(software, drop=("exemption_reason",))
    assert len(findings_of(root)[0]) == 1
    assert stakeholder_of(root, stunter.stem)["status"] == "missing"
    # A statement with no linked SwRS stays missing whatever its own waiver says.
    assert stakeholder_of(root, bundle["draft"].stem)["status"] == "missing"


D_MATRIX: dict[str, Any] = {
    "D1": _d1,
    "D2": _d2,
    "D3": _d3,
    "D5": _d5,
    "D7": _d7,
    "D8": _d8,
    "D9": _d9,
}


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
@pytest.mark.parametrize("cell", sorted(D_MATRIX))
def test_the_default_and_configured_value_matrix(tmp_path: Path, cell: str) -> None:
    D_MATRIX[cell](tmp_path)
