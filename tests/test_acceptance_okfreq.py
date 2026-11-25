"""Installed-wheel acceptance tests for okfreq StRS main paths."""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import InstalledWheelEnv


def _bootstrap_okfreq_project(project: Path, env: InstalledWheelEnv) -> Path:
    req_root = project / "requirements"
    env.run("okfreq", "init", str(req_root), cwd=project)
    config_path = req_root / "config.yml"
    config_text = config_path.read_text(encoding="utf-8").replace(
        "strs_test_coverage_mode: linked-swrs",
        "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
    )
    config_path.write_text(config_text, encoding="utf-8")
    env.run(
        "okfreq",
        "new",
        "strs",
        "Export data",
        "--path",
        str(req_root),
        "--project",
        "demo",
        "--description",
        "The tool SHALL export user data.",
        "--user-need",
        "Users need portable exports.",
        cwd=project,
    )
    env.run(
        "okfreq",
        "new",
        "swrs",
        "Write CSV export",
        "--path",
        str(req_root),
        "--project",
        "demo",
        "--description",
        "When export runs, the service SHALL emit CSV.",
        "--derives-from",
        "StRS-default-001",
        cwd=project,
    )
    return req_root


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_accepts_okfreq_001_s1_setup_bundle_and_author_linked_requirements(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okfreq initializes a bundle and authors linked StRS and SwRS documents."""
    project = tmp_path / "authoring"
    project.mkdir()
    req_root = _bootstrap_okfreq_project(project, installed_wheel_env)

    strs_doc = req_root / "tiers" / "strs" / "StRS-default-001.md"
    swrs_doc = req_root / "tiers" / "swrs" / "SwRS-default-001.md"
    assert strs_doc.is_file()
    assert swrs_doc.is_file()
    assert "StRS-default-001" in swrs_doc.read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_accepts_okfreq_001_s2_trace_markers_and_refresh_generated_coverage(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okfreq traces source/test/acceptance markers and updates coverage fields."""
    project = tmp_path / "trace-coverage"
    project.mkdir()
    req_root = _bootstrap_okfreq_project(project, installed_wheel_env)

    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    (project / "tests" / "test_export.py").write_text(
        "# @tests_req SwRS-default-001#S1\n# @tests_req SwRS-default-001#S2\n"
        "# @tests_req StRS-default-001#S1\n# @accepts_req StRS-default-001#S1\n",
        encoding="utf-8",
    )

    trace_res = installed_wheel_env.run("okfreq", "trace", str(req_root), "--json", cwd=project)
    trace_payload = json.loads(trace_res.stdout)
    assert trace_payload["implemented"]["SwRS-default-001"] == ["src/export.py"]
    assert trace_payload["accepted"]["StRS-default-001"] == ["tests/test_export.py"]

    installed_wheel_env.run("okfreq", "update-coverage", str(req_root), cwd=project)
    installed_wheel_env.run("okfreq", "update-coverage", str(req_root), "--check", cwd=project)
    strs_text = (req_root / "tiers" / "strs" / "StRS-default-001.md").read_text(encoding="utf-8")
    assert "accepted_in_files:" in strs_text


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_accepts_okfreq_001_s3_audit_requirements_with_validate_and_report(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okfreq validates the bundle and emits schema-valid JSON and Markdown reports."""
    project = tmp_path / "audit-report"
    project.mkdir()
    req_root = _bootstrap_okfreq_project(project, installed_wheel_env)

    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    (project / "tests" / "test_export.py").write_text(
        "# @tests_req SwRS-default-001#S1\n# @tests_req SwRS-default-001#S2\n"
        "# @tests_req StRS-default-001#S1\n# @accepts_req StRS-default-001#S1\n",
        encoding="utf-8",
    )
    installed_wheel_env.run("okfreq", "update-coverage", str(req_root), cwd=project)
    installed_wheel_env.run(
        "okfreq",
        "validate",
        str(req_root),
        "--check-links",
        "--project-root",
        str(project),
        cwd=project,
    )
    json_out = project / "dist" / "report.json"
    md_out = project / "dist" / "report.md"
    json_out.parent.mkdir()
    installed_wheel_env.run(
        "okfreq",
        "generate-report",
        str(req_root),
        "--output-json",
        str(json_out),
        "--output-summary-md",
        str(md_out),
        cwd=project,
    )
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["format_version"] == 2
    assert payload["stakeholder_test_coverage"]["covered"] == 1
    assert "StRS paths: tested 1/1, accepted 1/1" in md_out.read_text(encoding="utf-8")
