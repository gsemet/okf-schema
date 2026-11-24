"""Installed-product acceptance paths for testable knowledge-base operations."""

import subprocess
from collections.abc import Callable
from pathlib import Path


# @tests_req SwRS-OKFSCHEMA-OKFKB-001#S1
def test_repeated_search_is_read_only_and_stable(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    run_installed("okfkb", "init", "knowledge")
    run_installed("okfkb", "new-finding", "knowledge", "--title", "Clock drift")
    root = tmp_path / "knowledge"
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    first = run_installed("okfkb", "search", "clock", "knowledge", "--format", "json").stdout
    second = run_installed("okfkb", "search", "clock", "knowledge", "--format", "json").stdout
    assert first == second
    assert "Clock drift" in first
    assert {path: path.read_bytes() for path in root.rglob("*") if path.is_file()} == before


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
# @tests_req SwRS-OKFSCHEMA-OKFKB-003#S1
# @tests_req SwRS-OKFSCHEMA-OKFKB-003#S2
def test_record_finding_preserves_existing_evidence(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    run_installed("okfkb", "init", "knowledge")
    run_installed("okfkb", "new-finding", "knowledge", "--title", "First observation")
    findings = tmp_path / "knowledge" / "findings"
    first = next(findings.glob("*.md"))
    before = first.read_bytes()
    run_installed(
        "okfkb",
        "new-finding",
        "knowledge",
        "--title",
        "Second observation",
        "--context",
        "Observed in a controlled run.",
        "--confidence",
        "high",
    )
    documents = list(findings.glob("*.md"))
    assert len(documents) == 2
    assert first.read_bytes() == before
    second = next(document for document in documents if document != first)
    assert "Observed in a controlled run." in second.read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_update_indexes_and_lints_knowledge(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    run_installed("okfkb", "init", "knowledge")
    run_installed("okfkb", "new-finding", "knowledge", "--title", "Observable finding")
    run_installed("okfkb", "update", "knowledge")
    index = tmp_path / "knowledge" / "findings" / "index.md"
    assert "Observable finding" in index.read_text(encoding="utf-8")
    run_installed("okfkb", "update", "knowledge", "--check")
