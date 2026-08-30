"""Tests for the OKF frontmatter formatter."""

from __future__ import annotations

from pathlib import Path

from okf_schema.formatter import (
    FormattedResult,
    flatten_value,
    format_bundle,
    format_file,
    format_frontmatter,
    lint_bundle,
    lint_frontmatter,
)

# ---------------------------------------------------------------------------
# flatten_value
# ---------------------------------------------------------------------------


def test_flatten_value_flat_scalar() -> None:
    """Scalars pass through unchanged."""
    assert flatten_value("hello") == "hello"
    assert flatten_value(42) == 42
    assert flatten_value(True) is True


def test_flatten_value_flat_list() -> None:
    """Already-flat lists are unchanged."""
    assert flatten_value(["a", "b", "c"]) == ["a", "b", "c"]


def test_flatten_value_nested_list() -> None:
    """Nested lists are flattened."""
    assert flatten_value([["a", "b"], "c"]) == ["a", "b", "c"]


def test_flatten_value_deeply_nested_list() -> None:
    """Deeply nested lists are fully flattened."""
    assert flatten_value([[["a"]], "b"]) == ["a", "b"]


def test_flatten_value_dict_passthrough() -> None:
    """Dicts pass through unchanged."""
    assert flatten_value({"key": "value"}) == {"key": "value"}


def test_flatten_value_list_with_dicts() -> None:
    """Dicts inside lists are preserved, lists inside lists flattened."""
    assert flatten_value([[{"a": 1}], "b"]) == [{"a": 1}, "b"]


def test_flatten_value_mixed_nesting() -> None:
    """Complex mixed nesting is flattened correctly."""
    value = [["a", ["b", "c"]], [["d"]], "e"]
    assert flatten_value(value) == ["a", "b", "c", "d", "e"]


# ---------------------------------------------------------------------------
# format_frontmatter
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-CORE-003


def test_format_frontmatter_no_frontmatter() -> None:
    """Returns None when no frontmatter is present."""
    text = "# Hello\n\nBody text.\n"
    assert format_frontmatter(text) is None


def test_format_frontmatter_flatten_nested_tags() -> None:
    """Flattens nested list values in frontmatter."""
    text = "---\ntags: [[a, b], c]\n---\n\n# Hello\n"
    result = format_frontmatter(text)
    assert result is not None
    assert "tags:" in result
    assert "- a" in result or "[a, b, c]" in result
    # Ensure nested structure is gone
    assert "[[" not in result


def test_format_frontmatter_preserves_non_list_values() -> None:
    """Non-list values are preserved."""
    text = "---\ntitle: Hello\ntype: concept\n---\n\n# Hello\n"
    result = format_frontmatter(text)
    assert result == text


def test_format_frontmatter_preserves_comments() -> None:
    """Comments in frontmatter are preserved."""
    text = "---\ntitle: Hello\n# This is a comment\ntags: [a, b]\n---\n\n# Body\n"
    result = format_frontmatter(text)
    assert result == text
    assert "# This is a comment" in result


def test_format_frontmatter_idempotent() -> None:
    """Running twice on already-flat frontmatter produces same result."""
    text = "---\ntags: [a, b, c]\n---\n\n# Hello\n"
    result1 = format_frontmatter(text)
    assert result1 == text
    result2 = format_frontmatter(result1)
    assert result2 == result1


def test_format_frontmatter_deeply_nested() -> None:
    """Handles deeply nested lists."""
    text = "---\ntags: [[[a]], b]\n---\n\n# Hello\n"
    result = format_frontmatter(text)
    assert result is not None
    assert "[[[" not in result


def test_format_frontmatter_multiple_list_fields() -> None:
    """Flattens all list fields in frontmatter."""
    text = "---\ntags: [[a], b]\ncategories: [[x], y]\n---\n\n# Hello\n"
    result = format_frontmatter(text)
    assert result is not None
    assert "[[" not in result


# ---------------------------------------------------------------------------
# format_file
# ---------------------------------------------------------------------------


def test_format_file_in_place_modifies_file(tmp_path: Path) -> None:
    """In-place mode writes corrected content to file."""
    path = tmp_path / "concept.md"
    path.write_text("---\ntags: [[a, b], c]\n---\n\n# Hello\n")
    changed = format_file(path)
    assert changed is True
    content = path.read_text()
    assert "[[" not in content


