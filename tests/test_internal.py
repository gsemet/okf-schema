"""Tests for okf_schema internal infrastructure modules."""

from __future__ import annotations

from pathlib import Path

from okf_schema._internal.models import (
    BundleStats,
    ConceptInfo,
    Finding,
    Report,
    SearchResult,
)
from okf_schema._internal.utils import (
    build_link_graph,
    collect_markdown_files,
    extract_outgoing_links,
    find_broken_links,
    get_concept_info,
    has_markdown_files,
    resolve_link,
)
from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml, parse_yaml

# ---------------------------------------------------------------------------
# models.py
# ---------------------------------------------------------------------------


def test_finding_finding_defaults() -> None:
    """Finding should default path to None."""
    finding = Finding(code="E1", message="test message")
    assert finding.code == "E1"
    assert finding.message == "test message"
    assert finding.path is None


def test_finding_finding_with_path() -> None:
    """Finding should accept an optional path."""
    path = Path("/tmp/test.md")
    finding = Finding(code="E2", message="no type", path=path)
    assert finding.path == path


def test_report_report_defaults() -> None:
    """Report should default to empty error and warning lists."""
    report = Report()
    assert report.errors == []
    assert report.warnings == []
    assert report.is_conformant is True


def test_report_add_error() -> None:
    """add_error should append a Finding to errors."""
    report = Report()
    report.add_error("E1", "missing frontmatter")
    assert len(report.errors) == 1
    assert report.errors[0].code == "E1"
    assert report.is_conformant is False


def test_report_add_warning() -> None:
    """add_warning should append a Finding to warnings."""
    report = Report()
    report.add_warning("W1", "missing title")
    assert len(report.warnings) == 1
    assert report.warnings[0].code == "W1"
    assert report.is_conformant is True


def test_report_report_with_initial_lists() -> None:
    """Report should accept initial error and warning lists."""
    errors = [Finding("E1", "err")]
    warnings = [Finding("W1", "warn")]
    report = Report(errors=errors, warnings=warnings)
    assert report.errors == errors
    assert report.warnings == warnings
    assert report.is_conformant is False


def test_concept_info_concept_info_fields() -> None:
    """ConceptInfo should store title, description, and type."""
    info = ConceptInfo(title="My Title", description="A desc", type="concept")
    assert info.title == "My Title"
    assert info.description == "A desc"
    assert info.type == "concept"


def test_search_result_search_result_fields() -> None:
    """SearchResult should store path, type, and title."""
    result = SearchResult(path="concepts/test.md", type="concept", title="Test")
    assert result.path == "concepts/test.md"
    assert result.type == "concept"
    assert result.title == "Test"


def test_bundle_stats_bundle_stats_fields() -> None:
    """BundleStats should store all statistics fields."""
    stats = BundleStats(
        total_files=8,
        total_concepts=5,
        files_without_frontmatter=1,
        total_size=1024,
        total_links=10,
        broken_links=1,
        types_distribution={"concept": 3, "pattern": 2},
        tags_distribution={"python": 2, "cli": 1},
        directories=3,
    )
    assert stats.total_files == 8
    assert stats.total_concepts == 5
    assert stats.files_without_frontmatter == 1
    assert stats.total_size == 1024
    assert stats.total_links == 10
    assert stats.broken_links == 1
    assert stats.types_distribution == {"concept": 3, "pattern": 2}
    assert stats.tags_distribution == {"python": 2, "cli": 1}
    assert stats.directories == 3


# ---------------------------------------------------------------------------
# yaml.py
# ---------------------------------------------------------------------------


def test_extract_frontmatter_no_frontmatter() -> None:
    """Returns (None, text) when no frontmatter present."""
    text = "# Hello\n\nBody content."
    fm, body = extract_frontmatter(text)
    assert fm is None
    assert body == text


def test_extract_frontmatter_valid_frontmatter() -> None:
    """Parses --- delimited frontmatter correctly."""
    text = "---\ntitle: Test\n---\n\n# Body\n"
    fm, body = extract_frontmatter(text)
    assert fm == "\ntitle: Test"
    assert body == "\n# Body\n"


def test_extract_frontmatter_frontmatter_no_trailing_newline() -> None:
    """Handles frontmatter without trailing newline after delimiter."""
    text = "---\ntitle: Test\n---\n# Body"
    fm, body = extract_frontmatter(text)
    assert fm == "\ntitle: Test"
    assert body == "# Body"


def test_extract_frontmatter_malformed_no_closing_delimiter() -> None:
    """Returns (None, text) when closing --- is missing."""
    text = "---\ntitle: Test\n\n# Body"
    fm, body = extract_frontmatter(text)
    assert fm is None
    assert body == text


