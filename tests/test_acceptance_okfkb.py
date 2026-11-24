"""Acceptance tests for the knowledge-base stakeholder requirement.

The third main path of that requirement, proposing a consolidation for human
review, is an interactive workflow and carries an acceptance exemption instead
of a test.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the isolated install harness is POSIX-only",
)


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
def test_capture_an_immutable_finding(installed_distribution, tmp_path: Path) -> None:
    """A recorded finding keeps its evidence and date, and later operations never rewrite it."""
    distribution = installed_distribution
    distribution.run("okfkb", "init", "knowledge", cwd=tmp_path)

    created = distribution.run(
        "okfkb",
        "new-finding",
        "--title",
        "Stable clock",
        "--confidence",
        "high",
        "--tags",
        "timing",
        "knowledge",
        cwd=tmp_path,
    )

    findings = sorted((tmp_path / "knowledge" / "findings").glob("*.md"))
    assert created.returncode == 0
    assert len(findings) == 1
    finding = findings[0]
    recorded = finding.read_text(encoding="utf-8")
    assert recorded.startswith("---\n")
    assert "type: Finding" in recorded
    assert "title: Stable clock" in recorded
    assert "confidence: high" in recorded
    assert "generated:" in recorded
    assert "## Evidence" in recorded
    assert "## Observation" in recorded
    body = recorded.split("---", 2)[2]
    body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    generated_line = next(line for line in recorded.splitlines() if line.strip().startswith("at:"))

    distribution.run("okfkb", "update", "knowledge", cwd=tmp_path)
    distribution.run("okfkb", "new-finding", "--title", "Later", "knowledge", cwd=tmp_path)

    preserved = finding.read_text(encoding="utf-8")
    assert hashlib.sha256(preserved.split("---", 2)[2].encode("utf-8")).hexdigest() == body_digest
    assert generated_line in preserved
    assert "title: Stable clock" in preserved
    assert "confidence: high" in preserved


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_update_a_knowledge_base_indexes_and_lint(installed_distribution, tmp_path: Path) -> None:
    """Refreshing indexes and lint rebuilds navigation and reports a broken link."""
    distribution = installed_distribution
    distribution.run("okfkb", "init", "knowledge", cwd=tmp_path)
    distribution.run("okfkb", "new-finding", "--title", "Stable clock", "knowledge", cwd=tmp_path)
    finding = next((tmp_path / "knowledge" / "findings").glob("*.md"))
    authored = finding.read_text(encoding="utf-8").rstrip()
    authored_prose = "See [the missing concept](../concepts/absent.md).\n"
    finding.write_text(f"{authored}\n\n{authored_prose}", encoding="utf-8")

    refreshed = distribution.run("okfkb", "update", "knowledge", cwd=tmp_path)
    validated = distribution.run("okfkb", "validate", "knowledge", cwd=tmp_path, check=False)

    assert refreshed.returncode == 0
    finding_index = tmp_path / "knowledge" / "findings" / "index.md"
    assert finding_index.is_file()
    assert "Stable clock" in finding_index.read_text(encoding="utf-8")
    root_index = (tmp_path / "knowledge" / "index.md").read_text(encoding="utf-8")
    assert "findings/" in root_index

    updated = finding.read_text(encoding="utf-8")
    assert authored_prose in updated
    assert "## Observation" in updated
    assert "## Evidence" in updated

    assert validated.returncode == 1
    assert "[W2]" in validated.stderr
    assert "../concepts/absent.md" in validated.stderr