def test_format_file_in_place_no_change(tmp_path: Path) -> None:
    """In-place mode returns False when no changes needed."""
    path = tmp_path / "concept.md"
    path.write_text("---\ntags: [a, b, c]\n---\n\n# Hello\n")
    changed = format_file(path)
    assert changed is False


def test_format_file_check_mode_detects_changes(tmp_path: Path) -> None:
    """Check mode returns True when changes needed, no file modification."""
    path = tmp_path / "concept.md"
    original = "---\ntags: [[a, b], c]\n---\n\n# Hello\n"
    path.write_text(original)
    changed = format_file(path, check=True)
    assert changed is True
    assert path.read_text() == original


def test_format_file_check_mode_no_changes(tmp_path: Path) -> None:
    """Check mode returns False when already flat."""
    path = tmp_path / "concept.md"
    original = "---\ntags: [a, b, c]\n---\n\n# Hello\n"
    path.write_text(original)
    changed = format_file(path, check=True)
    assert changed is False


def test_format_file_diff_mode_returns_diff(tmp_path: Path) -> None:
    """Diff mode returns unified diff string."""
    path = tmp_path / "concept.md"
    path.write_text("---\ntags: [[a, b], c]\n---\n\n# Hello\n")
    changed = format_file(path, diff=True)
    assert changed is True
    # diff is stored in a side channel or returned — we'll check the file
    # wasn't modified
    assert "[[" in path.read_text()


def test_format_file_skip_no_frontmatter(tmp_path: Path) -> None:
    """Files without frontmatter are skipped silently."""
    path = tmp_path / "plain.md"
    original = "# Hello\n\nNo frontmatter here.\n"
    path.write_text(original)
    changed = format_file(path)
    assert changed is False
    assert path.read_text() == original


def test_format_file_preserves_body(tmp_path: Path) -> None:
    """Body content is preserved after formatting."""
    path = tmp_path / "concept.md"
    body = "\n# Title\n\nSome body text.\n\n- list item\n"
    path.write_text(f"---\ntags: [[a, b], c]\n---\n{body}")
    format_file(path)
    content = path.read_text()
    assert "# Title" in content
    assert "Some body text." in content
    assert "- list item" in content


# ---------------------------------------------------------------------------
# format_bundle
# ---------------------------------------------------------------------------


def test_format_bundle_formats_all_concepts(tmp_path: Path) -> None:
    """Formats all concept files in a bundle."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept1.md").write_text("---\ntags: [[a, b], c]\n---\n\n# One\n")
    (bundle / "concept2.md").write_text("---\ntags: [[x], y]\n---\n\n# Two\n")
    results = format_bundle(bundle)
    assert len(results) == 2
    assert all(isinstance(r, FormattedResult) for r in results)
    changed = [r for r in results if r.changed]
    assert len(changed) == 2


def test_format_bundle_skips_non_markdown(tmp_path: Path) -> None:
    """Non-markdown files are skipped."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "readme.txt").write_text("hello")
    (bundle / "concept.md").write_text("---\ntags: [a]\n---\n\n# One\n")
    results = format_bundle(bundle)
    assert len(results) == 1


def test_format_bundle_check_mode_no_modification(tmp_path: Path) -> None:
    """Check mode does not modify any files."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    original = "---\ntags: [[a, b], c]\n---\n\n# One\n"
    (bundle / "concept.md").write_text(original)
    results = format_bundle(bundle, check=True)
    assert len(results) == 1
    assert results[0].changed is True
    assert (bundle / "concept.md").read_text() == original


def test_format_bundle_diff_mode_returns_diffs(tmp_path: Path) -> None:
    """Diff mode returns diff strings in results."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept.md").write_text("---\ntags: [[a, b], c]\n---\n\n# One\n")
    results = format_bundle(bundle, diff=True)
    assert len(results) == 1
    assert results[0].changed is True
    assert results[0].diff is not None
    assert "---" in results[0].diff
    assert "+++" in results[0].diff