def test_extract_frontmatter_empty_frontmatter() -> None:
    """Handles empty frontmatter block."""
    text = "---\n---\n\nBody"
    fm, body = extract_frontmatter(text)
    assert fm == ""
    assert body == "\nBody"


def test_parse_yaml_valid_yaml() -> None:
    """Returns dict for valid YAML."""
    result = parse_yaml("title: Test\ntype: concept")
    assert result == {"title": "Test", "type": "concept"}


def test_parse_yaml_invalid_yaml() -> None:
    """Returns None for invalid YAML."""
    result = parse_yaml("title: : bad:")
    assert result is None


def test_parse_yaml_non_dict_yaml() -> None:
    """Returns None when YAML parses to non-dict."""
    result = parse_yaml("- item1\n- item2")
    assert result is None


def test_parse_yaml_empty_yaml() -> None:
    """Returns None for empty YAML."""
    result = parse_yaml("")
    assert result is None


def test_parse_yaml_date_normalization() -> None:
    """Unquoted ISO 8601 dates are converted to strings."""
    result = parse_yaml("timestamp: 2026-06-29")
    assert result == {"timestamp": "2026-06-29"}
    assert isinstance(result["timestamp"], str)


def test_parse_yaml_datetime_normalization() -> None:
    """Unquoted ISO 8601 datetimes are converted to strings."""
    result = parse_yaml("created: 2026-06-29T14:30:00")
    assert result == {"created": "2026-06-29T14:30:00"}
    assert isinstance(result["created"], str)


def test_parse_yaml_nested_date_normalization() -> None:
    """Dates inside nested structures are also converted."""
    result = parse_yaml("meta:\n  published: 2026-06-29")
    assert result == {"meta": {"published": "2026-06-29"}}
    assert isinstance(result["meta"]["published"], str)


def test_dump_yaml_dump_simple_dict() -> None:
    """Dumps a simple dict to YAML string."""
    result = dump_yaml({"title": "Test", "type": "concept"})
    assert "title: Test" in result
    assert "type: concept" in result


def test_dump_yaml_dump_preserves_quotes() -> None:
    """Round-trip preserves quotes via ruamel.yaml."""
    yaml_text = 'title: "Quoted Title"\ntype: concept'
    data = parse_yaml(yaml_text)
    assert data is not None
    result = dump_yaml(data)
    # ruamel.yaml should preserve the quoted style in round-trip
    assert "Quoted Title" in result


def test_dump_yaml_dump_list() -> None:
    """Dumps a dict containing a list."""
    result = dump_yaml({"tags": ["python", "cli"]})
    assert "tags:" in result
    assert "python" in result
    assert "cli" in result


def test_dump_yaml_removes_round_trip_trailing_whitespace() -> None:
    """Serialized frontmatter remains compatible with Git whitespace checks."""
    data = make_yaml().load(
        "description: A long requirement statement that wraps across a line\n"
        "  and continues without relying on trailing spaces\n"
    )

    result = dump_yaml(data)

    assert all(line == line.rstrip() for line in result.splitlines())


def test_make_yaml_preserve_quotes() -> None:
    """make_yaml should set preserve_quotes=True."""
    y = make_yaml()
    assert y.preserve_quotes is True


def test_make_yaml_default_flow_style() -> None:
    """make_yaml should set default_flow_style=False."""
    y = make_yaml()
    assert y.default_flow_style is False


def test_make_yaml_roundtrip_comments() -> None:
    """Round-trip preserves comments."""
    yaml_text = "# Header comment\ntitle: Test\ntype: concept"
    y = make_yaml()
    data = y.load(yaml_text)
    from io import StringIO

    buf = StringIO()
    y.dump(data, buf)
    result = buf.getvalue()
    assert "Header comment" in result


# ---------------------------------------------------------------------------
# utils.py
# ---------------------------------------------------------------------------


def test_collect_markdown_files_collects_sorted(tmp_path: Path) -> None:
    """Yields all .md files sorted."""
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.md").write_text("b")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("c")
    result = list(collect_markdown_files(tmp_path))
    assert len(result) == 3
    # Should be sorted
    assert result[0].name == "a.md"
    assert result[1].name == "b.md"
    assert result[2].name == "c.md"


def test_collect_markdown_files_skips_non_md(tmp_path: Path) -> None:
    """Ignores non-markdown files."""
    (tmp_path / "a.md").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    result = list(collect_markdown_files(tmp_path))
    assert len(result) == 1
    assert result[0].name == "a.md"


def test_resolve_link_external_https(tmp_path: Path) -> None:
    """Returns None for https:// links."""
    result = resolve_link("https://example.com", tmp_path / "a.md", tmp_path)
    assert result is None


def test_resolve_link_external_mailto(tmp_path: Path) -> None:
    """Returns None for mailto: links."""
    result = resolve_link("mailto:test@example.com", tmp_path / "a.md", tmp_path)
    assert result is None


