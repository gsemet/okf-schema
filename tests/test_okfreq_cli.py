"""Tests for the okfreq command line: skill installation and acceptance paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    ACCEPTANCE_PATHS_MODE,
    create_requirement,
    init_requirements,
    project_path,
)
from okf_schema.skill_installer import SKILL_FAMILIES


def frontmatter_of(path: Path) -> dict[str, Any]:
    """Return a requirement file's parsed frontmatter."""
    frontmatter, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data: dict[str, Any] = make_yaml().load(frontmatter)
    return data


def set_mode(root: Path, mode: str) -> None:
    """Select a stakeholder test-coverage mode in an initialized bundle."""
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    config.write_text(
        text.replace(
            "strs_test_coverage_mode: linked-swrs\n", f"strs_test_coverage_mode: {mode}\n"
        ),
        encoding="utf-8",
    )


def make_project(tmp_path: Path, mode: str = ACCEPTANCE_PATHS_MODE) -> dict[str, Any]:
    """Build an StRS with two main paths, its SwRS and their implementation."""
    root = init_requirements(tmp_path / "requirements")
    set_mode(root, mode)
    common: dict[str, Any] = {"project": "demo", "scope": "default", "origin": "native"}
    stunter = create_requirement(
        root, "StRS", "Export", "The tool SHALL export.", user_need="Users need reports.", **common
    )
    _declare(stunter, "S1", "S2")
    software = create_requirement(
        root, "SwRS", "Write", "The tool SHALL write.", derives_from=[stunter.stem], **common
    )
    _declare(software, "S1", "S2")
    tests = project_path(root) / "tests"
    tests.mkdir()
    (project_path(root) / "src").mkdir()
    (project_path(root) / "src" / "implementation.py").write_text(
        f"# @implements_req {software.stem}\n", encoding="utf-8"
    )
    return {"root": root, "stunter": stunter, "software": software, "tests": tests}


def _declare(path: Path, *ids: str) -> None:
    """Give a requirement the declared scenarios its tests fragment against."""
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    data["scenarios"] = [
        {"id": identifier, "title": f"Scenario {identifier}"} for identifier in ids
    ]
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def _undeclare(path: Path) -> None:
    """Drop a requirement's declared scenarios, as an unedited generator body does."""
    frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    data.pop("scenarios", None)
    path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def write_markers(project: dict[str, Any], name: str, markers: list[str]) -> Path:
    """Write a real test file whose marker comments a scanner reads."""
    target: Path = project["tests"] / name
    target.write_text("".join(f"{marker}\n" for marker in markers), encoding="utf-8")
    return target


