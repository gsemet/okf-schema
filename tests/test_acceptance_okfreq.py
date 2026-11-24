"""Acceptance tests of the ``okfreq`` capability, run on the installed wheel.

Each test walks one main path of ``StRS-OKFSCHEMA-OKFREQ-001`` through the installed console
script, in a fresh project that uses the mode ``linked-swrs-and-acceptance-paths``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.acceptance_support import InstalledProduct, combined_output

_MODE = "linked-swrs-and-acceptance-paths"


def _requirements(project: Path) -> Path:
    return project / ".agents" / "requirements"


def _identity(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    identifier = re.search(r"^id: (\S+)$", text, flags=re.MULTILINE)
    uuid = re.search(r"^uuid: (\S+)$", text, flags=re.MULTILINE)
    assert identifier and uuid
    return identifier.group(1), uuid.group(1)


def _okfreq(
    product: InstalledProduct, project: Path, *args: str, check: bool = True
) -> tuple[int, str]:
    result = product.run("okfreq", *args, cwd=project, check=check)
    return result.returncode, combined_output(result)


def _initialize_project(product: InstalledProduct, workspace: Path) -> Path:
    project = workspace / "demo"
    project.mkdir()
    _okfreq(product, project, "init", ".")
    config = _requirements(project) / "config.yml"
    text = config.read_text(encoding="utf-8")
    assert "strs_test_coverage_mode: linked-swrs\n" in text
    config.write_text(
        text.replace(
            "strs_test_coverage_mode: linked-swrs\n", f"strs_test_coverage_mode: {_MODE}\n"
        ),
        encoding="utf-8",
    )
    return project


def _new_requirement(
    product: InstalledProduct, project: Path, tier: str, title: str, *extra: str
) -> None:
    description = (
        f"When the {title} runs, the tool SHALL succeed."
        if tier == "swrs"
        else f"The tool SHALL provide {title}."
    )
    _okfreq(
        product,
        project,
        *("new", tier, title, "--description", description, "--project", "demo"),
        *extra,
        *("--path", "."),
    )


def _requirement_path(project: Path, identifier: str) -> Path:
    tier = identifier.split("-", 1)[0].lower()
    return _requirements(project) / "tiers" / tier / f"{identifier}.md"


def _write_markers(project: Path, *, ghost: bool = False) -> None:
    (project / "src").mkdir()
    (project / "tests").mkdir()
    ghost_marker = "\n\n# @implements_req SwRS-default-099\ndef ghost() -> None: ...\n"
    (project / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\ndef export_rows() -> int:\n    return 1\n"
        + (ghost_marker if ghost else ""),
        encoding="utf-8",
    )
    (project / "tests" / "test_export.py").write_text(
        "from src.export import export_rows\n\n\n"
        "# @tests_req SwRS-default-001#S1\n"
        "def test_export_rows() -> None:\n    assert export_rows() == 1\n\n\n"
        "# @tests_req SwRS-default-001#S2\n"
        "def test_export_rows_again() -> None:\n    assert export_rows() == 1\n\n\n"
        "# @accepts_req StRS-default-001#S1\n"
        "def test_export_acceptance() -> None:\n    assert export_rows() == 1\n",
        encoding="utf-8",
    )


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_init_then_new_creates_linked_requirements_with_stable_identity(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """A StRS and a deriving SwRS are created in a new project and keep a stable identity."""
    project = _initialize_project(installed_product, tmp_path)
    assert (_requirements(project) / "config.yml").is_file()

    _new_requirement(
        installed_product, project, "strs", "readable reports", "--user-need", "Review."
    )
    _new_requirement(
        installed_product, project, "swrs", "export rows", "--derives-from", "StRS-default-001"
    )
    stakeholder = _requirement_path(project, "StRS-default-001")
    software = _requirement_path(project, "SwRS-default-001")
    identities = {path: _identity(path) for path in (stakeholder, software)}
    _okfreq(installed_product, project, "lint", ".")
    _okfreq(installed_product, project, "update-coverage", ".")
    code, validated = _okfreq(installed_product, project, "validate", ".", check=False)
    _, indexed = _okfreq(installed_product, project, "index", ".")

    assert [identities[stakeholder][0], identities[software][0]] == [
        "StRS-default-001",
        "SwRS-default-001",
    ]
    assert identities[stakeholder][1] != identities[software][1]
    assert "derives_from:\n- StRS-default-001" in software.read_text(encoding="utf-8")
    assert "scenarios:" in stakeholder.read_text(encoding="utf-8")
    assert "derived_by:\n- SwRS-default-001" in stakeholder.read_text(encoding="utf-8")
    assert {path: _identity(path) for path in identities} == identities
    assert code == 0, validated
    assert "2 requirements, 0 errors" in validated
    assert indexed.split() == ["StRS-default-001", "SwRS-default-001"]


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_trace_reports_markers_and_update_coverage_refreshes_generated_fields(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Markers in source and tests are traced and written to the generated coverage fields."""
    project = _initialize_project(installed_product, tmp_path)
    _new_requirement(
        installed_product, project, "strs", "readable reports", "--user-need", "Review."
    )
    _new_requirement(
        installed_product, project, "swrs", "export rows", "--derives-from", "StRS-default-001"
    )
    _write_markers(project)
    stakeholder = _requirement_path(project, "StRS-default-001")
    software = _requirement_path(project, "SwRS-default-001")
    assert "accepted_in_files" not in stakeholder.read_text(encoding="utf-8")

    _, trace = _okfreq(installed_product, project, "trace", ".")
    _, trace_json = _okfreq(installed_product, project, "trace", ".", "--json")
    stale_code, _ = _okfreq(
        installed_product, project, "update-coverage", ".", "--check", check=False
    )
    _, updated = _okfreq(installed_product, project, "update-coverage", ".")
    fresh_code, _ = _okfreq(
        installed_product, project, "update-coverage", ".", "--check", check=False
    )

    assert "implemented: 1; tested: 1; accepted: 1; missing IDs: 0" in trace
    markers = json.loads(trace_json)
    assert markers["accepted"] == {"StRS-default-001": ["tests/test_export.py"]}
    assert {
        (marker["id"], marker["fragment"], marker["marker"])
        for marker in markers["scenario_markers"]
    } >= {
        ("SwRS-default-001", "S1", "tests"),
        ("SwRS-default-001", "S2", "tests"),
        ("StRS-default-001", "S1", "accepts"),
    }
    assert stale_code == 1
    assert "files updated" in updated
    assert fresh_code == 0
    assert "accepted_in_files:\n- tests/test_export.py" in stakeholder.read_text(encoding="utf-8")
    software_text = software.read_text(encoding="utf-8")
    assert "implemented_in_files:\n- src/export.py" in software_text
    assert "tested_in_files:\n- tests/test_export.py" in software_text
    assert "accepted_in_files" not in software_text


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_validate_and_report_expose_gaps_and_drift_before_delivery(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Validation and the report expose an unaccepted StRS, a coverage gap and a stale marker."""
    project = _initialize_project(installed_product, tmp_path)
    _new_requirement(
        installed_product, project, "strs", "readable reports", "--user-need", "Review."
    )
    _new_requirement(
        installed_product, project, "strs", "importable data", "--user-need", "Import."
    )
    _new_requirement(
        installed_product, project, "swrs", "export rows", "--derives-from", "StRS-default-001"
    )
    _new_requirement(
        installed_product, project, "swrs", "import rows", "--derives-from", "StRS-default-002"
    )
    _write_markers(project, ghost=True)
    _okfreq(installed_product, project, "update-coverage", ".")
    output_json = project / "dist" / "report.json"
    output_markdown = project / "dist" / "report.md"

    code, validated = _okfreq(installed_product, project, "validate", ".", check=False)
    _okfreq(
        installed_product,
        project,
        *("generate-report", ".", "--output-json", str(output_json)),
        *("--output-summary-md", str(output_markdown)),
    )

    assert code == 0, validated
    assert "4 requirements, 0 errors, 1 warnings" in validated
    assert "W004" in validated
    assert "StRS-default-002 has no acceptance test" in validated
    assert "StRS-default-001 has no acceptance test" not in validated
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["stakeholder_test_coverage"]["mode"] == _MODE
    assert report["stakeholder_test_coverage"]["paths"] == {"total": 2, "tested": 0, "accepted": 1}
    assert report["marker_coverage"]["missing_ids"] == ["SwRS-default-099"]
    assert report["marker_coverage"]["missing_tests"] == ["SwRS-default-002"]
    assert report["marker_coverage"]["missing_implementation"] == ["SwRS-default-002"]
    markdown = output_markdown.read_text(encoding="utf-8")
    assert "- StRS paths: tested 0/2, accepted 1/2" in markdown
    assert (
        "| default | StRS | StRS-default-001 | readable reports | ✅ covered | 0/1 | 1/1 ✅ |"
        in markdown
    )
    assert (
        "| default | StRS | StRS-default-002 | importable data | ❌ missing | 0/1 | 0/1 |"
        in markdown
    )
    assert (
        "| default | SwRS | SwRS-default-002 | import rows | ❌ missing | ❌ missing | S1, S2 |"
        in markdown
    )
