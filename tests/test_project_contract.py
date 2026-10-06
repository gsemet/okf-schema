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
    assert stakeholder["mode"] == "linked-swrs-and-validation-test"
    assert stakeholder["covered"] == stakeholder["requirements"]
