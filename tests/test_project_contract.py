"""Guard the live repository's maintained requirements and traceability evidence."""

from pathlib import Path

from okf_schema.okfreq.core import report, update_coverage, validate_requirements
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
    assert stakeholder["covered"] == stakeholder["requirements"] == 5
    # Twelve of the thirteen declared paths have an acceptance test; the interactive
    # consolidation path of StRS-OKFSCHEMA-OKFKB-001 is waived with a reason.
    assert stakeholder["paths"]["total"] == 13
    assert stakeholder["paths"]["accepted"] == 12
    records = {item["id"]: item for item in result["requirements"]}
    waived = records["StRS-OKFSCHEMA-OKFKB-001"]["stakeholder_test_coverage"]
    assert waived["acceptance_exemption"]["reason"].strip()
    assert (waived["paths"]["total"], waived["paths"]["accepted"]) == (3, 2)
    for strs_id, record in records.items():
        if strs_id.startswith("StRS-") and strs_id != "StRS-OKFSCHEMA-OKFKB-001":
            paths = record["stakeholder_test_coverage"]["paths"]
            assert paths["accepted"] == paths["total"] > 0, strs_id
    assert [item["id"] for item in evidence["exemptions"]] == ["SwRS-OKFSCHEMA-OKFKB-005"]


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
