"""Acceptance tests for the requirements stakeholder requirement.

Each test drives the installed ``okfreq`` console script in a fresh temporary
project, with no source checkout reachable from the interpreter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the isolated install harness is POSIX-only",
)

_BUNDLE = Path(".agents") / "requirements"


def _bundle(project: Path) -> Path:
    return project / _BUNDLE


def _requirement(project: Path, relative: str) -> Path:
    return _bundle(project) / "tiers" / relative


_GENERATED_FIELDS = (
    "derived_by:",
    "implemented_in_files:",
    "tested_in_files:",
    "accepted_in_files:",
    "status:",
    "verified:",
)


def _authored_lines(text: str) -> list[str]:
    """Return the requirement's authored lines, dropping generated fields and links."""
    lines = text.splitlines()
    end = lines.index("---", 1)
    kept: list[str] = []
    skipping = False
    for line in lines[1:end]:
        if line[:1] not in (" ", "-"):
            skipping = line.startswith(_GENERATED_FIELDS)
        if not skipping:
            kept.append(line)
    body = lines[end:]
    if "<!-- okf:links:start -->" in body:
        body = body[: body.index("<!-- okf:links:start -->")]
    combined = kept + body
    while combined and not combined[-1].strip():
        combined.pop()
    return combined


def _switch_to_acceptance_mode(distribution, project: Path) -> None:
    """Turn on the acceptance-paths mode through the project configuration."""
    config = _bundle(project) / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
        ),
        encoding="utf-8",
    )