def test_format_bundle_empty_bundle(tmp_path: Path) -> None:
    """Empty bundle returns empty results."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    results = format_bundle(bundle)
    assert results == []


def test_format_bundle_nested_directories(tmp_path: Path) -> None:
    """Recursively formats files in subdirectories."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    sub = bundle / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("---\ntags: [[a], b]\n---\n\n# Nested\n")
    results = format_bundle(bundle)
    assert len(results) == 1
    assert results[0].changed is True


def test_format_bundle_result_dataclass(tmp_path: Path) -> None:
    """FormattedResult has correct fields."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept.md").write_text("---\ntags: [a]\n---\n\n# One\n")
    results = format_bundle(bundle)
    assert len(results) == 1
    r = results[0]
    assert isinstance(r.path, Path)
    assert r.changed is False
    assert r.diff is None


# ---------------------------------------------------------------------------
# lint_frontmatter
# ---------------------------------------------------------------------------


def test_lint_frontmatter_converts_block_list_to_inline() -> None:
    """Block-style lists become inline."""
    text = "---\ntype: concept\ntags:\n  - a\n  - b\n---\n\n# Body\n"
    result = lint_frontmatter(text)
    assert result is not None
    assert "tags: [a, b]" in result


def test_lint_frontmatter_leaves_inline_list_unchanged() -> None:
    """Already-inline lists are untouched."""
    text = "---\ntype: concept\ntags: [a, b]\n---\n\n# Body\n"
    result = lint_frontmatter(text)
    assert result == text


def test_lint_frontmatter_returns_none_when_no_frontmatter() -> None:
    """No frontmatter means nothing to lint."""
    text = "# Just a heading\n"
    result = lint_frontmatter(text)
    assert result is None


def test_lint_frontmatter_converts_multiple_block_lists() -> None:
    """Multiple block lists are all converted."""
    text = "---\ntags:\n  - a\n  - b\nitems:\n  - x\n  - y\n---\n\n# Body\n"
    result = lint_frontmatter(text)
    assert result is not None
    assert "tags: [a, b]" in result
    assert "items: [x, y]" in result


def test_lint_frontmatter_preserves_comments() -> None:
    """YAML comments are preserved when converting block lists."""
    text = "---\ntype: concept\n# keep this comment\ntags:\n  - a\n  - b\n---\n\n# Body\n"
    result = lint_frontmatter(text)
    assert result is not None
    assert "tags: [a, b]" in result
    assert "# keep this comment" in result


# ---------------------------------------------------------------------------
# lint_bundle
# ---------------------------------------------------------------------------


def test_lint_bundle_modifies_files_in_place(tmp_path: Path) -> None:
    """lint_bundle converts block lists in all files."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept.md").write_text(
        "---\ntype: concept\ntags:\n  - a\n  - b\n---\n\n# One\n",
        encoding="utf-8",
    )
    results = lint_bundle(bundle)
    assert len(results) == 1
    assert results[0].changed is True
    text = (bundle / "concept.md").read_text(encoding="utf-8")
    assert "tags: [a, b]" in text


def test_lint_bundle_check_mode_no_changes(tmp_path: Path) -> None:
    """lint_bundle with check=True does not modify files."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    original = "---\ntype: concept\ntags:\n  - a\n  - b\n---\n\n# One\n"
    (bundle / "concept.md").write_text(original, encoding="utf-8")
    results = lint_bundle(bundle, check=True)
    assert len(results) == 1
    assert results[0].changed is True
    assert (bundle / "concept.md").read_text(encoding="utf-8") == original


def test_lint_bundle_diff_mode(tmp_path: Path) -> None:
    """lint_bundle with diff=True returns diffs."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept.md").write_text(
        "---\ntype: concept\ntags:\n  - a\n  - b\n---\n\n# One\n",
        encoding="utf-8",
    )
    results = lint_bundle(bundle, diff=True)
    assert len(results) == 1
    assert results[0].diff is not None
    assert "---" in results[0].diff


