"""CLI tests for the okfreq mode ``linked-swrs-and-acceptance-paths``."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator
from parametrization import Parametrization

from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import report_schema
from tests.test_okfreq_acceptance_paths import (
    NEW_MODE,
    OLD_MODES,
    STRS_1,
    STRS_2,
    SWRS_1,
    _doc,
    _frontmatter,
    _mark_everything,
    _set_fields,
    _write,
    make_project,
)

W004_MARKER = "has no acceptance test: no @accepts_req marker that counts names it."


def _run(*args: object, expected: int = 0) -> str:
    result = CliRunner().invoke(okfreq, [str(arg) for arg in args])
    assert result.exit_code == expected, result.output
    return result.output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_validate_prints_w003_and_w004_without_prose_and_exits_zero(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    output = _run("validate", root)
    lines = output.splitlines()
    assert lines[0] == "4 requirements, 0 errors, 3 warnings"
    assert (
        sum(line.startswith("W003 ") for line in lines) == 1
        and f"{STRS_2} declares no scenarios:." in output
    )
    assert sum(W004_MARKER in line for line in lines) == 2
    assert "W004" in _run("lint", root)
    payload = json.loads(_run("validate", root, "--json"))
    assert payload["errors"] == []
    assert any(item.startswith("W003 ") for item in payload["warnings"])


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_validate_and_lint_exit_nonzero_for_a_fragment_error(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_m.py", f"# @tests_req {SWRS_1}\n")
    expected = f"tests/test_m.py:1: @tests_req {SWRS_1} has no scenario fragment;"
    assert "1 errors" in _run("validate", root, expected=1)
    assert expected in _run("lint", root, expected=1)
    assert expected in json.loads(_run("validate", root, "--json", expected=1))["errors"][0]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_old_modes_print_no_acceptance_findings(tmp_path: Path) -> None:
    for mode in OLD_MODES:
        root = make_project(tmp_path / mode, mode)
        output = _run("validate", root, "--prose")
        assert "W003" not in output and "W004" not in output


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_trace_reports_accepted_counts_and_json_keys(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    assert "accepted: 2" in _run("trace", root)
    payload = json.loads(_run("trace", root, "--json"))
    assert payload["accepted"] == {STRS_1: ["tests/test_cov.py"], STRS_2: ["tests/test_cov.py"]}
    assert {
        "marker": "accepts",
        "id": STRS_1,
        "fragment": "S2",
        "file": "tests/test_cov.py",
        "line": 2,
    } in payload["scenario_markers"]


def test_update_coverage_in_the_new_mode_writes_both_generated_fields(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    assert _run("update-coverage", root, "--check", expected=1)
    _run("update-coverage", root)
    front = _frontmatter(_doc(root, STRS_1))
    assert front["tested_in_files"] == front["accepted_in_files"] == ["tests/test_cov.py"]
    assert front["scenarios"]
    _run("update-coverage", root, "--check")


@Parametrization.autodetect_parameters()
@Parametrization.case(name="old", mode="linked-swrs")
@Parametrization.case(name="validation", mode="linked-swrs-and-validation-test")
@Parametrization.case(name="new", mode=NEW_MODE)
def test_retire_refuses_an_id_named_by_an_accepts_marker(tmp_path: Path, mode: str) -> None:
    root = make_project(tmp_path, mode)
    _run("new", "strs", "Draft", "--description", "A draft.", "--project", "demo", "--path", root)
    draft = "StRS-default-003"
    _write(tmp_path, "tests/test_acc.py", f"# @accepts_req {draft}\n")
    output = _run("retire", draft, "--yes", "--path", root, expected=1)
    assert f"cannot retire {draft}: referenced by markers in tests/test_acc.py" in output
    assert _doc(root, draft).exists()


def test_new_prints_the_path_and_scaffolds_scenarios_in_the_new_mode(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    output = _run(
        "new",
        "swrs",
        "Fresh",
        "--description",
        "It SHALL.",
        "--project",
        "demo",
        "--derives-from",
        STRS_1,
        "--path",
        root,
    )
    created = _doc(root, "SwRS-default-003")
    assert output.startswith(f"Created {created}")
    assert _frontmatter(created)["scenarios"] == [
        {"id": "S1", "title": "<nominal behavior>"},
        {"id": "S2", "title": "<boundary or failure behavior>"},
    ]
    _run("new", "strs", "Fresh", "--description", "It SHALL.", "--project", "demo", "--path", root)
    assert _frontmatter(_doc(root, "StRS-default-003"))["scenarios"] == [
        {"id": "S1", "title": "<main path title>"}
    ]


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_generate_report_writes_json_schema_valid_with_paths_and_markdown(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    _set_fields(_doc(root, STRS_2), acceptance_exemption=True, acceptance_exemption_reason="manual")
    output_json, output_md = tmp_path / "out" / "report.json", tmp_path / "out" / "summary.md"
    output_json.parent.mkdir()
    _run("generate-report", root, "--output-json", output_json, "--output-summary-md", output_md)
    data = json.loads(output_json.read_text(encoding="utf-8"))
    Draft202012Validator(report_schema()).validate(data)
    assert data["stakeholder_test_coverage"]["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert "- StRS paths: tested 1/2, accepted 1/2" in output_md.read_text(encoding="utf-8")
    assert output_json.with_suffix(".schema.json").exists()
