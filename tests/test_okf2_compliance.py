"""Tests for OKF 0.2 validation and API features."""

from __future__ import annotations

from pathlib import Path

from okf_schema._internal.models import Report
from okf_schema.validator import (
    _derive_trust_tier,
    _is_stale,
    _validate_okf2_generated,
    _validate_okf2_lifecycle,
    _validate_okf2_sources,
    _validate_okf2_verified,
    validate_concept,
    validate_markdown_files,
)

# ---------------------------------------------------------------------------
# _derive_trust_tier
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-CORE-006


def test_derive_trust_tier_no_verified_returns_unverified() -> None:
    assert _derive_trust_tier({}) == "unverified"


def test_derive_trust_tier_empty_verified_list_returns_unverified() -> None:
    assert _derive_trust_tier({"verified": []}) == "unverified"


def test_derive_trust_tier_human_actor_returns_human_reviewed() -> None:
    fm = {"verified": [{"by": "human:alice", "at": "2026-01-01"}]}
    assert _derive_trust_tier(fm) == "human-reviewed"


def test_derive_trust_tier_bot_actor_returns_machine_confirmed() -> None:
    fm = {"verified": [{"by": "bot:ci", "at": "2026-01-01"}]}
    assert _derive_trust_tier(fm) == "machine-confirmed"


def test_derive_trust_tier_malformed_actor_returns_unverified() -> None:
    fm = {"verified": [{"by": "Alice", "at": "2026-01-01"}]}
    assert _derive_trust_tier(fm) == "unverified"


def test_derive_trust_tier_bare_mapping_normalized_to_list() -> None:
    fm = {"verified": {"by": "human:bob", "at": "2026-01-01"}}
    assert _derive_trust_tier(fm) == "human-reviewed"


def test_derive_trust_tier_mixed_machine_and_human_returns_human_reviewed() -> None:
    fm = {
        "verified": [
            {"by": "bot:ci", "at": "2026-01-01"},
            {"by": "human:alice", "at": "2026-01-01"},
        ]
    }
    assert _derive_trust_tier(fm) == "human-reviewed"


def test_derive_trust_tier_non_dict_entry_skipped() -> None:
    fm = {"verified": ["not-a-dict"]}
    assert _derive_trust_tier(fm) == "unverified"


def test_derive_trust_tier_verified_not_list_or_dict_returns_unverified() -> None:
    fm = {"verified": "invalid"}
    assert _derive_trust_tier(fm) == "unverified"


def test_derive_trust_tier_entry_without_by_skipped() -> None:
    fm = {"verified": [{"at": "2026-01-01"}]}
    assert _derive_trust_tier(fm) == "unverified"


def test_derive_trust_tier_machine_only_returns_machine_confirmed() -> None:
    fm = {
        "verified": [
            {"by": "bot:ci", "at": "2026-01-01"},
            {"by": "tool:scanner", "at": "2026-01-01"},
        ]
    }
    assert _derive_trust_tier(fm) == "machine-confirmed"


# ---------------------------------------------------------------------------
# _is_stale
# ---------------------------------------------------------------------------


def test_is_stale_no_stale_after_returns_false() -> None:
    assert _is_stale({}) is False


def test_is_stale_future_date_returns_false() -> None:
    assert _is_stale({"stale_after": "2099-12-31"}) is False


def test_is_stale_past_date_returns_true() -> None:
    assert _is_stale({"stale_after": "2000-01-01"}) is True


def test_is_stale_invalid_date_format_returns_false() -> None:
    assert _is_stale({"stale_after": "not-a-date"}) is False


def test_is_stale_value_error_returns_false() -> None:
    # Non-ISO date that matches regex but fails fromisoformat
    assert _is_stale({"stale_after": "2026-99-99"}) is False


# ---------------------------------------------------------------------------
# _validate_okf2_generated
# ---------------------------------------------------------------------------