def test_lint_bundle_no_changes_when_already_inline(tmp_path: Path) -> None:
    """lint_bundle returns changed=False when lists are already inline."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "concept.md").write_text(
        "---\ntype: concept\ntags: [a, b]\n---\n\n# One\n",
        encoding="utf-8",
    )
    results = lint_bundle(bundle)
    assert len(results) == 1
    assert results[0].changed is False


def test_update_frontmatter_links_adds_links_and_backlinks() -> None:
    """Injects links and backlinks into frontmatter."""
    from okf_schema.formatter import _update_frontmatter_links

    text = "---\ntype: concept\n---\n\n# Body\n"
    result = _update_frontmatter_links(text, ["b.md", "c.md"], ["d.md"])
    assert result is not None
    assert "links: [b.md, c.md]" in result
    assert "backlinks: [d.md]" in result


def test_update_frontmatter_links_updates_existing_links() -> None:
    """Replaces stale links with current ones."""
    from okf_schema.formatter import _update_frontmatter_links

    text = "---\ntype: concept\nlinks: [old.md]\nbacklinks: [stale.md]\n---\n\n# Body\n"
    result = _update_frontmatter_links(text, ["new.md"], ["fresh.md"])
    assert result is not None
    assert "links: [new.md]" in result
    assert "backlinks: [fresh.md]" in result
    assert "old.md" not in result
    assert "stale.md" not in result


def test_update_frontmatter_links_empty_lists_written() -> None:
    """Empty lists are still written to reflect current state."""
    from okf_schema.formatter import _update_frontmatter_links

    text = "---\ntype: concept\n---\n\n# Body\n"
    result = _update_frontmatter_links(text, [], [])
    assert result is not None
    assert "links: []" in result
    assert "backlinks: []" in result


def test_update_frontmatter_links_no_frontmatter_returns_none() -> None:
    """Returns None when no frontmatter is present."""
    from okf_schema.formatter import _update_frontmatter_links

    text = "# No frontmatter\n"
    result = _update_frontmatter_links(text, ["a.md"], ["b.md"])
    assert result is None


def test_update_frontmatter_links_no_change_when_values_match() -> None:
    """Returns original text when links already match."""
    from okf_schema.formatter import _update_frontmatter_links

    text = "---\ntype: concept\nlinks: [a.md]\nbacklinks: [b.md]\n---\n\n# Body\n"
    result = _update_frontmatter_links(text, ["a.md"], ["b.md"])
    assert result == text


def test_lint_bundle_links_adds_links_from_body(tmp_path: Path) -> None:
    """lint_bundle --links adds outgoing links from markdown body."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text(
        "---\ntype: concept\n---\n\n# A\n\nLink to [B](b.md)\n",
        encoding="utf-8",
    )
    (bundle / "b.md").write_text(
        "---\ntype: concept\n---\n\n# B\n\nLink to [A](a.md)\n",
        encoding="utf-8",
    )
    results = lint_bundle(bundle, links=True)
    assert len(results) == 2
    a_text = (bundle / "a.md").read_text(encoding="utf-8")
    b_text = (bundle / "b.md").read_text(encoding="utf-8")
    assert "links: [b.md]" in a_text
    assert "backlinks: [b.md]" in a_text
    assert "links: [a.md]" in b_text
    assert "backlinks: [a.md]" in b_text


def test_lint_bundle_links_links_mode_with_check(tmp_path: Path) -> None:
    """links=True with check=True does not modify files."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    original = "---\ntype: concept\n---\n\n# A\n\nLink to [B](b.md)\n"
    (bundle / "a.md").write_text(original, encoding="utf-8")
    (bundle / "b.md").write_text(
        "---\ntype: concept\n---\n\n# B\n\nLink to [A](a.md)\n",
        encoding="utf-8",
    )
    results = lint_bundle(bundle, check=True, links=True)
    assert any(r.changed for r in results)
    assert (bundle / "a.md").read_text(encoding="utf-8") == original


def test_lint_bundle_links_links_mode_no_changes_when_correct(tmp_path: Path) -> None:
    """links=True returns changed=False when links already match."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text(
        "---\ntype: concept\nlinks: [b.md]\nbacklinks: [b.md]\n---\n\n# A\n\nLink to [B](b.md)\n",
        encoding="utf-8",
    )
    (bundle / "b.md").write_text(
        "---\ntype: concept\nlinks: [a.md]\nbacklinks: [a.md]\n---\n\n# B\n\nLink to [A](a.md)\n",
        encoding="utf-8",
    )
    lint_bundle(bundle, links=True)
    assert all(not r.changed for r in lint_bundle(bundle, links=True))