def test_resolve_link_relative_path(tmp_path: Path) -> None:
    """Resolves relative paths from source file parent."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    source = subdir / "a.md"
    result = resolve_link("../other.md", source, tmp_path)
    assert result == (tmp_path / "other.md").resolve()


def test_resolve_link_absolute_bundle_path(tmp_path: Path) -> None:
    """Resolves absolute paths relative to bundle root."""
    source = tmp_path / "a.md"
    result = resolve_link("/concepts/test.md", source, tmp_path)
    assert result == (tmp_path / "concepts" / "test.md").resolve()


def test_resolve_link_relative_same_dir(tmp_path: Path) -> None:
    """Resolves relative paths in same directory."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    source = subdir / "a.md"
    target = subdir / "b.md"
    target.write_text("b")
    result = resolve_link("b.md", source, tmp_path)
    assert result == target.resolve()


def test_find_broken_links_broken_internal_link(tmp_path: Path) -> None:
    """Flags missing internal link targets."""
    source = tmp_path / "a.md"
    body = "[link](./missing.md)"
    result = find_broken_links(body, source, tmp_path)
    assert "./missing.md" in result


def test_find_broken_links_valid_internal_link(tmp_path: Path) -> None:
    """Ignores existing internal link targets."""
    target = tmp_path / "exists.md"
    target.write_text("exists")
    source = tmp_path / "a.md"
    body = "[link](./exists.md)"
    result = find_broken_links(body, source, tmp_path)
    assert result == []


def test_find_broken_links_external_link_ignored(tmp_path: Path) -> None:
    """Ignores external links."""
    source = tmp_path / "a.md"
    body = "[link](https://example.com)"
    result = find_broken_links(body, source, tmp_path)
    assert result == []


def test_find_broken_links_multiple_links_mixed(tmp_path: Path) -> None:
    """Handles mix of broken, valid, and external links."""
    target = tmp_path / "exists.md"
    target.write_text("exists")
    source = tmp_path / "a.md"
    body = "[a](./exists.md) [b](./missing.md) [c](https://example.com)"
    result = find_broken_links(body, source, tmp_path)
    assert result == ["./missing.md"]


def test_has_markdown_files_has_markdown(tmp_path: Path) -> None:
    """Returns True when directory contains .md files."""
    (tmp_path / "a.md").write_text("a")
    assert has_markdown_files(tmp_path) is True


def test_has_markdown_files_no_markdown(tmp_path: Path) -> None:
    """Returns False when directory has no .md files."""
    (tmp_path / "a.txt").write_text("a")
    assert has_markdown_files(tmp_path) is False


def test_has_markdown_files_nested_markdown(tmp_path: Path) -> None:
    """Returns True when subdirectory contains .md files."""
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "a.md").write_text("a")
    assert has_markdown_files(tmp_path) is True


def test_has_markdown_files_not_a_directory(tmp_path: Path) -> None:
    """Returns False when path is not a directory."""
    file_path = tmp_path / "a.txt"
    file_path.write_text("a")
    assert has_markdown_files(file_path) is False


def test_get_concept_info_complete_frontmatter(tmp_path: Path) -> None:
    """Extracts all fields from frontmatter."""
    path = tmp_path / "my-concept.md"
    path.write_text("---\ntitle: My Title\ndescription: A desc\ntype: concept\n---\n\nBody")
    info = get_concept_info(path)
    assert info.title == "My Title"
    assert info.description == "A desc"
    assert info.type == "concept"


def test_get_concept_info_missing_frontmatter(tmp_path: Path) -> None:
    """Falls back to stem-based title when no frontmatter."""
    path = tmp_path / "my-concept.md"
    path.write_text("# Body\n\nContent")
    info = get_concept_info(path)
    assert info.title == "My Concept"
    assert info.description == ""
    assert info.type == ""


def test_get_concept_info_partial_frontmatter(tmp_path: Path) -> None:
    """Handles partial frontmatter gracefully."""
    path = tmp_path / "test.md"
    path.write_text("---\ntitle: Only Title\n---\n\nBody")
    info = get_concept_info(path)
    assert info.title == "Only Title"
    assert info.description == ""
    assert info.type == ""


def test_get_concept_info_stem_with_underscores(tmp_path: Path) -> None:
    """Converts underscores to spaces in fallback title."""
    path = tmp_path / "my_concept.md"
    path.write_text("Body")
    info = get_concept_info(path)
    assert info.title == "My Concept"


# ---------------------------------------------------------------------------
# schemas/__init__.py
# ---------------------------------------------------------------------------


def test_builtin_schema_get_builtin_schema_returns_dict() -> None:
    """get_builtin_schema returns a dict."""
    from okf_schema.schemas import get_builtin_schema

    schema = get_builtin_schema()
    assert isinstance(schema, dict)