def _author_linked_requirements(distribution, project: Path) -> None:
    """Create one StRS with its main path and one SwRS deriving from it."""
    distribution.run(
        "okfreq",
        "new",
        "strs",
        "Deliver reports",
        "--description",
        "The tool SHALL deliver reports.",
        "--project",
        "example",
        "--user-need",
        "Teams need reports.",
        "--lifecycle",
        "proposed",
        "--path",
        str(project),
        cwd=project.parent,
    )
    distribution.run(
        "okfreq",
        "new",
        "swrs",
        "Produce a report",
        "--description",
        "The tool SHALL produce a report.",
        "--project",
        "example",
        "--derives-from",
        "StRS-default-001",
        "--lifecycle",
        "proposed",
        "--path",
        str(project),
        cwd=project.parent,
    )
    stakeholder = _requirement(project, "strs/StRS-default-001.md")
    stakeholder.write_text(
        stakeholder.read_text(encoding="utf-8").replace("<main path title>", "Export the report"),
        encoding="utf-8",
    )
    software = _requirement(project, "swrs/SwRS-default-001.md")
    software.write_text(
        software.read_text(encoding="utf-8")
        .replace("<nominal behavior>", "Produce a report")
        .replace("<boundary or failure behavior>", "Refuse an empty selection"),
        encoding="utf-8",
    )


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_set_up_a_bundle_and_author_linked_requirements(
    installed_distribution, tmp_path: Path
) -> None:
    """Initialization ships the guidance, and new requirements arrive linked and indexed."""
    distribution = installed_distribution
    project = tmp_path / "project"

    created = distribution.run("okfreq", "init", str(project), cwd=tmp_path)

    assert created.returncode == 0
    guidance = _bundle(project) / "guidelines" / "requirements.guidelines.md"
    assert guidance.is_file()
    assert "SHALL" in guidance.read_text(encoding="utf-8") or guidance.stat().st_size > 0
    assert (_bundle(project) / "config.yml").is_file()
    assert (_bundle(project) / "tiers" / "_schema" / "strs.schema.yaml").is_file()
    assert (_bundle(project) / "tiers" / "_schema" / "swrs.schema.yaml").is_file()

    _author_linked_requirements(distribution, project)
    refreshed = distribution.run("okfreq", "lint", str(project), cwd=tmp_path)

    stakeholder = _requirement(project, "strs/StRS-default-001.md").read_text(encoding="utf-8")
    software = _requirement(project, "swrs/SwRS-default-001.md").read_text(encoding="utf-8")
    assert "id: StRS-default-001" in stakeholder
    assert "id: SwRS-default-001" in software
    assert "derives_from:\n- StRS-default-001" in software

    validated = distribution.run("okfreq", "validate", str(project), cwd=tmp_path, check=False)
    assert refreshed.returncode == 0
    assert "indexes updated" in refreshed.stdout
    assert validated.returncode == 0
    assert "2 requirements, 0 errors" in validated.stdout

    stakeholder_index = _requirement(project, "strs/index.md").read_text(encoding="utf-8")
    software_index = _requirement(project, "swrs/index.md").read_text(encoding="utf-8")
    assert "StRS-default-001" in stakeholder_index
    assert "SwRS-default-001" in software_index


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_trace_markers_and_refresh_generated_coverage(
    installed_distribution, tmp_path: Path
) -> None:
    """Coverage fields follow the markers and leave every authored field alone."""
    distribution = installed_distribution
    project = tmp_path / "project"
    distribution.run("okfreq", "init", str(project), cwd=tmp_path)
    _switch_to_acceptance_mode(distribution, project)
    _author_linked_requirements(distribution, project)

    (project / "src").mkdir(exist_ok=True)
    (project / "src" / "report.py").write_text(
        "# @implements_req SwRS-default-001#S1\n"
        'def build_report() -> None:\n    """Build the report."""\n',
        encoding="utf-8",
    )
    (project / "tests").mkdir(exist_ok=True)
    (project / "tests" / "test_report.py").write_text(
        "# @tests_req SwRS-default-001#S1\n"
        'def test_report() -> None:\n    """Exercise the nominal scenario."""\n',
        encoding="utf-8",
    )
    (project / "tests" / "test_acceptance_report.py").write_text(
        "# @accepts_req StRS-default-001#S1\n"
        'def test_acceptance() -> None:\n    """Walk the main path."""\n',
        encoding="utf-8",
    )
    software = _requirement(project, "swrs/SwRS-default-001.md")
    stakeholder = _requirement(project, "strs/StRS-default-001.md")
    authored_software = _authored_lines(software.read_text(encoding="utf-8"))
    authored_stakeholder = _authored_lines(stakeholder.read_text(encoding="utf-8"))

    traced = distribution.run("okfreq", "trace", str(project), cwd=tmp_path)
    refreshed = distribution.run("okfreq", "update-coverage", str(project), cwd=tmp_path)

    assert traced.returncode == 0
    assert "implemented: 1" in traced.stdout
    assert "tested: 1" in traced.stdout
    assert "accepted: 1" in traced.stdout
    assert refreshed.returncode == 0
    assert "2 files updated" in refreshed.stdout

    covered = software.read_text(encoding="utf-8")
    assert "implemented_in_files:\n- src/report.py" in covered
    assert "tested_in_files:\n- tests/test_report.py" in covered
    assert _authored_lines(covered) == authored_software

    stakeholder_covered = stakeholder.read_text(encoding="utf-8")
    assert "accepted_in_files:\n- tests/test_acceptance_report.py" in stakeholder_covered
    assert _authored_lines(stakeholder_covered) == authored_stakeholder


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_audit_the_requirements_base_with_validate_and_a_report(
    installed_distribution, tmp_path: Path
) -> None:
    """Validation names a broken marker and the report shows which paths are covered."""
    distribution = installed_distribution
    project = tmp_path / "project"
    distribution.run("okfreq", "init", str(project), cwd=tmp_path)
    _switch_to_acceptance_mode(distribution, project)
    _author_linked_requirements(distribution, project)

    (project / "src").mkdir(exist_ok=True)
    (project / "src" / "report.py").write_text(
        "# @implements_req SwRS-default-001#S1\ndef build_report():\n    pass\n",
        encoding="utf-8",
    )
    (project / "tests").mkdir(exist_ok=True)
    (project / "tests" / "test_report.py").write_text(
        "# @tests_req SwRS-default-001#S1\ndef test_report():\n    pass\n",
        encoding="utf-8",
    )
    acceptance = project / "tests" / "test_acceptance_report.py"
    acceptance.write_text(
        "# @accepts_req StRS-default-001#S9\ndef test_acceptance():\n    pass\n",
        encoding="utf-8",
    )

    broken = distribution.run(
        "okfreq", "validate", "--json", str(project), cwd=tmp_path, check=False
    )
    payload = json.loads(broken.stdout)
    assert broken.returncode == 1
    assert payload["requirements"] == 2
    assert any("names no declared scenario" in error for error in payload["errors"])
    assert any("W004" in warning for warning in payload["warnings"])

    acceptance.write_text(
        "# @accepts_req StRS-default-001#S1\ndef test_acceptance():\n    pass\n",
        encoding="utf-8",
    )
    healthy = distribution.run("okfreq", "validate", str(project), cwd=tmp_path, check=False)
    generated = distribution.run(
        "okfreq",
        "generate-report",
        "--output-json",
        str(tmp_path / "report.json"),
        "--output-summary-md",
        str(tmp_path / "report.md"),
        str(project),
        cwd=tmp_path,
    )

    assert healthy.returncode == 0
    assert "2 requirements, 0 errors, 0 warnings" in healthy.stdout
    assert generated.returncode == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["format_version"] == 2
    assert report["stakeholder_test_coverage"]["mode"] == "linked-swrs-and-acceptance-paths"
    paths = report["stakeholder_test_coverage"]["paths"]
    assert paths["total"] == 1
    assert paths["accepted"] == 1
    assert "StRS-default-001" in (tmp_path / "report.md").read_text(encoding="utf-8")
