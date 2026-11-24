"""Guard the live repository's maintained requirements and traceability evidence."""

from pathlib import Path

from okf_schema.okfreq.core import (
    _scenario_headings,
    _scenario_title,
    load_requirements,
    report,
    update_coverage,
    validate_requirements,
)
from okf_schema.okfreq.navigation import lint_indexes


def test_live_requirements_preserve_complete_real_evidence() -> None:
    """New changes must keep the actual project bundle valid, current and traceable."""
    project = Path(__file__).parents[1]
    root = project / "requirements"
    assert validate_requirements(root, prose=True, check_links=True, project_root=project) == []
    assert update_coverage(root, check=True) == []
    assert lint_indexes(root, check=True) == []
    result = report(root)
    evidence = result["marker_coverage"]
    for category in (
        "missing_ids",
        "duplicates",
        "non_leaf",
        "warnings",
        "missing_implementation",
        "missing_tests",
    ):
        assert evidence[category] == [], (category, evidence[category])
    stakeholder = result["stakeholder_test_coverage"]
    assert stakeholder["mode"] == "linked-swrs-and-acceptance-paths"
    assert stakeholder["covered"] == stakeholder["requirements"]
    # StRS-OKFSCHEMA-OKFKB-001 is covered through its justified acceptance waiver: its
    # consolidation path stays unaccepted, and the waiver never fills the counters.
    assert stakeholder["paths"]["accepted"] == stakeholder["paths"]["total"] - 1 > 0
    waived = {
        record["id"]: record["stakeholder_test_coverage"]
        for record in result["requirements"]
        if "acceptance_exemption" in record.get("stakeholder_test_coverage", {})
    }
    assert list(waived) == ["StRS-OKFSCHEMA-OKFKB-001"]
    kb = waived["StRS-OKFSCHEMA-OKFKB-001"]
    assert kb["status"] == "covered"
    assert kb["accepted"] is False
    assert kb["paths"]["accepted"] == kb["paths"]["total"] - 1
    assert {"id": "SwRS-OKFSCHEMA-OKFKB-005", "status": "exempt"} in kb["linked_swrs"]


def test_repository_guideline_is_the_installed_shipped_text() -> None:
    """The repository's guideline is `okfreq init` output, never hand-maintained."""
    from okf_schema.okfreq.core import GUIDELINE_NAME, _strip_own_markers

    project = Path(__file__).parents[1]
    shipped = project / "src/okf_schema/data/requirements/guidelines" / GUIDELINE_NAME
    installed = project / "requirements/guidelines" / GUIDELINE_NAME
    assert installed.read_text(encoding="utf-8") == _strip_own_markers(
        shipped.read_text(encoding="utf-8")
    )
    assert (project / "requirements/guidelines/project.guidelines.md").is_file()


def test_scenario_headings_recall_their_declared_ids_and_titles() -> None:
    """Every live and example body heading names its scenario as ``S<n>: <title>``."""
    project = Path(__file__).parents[1]
    for root in (project / "requirements", project / "examples/okfreq-examples/requirements"):
        for identifier, (_, data, text) in load_requirements(root).items():
            if "scenarios" not in data:
                continue
            kind = "Path" if data["type"] == "StRS" else "Scenario"
            expected = [f"{kind} {entry['id']}: {entry['title']}" for entry in data["scenarios"]]
            headings = _scenario_headings(text)
            assert headings == expected, (root, identifier)
            assert [_scenario_title(heading) for heading in headings] == [
                entry["title"] for entry in data["scenarios"]
            ]
