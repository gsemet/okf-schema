"""Installed-wheel acceptance tests for okfkb StRS main paths."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import InstalledWheelEnv


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
def test_accepts_okfkb_001_s1_capture_immutable_finding(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okfkb initializes a KB, captures an immutable finding, and validates cleanly."""
    kb = tmp_path / "kb"
    installed_wheel_env.run("okfkb", "init", str(kb), cwd=tmp_path)
    installed_wheel_env.run(
        "okfkb",
        "new-finding",
        str(kb),
        "--title",
        "Cache invalidation race",
        "--description",
        "Concurrent writes drop the latest key under load.",
        cwd=tmp_path,
    )
    findings = list((kb / "findings").glob("*.md"))
    finding_docs = [f for f in findings if f.name != "index.md"]
    assert len(finding_docs) == 1
    assert "Cache invalidation race" in finding_docs[0].read_text(encoding="utf-8")
    installed_wheel_env.run("okf-schema", "validate", "--path", str(kb), cwd=tmp_path)


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_accepts_okfkb_001_s2_update_kb_indexes_and_lint(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okfkb update refreshes generated indexes and validates cleanly."""
    kb = tmp_path / "kb-update"
    installed_wheel_env.run("okfkb", "init", str(kb), cwd=tmp_path)
    installed_wheel_env.run(
        "okfkb",
        "new-finding",
        str(kb),
        "--title",
        "Retry backoff ceiling",
        "--description",
        "Exponential backoff caps at 30 seconds.",
        cwd=tmp_path,
    )
    installed_wheel_env.run("okfkb", "update", str(kb), cwd=tmp_path)
    installed_wheel_env.run("okfkb", "validate", str(kb), cwd=tmp_path)
    findings_index = (kb / "findings" / "index.md").read_text(encoding="utf-8")
    assert "Retry backoff ceiling" in findings_index
