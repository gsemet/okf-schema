"""Verify okfreq acceptance-paths documentation examples and link targets."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from okf_schema.okfreq.core import (
    create_requirement,
    initialize_bundle,
    report,
    validate_requirements,
    write_markdown_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DOC = REPO_ROOT / "docs/source/reference/okfreq-acceptance-paths.md"
EXPLANATION_DOC = REPO_ROOT / "docs/source/explanation/okfreq-acceptance-paths.md"
FRONTMATTER_DOC = REPO_ROOT / "docs/source/reference/okfreq-frontmatter.md"


def _captioned_blocks(path: Path) -> dict[str, str]:
    """Extract `{caption: code}` from MyST `{code-block}` directives."""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"```\{code-block\}\s+\w+\n:caption:\s*(.+?)\n\n(.*?)```",
        flags=re.DOTALL,
    )
    return {match.group(1).strip(): match.group(2).strip() for match in pattern.finditer(text)}


def _setup_demo_bundle(tmp_path: Path) -> Path:
    bundle, _ = initialize_bundle(tmp_path / "requirements")
    config = yaml.safe_load((bundle / "config.yml").read_text(encoding="utf-8"))
    config["strs_test_coverage_mode"] = "linked-swrs-and-acceptance-paths"
    config["scopes"] = {
        "demo": {
            "id_token": "DEMO",
            "folder": "demo",
            "source_dirs": ["src"],
            "test_dirs": ["tests"],
        }
    }
    (bundle / "config.yml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    return bundle


def _write_marker_files(project_root: Path, block: str) -> None:
    current: Path | None = None
    lines_by_file: dict[Path, list[str]] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("# tests/") or stripped.startswith("# src/"):
            current = project_root / stripped.removeprefix("# ").strip()
            lines_by_file.setdefault(current, [])
        elif current is not None and stripped:
            lines_by_file[current].append(line)
    for target, lines in lines_by_file.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    _, fm_raw, body = text.split("---", 2)
    fm = yaml.safe_load(fm_raw)
    fm.update(updates)
    rendered = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
    path.write_text(rendered, encoding="utf-8")


def test_w003_and_w004_doc_labels_exist() -> None:
    """W003 and W004 documentation anchor labels exist in Sphinx sources."""
    assert "(okfreq-declared-scenarios)=" in FRONTMATTER_DOC.read_text(encoding="utf-8")
    assert "(okfreq-execution-cost)=" in EXPLANATION_DOC.read_text(encoding="utf-8")


def test_worked_example_1_matches_runtime(tmp_path: Path) -> None:
    """Example 1 in okfreq-acceptance-paths.md matches real okfreq output."""
    blocks = _captioned_blocks(REFERENCE_DOC)
    fm = yaml.safe_load(blocks["Example 1 StRS frontmatter"])
    expected_json = json.loads(blocks["Example 1 JSON excerpt"])
    expected_row = blocks["Example 1 Markdown row"]

    bundle = _setup_demo_bundle(tmp_path)
    strs_path = create_requirement(
        bundle,
        "StRS",
        fm["title"],
        "The capability SHALL export reports.",
        project="demo",
        scope="demo",
        origin="native",
        user_need="Users need exported reports.",
        lifecycle=fm["req_lifecycle"],
    )
    _update_frontmatter(strs_path, {"scenarios": fm["scenarios"]})
    swrs_path = create_requirement(
        bundle,
        "SwRS",
        "Export helper",
        "The service SHALL export.",
        project="demo",
        scope="demo",
        origin="native",
        derives_from=[fm["id"]],
        lifecycle="proposed",
    )
    _update_frontmatter(swrs_path, {"scenarios": [{"id": "S1", "title": "Nominal"}]})
    (tmp_path / "src/export.py").write_text("# @implements_req SwRS-DEMO-001\n", encoding="utf-8")
    _write_marker_files(tmp_path, blocks["Example 1 test markers"])
    with (tmp_path / "tests/test_export_fast.py").open("a", encoding="utf-8") as handle:
        handle.write("# @tests_req SwRS-DEMO-001#S1\n")

    assert validate_requirements(bundle) == []
    rep = report(bundle)
    strs_rec = next(r for r in rep["requirements"] if r["id"] == fm["id"])
    cov = strs_rec["stakeholder_test_coverage"]
    for key, value in expected_json.items():
        assert cov[key] == value

    md_path = tmp_path / "report.md"
    write_markdown_report(bundle, md_path)
    assert expected_row in md_path.read_text(encoding="utf-8")


def test_worked_example_2_matches_runtime(tmp_path: Path) -> None:
    """Example 2 in okfreq-acceptance-paths.md matches real okfreq output."""
    blocks = _captioned_blocks(REFERENCE_DOC)
    fm = yaml.safe_load(blocks["Example 2 SwRS frontmatter"])
    expected_json = json.loads(blocks["Example 2 JSON excerpt"])
    expected_row = blocks["Example 2 Markdown row"]

    bundle = _setup_demo_bundle(tmp_path)
    create_requirement(
        bundle,
        "StRS",
        "Export reports",
        "The capability SHALL export reports.",
        project="demo",
        scope="demo",
        origin="native",
        user_need="Users need exported reports.",
        lifecycle="proposed",
    )
    swrs_path = create_requirement(
        bundle,
        "SwRS",
        fm["title"],
        "The service SHALL format CSV output.",
        project="demo",
        scope="demo",
        origin="native",
        derives_from=fm["derives_from"],
        lifecycle=fm["req_lifecycle"],
    )
    _update_frontmatter(swrs_path, {"scenarios": fm["scenarios"]})
    (tmp_path / "src/export.py").write_text(f"# @implements_req {fm['id']}\n", encoding="utf-8")
    _write_marker_files(tmp_path, blocks["Example 2 test markers"])

    rep = report(bundle)
    swrs_rec = next(r for r in rep["requirements"] if r["id"] == fm["id"])
    assert swrs_rec["tests"] == expected_json["tests"]
    assert swrs_rec["transitions"] == expected_json["transitions"]

    md_path = tmp_path / "report.md"
    write_markdown_report(bundle, md_path)
    assert expected_row in md_path.read_text(encoding="utf-8")


def test_worked_example_3_matches_runtime(tmp_path: Path) -> None:
    """Example 3 in okfreq-acceptance-paths.md matches real okfreq output."""
    blocks = _captioned_blocks(REFERENCE_DOC)
    expected_json = json.loads(blocks["Example 3 JSON excerpt"])
    expected_row = blocks["Example 3 Markdown row"]

    bundle = _setup_demo_bundle(tmp_path)
    create_requirement(
        bundle,
        "StRS",
        "First",
        "First StRS SHALL work.",
        project="demo",
        scope="demo",
        origin="native",
        user_need="First need.",
        lifecycle="proposed",
    )
    strs2_path = create_requirement(
        bundle,
        "StRS",
        "Inspect report summary",
        "The capability SHALL show summary counts.",
        project="demo",
        scope="demo",
        origin="native",
        user_need="Users need summary counts.",
        lifecycle="proposed",
    )
    # Remove scenarios: and write body matching Example 3
    text = strs2_path.read_text(encoding="utf-8")
    _, fm_raw, _ = text.split("---", 2)
    fm = yaml.safe_load(fm_raw)
    fm.pop("scenarios", None)
    body = "\n\n## Inspect report summary\n\n### Main paths\n\n#### Path 1: Print summary counts\n"
    strs2_path.write_text(f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}", encoding="utf-8")
    _write_marker_files(tmp_path, blocks["Example 3 test markers"])

    findings = validate_requirements(bundle)
    assert any(f.startswith("W003 ") and "StRS-DEMO-002" in f for f in findings)
    assert any(f.startswith("W004 ") and "StRS-DEMO-002" in f for f in findings)

    rep = report(bundle)
    strs_rec = next(r for r in rep["requirements"] if r["id"] == "StRS-DEMO-002")
    cov = strs_rec["stakeholder_test_coverage"]
    for key, value in expected_json.items():
        assert cov[key] == value

    md_path = tmp_path / "report.md"
    write_markdown_report(bundle, md_path)
    assert expected_row in md_path.read_text(encoding="utf-8")
