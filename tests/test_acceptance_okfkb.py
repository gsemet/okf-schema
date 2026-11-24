"""Acceptance paths for the installed okfkb CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _run(runtime: dict[str, Any], *arguments: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(runtime["bin"] / "okfkb"), *arguments],
        cwd=cwd,
        env=runtime["env"],
        check=False,
        capture_output=True,
        text=True,
    )


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
def test_accepts_immutable_finding_capture(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = tmp_path / "kb"
    assert _run(installed_runtime, "init", str(bundle), cwd=tmp_path).returncode == 0
    created = _run(
        installed_runtime,
        "new-finding",
        str(bundle),
        "--title",
        "Observed export behavior",
        "--description",
        "CSV output remains stable across processes",
        "--context",
        "Observed through the installed command.",
        cwd=tmp_path,
    )
    assert created.returncode == 0, created.stderr
    findings = list((bundle / "findings").glob("*.md"))
    assert len(findings) == 1
    first_finding = findings[0]
    original = first_finding.read_bytes()
    fetched = _run(
        installed_runtime,
        "get",
        first_finding.relative_to(bundle).as_posix(),
        str(bundle),
        "--format",
        "json",
        cwd=tmp_path,
    )
    assert fetched.returncode == 0, fetched.stderr
    fetched_data = json.loads(fetched.stdout)
    assert fetched_data["title"] == "Observed export behavior"
    assert "CSV output remains stable across processes" in original.decode()
    second = _run(
        installed_runtime,
        "new-finding",
        str(bundle),
        "--title",
        "Earlier evidence stays immutable",
        "--description",
        "A subsequent capture must preserve the first finding.",
        cwd=tmp_path,
    )
    assert second.returncode == 0, second.stderr
    assert first_finding.read_bytes() == original
    assert len(list((bundle / "findings").glob("*.md"))) == 2


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_accepts_index_and_lint_update(installed_runtime: dict[str, Any], tmp_path: Path) -> None:
    bundle = tmp_path / "kb"
    assert _run(installed_runtime, "init", str(bundle), cwd=tmp_path).returncode == 0
    created = _run(
        installed_runtime,
        "new-finding",
        str(bundle),
        "--title",
        "Indexable evidence",
        "--description",
        "A finding for the update path.",
        cwd=tmp_path,
    )
    assert created.returncode == 0, created.stderr
    updated = _run(installed_runtime, "update", str(bundle), cwd=tmp_path)
    assert updated.returncode == 0, updated.stderr
    index = bundle / "index.md"
    assert index.is_file()
    assert "findings" in index.read_text(encoding="utf-8").lower()
    checked = _run(installed_runtime, "update", str(bundle), "--check", cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    assert "0 updated" in checked.stdout.lower()
    assert "properly linted" in checked.stdout.lower()