def test_validate_okf2_generated_no_generated_no_timestamp_no_finding(tmp_path: Path) -> None:
    """No generated or timestamp → no E7/W8 (W3 handles missing provenance)."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_generated(path, {}, report)
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_generated_e7_generated_missing_at(tmp_path: Path) -> None:
    """E7: generated block present but missing `at`."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_generated(path, {"generated": {"by": "bot:ci"}}, report)
    assert any(f.code == "E7" for f in report.errors)


def test_validate_okf2_generated_w8_timestamp_present_no_generated(tmp_path: Path) -> None:
    """W8: deprecated `timestamp` field emits W8."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_generated(path, {"timestamp": "2026-01-01"}, report)
    assert any(f.code == "W8" for f in report.warnings)


def test_validate_okf2_generated_valid_generated_no_finding(tmp_path: Path) -> None:
    """No findings when generated.at is present and well-formed."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_generated(
        path, {"generated": {"at": "2026-01-01T00:00:00Z", "by": "bot:ci"}}, report
    )
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_generated_generated_non_dict_no_e7(tmp_path: Path) -> None:
    """Non-dict `generated` value does not emit E7 (E4 handles schema errors)."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_generated(path, {"generated": "invalid"}, report)
    assert not any(f.code == "E7" for f in report.errors)


# ---------------------------------------------------------------------------
# _validate_okf2_sources
# ---------------------------------------------------------------------------


def test_validate_okf2_sources_no_sources_no_findings(tmp_path: Path) -> None:
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_sources(path, {}, "", tmp_path, report)
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_sources_e8_entry_missing_resource(tmp_path: Path) -> None:
    """E8: sources entry missing `resource`."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_sources(path, {"sources": [{"id": "ref-1", "title": "X"}]}, "", tmp_path, report)
    assert any(f.code == "E8" for f in report.errors)


def test_validate_okf2_sources_valid_sources_no_e8(tmp_path: Path) -> None:
    """Valid sources entry with resource → no E8."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": [{"resource": "https://example.com/paper.pdf", "id": "ref-1"}]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert not any(f.code == "E8" for f in report.errors)


def test_validate_okf2_sources_w9_citations_heading_in_body(tmp_path: Path) -> None:
    """W9: body `# Citations` section emits W9."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    body = "Some content.\n\n# Citations\n\n- https://example.com\n"
    _validate_okf2_sources(path, {}, body, tmp_path, report)
    assert any(f.code == "W9" for f in report.warnings)


def test_validate_okf2_sources_w12_footnote_no_matching_source(tmp_path: Path) -> None:
    """W12: footnote [^ref-1] with no matching sources[].id."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    body = "This is important.[^ref-1]\n"
    fm = {"sources": [{"resource": "https://example.com/", "id": "other"}]}
    _validate_okf2_sources(path, fm, body, tmp_path, report)
    assert any(f.code == "W12" for f in report.warnings)


def test_validate_okf2_sources_no_w12_when_footnote_matched(tmp_path: Path) -> None:
    """No W12 when footnote matches a sources[].id."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    body = "This is important.[^ref-1]\n"
    fm = {"sources": [{"resource": "https://example.com/", "id": "ref-1"}]}
    _validate_okf2_sources(path, fm, body, tmp_path, report)
    assert not any(f.code == "W12" for f in report.warnings)


def test_validate_okf2_sources_w13_broken_path_resource(tmp_path: Path) -> None:
    """W13: path-form resource that doesn't exist."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": [{"resource": "docs/missing-file.pdf"}]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert any(f.code == "W13" for f in report.warnings)


def test_validate_okf2_sources_no_w13_for_url_resource(tmp_path: Path) -> None:
    """W13 not emitted for URL-form resources."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": [{"resource": "https://example.com/paper.pdf"}]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert not any(f.code == "W13" for f in report.warnings)


