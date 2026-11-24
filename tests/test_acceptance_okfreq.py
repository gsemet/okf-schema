"""Installed-product acceptance paths for requirements management."""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path


def create_requirements(
    tmp_path: Path, run: Callable[..., subprocess.CompletedProcess[str]]
) -> tuple[Path, Path]:
    run("okfreq", "init", ".")
    config = tmp_path / ".agents" / "requirements" / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
        ),
        encoding="utf-8",
    )
    run(
        "okfreq",
        "new",
        "strs",
        "Export",
        "--description",
        "The tool SHALL export reports.",
        "--project",
        "demo",
        "--user-need",
        "Users need portable reports.",
        "--path",
        ".agents/requirements",
    )
    run(
        "okfreq",
        "new",
        "swrs",
        "Write CSV",
        "--description",
        "The tool SHALL write CSV.",
        "--project",
        "demo",
        "--derives-from",
        "StRS-default-001",
        "--path",
        ".agents/requirements",
    )
    return (
        tmp_path / ".agents" / "requirements" / "tiers" / "strs" / "StRS-default-001.md",
        tmp_path / ".agents" / "requirements" / "tiers" / "swrs" / "SwRS-default-001.md",
    )


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_author_and_validate_derived_requirements(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    strs, swrs = create_requirements(tmp_path, run_installed)
    graph = json.loads(run_installed("okfreq", "graph", ".agents/requirements", "--json").stdout)
    assert graph["derived_by"]["StRS-default-001"] == ["SwRS-default-001"]
    before = (strs.read_bytes(), swrs.read_bytes())
    run_installed("okfreq", "validate", ".agents/requirements")
    assert (strs.read_bytes(), swrs.read_bytes()) == before


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S1
def test_trace_refresh_and_report_coverage(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    strs, swrs = create_requirements(tmp_path, run_installed)
    run_installed("okfreq", "install-skills", "skills")
    instructions = (tmp_path / "skills" / "okfreq" / "references" / "operations.md").read_text(
        encoding="utf-8"
    )
    assert "okfreq trace" in instructions and "okfreq generate-report" in instructions
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_export.py").write_text(
        "# @tests_req SwRS-default-001#S1\n# @tests_req SwRS-default-001#S2\n"
        "# @accepts_req StRS-default-001#S1\n",
        encoding="utf-8",
    )
    trace = json.loads(run_installed("okfreq", "trace", ".agents/requirements", "--json").stdout)
    assert not trace["missing_ids"]
    run_installed("okfreq", "update-coverage", ".agents/requirements")
    assert "src/export.py" in swrs.read_text(encoding="utf-8")
    assert "tests/test_export.py" in strs.read_text(encoding="utf-8")
    run_installed(
        "okfreq",
        "generate-report",
        ".agents/requirements",
        "--output-json",
        "report.json",
        "--output-summary-md",
        "report.md",
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["stakeholder_test_coverage"]["covered"] == 1
    assert "StRS-default-001" in (tmp_path / "report.md").read_text(encoding="utf-8")


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S2
def test_installed_guidance_and_diagnostics_distinguish_coverage_gaps(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    create_requirements(tmp_path, run_installed)
    run_installed("okfreq", "install-skills", "skills")
    instructions = (tmp_path / "skills" / "okfreq" / "references" / "operations.md").read_text(
        encoding="utf-8"
    )
    assert "W15" in instructions and "E10" in instructions
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "concept.schema.yaml").write_text(
        "type: object\nproperties:\n"
        "  local:\n    type: string\n"
        "    x-okf-link: {resolution: document-relative, syntax: plain}\n"
        "  source:\n    type: string\n"
        "    x-okf-link: {resolution: project-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    (tmp_path / "concept.md").write_text(
        "---\ntype: concept\nlocal: missing.md\nsource: src/missing.py\n---\n",
        encoding="utf-8",
    )
    result = run_installed(
        "okf-schema",
        "validate-md",
        "--input",
        "concept.md",
        "--schemas-dir",
        "schemas",
        "--check-links",
        check=False,
    )
    assert result.returncode != 0
    assert "E10" in result.stdout + result.stderr and "W15" in result.stdout + result.stderr
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_export.py").write_text(
        "# @tests_req SwRS-default-999#S1\n", encoding="utf-8"
    )
    trace = json.loads(run_installed("okfreq", "trace", ".agents/requirements", "--json").stdout)
    assert "SwRS-default-999" in trace["missing_ids"]
    run_installed("okfreq", "generate-report", ".agents/requirements", "--output-json", "gaps.json")
    report = json.loads((tmp_path / "gaps.json").read_text(encoding="utf-8"))
    assert report["totals"]["tested"] == 0
    assert report["execution_evidence"]["status"] == "not_collected"


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_invalid_requirement_reports_structural_error(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    _, swrs = create_requirements(tmp_path, run_installed)
    run_installed(
        "okfreq", "generate-report", ".agents/requirements", "--output-json", "audit.json"
    )
    report = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert len(report["requirements"]) == 2
    swrs.write_text(
        swrs.read_text(encoding="utf-8").replace(
            "derives_from:\n- StRS-default-001", "derives_from:\n- StRS-default-999"
        ),
        encoding="utf-8",
    )
    before = swrs.read_bytes()
    result = run_installed("okfreq", "validate", ".agents/requirements", "--json", check=False)
    assert result.returncode != 0
    assert "StRS-default-999" in result.stdout
    assert swrs.read_bytes() == before
