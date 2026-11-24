"""Acceptance paths for the installed okfreq CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _run(runtime: dict[str, Any], *arguments: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(runtime["bin"] / "okfreq"), *arguments],
        cwd=cwd,
        env=runtime["env"],
        check=False,
        capture_output=True,
        text=True,
    )


def _bundle(runtime: dict[str, Any], tmp_path: Path) -> Path:
    bundle = tmp_path / "requirements"
    completed = _run(runtime, "init", str(bundle), cwd=tmp_path)
    assert completed.returncode == 0, completed.stderr
    return bundle


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_accepts_bundle_setup_and_linked_authoring(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = _bundle(installed_runtime, tmp_path)
    stakeholder = _run(
        installed_runtime,
        "new",
        "strs",
        "Readable reports",
        "--description",
        "Users SHALL review readable reports.",
        "--project",
        "demo",
        "--user-need",
        "Review outcomes clearly.",
        "--path",
        str(bundle),
        cwd=tmp_path,
    )
    assert stakeholder.returncode == 0, stakeholder.stderr
    stakeholder_file = bundle / "tiers/strs/StRS-default-001.md"
    assert stakeholder_file.is_file()
    software = _run(
        installed_runtime,
        "new",
        "swrs",
        "Export rows",
        "--description",
        "The tool SHALL export selected rows.",
        "--project",
        "demo",
        "--derives-from",
        "StRS-default-001",
        "--path",
        str(bundle),
        cwd=tmp_path,
    )
    assert software.returncode == 0, software.stderr
    software_file = bundle / "tiers/swrs/SwRS-default-001.md"
    stakeholder_text = stakeholder_file.read_text(encoding="utf-8")
    software_text = software_file.read_text(encoding="utf-8")
    assert "user_need: Review outcomes clearly." in stakeholder_text
    assert "derives_from:\n- StRS-default-001" in software_text
    assert "### Normative behavior" in software_text


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_accepts_trace_and_coverage_refresh(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = _bundle(installed_runtime, tmp_path)
    created = _run(
        installed_runtime,
        "new",
        "strs",
        "Trace evidence",
        "--description",
        "Users SHALL inspect linked evidence.",
        "--project",
        "demo",
        "--path",
        str(bundle),
        cwd=tmp_path,
    )
    assert created.returncode == 0, created.stderr
    created = _run(
        installed_runtime,
        "new",
        "swrs",
        "Expose marker evidence",
        "--description",
        "The tool SHALL expose marker evidence.",
        "--project",
        "demo",
        "--derives-from",
        "StRS-default-001",
        "--path",
        str(bundle),
        cwd=tmp_path,
    )
    assert created.returncode == 0, created.stderr
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src/feature.py").write_text(
        "# @implements_req SwRS-default-001\n", encoding="utf-8"
    )
    (tmp_path / "tests/test_feature.py").write_text(
        "# @tests_req SwRS-default-001\n", encoding="utf-8"
    )
    traced = _run(installed_runtime, "trace", str(bundle), "--json", cwd=tmp_path)
    assert traced.returncode == 0, traced.stderr
    trace = json.loads(traced.stdout)
    assert trace["implemented"]["SwRS-default-001"] == ["src/feature.py"]
    assert trace["tested"]["SwRS-default-001"] == ["tests/test_feature.py"]
    assert trace["missing_ids"] == []
    refreshed = _run(installed_runtime, "update-coverage", str(bundle), cwd=tmp_path)
    assert refreshed.returncode == 0, refreshed.stderr
    software = bundle / "tiers/swrs/SwRS-default-001.md"
    assert "implemented_in_files:\n- src/feature.py" in software.read_text(encoding="utf-8")
    assert "tested_in_files:\n- tests/test_feature.py" in software.read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_accepts_validation_and_report(installed_runtime: dict[str, Any], tmp_path: Path) -> None:
    bundle = _bundle(installed_runtime, tmp_path)
    validated = _run(installed_runtime, "validate", str(bundle), cwd=tmp_path)
    assert validated.returncode == 0, validated.stderr
    assert "0 errors" in validated.stdout
    report = tmp_path / "report.json"
    generated = _run(
        installed_runtime,
        "generate-report",
        str(bundle),
        "--output-json",
        str(report),
        cwd=tmp_path,
    )
    assert generated.returncode == 0, generated.stderr
    payload = json.loads(report.read_text())
    assert payload["format_version"] == 2
    assert payload["totals"]["requirements"] == 0
    assert payload["execution_evidence"]["status"] == "not_collected"
    schema = json.loads(report.with_suffix(".schema.json").read_text())
    assert schema["properties"]["format_version"]["const"] == 2
