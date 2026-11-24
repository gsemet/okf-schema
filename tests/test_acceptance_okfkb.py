"""Acceptance tests: the StRS main paths of the okfkb scope, through the installed console scripts.

Each test walks one declared main path in a fresh temporary project with the installed
``okfkb`` command, with no source checkout on ``PYTHONPATH``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def _snapshot(root: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _body(path: Path) -> str:
    """Return the authored body, without the generated Links section."""
    body = path.read_text(encoding="utf-8").split("\n---\n", 1)[1]
    return body.split("<!-- okf:links:start -->", 1)[0].rstrip("\n")


def _record(installed_wheel, tmp_path: Path, title: str, *options: str) -> Path:
    result = installed_wheel.run(
        "okfkb", "new-finding", "knowledge", "--title", title, *options, cwd=tmp_path
    )
    created = re.search(r"Created (\S+\.md)", result.stdout)
    assert created, result.stdout
    return tmp_path / created.group(1)


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
def test_capture_an_immutable_finding(installed_wheel, tmp_path: Path) -> None:
    """A recorded Finding keeps its body through maintenance and later Findings."""
    installed_wheel.run("okfkb", "init", "knowledge", cwd=tmp_path)
    finding = _record(
        installed_wheel,
        tmp_path,
        "PLL lock time",
        "--confidence",
        "medium",
        "--context",
        "Bench run at 25 C",
        "--tags",
        "pll,timing",
    )
    assert finding.parent == tmp_path / "knowledge" / "findings"
    finding.write_text(
        finding.read_text(encoding="utf-8").replace(
            "<!-- Describe what you observed. -->", "The PLL locked after 42 us."
        ),
        encoding="utf-8",
    )
    installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    body = _body(finding)

    _record(installed_wheel, tmp_path, "PLL cold wait", "--tags", "pll")
    installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    fetched = installed_wheel.run(
        "okfkb", "get", finding.stem, "knowledge", "--format", "json", cwd=tmp_path
    )
    installed_wheel.run("okfkb", "validate", "knowledge", cwd=tmp_path)

    assert _body(finding) == body
    assert "The PLL locked after 42 us." in body
    node = json.loads(fetched.stdout)
    assert node["type"] == "Finding"
    assert node["confidence"] == "medium"
    assert node["tags"] == ["pll", "timing"]
    assert "The PLL locked after 42 us." in node["body"]


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_update_a_knowledge_bases_indexes_and_lint(installed_wheel, tmp_path: Path) -> None:
    """update writes the tier indexes and normalized frontmatter; authored text stays."""
    installed_wheel.run("okfkb", "init", "knowledge", cwd=tmp_path)
    concept = tmp_path / "knowledge" / "concepts" / "cache.md"
    concept.write_text(
        "---\ntype: Concept\ntitle: Cache\ndescription: How the cache works\n"
        "generated: {at: '2026-11-24T08:00:00Z'}\ntags:\n  - storage\n  - hot\n---\n\n"
        "# Cache\n\nAuthored explanation.\n",
        encoding="utf-8",
    )
    _record(installed_wheel, tmp_path, "Cache miss rate", "--tags", "storage")

    result = installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    assert "Index:" in result.stdout
    assert "Linted:" in result.stdout
    after = _snapshot(tmp_path / "knowledge")
    installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    assert _snapshot(tmp_path / "knowledge") == after
    installed_wheel.run("okfkb", "validate", "knowledge", cwd=tmp_path)

    assert "tags: [storage, hot]" in concept.read_text(encoding="utf-8")
    assert concept.read_text(encoding="utf-8").endswith("# Cache\n\nAuthored explanation.\n")
    assert "Cache" in (tmp_path / "knowledge" / "concepts" / "index.md").read_text(encoding="utf-8")
    assert "Cache miss rate" in (tmp_path / "knowledge" / "findings" / "index.md").read_text(
        encoding="utf-8"
    )


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S3
def test_propose_a_consolidation_for_human_review(installed_wheel, tmp_path: Path) -> None:
    """The distill skill proposes before writing; a confirmed Concept keeps its evidence links."""
    installed_wheel.run("okfkb", "init", "knowledge", cwd=tmp_path)
    installed_wheel.run("okfkb", "install-skills", "skills", cwd=tmp_path)
    distill = (tmp_path / "skills" / "okfkb-distill" / "SKILL.md").read_text(encoding="utf-8")
    assert "It proposes changes; a human confirms" in distill
    assert "Ask before every write" in distill
    assert "Never edit or delete a Finding body" in distill

    first = _record(installed_wheel, tmp_path, "PLL lock time", "--tags", "pll")
    second = _record(installed_wheel, tmp_path, "PLL cold wait", "--tags", "pll")
    installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    bodies = {path: _body(path) for path in (first, second)}
    candidates = installed_wheel.run(
        "okfkb", "query", "type:finding tag:pll", "knowledge", "--format", "paths", cwd=tmp_path
    )
    assert set(candidates.stdout.split()) == {
        f"findings/{first.name}",
        f"findings/{second.name}",
    }

    sources = ", ".join(f"findings/{path.stem}" for path in (first, second))
    (tmp_path / "knowledge" / "structures" / "pll-start-up.md").write_text(
        "---\ntype: Structure\ntitle: PLL start-up\ndescription: How the PLL starts\n"
        f"generated: {{at: '2026-11-24T08:00:00Z'}}\nderived_from: [{sources}]\n---\n\n"
        "# PLL start-up\n\nConsolidated after human review.\n",
        encoding="utf-8",
    )
    installed_wheel.run("okfkb", "update", "knowledge", cwd=tmp_path)
    installed_wheel.run("okfkb", "validate", "knowledge", "--check-links", cwd=tmp_path)
    fetched = installed_wheel.run(
        "okfkb", "get", first.stem, "knowledge", "--format", "frontmatter", cwd=tmp_path
    )

    assert "structures/pll-start-up" in fetched.stdout
    assert {path: _body(path) for path in (first, second)} == bodies