def covering_markers(project: dict[str, Any]) -> list[str]:
    """Return the markers that make the fixture validate cleanly."""
    stunter, software = project["stunter"].stem, project["software"].stem
    return [
        f"# @tests_req {software}#S1",
        f"# @tests_req {software}#S2",
        f"# @tests_req {stunter}#S1",
        f"# @tests_req {stunter}#S2",
        f"# @accepts_req {stunter}#S1",
        f"# @accepts_req {stunter}#S2",
    ]


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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
@pytest.mark.parametrize(
    "markers",
    [
        ["# @tests_req {swrs}"],
        ["# @tests_req {swrs}#S9"],
        ["# @accepts_req {swrs}#S1"],
        ["# @tests_req {strs}"],
    ],
    ids=["no-fragment", "undeclared-fragment", "accepts-on-swrs", "no-fragment-on-strs"],
)
def test_validate_exits_one_on_each_acceptance_error(tmp_path: Path, markers: list[str]) -> None:
    project = make_project(tmp_path)
    write_markers(
        project,
        "test_flow.py",
        [
            marker.format(strs=project["stunter"].stem, swrs=project["software"].stem)
            for marker in markers
        ],
    )

    result = CliRunner().invoke(okfreq, ["validate", str(project["root"])])

    assert result.exit_code == 1
    assert "1 errors" in result.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_validate_exits_zero_while_printing_w003_and_w004(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    _undeclare(project["stunter"])
    write_markers(
        project,
        "test_flow.py",
        [
            f"# @tests_req {project['software'].stem}#S1",
            f"# @tests_req {project['software'].stem}#S2",
        ],
    )

    result = CliRunner().invoke(okfreq, ["validate", str(project["root"])])

    assert result.exit_code == 0, result.output
    assert "0 errors, 2 warnings" in result.output
    assert "W003" in result.output
    assert "W004" in result.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_lint_fails_on_each_acceptance_error(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    write_markers(project, "test_flow.py", [f"# @tests_req {project['software'].stem}"])

    result = CliRunner().invoke(okfreq, ["lint", str(project["root"])])

    assert result.exit_code == 1
    assert "has no scenario fragment" in result.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_lint_prints_the_warnings_without_failing(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    write_markers(
        project,
        "test_flow.py",
        [
            f"# @tests_req {project['software'].stem}#S1",
            f"# @tests_req {project['software'].stem}#S2",
        ],
    )

    result = CliRunner().invoke(okfreq, ["lint", str(project["root"])])

    # Warnings stay advisory: `lint` fails on structural errors only.
    assert result.exit_code == 0, result.output
    assert "W004" in result.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_trace_prints_the_accepted_count_and_json_keys(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    write_markers(project, "test_flow.py", covering_markers(project))
    runner = CliRunner()

    plain = runner.invoke(okfreq, ["trace", str(project["root"])])
    as_json = runner.invoke(okfreq, ["trace", str(project["root"]), "--json"])

    assert plain.exit_code == 0
    assert plain.output.strip() == "implemented: 1; tested: 1; accepted: 1; missing IDs: 0"
    assert json.loads(as_json.output)["scenario_markers"][2]["fragment"] == "S1"
    payload = json.loads(as_json.output)
    assert payload["accepted"] == {
        project["stunter"].stem: ["tests/test_flow.py", "tests/test_flow.py"]
    }
    assert payload["scenario_markers"][0] == {
        "marker": "tests",
        "id": project["software"].stem,
        "fragment": "S1",
        "file": "tests/test_flow.py",
        "line": 1,
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_update_coverage_writes_the_statement_fields(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    write_markers(project, "test_flow.py", covering_markers(project))

    result = CliRunner().invoke(okfreq, ["update-coverage", str(project["root"])])
    check = CliRunner().invoke(okfreq, ["update-coverage", str(project["root"]), "--check"])

    assert result.exit_code == 0, result.output
    fields = frontmatter_of(project["stunter"])
    assert fields["tested_in_files"] == ["tests/test_flow.py"]
    assert fields["accepted_in_files"] == ["tests/test_flow.py"]
    assert check.exit_code == 0
    assert "0 files" in check.output
    assert frontmatter_of(project["software"])["tested_in_files"] == ["tests/test_flow.py"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_generate_report_writes_the_acceptance_columns(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    write_markers(project, "test_flow.py", covering_markers(project))
    destination = tmp_path / "dist"

    result = CliRunner().invoke(
        okfreq,
        [
            "generate-report",
            str(project["root"]),
            "--output-json",
            str(destination / "requirements.json"),
            "--output-summary-md",
            str(destination / "requirements.md"),
        ],
    )

    assert result.exit_code == 0, result.output
    summary = (destination / "requirements.md").read_text(encoding="utf-8")
    assert "| Scope | Tier | ID | Name | Tests | Tested | Accepted |" in summary
    assert "Missing transitions" in summary
    assert "✅ covered | ✅ 2/2 | ✅ 2/2 |" in summary
    payload = json.loads((destination / "requirements.json").read_text(encoding="utf-8"))
    assert payload["format_version"] == 2
    assert payload["stakeholder_test_coverage"]["paths"] == {"total": 2, "tested": 2, "accepted": 2}


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S7
def test_new_pre_fills_the_scenarios_of_both_tiers(tmp_path: Path) -> None:
    root = init_requirements(tmp_path / "requirements")
    set_mode(root, ACCEPTANCE_PATHS_MODE)
    runner = CliRunner()

    first = runner.invoke(
        okfreq,
        [
            "new",
            "strs",
            "Export",
            "--description",
            "The tool SHALL export.",
            "--user-need",
            "Users need reports.",
            "--project",
            "demo",
            "--path",
            str(root),
        ],
    )
    second = runner.invoke(
        okfreq,
        [
            "new",
            "swrs",
            "Write",
            "--description",
            "The tool SHALL write.",
            "--derives-from",
            "StRS-default-001",
            "--project",
            "demo",
            "--path",
            str(root),
        ],
    )

    assert (first.exit_code, second.exit_code) == (0, 0), first.output + second.output
    stunter = root / "tiers" / "strs" / "StRS-default-001.md"
    software = root / "tiers" / "swrs" / "SwRS-default-001.md"
    assert frontmatter_of(stunter)["scenarios"] == [{"id": "S1", "title": "<main path title>"}]
    assert "#### Path S1: <main path title>" in stunter.read_text(encoding="utf-8")
    assert [entry["id"] for entry in frontmatter_of(software)["scenarios"]] == ["S1", "S2"]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_retire_exits_non_zero_on_an_acceptance_reference(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project["software"].unlink()
    write_markers(project, "test_flow.py", [f"# @accepts_req {project['stunter'].stem}#S1"])
    before = project["stunter"].read_text(encoding="utf-8")

    result = CliRunner().invoke(
        okfreq, ["retire", project["stunter"].stem, "--path", str(project["root"]), "--yes"]
    )

    assert result.exit_code == 1
    assert "referenced by markers in tests/test_flow.py" in result.output
    assert project["stunter"].read_text(encoding="utf-8") == before
