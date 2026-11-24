"""Acceptance tests of the ``okfkb`` capability, run on the installed wheel.

Each test walks one main path of ``StRS-OKFSCHEMA-OKFKB-001`` through the installed console
script. Path S3 is an interactive consolidation reviewed by a human; it has no command to run
and the StRS carries the matching acceptance exemption.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from tests.acceptance_support import InstalledProduct, combined_output

_CONCEPT = textwrap.dedent(
    """\
    ---
    type: Concept
    title: Fixed wait is shorter than the observed cold PLL lock time
    description: The fixed wait does not cover the captured timing.
    generated:
      at: '2026-10-19T12:00:00Z'
      by: human:acceptance
    kb_status: active
    tags: [boot, pll]
    derived_from: [findings/{pll}, findings/{wait}]
    ---

    # Fixed wait and observed cold PLL timing

    The captured cold lock time is 800 microseconds.
    """
)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _findings(bundle: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted((bundle / "findings").glob("*.md"))
        if path.name != "index.md"
    }


def _body_without_links(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    return body.split("<!-- okf:links:start -->", 1)[0].rstrip("\n")


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S1
def test_new_finding_stores_a_new_evidence_file_and_leaves_earlier_findings_unchanged(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Each recorded finding is a new file; recording a later one never touches an earlier one."""
    installed_product.run("okfkb", "init", "knowledge", cwd=tmp_path, check=True)
    bundle = tmp_path / "knowledge"
    assert _findings(bundle) == {}

    first = installed_product.run(
        "okfkb",
        *("new-finding", str(bundle), "--title", "PLL lock time", "--confidence", "medium"),
        *("--tags", "pll,timing"),
        cwd=tmp_path,
        check=True,
    )
    after_first = _findings(bundle)
    second = installed_product.run(
        "okfkb",
        *("new-finding", str(bundle), "--title", "Bootloader wait", "--tags", "boot"),
        cwd=tmp_path,
        check=True,
    )
    after_second = _findings(bundle)

    assert len(after_first) == 1
    (first_name, first_bytes), *_ = after_first.items()
    assert first_name.endswith("-pll-lock-time.md")
    assert f"findings/{first_name}" in first.stdout
    assert len(after_second) == 2
    assert after_second[first_name] == first_bytes
    (second_name,) = set(after_second) - {first_name}
    assert second_name.endswith("-bootloader-wait.md")
    assert f"findings/{second_name}" in second.stdout
    stored = first_bytes.decode("utf-8")
    assert "type: Finding" in stored
    assert "title: PLL lock time" in stored
    assert "confidence: medium" in stored


# @accepts_req StRS-OKFSCHEMA-OKFKB-001#S2
def test_update_regenerates_indexes_and_derived_links_and_lint_does_not_rewrite_knowledge(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Update refreshes indexes and derived links; validation reports issues and writes nothing."""
    installed_product.run("okfkb", "init", "knowledge", cwd=tmp_path, check=True)
    bundle = tmp_path / "knowledge"
    for title in ("PLL lock time", "Bootloader wait"):
        installed_product.run(
            "okfkb", "new-finding", str(bundle), "--title", title, cwd=tmp_path, check=True
        )
    stems = [path.stem for path in (bundle / "findings").glob("*.md")]
    pll = next(stem for stem in stems if stem.endswith("pll-lock-time"))
    wait = next(stem for stem in stems if stem.endswith("bootloader-wait"))
    concept = bundle / "concepts" / "cold-pll-wait.md"
    concept.write_text(_CONCEPT.format(pll=pll, wait=wait), encoding="utf-8")
    authored_bodies = {
        path: _body_without_links(path)
        for path in (bundle / "findings" / f"{pll}.md", bundle / "findings" / f"{wait}.md", concept)
    }
    before = _snapshot(tmp_path)

    stale = installed_product.run("okfkb", "validate", str(bundle), cwd=tmp_path)

    assert stale.returncode == 1, combined_output(stale)
    assert "derives_to" in combined_output(stale)
    assert "okfkb update" in combined_output(stale)
    assert _snapshot(tmp_path) == before
    assert not (bundle / "concepts" / "index.md").exists()

    updated = installed_product.run("okfkb", "update", str(bundle), cwd=tmp_path)
    clean = installed_product.run("okfkb", "validate", str(bundle), cwd=tmp_path)

    assert updated.returncode == 0, combined_output(updated)
    assert clean.returncode == 0, combined_output(clean)
    assert "Bundle is conformant (0 errors, 0 warnings)" in combined_output(clean)
    findings_index = (bundle / "findings" / "index.md").read_text(encoding="utf-8")
    assert f"[PLL lock time]({pll}.md)" in findings_index
    assert f"[Bootloader wait]({wait}.md)" in findings_index
    concepts_index = (bundle / "concepts" / "index.md").read_text(encoding="utf-8")
    assert "(cold-pll-wait.md)" in concepts_index
    for stem in (pll, wait):
        finding = (bundle / "findings" / f"{stem}.md").read_text(encoding="utf-8")
        assert "derives_to: [concepts/cold-pll-wait]" in finding
        assert "[concepts/cold-pll-wait](../concepts/cold-pll-wait.md)" in finding
    assert {path: _body_without_links(path) for path in authored_bodies} == authored_bodies
