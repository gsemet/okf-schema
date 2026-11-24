"""Acceptance tests: the StRS main paths of the okfreq scope, through the installed console scripts.

Each test walks one declared main path in a fresh temporary project with the installed
``okfreq`` command, with no source checkout on ``PYTHONPATH``.
"""

from __future__ import annotations

import json
from pathlib import Path

_BUNDLE = Path(".agents") / "requirements"


def _snapshot(root: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _requirement(tmp_path: Path, tier: str, identifier: str) -> str:
    return (tmp_path / _BUNDLE / "tiers" / tier / f"{identifier}.md").read_text(encoding="utf-8")


def _author_requirements(installed_wheel, tmp_path: Path) -> None:
    installed_wheel.run("okfreq", "init", ".", cwd=tmp_path)
    installed_wheel.run(
        "okfreq",
        "new",
        "strs",
        "Export a report",
        "--description",
        "When a user requests an export, the shop SHALL write a CSV report.",
        "--user-need",
        "Users need their orders in a spreadsheet.",
        "--project",
        "shop",
        "--lifecycle",
        "proposed",
        cwd=tmp_path,
    )
    for title, description in (
        ("Write CSV rows", "When an export runs, the exporter SHALL write one row per order."),
        ("Quote CSV fields", "When a field holds a comma, the exporter SHALL quote the field."),
    ):
        installed_wheel.run(
            "okfreq",
            "new",
            "swrs",
            title,
            "--description",
            description,
            "--project",
            "shop",
            "--derives-from",
            "StRS-default-001",
            "--lifecycle",
            "proposed",
            cwd=tmp_path,
        )


def _write_markers(tmp_path: Path, *tested: str) -> None:
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "src" / "export.py").write_text(
        "# @implements_req SwRS-default-001\n# @implements_req SwRS-default-002\n"
        "def export(orders):\n    return orders\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_export.py").write_text(
        "".join(f"# @tests_req {identifier}\n" for identifier in tested)
        + "def test_export():\n    pass\n",
        encoding="utf-8",
    )


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S1
def test_set_up_a_bundle_and_author_linked_requirements(installed_wheel, tmp_path: Path) -> None:
    """init, new and lint give a valid bundle whose SwRS derive from the StRS."""
    _author_requirements(installed_wheel, tmp_path)
    installed_wheel.run("okfreq", "lint", cwd=tmp_path)

    validated = installed_wheel.run("okfreq", "validate", cwd=tmp_path)
    graph = installed_wheel.run("okfreq", "graph", cwd=tmp_path)
    index = installed_wheel.run("okfreq", "index", cwd=tmp_path)

    assert (tmp_path / _BUNDLE / "config.yml").is_file()
    assert (tmp_path / _BUNDLE / "guidelines" / "requirements.guidelines.md").is_file()
    assert "3 requirements, 0 errors" in validated.stdout
    assert "user_need: Users need their orders in a spreadsheet." in _requirement(
        tmp_path, "strs", "StRS-default-001"
    )
    assert "- StRS-default-001" in _requirement(tmp_path, "swrs", "SwRS-default-002")
    assert "StRS-default-001" in graph.stdout
    assert "SwRS-default-001" in graph.stdout
    assert index.stdout.split() == ["StRS-default-001", "SwRS-default-001", "SwRS-default-002"]


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S2
def test_trace_markers_and_refresh_generated_coverage(installed_wheel, tmp_path: Path) -> None:
    """trace reads the markers; update-coverage previews, then writes the generated fields."""
    _author_requirements(installed_wheel, tmp_path)
    _write_markers(tmp_path, "SwRS-default-001", "SwRS-default-002")

    traced = json.loads(installed_wheel.run("okfreq", "trace", "--json", cwd=tmp_path).stdout)
    before = _snapshot(tmp_path / _BUNDLE)
    preview = installed_wheel.run("okfreq", "update-coverage", "--check", cwd=tmp_path, check=False)
    assert preview.returncode == 1
    assert _snapshot(tmp_path / _BUNDLE) == before

    installed_wheel.run("okfreq", "update-coverage", cwd=tmp_path)
    installed_wheel.run("okfreq", "update-coverage", "--check", cwd=tmp_path)

    assert traced["implemented"]["SwRS-default-001"] == ["src/export.py"]
    assert traced["tested"]["SwRS-default-002"] == ["tests/test_export.py"]
    swrs = _requirement(tmp_path, "swrs", "SwRS-default-001")
    assert "implemented_in_files:\n- src/export.py\n" in swrs
    assert "tested_in_files:\n- tests/test_export.py\n" in swrs
    strs = _requirement(tmp_path, "strs", "StRS-default-001")
    assert "derived_by:\n- SwRS-default-001\n- SwRS-default-002\n" in strs
    assert "When a user requests an export, the shop SHALL write a CSV report." in strs


# @accepts_req StRS-OKFSCHEMA-OKFREQ-001#S3
def test_audit_the_requirements_base_with_validate_and_a_report(
    installed_wheel, tmp_path: Path
) -> None:
    """validate and generate-report show the coverage gap without changing the requirements."""
    _author_requirements(installed_wheel, tmp_path)
    _write_markers(tmp_path, "SwRS-default-001")
    installed_wheel.run("okfreq", "update-coverage", cwd=tmp_path)
    before = _snapshot(tmp_path / _BUNDLE)

    validated = json.loads(installed_wheel.run("okfreq", "validate", "--json", cwd=tmp_path).stdout)
    installed_wheel.run(
        "okfreq",
        "generate-report",
        "--output-json",
        "dist/report.json",
        "--output-summary-md",
        "dist/report.md",
        cwd=tmp_path,
    )
    report = json.loads((tmp_path / "dist" / "report.json").read_text(encoding="utf-8"))
    summary = (tmp_path / "dist" / "report.md").read_text(encoding="utf-8")

    assert validated["errors"] == []
    assert report["totals"]["requirements"] == 3
    assert report["totals"]["tested"] == 1
    assert report["marker_coverage"]["missing_tests"] == ["SwRS-default-002"]
    assert "SwRS test-link coverage: 50.0% (1/2)" in summary
    assert _snapshot(tmp_path / _BUNDLE) == before