def test_lint_bundle_links_skips_external_links(tmp_path: Path) -> None:
    """External URLs are not included in links."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text(
        "---\ntype: concept\n---\n\n# A\n\n[External](https://example.com)\n",
        encoding="utf-8",
    )
    lint_bundle(bundle, links=True)
    a_text = (bundle / "a.md").read_text(encoding="utf-8")
    assert "links: []" in a_text
    assert "backlinks: []" in a_text


def test_lint_bundle_links_skips_self_links(tmp_path: Path) -> None:
    """Self-links are not included in links."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text(
        "---\ntype: concept\n---\n\n# A\n\n[Self](a.md)\n",
        encoding="utf-8",
    )
    lint_bundle(bundle, links=True)
    a_text = (bundle / "a.md").read_text(encoding="utf-8")
    assert "links: []" in a_text
    assert "backlinks: []" in a_text


def test_lint_bundle_links_skips_reserved_files(tmp_path: Path) -> None:
    """Reserved files are excluded from link graph."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "index.md").write_text(
        "---\ntype: index\n---\n\n# Index\n\n[Link](concept.md)\n",
        encoding="utf-8",
    )
    (bundle / "concept.md").write_text(
        "---\ntype: concept\n---\n\n# Concept\n",
        encoding="utf-8",
    )
    lint_bundle(bundle, links=True)
    concept_text = (bundle / "concept.md").read_text(encoding="utf-8")
    assert "backlinks: []" in concept_text


# ---------------------------------------------------------------------------
# OKF 0.2: list-of-mapping field exemptions
# ---------------------------------------------------------------------------


def test_lint_frontmatter_okf2_exemptions_sources_block_style_preserved() -> None:
    """Block-style `sources` list-of-mapping is NOT converted to inline."""
    text = (
        "---\ntype: concept\n"
        "sources:\n"
        "  - resource: https://example.com/\n"
        "    id: ref-1\n"
        "---\n\n# Body\n"
    )
    result = lint_frontmatter(text)
    # sources should remain block-style (not inlined to flow-style)
    assert result is not None
    assert "sources:" in result
    # The list must not be collapsed into a single line
    assert "- resource" in result


def test_lint_frontmatter_okf2_exemptions_verified_block_style_preserved() -> None:
    """Block-style `verified` list-of-mapping is NOT converted to inline."""
    text = (
        "---\ntype: concept\nverified:\n  - by: human:alice\n    at: '2026-01-01'\n---\n\n# Body\n"
    )
    result = lint_frontmatter(text)
    assert result is not None
    assert "verified:" in result
    assert "- by: human:alice" in result


def test_lint_frontmatter_okf2_exemptions_scalar_lists_still_inlined() -> None:
    """Regular scalar lists (tags) are still converted to inline."""
    text = "---\ntype: concept\ntags:\n  - a\n  - b\n---\n\n# Body\n"
    result = lint_frontmatter(text)
    assert result is not None
    assert "tags: [a, b]" in result


def test_lint_frontmatter_okf2_exemptions_generated_dict_not_altered() -> None:
    """Block-style `generated` dict is preserved (not a list, not inlined)."""
    text = (
        "---\ntype: concept\n"
        "generated:\n"
        "  at: '2026-01-01T00:00:00Z'\n"
        "  by: bot:test\n"
        "---\n\n# Body\n"
    )
    result = lint_frontmatter(text)
    assert result is not None
    # generated dict should still be present (block-style dict preserved)
    assert "generated:" in result


def test_lint_frontmatter_migrates_legacy_timestamp() -> None:
    text = "---\ntype: concept\ntimestamp: '2026-01-01T00:00:00Z'\ntitle: Example\n---\n\n# Body\n"

    result = lint_frontmatter(text)

    assert result is not None
    assert "timestamp:" not in result
    assert "generated:\n  at: '2026-01-01T00:00:00Z'" in result
    assert result.endswith("# Body\n")


def test_lint_frontmatter_removes_redundant_legacy_timestamp() -> None:
    text = (
        "---\ntype: concept\ngenerated:\n  at: '2026-02-01T00:00:00Z'\n"
        "timestamp: '2026-01-01T00:00:00Z'\n---\n\n# Body\n"
    )

    result = lint_frontmatter(text)

    assert result is not None
    assert "timestamp:" not in result
    assert "at: '2026-02-01T00:00:00Z'" in result