def test_validate_okf2_sources_no_w13_for_scope_descriptor(tmp_path: Path) -> None:
    """W13 not emitted for scope descriptors (no path separators or extension)."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": [{"resource": "myproject"}]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert not any(f.code == "W13" for f in report.warnings)


def test_validate_okf2_sources_no_w13_for_existing_path_resource(tmp_path: Path) -> None:
    """W13 not emitted when path-form resource resolves to an existing file."""
    path = tmp_path / "f.md"
    path.touch()
    existing = tmp_path / "existing.pdf"
    existing.write_bytes(b"fake pdf")
    report = Report()
    fm = {"sources": [{"resource": "existing.pdf"}]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert not any(f.code == "W13" for f in report.warnings)


def test_validate_okf2_sources_bare_dict_sources_normalized(tmp_path: Path) -> None:
    """Bare dict `sources` (not list) is treated as single-element list."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": {"resource": "https://example.com/"}}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    assert not any(f.code == "E8" for f in report.errors)


def test_validate_okf2_sources_non_dict_entry_skipped(tmp_path: Path) -> None:
    """Non-dict entries in sources list are skipped without error."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    fm = {"sources": ["not-a-dict"]}
    _validate_okf2_sources(path, fm, "", tmp_path, report)
    # No crash, no E8 for non-dict entries
    assert not any(f.code == "E8" for f in report.errors)


def test_validate_okf2_sources_sources_not_list_or_dict(tmp_path: Path) -> None:
    """sources with invalid type (string) is skipped gracefully."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_sources(path, {"sources": "invalid"}, "", tmp_path, report)
    assert report.errors == []


# ---------------------------------------------------------------------------
# _validate_okf2_verified
# ---------------------------------------------------------------------------


def test_validate_okf2_verified_no_verified_no_findings(tmp_path: Path) -> None:
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {}, report)
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_verified_e9_missing_by(tmp_path: Path) -> None:
    """E9: verified entry missing `by`."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": [{"at": "2026-01-01"}]}, report)
    assert any(f.code == "E9" for f in report.errors)


def test_validate_okf2_verified_e9_missing_at(tmp_path: Path) -> None:
    """E9: verified entry missing `at`."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": [{"by": "human:alice"}]}, report)
    assert any(f.code == "E9" for f in report.errors)


def test_validate_okf2_verified_w10_malformed_actor(tmp_path: Path) -> None:
    """W10: verified entry has malformed `by` actor string."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": [{"by": "Alice", "at": "2026-01-01"}]}, report)
    assert any(f.code == "W10" for f in report.warnings)


def test_validate_okf2_verified_valid_entry_no_findings(tmp_path: Path) -> None:
    """Valid verified entry → no findings."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(
        path,
        {"verified": [{"by": "human:alice", "at": "2026-01-01"}]},
        report,
    )
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_verified_bare_dict_verified_normalized(tmp_path: Path) -> None:
    """Bare dict `verified` treated as single-element list."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": {"by": "human:alice", "at": "2026-01-01"}}, report)
    assert report.errors == []
    assert report.warnings == []


def test_validate_okf2_verified_non_dict_entry_skipped(tmp_path: Path) -> None:
    """Non-dict entries in verified list are skipped."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": ["not-a-dict"]}, report)
    assert report.errors == []