def test_builtin_schema_schema_requires_type() -> None:
    """Built-in schema requires type field."""
    from jsonschema import Draft202012Validator

    from okf_schema.schemas import get_builtin_schema

    schema = get_builtin_schema()
    validator = Draft202012Validator(schema)
    # Missing type should fail
    errors = list(validator.iter_errors({}))
    assert any("type" in str(e.validator_value) or "type" in e.message for e in errors)


def test_builtin_schema_schema_rejects_empty_type() -> None:
    """Built-in schema rejects empty type string."""
    from jsonschema import Draft202012Validator

    from okf_schema.schemas import get_builtin_schema

    schema = get_builtin_schema()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors({"type": ""}))
    assert len(errors) > 0


def test_builtin_schema_schema_accepts_valid_type() -> None:
    """Built-in schema accepts non-empty type string."""
    from jsonschema import Draft202012Validator

    from okf_schema.schemas import get_builtin_schema

    schema = get_builtin_schema()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors({"type": "concept"}))
    assert errors == []


# ---------------------------------------------------------------------------
# extract_outgoing_links
# ---------------------------------------------------------------------------


def test_extract_outgoing_links_extracts_internal_links(tmp_path: Path) -> None:
    """Extracts internal markdown links as relative paths."""
    source = tmp_path / "a.md"
    body = "[Link](b.md) [Another](sub/c.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["b.md", "sub/c.md"]


def test_extract_outgoing_links_skips_external_links(tmp_path: Path) -> None:
    """External URLs are excluded."""
    source = tmp_path / "a.md"
    body = "[External](https://example.com) [Local](b.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["b.md"]


def test_extract_outgoing_links_skips_self_links(tmp_path: Path) -> None:
    """Links to self are excluded."""
    source = tmp_path / "a.md"
    body = "[Self](a.md) [Other](b.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["b.md"]


def test_extract_outgoing_links_deduplicates_links(tmp_path: Path) -> None:
    """Duplicate links appear only once."""
    source = tmp_path / "a.md"
    body = "[First](b.md) [Second](b.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["b.md"]


def test_extract_outgoing_links_skips_links_outside_bundle(tmp_path: Path) -> None:
    """Links resolving outside bundle are excluded."""
    source = tmp_path / "sub" / "a.md"
    source.parent.mkdir(parents=True)
    body = "[Outside](../../outside.md) [Local](b.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["sub/b.md"]


def test_extract_outgoing_links_sorts_results(tmp_path: Path) -> None:
    """Results are sorted alphabetically."""
    source = tmp_path / "src.md"
    body = "[Z](z.md) [A](a.md) [M](m.md)"
    result = extract_outgoing_links(body, source, tmp_path)
    assert result == ["a.md", "m.md", "z.md"]


# ---------------------------------------------------------------------------
# build_link_graph
# ---------------------------------------------------------------------------


def test_build_link_graph_builds_outgoing_and_incoming(tmp_path: Path) -> None:
    """Builds both outgoing and incoming link graphs."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: concept\n---\n\n# A\n\nLink to [B](b.md)\n")
    (bundle / "b.md").write_text("---\ntype: concept\n---\n\n# B\n\nLink to [A](a.md)\n")
    outgoing, incoming = build_link_graph(bundle)
    assert outgoing == {"a.md": ["b.md"], "b.md": ["a.md"]}
    assert incoming == {"a.md": ["b.md"], "b.md": ["a.md"]}


def test_build_link_graph_skips_reserved_files(tmp_path: Path) -> None:
    """Reserved files are excluded from the graph."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "index.md").write_text("---\ntype: index\n---\n\n# Index\n\n[Link](concept.md)\n")
    (bundle / "concept.md").write_text("---\ntype: concept\n---\n\n# Concept\n")
    outgoing, incoming = build_link_graph(bundle)
    assert "index.md" not in outgoing
    assert "concept.md" not in incoming


def test_build_link_graph_multiple_backlinks(tmp_path: Path) -> None:
    """A concept can have multiple backlinks."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: concept\n---\n\n# A\n\nLink to [C](c.md)\n")
    (bundle / "b.md").write_text("---\ntype: concept\n---\n\n# B\n\nLink to [C](c.md)\n")
    (bundle / "c.md").write_text("---\ntype: concept\n---\n\n# C\n")
    outgoing, incoming = build_link_graph(bundle)
    assert incoming["c.md"] == ["a.md", "b.md"]


def test_build_link_graph_no_links(tmp_path: Path) -> None:
    """Concepts with no links produce empty graphs."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.md").write_text("---\ntype: concept\n---\n\n# A\n")
    outgoing, incoming = build_link_graph(bundle)
    assert outgoing == {}
    assert incoming == {}
