"""Tests for the okfreq mode ``linked-swrs-and-acceptance-paths`` (library level)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.core import (
    STATUS_PROJECTION,
    RequirementError,
    create_requirement,
    init_requirements,
    load_config,
    load_requirements,
    marker_scan,
    report,
    report_schema,
    retire_requirement,
    update_coverage,
    validate_requirements,
    write_markdown_report,
)

NEW_MODE = "linked-swrs-and-acceptance-paths"
OLD_MODES = ("linked-swrs", "linked-swrs-and-validation-test")
STRS_1 = "StRS-default-001"  # declares S1, S2
STRS_2 = "StRS-default-002"  # declares no scenarios
SWRS_1 = "SwRS-default-001"  # derives from STRS_1, declares S1, S2
SWRS_2 = "SwRS-default-002"  # derives from STRS_2, declares no scenarios
FRAGMENT_MISSING = (
    "tests/test_m.py:1: {kw} {id} has no scenario fragment; {id} declares scenarios S1, S2: "
    "write {kw} {id}#S<n> (this marker does not count)"
)
FRAGMENT_UNKNOWN = (
    "tests/test_m.py:1: {kw} {id}#{fragment} names no declared scenario of {id} {suffix}"
)


def _set_fields(document: Path, **fields: object) -> None:
    """Rewrite authored frontmatter fields of one requirement document."""
    frontmatter, body = extract_frontmatter(document.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    data.update(fields)
    if "req_lifecycle" in fields and "status" in data:
        data["status"] = STATUS_PROJECTION[str(data["req_lifecycle"])]
    document.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def _set_body(document: Path, body: str) -> None:
    frontmatter, _ = extract_frontmatter(document.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    document.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def _edit_config(root: Path, old: str, new: str) -> None:
    config = root / "config.yml"
    text = config.read_text(encoding="utf-8")
    assert old in text
    config.write_text(text.replace(old, new), encoding="utf-8")


def _set_mode(root: Path, mode: str) -> None:
    current = load_config(root)["strs_test_coverage_mode"]
    _edit_config(root, f"strs_test_coverage_mode: {current}", f"strs_test_coverage_mode: {mode}")


def _scenarios(*ids: str) -> list[dict[str, str]]:
    return [{"id": scenario, "title": f"Path {scenario}"} for scenario in ids]


def _write(project: Path, name: str, text: str) -> Path:
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _new(root: Path, level: str, title: str, derives_from: list[str] | None = None) -> Path:
    return create_requirement(
        root,
        level,
        title,
        f"The {title} capability SHALL work.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=derives_from,
    )


def make_project(tmp_path: Path, mode: str = NEW_MODE) -> Path:
    """Return a bundle root with the four requirements documented above, in ``mode``."""
    root = init_requirements(tmp_path)
    assert isinstance(root, Path)
    strs_1 = _new(root, "StRS", "Export")
    strs_2 = _new(root, "StRS", "Share")
    swrs_1 = _new(root, "SwRS", "Write", [STRS_1])
    swrs_2 = _new(root, "SwRS", "Send", [STRS_2])
    _set_fields(strs_1, scenarios=_scenarios("S1", "S2"))
    _set_fields(swrs_1, scenarios=_scenarios("S1", "S2"))
    assert (strs_2.exists(), swrs_2.exists()) == (True, True)
    _set_mode(root, mode)
    return root


def _doc(root: Path, identifier: str) -> Path:
    return load_requirements(root)[identifier][0]


def _frontmatter(path: Path) -> dict[str, Any]:
    frontmatter, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    return dict(make_yaml().load(frontmatter))


def _errors(findings: list[str]) -> list[str]:
    return [item for item in findings if not re.match(r"[WI]\d{3} ", item)]


def _warnings(findings: list[str], code: str) -> list[str]:
    return [item for item in findings if item.startswith(f"{code} ")]


def _strs_record(data: dict[str, Any], identifier: str = STRS_1) -> dict[str, Any]:
    return next(item for item in data["requirements"] if item["id"] == identifier)


def _rows(markdown: str) -> dict[str, list[str]]:
    """Map each requirement ID of the Markdown tables to its cells."""
    cells = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in markdown.splitlines()
        if "|" in line
    ]
    return {row[2]: row for row in cells if len(row) > 3 and row[1] in ("StRS", "SwRS")}


def _approve(path: Path) -> None:
    _set_fields(
        path,
        req_lifecycle="approved",
        owner_email="po@example.org",
        approved_by="po@example.org",
        approved_at="2026-10-28T09:00:00+01:00",
    )


# --- configuration, scaffold, marker scan -------------------------------------------------------


def test_mode_is_accepted_and_unknown_modes_are_refused(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert load_config(root)["strs_test_coverage_mode"] == NEW_MODE
    _set_mode(root, "bogus")
    with pytest.raises(RequirementError) as caught:
        load_config(root)
    for mode in (*OLD_MODES, NEW_MODE):
        assert mode in str(caught.value)


def test_init_scaffold_declares_scenarios_waiver_and_swrs_refusal(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    schemas = root / "tiers" / "_schema"
    base = make_yaml().load((schemas / "base.schema.yaml").read_text(encoding="utf-8"))
    strs = make_yaml().load((schemas / "strs.schema.yaml").read_text(encoding="utf-8"))
    swrs = make_yaml().load((schemas / "swrs.schema.yaml").read_text(encoding="utf-8"))
    assert (
        base["properties"]["scenarios"]["items"]["properties"]["id"]["pattern"] == "^S[1-9][0-9]*$"
    )
    assert (
        "adds scenarios: to the frontmatter" in base["properties"]["req_lifecycle"]["description"]
    )
    strs_properties = strs["allOf"][1]["properties"]
    assert {"acceptance_exemption", "acceptance_exemption_reason", "accepted_in_files"} <= set(
        strs_properties
    )
    assert strs["allOf"][1]["then"]["required"] == ["acceptance_exemption_reason"]
    assert swrs["allOf"][1]["properties"]["accepted_in_files"]["maxItems"] == 0
    config = load_config(root)
    assert config["markers"]["accepts"] == "@accepts_req"
    assert "accepted_in_files" in config["generated_fields"]


def test_config_without_accepts_keyword_gets_the_default(tmp_path: Path) -> None:
    root = make_project(tmp_path, "linked-swrs")
    _edit_config(root, "  accepts: '@accepts_req'\n", "")
    assert load_config(root)["markers"]["accepts"] == "@accepts_req"


@Parametrization.autodetect_parameters()
@Parametrization.case(name="old", mode="linked-swrs")
@Parametrization.case(name="validation", mode="linked-swrs-and-validation-test")
@Parametrization.case(name="new", mode=NEW_MODE)
def test_two_marker_kinds_sharing_a_keyword_are_refused_in_every_mode(
    tmp_path: Path, mode: str
) -> None:
    root = make_project(tmp_path, mode)
    _edit_config(root, "accepts: '@accepts_req'", "accepts: '@tests_req'")
    with pytest.raises(
        RequirementError, match=r"markers\.tests and markers\.accepts use the same keyword"
    ):
        load_config(root)
    _edit_config(root, "accepts: '@tests_req'", "accepts: '@accepts_req'")
    _edit_config(root, "tests: '@tests_req'", "tests: '@proves'")
    _write(tmp_path, "tests/test_m.py", f"# @proves {SWRS_2}\n")
    assert marker_scan(root)["tested"] == {SWRS_2: ["tests/test_m.py"]}


@Parametrization.autodetect_parameters()
@Parametrization.case(name="fragment", line=f"# @accepts_req {STRS_1}#S1", fragment="S1")
@Parametrization.case(name="zero", line=f"# @accepts_req {STRS_1}#S0", fragment="S0")
@Parametrization.case(name="leading-zero", line=f"# @accepts_req {STRS_1}#S01", fragment="S01")
@Parametrization.case(name="word", line=f"# @accepts_req {STRS_1}#path1", fragment=None)
@Parametrization.case(name="trailing-letter", line=f"# @accepts_req {STRS_1}#S1a", fragment=None)
@Parametrization.case(name="lowercase", line=f"# @accepts_req {STRS_1}#s1", fragment=None)
@Parametrization.case(name="bare-hash", line=f"# @accepts_req {STRS_1}#", fragment=None)
@Parametrization.case(name="no-fragment", line=f"# @accepts_req {STRS_1}", fragment=None)
@Parametrization.case(name="commented-out", line=f"# # @accepts_req {STRS_1}#S1", fragment="absent")
def test_marker_scan_captures_the_scenario_fragment(
    tmp_path: Path, line: str, fragment: str | None
) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_m.py", f"{line}\n")
    scan = marker_scan(root)
    if fragment == "absent":
        assert scan["scenario_markers"] == [] and scan["accepted"] == {}
        return
    assert scan["scenario_markers"] == [
        {
            "marker": "accepts",
            "id": STRS_1,
            "fragment": fragment,
            "file": "tests/test_m.py",
            "line": 1,
        }
    ]
    assert scan["accepted"] == {STRS_1: ["tests/test_m.py"]}


def test_marker_scan_keys_dedupes_and_skips_accepts_in_source(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(
        tmp_path,
        "tests/test_m.py",
        f"# @tests_req {SWRS_1}#S1\n\n# @tests_req {SWRS_1}#S1\n# @accepts_req NOPE-1\n",
    )
    _write(tmp_path, "src/m.py", f"# @accepts_req {STRS_1}#S1\n# @implements_req {SWRS_1}\n")
    scan = marker_scan(root)
    assert set(scan) == {
        "accepted",
        "duplicates",
        "implemented",
        "missing_ids",
        "non_leaf",
        "scenario_markers",
        "tested",
        "validation_tests",
        "warnings",
    }
    assert scan["scenario_markers"] == [
        {"marker": "tests", "id": SWRS_1, "fragment": "S1", "file": "tests/test_m.py", "line": 1}
    ]
    assert scan["accepted"] == {} and scan["missing_ids"] == ["NOPE-1"]
    assert scan["implemented"] == {SWRS_1: ["src/m.py"]}


# --- Rule 4: which markers count ---------------------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="strs-test-no-fragment", marker="tests", target=STRS_1, fragment="", error="missing"
)
@Parametrization.case(
    name="strs-accept-no-fragment", marker="accepts", target=STRS_1, fragment="", error="missing"
)
@Parametrization.case(
    name="swrs-test-no-fragment", marker="tests", target=SWRS_1, fragment="", error="missing"
)
@Parametrization.case(
    name="word-fragment", marker="tests", target=STRS_1, fragment="#path1", error="missing"
)
@Parametrization.case(
    name="strs-accept-undeclared", marker="accepts", target=STRS_1, fragment="#S4", error="S1, S2"
)
@Parametrization.case(
    name="zero-fragment", marker="tests", target=STRS_1, fragment="#S0", error="S1, S2"
)
@Parametrization.case(
    name="leading-zero-fragment", marker="tests", target=SWRS_1, fragment="#S01", error="S1, S2"
)
@Parametrization.case(
    name="fragment-without-scenarios", marker="accepts", target=STRS_2, fragment="#S1", error="none"
)
@Parametrization.case(
    name="swrs-fragment-without-scenarios",
    marker="tests",
    target=SWRS_2,
    fragment="#S1",
    error="none",
)
@Parametrization.case(name="declared", marker="accepts", target=STRS_1, fragment="#S2", error=None)
@Parametrization.case(
    name="swrs-declared", marker="tests", target=SWRS_1, fragment="#S1", error=None
)
@Parametrization.case(
    name="no-scenarios-fragmentless", marker="accepts", target=STRS_2, fragment="", error=None
)
@Parametrization.case(
    name="swrs-no-scenarios-fragmentless", marker="tests", target=SWRS_2, fragment="", error=None
)
def test_marker_fragment_rules(
    tmp_path: Path, marker: str, target: str, fragment: str, error: str | None
) -> None:
    root = make_project(tmp_path)
    keyword = f"@{marker}_req"
    _write(tmp_path, "tests/test_m.py", f"# {keyword} {target}{fragment}\n")
    errors = [e for e in _errors(validate_requirements(root)) if e.startswith("tests/test_m.py")]
    if error is None:
        assert errors == []
    elif error == "missing":
        assert errors == [FRAGMENT_MISSING.format(kw=keyword, id=target)]
    elif error == "none":
        suffix = f"({target} declares no scenarios:)"
        assert errors == [
            FRAGMENT_UNKNOWN.format(kw=keyword, id=target, fragment="S1", suffix=suffix)
        ]
    else:
        suffix = "(declared: S1, S2)"
        assert errors == [
            FRAGMENT_UNKNOWN.format(kw=keyword, id=target, fragment=fragment[1:], suffix=suffix)
        ]


def test_custom_keywords_appear_in_fragment_errors(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _edit_config(root, "accepts: '@accepts_req'", "accepts: '@accepts_main_path'")
    _write(tmp_path, "tests/test_m.py", f"# @accepts_main_path {STRS_1}\n")
    assert FRAGMENT_MISSING.format(kw="@accepts_main_path", id=STRS_1) in _errors(
        validate_requirements(root)
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_markers_outside_the_new_mode_ignore_fragment_rules(tmp_path: Path) -> None:
    root = make_project(tmp_path, "linked-swrs")
    _write(
        tmp_path,
        "tests/test_m.py",
        f"# @tests_req {SWRS_1}\n# @tests_req {SWRS_2}#S9\n# @accepts_req {STRS_1}\n",
    )
    assert validate_requirements(root) == []


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S2
def test_accepts_marker_on_a_swrs_is_a_schema_error(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_m.py", f"# @accepts_req {SWRS_1}#S1\n")
    errors = _errors(validate_requirements(root))
    assert len(errors) == 1
    assert errors[0].endswith(
        "@accepts_req SwRS-default-001: Never present. @accepts_req names a StRS main path; "
        "mark a SwRS test with @tests_req <SwRS-ID>#S<n>."
    )
    assert SWRS_1 in errors[0] and "tests/test_m.py:1" in errors[0]
    assert marker_scan(root)["tested"] == {}


@Parametrization.autodetect_parameters()
@Parametrization.case(name="no-max-items", old="      maxItems: 0\n", new="")
@Parametrization.case(
    name="property-missing",
    old=(
        "    accepted_in_files:\n      type: array\n      maxItems: 0\n"
        "      description: Never present. @accepts_req names a StRS main path; mark a\n"
        "        SwRS test with @tests_req <SwRS-ID>#S<n>.\n"
    ),
    new="",
)
def test_outdated_swrs_schema_is_one_actionable_error(tmp_path: Path, old: str, new: str) -> None:
    root = make_project(tmp_path)
    schema = root / "tiers" / "_schema" / "swrs.schema.yaml"
    text = schema.read_text(encoding="utf-8")
    assert old in text
    schema.write_text(text.replace(old, new), encoding="utf-8")
    errors = _errors(validate_requirements(root))
    assert len(errors) == 1
    assert "swrs.schema.yaml: accepted_in_files is not refused" in errors[0]
    assert "okf-schema 0.18.0" in errors[0] and "maxItems: 0" in errors[0]
    _set_mode(root, "linked-swrs")
    assert _errors(validate_requirements(root)) == []


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="duplicate", value=_scenarios("S1", "S1"), problem="entry 2 repeats id S1"
)
@Parametrization.case(
    name="bad-id", value=[{"id": "X1", "title": "t"}], problem="has id 'X1' that is not S<n>"
)
@Parametrization.case(
    name="empty-title", value=[{"id": "S1", "title": " "}], problem="has an empty or missing title"
)
@Parametrization.case(
    name="not-a-list", value={"id": "S1", "title": "t"}, problem="must be a list of mappings"
)
def test_malformed_scenarios_name_the_problem_in_the_new_mode_only(
    tmp_path: Path, value: object, problem: str
) -> None:
    root = make_project(tmp_path)
    document = _doc(root, STRS_2)
    _set_fields(document, scenarios=value)
    errors = [
        e
        for e in _errors(validate_requirements(root))
        if "(each entry is {id: S<n>, title: <text>}" in e
    ]
    assert len(errors) == 1 and "md: scenarios: " in errors[0] and problem in errors[0]
    _set_mode(root, "linked-swrs")
    assert not [e for e in _errors(validate_requirements(root)) if "each entry is" in e]


# --- waiver ------------------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_effective_waiver_suppresses_w004_and_is_reported(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_m.py", f"# @tests_req {SWRS_2}\n")
    _set_fields(
        _doc(root, STRS_2),
        acceptance_exemption=True,
        acceptance_exemption_reason="manual hardware step",
    )
    findings = validate_requirements(root)
    assert not any(STRS_2 in item for item in _warnings(findings, "W004"))
    record = _strs_record(report(root), STRS_2)
    assert record["stakeholder_test_coverage"]["acceptance_exemption"] == {
        "reason": "manual hardware step"
    }
    assert record["stakeholder_test_coverage"]["status"] == "covered"


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_blank_waiver_reason_is_an_error_and_the_waiver_is_ineffective(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_m.py", f"# @tests_req {SWRS_2}\n")
    document = _doc(root, STRS_2)
    _set_fields(document, acceptance_exemption=True, acceptance_exemption_reason="   ")
    findings = validate_requirements(root)
    assert any(
        item.endswith("acceptance_exemption_reason must not be blank") for item in _errors(findings)
    )
    assert any(STRS_2 in item for item in _warnings(findings, "W004"))
    record = _strs_record(report(root), STRS_2)["stakeholder_test_coverage"]
    assert "acceptance_exemption" not in record and record["status"] == "missing"


# --- W003 / W004 -------------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S3
def test_w003_quotes_headings_and_preserves_explicit_ids(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    body = (
        "## Share\n\n### Main paths\n\n#### Path S3: Open the report\n\ntext\n\n"
        "#### Path 1: Comment\n\n#### Path S1: Resolve\n\n"
        "### Rationale and constraints\n\n#### Not a path\n"
    )
    _set_body(_doc(root, STRS_2), body)
    (w003,) = [item for item in _warnings(validate_requirements(root), "W003") if STRS_2 in item]
    assert f"{STRS_2} declares no scenarios:." in w003
    assert (
        'Headings found in the body: "#### Path S3: Open the report"; "#### Path 1: Comment"; '
        in w003
    )
    assert '"#### Path S1: Resolve". Add this block to the frontmatter' in w003
    assert "Not a path" not in w003
    assert (
        "scenarios:\n- id: S3\n  title: Open the report\n- id: S2\n  title: Comment\n"
        "- id: S1\n  title: Resolve\n"
    ) in w003
    assert "(on an approved requirement, log the change in the bundle's tiers/log.md)" in w003
    assert w003.endswith(
        "https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html#okfreq-declared-scenarios"
    )


def test_w003_without_headings_proposes_a_placeholder(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    (w003,) = [item for item in _warnings(validate_requirements(root), "W003") if STRS_2 in item]
    assert "No main-path heading was found in the body." in w003
    assert "scenarios:\n- id: S1\n  title: <main path title>\n" in w003


def test_w003_and_w004_skip_dead_requirements_and_other_modes(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert [item for item in _warnings(validate_requirements(root), "W003") if STRS_2 in item]
    _set_fields(_doc(root, STRS_2), req_lifecycle="deprecated")
    assert [item for item in validate_requirements(root) if STRS_2 in item] == []
    for mode in OLD_MODES:
        _set_mode(root, mode)
        assert not [
            item for item in validate_requirements(root) if item.startswith(("W003", "W004"))
        ]
        _set_mode(root, NEW_MODE)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S6
def test_approved_strs_gaining_only_scenarios_still_validates(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _approve(_doc(root, STRS_2))
    assert _errors(validate_requirements(root)) == []
    _set_fields(_doc(root, STRS_2), scenarios=_scenarios("S1"))
    assert _errors(validate_requirements(root)) == []
    assert not [item for item in _warnings(validate_requirements(root), "W003") if STRS_2 in item]


def test_w004_text_is_independent_of_w003_and_suppressed_by_counting_markers(
    tmp_path: Path,
) -> None:
    root = make_project(tmp_path)
    findings = validate_requirements(root)
    assert [item for item in _warnings(findings, "W003") if STRS_1 in item] == []
    (w004,) = [
        item
        for item in _warnings(findings, "W004")
        if f" {STRS_1} " in item or f": {STRS_1} " in item
    ]
    assert f"{STRS_1} has no acceptance test: no @accepts_req marker that counts names it." in w004
    assert (
        f"@accepts_req {STRS_1}#S<n> (@accepts_req {STRS_1} while it declares no scenarios:)"
        in w004
    )
    assert w004.endswith("okfreq-acceptance-paths.html#okfreq-execution-cost")
    # A fragmentless marker on a StRS that declares scenarios does not count.
    _write(tmp_path, "tests/test_m.py", f"# @accepts_req {STRS_1}\n")
    assert [item for item in _warnings(validate_requirements(root), "W004") if STRS_1 in item]
    # Each counting marker clears W004; the undeclared StRS keeps W003 only.
    _write(tmp_path, "tests/test_m.py", f"# @accepts_req {STRS_1}#S1\n# @accepts_req {STRS_2}\n")
    findings = validate_requirements(root)
    assert not [item for item in _warnings(findings, "W004") if STRS_1 in item or STRS_2 in item]
    assert [item for item in _warnings(findings, "W003") if STRS_2 in item]


# --- Rule 5 counters, update-coverage, report --------------------------------------------------


def _mark_everything(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "tests/test_cov.py",
        f"# @tests_req {STRS_1}#S1\n# @accepts_req {STRS_1}#S2\n"
        f"# @tests_req {SWRS_1}#S1\n# @tests_req {SWRS_1}\n# @tests_req {SWRS_2}\n"
        f"# @accepts_req {STRS_2}\n",
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_counters_are_independent_and_covered_needs_every_condition(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    data = report(root)
    strs_1 = _strs_record(data)["stakeholder_test_coverage"]
    assert strs_1["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert (strs_1["tested"], strs_1["accepted"]) == (False, False)
    defined = {"status": "defined", "files": ["tests/test_cov.py"], "count": 1}
    assert strs_1["tests"] == strs_1["acceptance_tests"] == strs_1["validation_tests"] == defined
    assert strs_1["linked_swrs"] == [{"id": SWRS_1, "status": "missing"}]
    assert strs_1["status"] == "missing"
    swrs_1 = _strs_record(data, SWRS_1)
    assert swrs_1["transitions"] == {"tested": ["S1"], "missing": ["S2"]}
    strs_2 = _strs_record(data, STRS_2)["stakeholder_test_coverage"]
    assert strs_2["paths"] == {"total": 0, "tested": 0, "accepted": 0}
    assert strs_2["linked_swrs"] == [{"id": SWRS_2, "status": "covered"}]
    assert strs_2["status"] == "covered" and strs_2["mode"] == NEW_MODE
    _write(
        tmp_path,
        "tests/test_more.py",
        f"# @tests_req {SWRS_1}#S2\n# @tests_req {STRS_1}#S2\n# @accepts_req {STRS_1}#S1\n",
    )
    full = report(root)
    done = _strs_record(full)["stakeholder_test_coverage"]
    assert done["status"] == "covered" and (done["tested"], done["accepted"]) == (True, True)
    assert done["paths"] == {"total": 2, "tested": 2, "accepted": 2}


def test_exempt_swrs_counts_and_accept_marker_is_required_without_waiver(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _write(tmp_path, "tests/test_cov.py", f"# @tests_req {SWRS_2}\n")
    assert _strs_record(report(root), STRS_2)["stakeholder_test_coverage"]["status"] == "missing"
    _set_fields(_doc(root, SWRS_2), annotation_exemption=True, exemption_reason="declarative")
    (tmp_path / "tests/test_cov.py").unlink()
    _write(tmp_path, "tests/test_cov.py", f"# @accepts_req {STRS_2}\n")
    record = _strs_record(report(root), STRS_2)["stakeholder_test_coverage"]
    assert (
        record["linked_swrs"] == [{"id": SWRS_2, "status": "exempt"}]
        and record["status"] == "covered"
    )


def test_update_coverage_writes_generated_fields_and_keeps_scenarios(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    _write(tmp_path, "tests/test_bad.py", f"# @tests_req {SWRS_1}\n# @accepts_req {STRS_1}\n")
    assert update_coverage(root)
    strs_1 = _frontmatter(_doc(root, STRS_1))
    assert strs_1["tested_in_files"] == ["tests/test_cov.py"]
    assert strs_1["accepted_in_files"] == ["tests/test_cov.py"]
    assert strs_1["scenarios"] == _scenarios("S1", "S2")
    swrs_1 = _frontmatter(_doc(root, SWRS_1))
    assert swrs_1["tested_in_files"] == ["tests/test_cov.py"] and "accepted_in_files" not in swrs_1
    assert update_coverage(root, check=True) == []


# --- D1/D2: the other modes keep their behavior --------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(name="old", mode="linked-swrs")
@Parametrization.case(name="validation", mode="linked-swrs-and-validation-test")
def test_old_modes_are_unchanged_by_fragments_and_accepts_markers(
    tmp_path: Path, mode: str
) -> None:
    root = make_project(tmp_path, mode)
    _write(
        tmp_path,
        "tests/test_cov.py",
        f"# @tests_req {SWRS_1}\n# @tests_req {SWRS_2}\n# @tests_req {STRS_2}\n",
    )
    plain_findings, plain_report = validate_requirements(root), report(root)
    _write(
        tmp_path,
        "tests/test_cov.py",
        f"# @tests_req {SWRS_1}#S1\n# @tests_req {SWRS_2}#S9\n# @tests_req {STRS_2}#path1\n"
        f"# @accepts_req {STRS_1}#S1\n",
    )
    assert validate_requirements(root) == plain_findings == []
    suffixed = report(root)
    assert suffixed["stakeholder_test_coverage"] == plain_report["stakeholder_test_coverage"]
    assert suffixed["totals"] == plain_report["totals"]
    assert "paths" not in suffixed["stakeholder_test_coverage"]
    assert "transitions" not in _strs_record(suffixed, SWRS_1)


def test_old_mode_update_coverage_strips_strs_test_fields(tmp_path: Path) -> None:
    root = make_project(tmp_path, "linked-swrs")
    document = _doc(root, STRS_1)
    _set_fields(
        document, tested_in_files=["tests/test_x.py"], accepted_in_files=["tests/test_x.py"]
    )
    assert update_coverage(root)
    stripped = _frontmatter(document)
    assert "tested_in_files" not in stripped and "accepted_in_files" not in stripped
    assert stripped["scenarios"] == _scenarios("S1", "S2")


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S5
def test_okfreq_new_scaffold_depends_on_the_mode(tmp_path: Path) -> None:
    old_root = make_project(tmp_path / "old", "linked-swrs")
    old_swrs = _new(old_root, "SwRS", "Old swrs", [STRS_1])
    old_strs = _new(old_root, "StRS", "Old strs")
    old_text = old_swrs.read_text(encoding="utf-8")
    assert (
        "### Scenario: <nominal behavior>" in old_text
        and "### Scenario: <boundary or failure behavior>" in old_text
    )
    assert "scenarios" not in _frontmatter(old_swrs) and "scenarios" not in _frontmatter(old_strs)
    assert (
        "Main paths" not in old_strs.read_text(encoding="utf-8") and "Scenario S1" not in old_text
    )
    new_root = make_project(tmp_path / "new")
    new_swrs = _new(new_root, "SwRS", "New swrs", [STRS_1])
    new_strs = _new(new_root, "StRS", "New strs")
    swrs_text = new_swrs.read_text(encoding="utf-8")
    assert "### Scenario S1: <nominal behavior>" in swrs_text
    assert "### Scenario S2: <boundary or failure behavior>" in swrs_text
    assert _frontmatter(new_swrs)["scenarios"] == [
        {"id": "S1", "title": "<nominal behavior>"},
        {"id": "S2", "title": "<boundary or failure behavior>"},
    ]
    strs_text = new_strs.read_text(encoding="utf-8")
    assert strs_text.index("### Main paths\n\n#### Path S1: <main path title>") < strs_text.index(
        "### Preserved stakeholder intent"
    )
    assert _frontmatter(new_strs)["scenarios"] == [{"id": "S1", "title": "<main path title>"}]


# --- report shape, schema, Markdown ------------------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(name="unwaived", waived=False)
@Parametrization.case(name="waived", waived=True)
def test_report_fields_validate_against_the_report_schema(tmp_path: Path, waived: bool) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    if waived:
        _set_fields(
            _doc(root, STRS_1), acceptance_exemption=True, acceptance_exemption_reason="no harness"
        )
    data = report(root)
    Draft202012Validator(report_schema()).validate(data)
    record = _strs_record(data)["stakeholder_test_coverage"]
    assert ("acceptance_exemption" in record) is waived
    assert data["format_version"] == 2
    assert data["stakeholder_test_coverage"]["paths"] == {"total": 2, "tested": 1, "accepted": 1}
    assert data["coverage_definition"]["stakeholder_test_coverage_mode"] == NEW_MODE
    assert "main path" in data["coverage_definition"]["stakeholder_tests"]
    assert data["marker_coverage"]["validation_tests"] == {
        STRS_1: ["tests/test_cov.py"],
        STRS_2: ["tests/test_cov.py"],
    }


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S4
def test_markdown_report_adds_path_columns(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    _mark_everything(tmp_path)
    destination = tmp_path / "report.md"
    write_markdown_report(root, destination)
    text = destination.read_text(encoding="utf-8")
    assert "- StRS paths: tested 1/2, accepted 1/2" in text
    assert "Tested | Accepted" in text and "Missing transitions" in text
    rows = _rows(text)
    assert rows[STRS_1][-2:] == ["1/2", "1/2"] and rows[STRS_2][-2:] == [
        "❌ no paths",
        "✅ no paths",
    ]
    assert rows[SWRS_1][-1] == "S2" and rows[SWRS_2][-1] == "—"
    _write(
        tmp_path,
        "tests/test_all.py",
        f"# @tests_req {STRS_1}#S2\n# @accepts_req {STRS_1}#S1\n# @tests_req {SWRS_1}#S2\n",
    )
    _set_fields(_doc(root, STRS_2), acceptance_exemption=True, acceptance_exemption_reason="manual")
    write_markdown_report(root, destination)
    rows = _rows(destination.read_text(encoding="utf-8"))
    assert rows[STRS_1][-2:] == ["2/2 ✅", "2/2 ✅"] and rows[STRS_2][-1] == "exempt"


# --- retire ------------------------------------------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(name="old", mode="linked-swrs")
@Parametrization.case(name="validation", mode="linked-swrs-and-validation-test")
@Parametrization.case(name="new", mode=NEW_MODE)
def test_retire_is_refused_while_an_accepts_marker_names_the_id(tmp_path: Path, mode: str) -> None:
    root = make_project(tmp_path, mode)
    draft = _new(root, "StRS", "Draft")
    _write(tmp_path, "tests/test_acc.py", f"# @accepts_req {draft.stem}\n")
    with pytest.raises(
        RequirementError,
        match=rf"cannot retire {draft.stem}: referenced by markers in tests/test_acc\.py",
    ):
        retire_requirement(root, draft.stem)
    assert draft.exists() and draft.stem not in load_config(root)["retired_ids"]
    (tmp_path / "tests/test_acc.py").unlink()
    assert retire_requirement(root, draft.stem) == draft
    assert draft.stem in load_config(root)["retired_ids"]