def test_validate_okf2_verified_verified_not_list_or_dict(tmp_path: Path) -> None:
    """verified with invalid type is skipped gracefully."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_verified(path, {"verified": "invalid"}, report)
    assert report.errors == []


# ---------------------------------------------------------------------------
# _validate_okf2_lifecycle
# ---------------------------------------------------------------------------


def test_validate_okf2_lifecycle_no_stale_after_no_w11(tmp_path: Path) -> None:
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_lifecycle(path, {}, report)
    assert report.warnings == []


def test_validate_okf2_lifecycle_future_stale_after_no_w11(tmp_path: Path) -> None:
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_lifecycle(path, {"stale_after": "2099-12-31"}, report)
    assert report.warnings == []


def test_validate_okf2_lifecycle_past_stale_after_emits_w11(tmp_path: Path) -> None:
    """W11: past stale_after date."""
    path = tmp_path / "f.md"
    path.touch()
    report = Report()
    _validate_okf2_lifecycle(path, {"stale_after": "2000-01-01"}, report)
    assert any(f.code == "W11" for f in report.warnings)


# ---------------------------------------------------------------------------
# Integration: validate_concept with OKF 0.2 fields
# ---------------------------------------------------------------------------


def test_validate_concept_okf2_generated_at_satisfies_w3(tmp_path: Path) -> None:
    """generated.at satisfies W3 (no missing-timestamp warning)."""
    path = tmp_path / "concept.md"
    path.write_text(
        "---\ntype: concept\ntitle: T\ndescription: D\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n  by: bot:test\n---\n'
    )
    report = Report()
    validate_concept(path, report, tmp_path, None)
    assert not any(f.code == "W3" for f in report.warnings)


def test_validate_concept_okf2_timestamp_only_emits_w3_then_w8(tmp_path: Path) -> None:
    """timestamp field satisfies W3 but emits W8 (deprecated)."""
    path = tmp_path / "concept.md"
    path.write_text(
        '---\ntype: concept\ntitle: T\ndescription: D\ntimestamp: "2026-01-01T00:00:00Z"\n---\n'
    )
    report = Report()
    validate_concept(path, report, tmp_path, None)
    # W3 should NOT be present (timestamp satisfies provenance check)
    assert not any(f.code == "W3" for f in report.warnings)
    # W8 should be present (timestamp is deprecated)
    assert any(f.code == "W8" for f in report.warnings)


def test_validate_concept_okf2_neither_generated_nor_timestamp_emits_w3(tmp_path: Path) -> None:
    """Neither generated nor timestamp → W3."""
    path = tmp_path / "concept.md"
    path.write_text("---\ntype: concept\ntitle: T\ndescription: D\n---\n")
    report = Report()
    validate_concept(path, report, tmp_path, None)
    assert any(f.code == "W3" for f in report.warnings)


def test_validate_concept_okf2_e7_generated_missing_at(tmp_path: Path) -> None:
    """E7: generated block without at field."""
    path = tmp_path / "concept.md"
    path.write_text(
        "---\ntype: concept\ntitle: T\ndescription: D\ngenerated:\n  by: bot:test\n---\n"
    )
    report = Report()
    validate_concept(path, report, tmp_path, None)
    assert any(f.code == "E7" for f in report.errors)


def test_validate_concept_okf2_stale_concept_emits_w11(tmp_path: Path) -> None:
    """W11: stale concept file."""
    path = tmp_path / "concept.md"
    path.write_text(
        "---\ntype: concept\ntitle: T\ndescription: D\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n'
        'stale_after: "2000-01-01"\n---\n'
    )
    report = Report()
    validate_concept(path, report, tmp_path, None)
    assert any(f.code == "W11" for f in report.warnings)


# ---------------------------------------------------------------------------
# Integration: validate_markdown_files with OKF 0.2 fields
# ---------------------------------------------------------------------------


def test_validate_markdown_files_okf2_w8_via_validate_md(tmp_path: Path) -> None:
    """W8 is emitted by validate_markdown_files for deprecated timestamp."""
    path = tmp_path / "f.md"
    path.write_text(
        '---\ntype: concept\ntitle: T\ndescription: D\ntimestamp: "2026-01-01T00:00:00Z"\n---\n'
    )
    report = validate_markdown_files([path])
    assert any(f.code == "W8" for f in report.warnings)


def test_validate_markdown_files_okf2_verified_fields_validated_via_validate_md(
    tmp_path: Path,
) -> None:
    """E9 emitted by validate_markdown_files for invalid verified block."""
    path = tmp_path / "f.md"
    path.write_text(
        "---\ntype: concept\ntitle: T\ndescription: D\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n'
        "verified:\n  - method: peer-review\n---\n"
    )
    report = validate_markdown_files([path])
    assert any(f.code == "E9" for f in report.errors)
