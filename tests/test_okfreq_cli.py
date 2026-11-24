"""Tests for the standalone okfreq skill-installation command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import create_requirement, init_requirements, tiers_path
from okf_schema.skill_installer import SKILL_FAMILIES


def test_install_skills_help_matches_shared_destination_contract() -> None:
    """okfreq install-skills exposes the common destination selectors."""
    runner = CliRunner()
    result = runner.invoke(okfreq, ["install-skills", "--help"])

    assert result.exit_code == 0
    assert "DESTINATION" in result.output
    for option in ("--agent-copilot", "--local-copilot", "--local-agents"):
        assert option in result.output
    assert "--force" not in result.output


def test_install_skills_installs_only_requirements_family(tmp_path: Path) -> None:
    """okfreq install-skills installs the base and companion requirements skills."""
    runner = CliRunner()
    destination = tmp_path / "skills"

    result = runner.invoke(okfreq, ["install-skills", str(destination)])

    assert result.exit_code == 0, result.output
    assert result.output.startswith(f"Destination: {destination.resolve()}\n")
    assert [line.split(": ")[-1] for line in result.output.splitlines()[1:]] == list(
        SKILL_FAMILIES["okfreq"]
    )
    for skill in SKILL_FAMILIES["okfreq"]:
        assert (destination / skill / "SKILL.md").is_file()
    assert not (destination / "okfkb" / "SKILL.md").exists()


def test_install_skills_local_copilot_selector_resolves_from_working_directory(
    tmp_path: Path,
) -> None:
    """The local Copilot selector uses the command working directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as working_directory:
        result = runner.invoke(okfreq, ["install-skills", "--local-copilot"])

    assert result.exit_code == 0, result.output
    assert (Path(working_directory) / ".github" / "skills" / "okfreq" / "SKILL.md").is_file()


def test_install_skills_relative_destination_resolves_from_working_directory(
    tmp_path: Path,
) -> None:
    """An explicit relative destination is resolved from the command directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as working_directory:
        result = runner.invoke(okfreq, ["install-skills", "vendor/skills"])

    destination = Path(working_directory) / "vendor" / "skills"
    assert result.exit_code == 0, result.output
    assert f"Destination: {destination}" in result.output
    assert (destination / "okfreq" / "SKILL.md").is_file()


def test_install_skills_agent_copilot_selector_matches_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The explicit global selector targets the same location as the default."""
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    runner = CliRunner()

    result = runner.invoke(okfreq, ["install-skills", "--agent-copilot"])

    destination = home / ".copilot" / "skills"
    assert result.exit_code == 0, result.output
    assert (destination / "okfreq" / "SKILL.md").is_file()


# Default and configured-value matrix (D1-D7) of mode linked-swrs-and-acceptance-paths.
# Marker lines are built at run time so this file carries no marker for these fixtures.

ACCEPTANCE_MODE = "linked-swrs-and-acceptance-paths"
STRS_A, STRS_B, STRS_C = "StRS-default-001", "StRS-default-002", "StRS-default-003"
SWRS_A = "SwRS-default-001"
MATRIX_MARKERS = (
    ("accepts", f"{STRS_A}#S1"),
    ("tests", f"{STRS_A}#S2"),
    ("tests", STRS_A),
    ("tests", STRS_B),
    ("tests", SWRS_A),
    ("tests", f"{SWRS_A}#S9"),
    ("accepts", SWRS_A),
    ("accepts", STRS_C),
)


def _edit_config(root: Path, old: str, new: str) -> None:
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    assert old in text
    config.write_text(text.replace(old, new), encoding="utf-8")


