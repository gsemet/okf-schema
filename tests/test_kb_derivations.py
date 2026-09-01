"""Tests for authored and computed OKFKB derivation relationships."""

from __future__ import annotations

from pathlib import Path

from okf_schema.api import lint_bundle, validate_bundle
from okf_schema.okfkb.derivations import build_derivation_graph, supports_derivation_graph
from okf_schema.okfkb.scaffold import scaffold_kb


def _document(
    document_type: str,
    title: str,
    *,
    derived_from: list[str] | None = None,
    derives_to: list[str] | None = None,
) -> str:
    """Return a minimal schema-valid KB document for graph tests."""
    lines = [
        "---",
        f"type: {document_type}",
        f"title: {title}",
        f"description: {title}",
    ]
    if document_type == "Finding":
        lines.extend(["confidence: high", "context: Test context."])
    if derived_from is not None:
        lines.append(f"derived_from: [{', '.join(derived_from)}]")
    if derives_to is not None:
        lines.append(f"derives_to: [{', '.join(derives_to)}]")
    lines.extend(
        [
            "generated:",
            "  at: '2026-08-31T00:00:00Z'",
            "  by: human:test",
            "---",
            "",
            f"# {title}",
            "",
        ]
    )
    return "\n".join(lines)


def _bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "knowledge"
    scaffold_kb(bundle)
    (bundle / "findings" / "observed-failure.md").write_text(
        _document("Finding", "Observed failure"), encoding="utf-8"
    )
    (bundle / "concepts" / "stable-explanation.md").write_text(
        _document(
            "Concept",
            "Stable explanation",
            derived_from=["findings/observed-failure"],
        ),
        encoding="utf-8",
    )
    return bundle


# @tests_req SwRS-OKFSCHEMA-OKFKB-006


def test_build_derivation_graph_reflects_authored_edges(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    graph = build_derivation_graph(bundle)
    assert graph.derives_to["findings/observed-failure"] == ["concepts/stable-explanation"]
    assert graph.derives_to["concepts/stable-explanation"] == []
    assert graph.invalid == []


def test_lint_materializes_guarded_reverse_edges_idempotently(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    assert supports_derivation_graph(bundle)

    lint_bundle(bundle, links=True)
    finding = (bundle / "findings" / "observed-failure.md").read_text(encoding="utf-8")
    concept = (bundle / "concepts" / "stable-explanation.md").read_text(encoding="utf-8")

    assert "derived_from: [findings/observed-failure]" in concept
    assert "# knowledge graph fields generated automatically — do not edit manually" in finding
    assert "derives_to: [concepts/stable-explanation]" in finding
    assert "derives_to: []" in concept
    assert all(not result.changed for result in lint_bundle(bundle, links=True))


def test_lint_check_reports_drift_without_writing(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    path = bundle / "findings" / "observed-failure.md"
    original = path.read_text(encoding="utf-8")
    results = lint_bundle(bundle, check=True, links=True)
    assert any(result.changed for result in results)
    assert path.read_text(encoding="utf-8") == original


def test_validation_reports_stale_graph_read_only_then_lint_repairs(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    path = bundle / "findings" / "observed-failure.md"
    original = path.read_text(encoding="utf-8")

    report = validate_bundle(bundle)
    assert any(finding.code == "W14" for finding in report.warnings)
    assert path.read_text(encoding="utf-8") == original

    lint_bundle(bundle, links=True)
    repaired = validate_bundle(bundle)
    assert not any(finding.code == "W14" for finding in repaired.warnings)


def test_validation_reports_noncanonical_or_missing_authored_source(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    concept_path = bundle / "concepts" / "stable-explanation.md"
    concept_path.write_text(
        _document(
            "Concept",
            "Stable explanation",
            derived_from=["findings/observed-failure.md"],
            derives_to=[],
        ),
        encoding="utf-8",
    )
    report = validate_bundle(bundle)
    messages = [finding.message for finding in report.warnings if finding.code == "W14"]
    assert any("extensionless" in message for message in messages)


def test_generic_okf_bundle_does_not_gain_derivation_fields(tmp_path: Path) -> None:
    bundle = tmp_path / "generic"
    bundle.mkdir()
    path = bundle / "concept.md"
    path.write_text(
        "---\ntype: Concept\ntitle: Generic\ndescription: Generic\n---\n\n# Generic\n",
        encoding="utf-8",
    )
    lint_bundle(bundle, links=True)
    assert "derives_to" not in path.read_text(encoding="utf-8")