def _set_frontmatter(file: Path, **updates: object) -> None:
    frontmatter, body = extract_frontmatter(file.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    data.update(updates)
    file.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def _frontmatter(file: Path) -> dict:
    frontmatter, _ = extract_frontmatter(file.read_text(encoding="utf-8"))
    assert frontmatter is not None
    return dict(make_yaml().load(frontmatter))


def matrix_project(
    tmp_path: Path,
    mode: str = "linked-swrs",
    tests: str = "@tests_req",
    accepts: str = "@accepts_req",
) -> Path:
    """Build the shared fixture of the matrix in a fresh okfreq init and return the bundle."""
    root = init_requirements(tmp_path)
    assert isinstance(root, Path)
    common = {"project": "demo", "scope": "default", "origin": "native"}
    strs_a = create_requirement(root, "StRS", "Export", "Users SHALL export.", **common)
    create_requirement(root, "StRS", "Import", "Users SHALL import.", **common)
    create_requirement(root, "StRS", "Share", "Users SHALL share.", **common)
    swrs_a = create_requirement(
        root, "SwRS", "Write", "The tool SHALL write.", derives_from=[STRS_A], **common
    )
    text = strs_a.read_text(encoding="utf-8")
    strs_a.write_text(
        text.replace(
            "### Preserved stakeholder intent",
            "### Main paths\n\n#### Path 1: Export a report\n\n#### Path 2: The disk is full\n\n"
            "### Preserved stakeholder intent",
        ),
        encoding="utf-8",
    )
    paths = [{"id": "S1", "title": "Export a report"}, {"id": "S2", "title": "The disk is full"}]
    _set_frontmatter(strs_a, scenarios=paths)
    _set_frontmatter(
        swrs_a, scenarios=[{"id": "S1", "title": "Write"}, {"id": "S2", "title": "Fail"}]
    )
    keywords = {"tests": tests, "accepts": accepts}
    project = tmp_path
    (project / "src").mkdir()
    (project / "src" / "write.py").write_text(f"\n# @implements_req {SWRS_A}\n", encoding="utf-8")
    (project / "tests").mkdir()
    (project / "tests" / "test_matrix.py").write_text(
        "\n" + "".join(f"# {keywords[kind]} {target}\n" for kind, target in MATRIX_MARKERS),
        encoding="utf-8",
    )
    _edit_config(root, "  tests: '@tests_req'", f"  tests: '{tests}'")
    _edit_config(root, "  accepts: '@accepts_req'", f"  accepts: '{accepts}'")
    _edit_config(root, "strs_test_coverage_mode: linked-swrs", f"strs_test_coverage_mode: {mode}")
    return root


def run(*args: str) -> tuple[int, str]:
    result = CliRunner().invoke(okfreq, list(args))
    return result.exit_code, result.output


def validation(root: Path) -> tuple[int, dict]:
    exit_code, output = run("validate", str(root), "--json")
    return exit_code, json.loads(output)


def report_of(root: Path, tmp_path: Path) -> tuple[dict, str]:
    destination = tmp_path / "out"
    exit_code, output = run(
        "generate-report",
        str(root),
        "--output-json",
        str(destination / "report.json"),
        "--output-summary-md",
        str(destination / "report.md"),
    )
    assert exit_code == 0, output
    return (
        json.loads((destination / "report.json").read_text(encoding="utf-8")),
        (destination / "report.md").read_text(encoding="utf-8"),
    )


def records(data: dict) -> dict[str, dict]:
    return {item["id"]: item for item in data["requirements"]}


def warning_ids(findings: list[str], code: str) -> list[str]:
    return sorted(
        identifier
        for finding in findings
        if finding.startswith(f"{code} ")
        for identifier in (STRS_A, STRS_B, STRS_C)
        if f"{identifier} declares" in finding or f"{identifier} has" in finding
    )


@Parametrization.autodetect_parameters()
@Parametrization.case(name="d1_linked_swrs", mode="linked-swrs")
@Parametrization.case(name="d2_validation_test", mode="linked-swrs-and-validation-test")
def test_old_modes_only_show_the_every_mode_changes(tmp_path: Path, mode: str) -> None:
    root = matrix_project(tmp_path, mode)
    strs_a = tiers_path(root) / "strs" / f"{STRS_A}.md"
    _set_frontmatter(strs_a, tested_in_files=["tests/a.py"], accepted_in_files=["tests/b.py"])

    exit_code, result = validation(root)
    assert (exit_code, result["errors"]) == (0, [])
    assert not [item for item in result["warnings"] if item.startswith(("W003", "W004"))]

    exit_code, output = run("trace", str(root))
    assert exit_code == 0
    assert "accepted: 3" in output
    trace = json.loads(run("trace", str(root), "--json")[1])
    assert set(trace["accepted"]) == {STRS_A, SWRS_A, STRS_C}
    assert len(trace["scenario_markers"]) == 8

    assert run("update-coverage", str(root))[0] == 0
    assert "tested_in_files" not in _frontmatter(strs_a)
    assert "accepted_in_files" not in _frontmatter(strs_a)

    data, markdown = report_of(root, tmp_path)
    assert data["format_version"] == 2
    assert "paths" not in data["stakeholder_test_coverage"]
    assert "transitions" not in records(data)[SWRS_A]
    assert records(data)[SWRS_A]["tests"]["status"] == "covered"
    assert "StRS paths" not in markdown
    stakeholder = records(data)[STRS_A]["stakeholder_test_coverage"]
    assert "paths" not in stakeholder
    if mode == "linked-swrs-and-validation-test":
        assert stakeholder["validation_tests"]["files"] == ["tests/test_matrix.py"]
        b_coverage = records(data)[STRS_B]["stakeholder_test_coverage"]
        assert b_coverage["validation_tests"]["files"] == ["tests/test_matrix.py"]
        assert records(data)[STRS_C]["stakeholder_test_coverage"]["validation_tests"]["count"] == 0

    exit_code, output = run("retire", STRS_C, "--path", str(root), "--yes")
    assert exit_code != 0
    assert "tests/test_matrix.py" in output
    assert (tiers_path(root) / "strs" / f"{STRS_C}.md").exists()


@Parametrization.autodetect_parameters()
@Parametrization.case(name="d3_default_markers", tests="@tests_req", accepts="@accepts_req")
@Parametrization.case(name="d4_custom_markers", tests="@verifies", accepts="@accepts")
def test_acceptance_mode_matrix(tmp_path: Path, tests: str, accepts: str) -> None:
    root = matrix_project(tmp_path, ACCEPTANCE_MODE, tests, accepts)
    file = "tests/test_matrix.py"

    exit_code, result = validation(root)

    assert exit_code == 1
    assert sorted(result["errors"]) == sorted(
        [
            f"{file}:4: {tests} {STRS_A} has no scenario fragment; {STRS_A} declares scenarios "
            f"S1, S2: write {tests} {STRS_A}#S<n> (this marker does not count)",
            f"{file}:6: {tests} {SWRS_A} has no scenario fragment; {SWRS_A} declares scenarios "
            f"S1, S2: write {tests} {SWRS_A}#S<n> (this marker does not count)",
            f"{file}:7: {tests} {SWRS_A}#S9 names no declared scenario of {SWRS_A} "
            "(declared: S1, S2)",
            f"{file}:8: {accepts} {SWRS_A}: Never present. @accepts_req names a StRS main path; "
            "mark a SwRS test with @tests_req <SwRS-ID>#S<n>.",
        ]
    )
    assert warning_ids(result["warnings"], "W003") == [STRS_B, STRS_C]
    assert warning_ids(result["warnings"], "W004") == [STRS_B]
    exit_code, output = run("lint", str(root))
    assert exit_code != 0
    assert "has no scenario fragment" in output

    data, markdown = report_of(root, tmp_path)
    coverage = records(data)
    stakeholder = coverage[STRS_A]["stakeholder_test_coverage"]
    assert stakeholder["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert stakeholder["validation_tests"] == stakeholder["acceptance_tests"]
    b_coverage = coverage[STRS_B]["stakeholder_test_coverage"]
    assert (b_coverage["tested"], b_coverage["accepted"]) == (True, False)
    assert coverage[SWRS_A]["transitions"] == {"tested": [], "missing": ["S1", "S2"]}
    assert f"| {STRS_A} | Export | ❌ missing | 1/2 | 1/2 |" in markdown
    assert f"| {STRS_B} | Import | ❌ missing | ✅ no paths | ❌ no paths |" in markdown

    assert run("update-coverage", str(root))[0] == 0
    strs_a = _frontmatter(tiers_path(root) / "strs" / f"{STRS_A}.md")
    assert strs_a["tested_in_files"] == strs_a["accepted_in_files"] == [file]


def test_acceptance_mode_with_a_config_written_before_the_mode(tmp_path: Path) -> None:
    root = matrix_project(tmp_path, ACCEPTANCE_MODE)
    _edit_config(root, "  accepts: '@accepts_req'\n", "")
    _edit_config(root, "tested_in_files,\n  accepted_in_files,", "tested_in_files,\n ")
    strs_b = tiers_path(root) / "strs" / f"{STRS_B}.md"
    _set_frontmatter(strs_b, accepted_in_files=["tests/hand.py"])

    exit_code, result = validation(root)
    assert exit_code == 1
    assert len(result["errors"]) == 4
    assert run("update-coverage", str(root))[0] == 0

    assert "accepted_in_files" not in _frontmatter(tiers_path(root) / "strs" / f"{STRS_A}.md")
    assert _frontmatter(strs_b)["accepted_in_files"] == ["tests/hand.py"]
    assert _frontmatter(strs_b)["tested_in_files"] == ["tests/test_matrix.py"]


def test_acceptance_mode_with_a_swrs_schema_written_before_the_mode(tmp_path: Path) -> None:
    root = matrix_project(tmp_path, "linked-swrs")
    schema = tiers_path(root) / "_schema" / "swrs.schema.yaml"
    shipped = schema.read_text(encoding="utf-8")
    start = shipped.index("    accepted_in_files:")
    schema.write_text(shipped[:start] + shipped[shipped.index("  required:") :], encoding="utf-8")
    assert validation(root)[0] == 0

    _edit_config(
        root, "strs_test_coverage_mode: linked-swrs", f"strs_test_coverage_mode: {ACCEPTANCE_MODE}"
    )
    exit_code, result = validation(root)

    assert exit_code == 1
    (error,) = [item for item in result["errors"] if "accepted_in_files" in item]
    assert "swrs.schema.yaml: accepted_in_files is not refused" in error
    assert "maxItems: 0" in error
    assert not [item for item in result["errors"] if item.startswith("tests/test_matrix.py:8:")]

    schema.write_text(shipped, encoding="utf-8")
    assert len(validation(root)[1]["errors"]) == 4


def test_unsupported_mode_fails_validation(tmp_path: Path) -> None:
    root = matrix_project(tmp_path, "unsupported")

    exit_code, output = run("validate", str(root))

    assert exit_code != 0
    assert f"linked-swrs, linked-swrs-and-validation-test, {ACCEPTANCE_MODE}" in output


def test_new_prefills_scenarios_from_the_cli_in_the_acceptance_mode(tmp_path: Path) -> None:
    root = init_requirements(tmp_path)
    assert isinstance(root, Path)
    _edit_config(
        root, "strs_test_coverage_mode: linked-swrs", f"strs_test_coverage_mode: {ACCEPTANCE_MODE}"
    )
    common = ["--project", "demo", "--path", str(root)]

    exit_code, output = run(
        "new", "strs", "Export", "--description", "Users SHALL export.", *common
    )
    assert exit_code == 0, output
    exit_code, output = run(
        "new",
        "swrs",
        "Write",
        "--description",
        "The tool SHALL write.",
        "--derives-from",
        STRS_A,
        *common,
    )
    assert exit_code == 0, output

    strs = tiers_path(root) / "strs" / f"{STRS_A}.md"
    assert _frontmatter(strs)["scenarios"] == [{"id": "S1", "title": "<main path title>"}]
    assert "#### Path S1: <main path title>" in strs.read_text(encoding="utf-8")
    swrs = _frontmatter(tiers_path(root) / "swrs" / f"{SWRS_A}.md")
    assert [entry["id"] for entry in swrs["scenarios"]] == ["S1", "S2"]
