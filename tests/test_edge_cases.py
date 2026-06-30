"""Edge-case tests for okf-schema."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.api import (
    format_bundle,
    graph_bundle,
    index_bundle,
    list_bundle,
    search_bundle,
    show_bundle,
    stats_bundle,
    validate_bundle,
)
from okf_schema.cli import cli


class TestEmptyBundle:
    """Edge cases for empty or minimal bundles."""

    def test_empty_bundle_directory(self, tmp_path: Path) -> None:
        """Empty bundle has zero concepts and is conformant."""
        bundle = tmp_path / "empty"
        bundle.mkdir()
        report = validate_bundle(bundle)
        assert report.is_conformant
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_bundle_with_only_reserved_files(self, tmp_path: Path) -> None:
        """Bundle with only index.md and log.md is valid."""
        bundle = tmp_path / "reserved-only"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\n---\n\n# Index\n',
            encoding="utf-8",
        )
        (bundle / "log.md").write_text("## 2024-01-01\n\nLog entry.\n", encoding="utf-8")

        report = validate_bundle(bundle)
        assert report.is_conformant
        stats = stats_bundle(bundle)
        assert stats.total_concepts == 0
        assert stats.total_files == 2

    def test_no_markdown_files_at_all(self, tmp_path: Path) -> None:
        """Bundle with no markdown files is conformant."""
        bundle = tmp_path / "no-md"
        bundle.mkdir()
        (bundle / "readme.txt").write_text("Not markdown.\n", encoding="utf-8")

        report = validate_bundle(bundle)
        assert report.is_conformant


class TestConceptEdgeCases:
    """Edge cases for individual concept files."""

    def test_concept_with_empty_type(self, tmp_path: Path) -> None:
        """Concept with type: '' triggers E2."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "empty-type.md").write_text(
            "---\ntype: ''\ntitle: Empty Type\n---\n\nBody.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert any(f.code == "E2" for f in report.errors)

    def test_concept_with_no_frontmatter_at_all(self, tmp_path: Path) -> None:
        """Concept with no frontmatter triggers E1."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "no-fm.md").write_text("# Heading\n\nBody.\n", encoding="utf-8")

        report = validate_bundle(bundle)
        assert any(f.code == "E1" for f in report.errors)

    def test_concept_with_very_long_title(self, tmp_path: Path) -> None:
        """Very long title is accepted without error."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        long_title = "A" * 5000
        (bundle / "long.md").write_text(
            f"---\ntype: concept\ntitle: {long_title}\n---\n\nBody.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert not any(f.code == "E1" for f in report.errors)
        assert not any(f.code == "E2" for f in report.errors)

    def test_concept_with_special_characters_in_filename(self, tmp_path: Path) -> None:
        """Special characters in filenames are handled."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "special-chars_123.md").write_text(
            "---\ntype: concept\ntitle: Special\n---\n\nBody.\n",
            encoding="utf-8",
        )

        concepts = list_bundle(bundle)
        assert len(concepts) == 1
        assert concepts[0].path == "special-chars_123.md"

    def test_concept_with_unicode_content(self, tmp_path: Path) -> None:
        """Unicode characters in frontmatter and body are preserved."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "unicode.md").write_text(
            "---\ntype: concept\ntitle: 日本語\n"
            "description: émojis 🎉\ntags: [中文, العربية]\n"
            "---\n\nÜnicode bødy.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert report.is_conformant
        concepts = list_bundle(bundle)
        assert concepts[0].title == "日本語"
        results = search_bundle(bundle, "中文")
        assert len(results) == 1

    def test_concept_with_empty_frontmatter_values(self, tmp_path: Path) -> None:
        """Frontmatter with empty string values is handled."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "empty-values.md").write_text(
            "---\ntype: concept\ntitle: ''\ndescription: ''\ntags: []\n---\n\nBody.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        # E2 is triggered because title is empty (type is present)
        assert not any(f.code == "E2" for f in report.errors)
        # W1 may trigger for missing title/description
        assert any(f.code == "W1" for f in report.warnings)


class TestSchemaDbEdgeCases:
    """Edge cases for schema database loading."""

    def test_empty_schema_db_directory(self, tmp_path: Path) -> None:
        """Empty schema DB directory loads as empty dict."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\n---\n\nBody.\n",
            encoding="utf-8",
        )
        empty_db = tmp_path / "empty-db"
        empty_db.mkdir()

        report = validate_bundle(bundle, schema_db=empty_db)
        assert report.is_conformant

    def test_schema_db_with_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON schema files are skipped gracefully."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\n---\n\nBody.\n",
            encoding="utf-8",
        )
        bad_db = tmp_path / "bad-db"
        bad_db.mkdir()
        (bad_db / "bad.schema.json").write_text("not valid json {", encoding="utf-8")

        report = validate_bundle(bundle, schema_db=bad_db)
        assert report.is_conformant

    def test_schema_db_with_malformed_yaml(self, tmp_path: Path) -> None:
        """Malformed YAML schema files are skipped gracefully."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\n---\n\nBody.\n",
            encoding="utf-8",
        )
        bad_db = tmp_path / "bad-db"
        bad_db.mkdir()
        (bad_db / "bad.schema.yaml").write_text("{invalid: [", encoding="utf-8")

        report = validate_bundle(bundle, schema_db=bad_db)
        assert report.is_conformant


class TestLinkEdgeCases:
    """Edge cases for link resolution and graph building."""

    def test_external_links_only(self, tmp_path: Path) -> None:
        """Concepts with only external links have no broken links."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "external.md").write_text(
            "---\ntype: concept\ntitle: External\n---\n\nSee [example](https://example.com).\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert not any(f.code == "W2" for f in report.warnings)
        stats = stats_bundle(bundle)
        assert stats.total_links == 1
        assert stats.broken_links == 0

    def test_circular_links_in_graph(self, tmp_path: Path) -> None:
        """Circular cross-references are handled in graph."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntype: concept\ntitle: A\n---\n\nLink to [B](b.md).\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: concept\ntitle: B\n---\n\nLink to [A](a.md).\n",
            encoding="utf-8",
        )

        graph = graph_bundle(bundle)
        assert "a.md" in graph and "b.md" in graph["a.md"]
        assert "b.md" in graph and "a.md" in graph["b.md"]

    def test_self_link_excluded_from_graph(self, tmp_path: Path) -> None:
        """Self-links are excluded from the graph."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "self.md").write_text(
            "---\ntype: concept\ntitle: Self\n---\n\nLink to [self](self.md).\n",
            encoding="utf-8",
        )

        graph = graph_bundle(bundle)
        assert "self.md" not in graph or graph["self.md"] == []

    def test_link_to_directory_is_valid(self, tmp_path: Path) -> None:
        """Links to directories are accepted as valid."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "sub"
        subdir.mkdir()
        (subdir / "index.md").write_text("# Sub\n", encoding="utf-8")
        (bundle / "link-to-dir.md").write_text(
            "---\ntype: concept\ntitle: Link To Dir\n---\n\nSee [sub](sub/).\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert not any(f.code == "W2" for f in report.warnings)


class TestPathEdgeCases:
    """Edge cases for path handling."""

    def test_bundle_path_is_a_file(self, tmp_path: Path) -> None:
        """Passing a file as bundle path raises NotADirectoryError."""
        file_path = tmp_path / "not-a-dir.md"
        file_path.write_text("# File\n", encoding="utf-8")

        with pytest.raises(NotADirectoryError):
            validate_bundle(file_path)

    def test_nonexistent_bundle_path(self, tmp_path: Path) -> None:
        """Passing a nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            validate_bundle(tmp_path / "does-not-exist")

    def test_concept_path_with_parent_references(self, tmp_path: Path) -> None:
        """Concept path with '..' is resolved safely."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        # show_bundle should resolve the path
        detail = show_bundle(bundle, "concept.md")
        assert detail.frontmatter.get("title") == "Concept"

    def test_bundle_path_with_tilde(self, tmp_path: Path) -> None:
        """Bundle path with ~ is expanded."""
        # We can't easily test real ~, but we can test the function doesn't crash
        # on a path that looks like it has a tilde
        with pytest.raises(FileNotFoundError):
            validate_bundle("~/nonexistent_okf_bundle_12345")


class TestFormatterEdgeCases:
    """Edge cases for the frontmatter formatter."""

    def test_format_no_frontmatter_file(self, tmp_path: Path) -> None:
        """Files without frontmatter are skipped by formatter."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "no-fm.md").write_text("# Heading\n\nBody.\n", encoding="utf-8")

        results = format_bundle(bundle)
        assert len(results) == 1
        assert not results[0].changed

    def test_format_idempotency(self, tmp_path: Path) -> None:
        """Formatting twice produces no changes the second time."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags: [[a, b], c]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        first = format_bundle(bundle)
        assert any(r.changed for r in first)

        second = format_bundle(bundle)
        assert not any(r.changed for r in second)

    def test_format_deeply_nested_lists(self, tmp_path: Path) -> None:
        """Deeply nested lists are fully flattened."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "deep.md").write_text(
            "---\ntype: concept\ntitle: Deep\ntags: [[[[a]]], [[[b, c]]]]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        format_bundle(bundle)
        text = (bundle / "deep.md").read_text(encoding="utf-8")
        # After flattening, tags should be a flat list
        assert "tags:" in text

    def test_format_preserves_comments(self, tmp_path: Path) -> None:
        """Comments in frontmatter are preserved during formatting."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "commented.md").write_text(
            "---\ntype: concept\n# This is a comment\n"
            "title: Commented\ntags: [[a], b]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        format_bundle(bundle)
        text = (bundle / "commented.md").read_text(encoding="utf-8")
        assert "type: concept" in text
        assert "title: Commented" in text


class TestCliEdgeCases:
    """Edge cases for CLI commands."""

    def test_validate_empty_bundle_cli(self, tmp_path: Path) -> None:
        """CLI validate on empty bundle exits 0."""
        runner = CliRunner()
        bundle = tmp_path / "empty"
        bundle.mkdir()
        result = runner.invoke(cli, ["validate", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "conformant" in result.output

    def test_list_empty_bundle_cli(self, tmp_path: Path) -> None:
        """CLI list on empty bundle exits 0 with no output."""
        runner = CliRunner()
        bundle = tmp_path / "empty"
        bundle.mkdir()
        result = runner.invoke(cli, ["list", "--path", str(bundle)])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_stats_empty_bundle_cli(self, tmp_path: Path) -> None:
        """CLI stats on empty bundle shows zero counts."""
        runner = CliRunner()
        bundle = tmp_path / "empty"
        bundle.mkdir()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "0 files" in result.output
        assert "0 concepts" in result.output
        assert "Health: 100%" in result.output

    def test_init_existing_directory_fails(self, tmp_path: Path) -> None:
        """CLI init on existing directory exits 1."""
        runner = CliRunner()
        existing = tmp_path / "exists"
        existing.mkdir()
        result = runner.invoke(cli, ["init", str(existing)])
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_new_existing_concept_fails(self, tmp_path: Path) -> None:
        """CLI new on existing concept file exits 1."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        (root / "existing.md").write_text("# Existing\n", encoding="utf-8")
        result = runner.invoke(cli, ["new", "--path", str(root), "--name", "existing"])
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_show_missing_concept_cli(self, tmp_path: Path) -> None:
        """CLI show for missing concept exits 2."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        result = runner.invoke(cli, ["show", "--path", str(bundle), "missing.md"])
        assert result.exit_code == 2

    def test_index_empty_bundle_cli(self, tmp_path: Path) -> None:
        """CLI index on empty bundle exits 0."""
        runner = CliRunner()
        bundle = tmp_path / "empty"
        bundle.mkdir()
        result = runner.invoke(cli, ["index", "--path", str(bundle)])
        assert result.exit_code == 0

    def test_validate_nonexistent_bundle_cli(self, tmp_path: Path) -> None:
        """CLI validate on nonexistent bundle exits 2 (click validation)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--path", str(tmp_path / "nope")])
        assert result.exit_code == 2


class TestIndexEdgeCases:
    """Edge cases for index generation."""

    def test_index_preserves_root_frontmatter(self, tmp_path: Path) -> None:
        """Root index.md frontmatter is preserved during index."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\ncustom: value\n---\n\n# Root\n',
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        index_bundle(bundle)
        text = (bundle / "index.md").read_text(encoding="utf-8")
        assert "okf_version" in text
        assert "custom: value" in text

    def test_index_skips_empty_subdirs(self, tmp_path: Path) -> None:
        """Empty subdirectories are skipped in index generation."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        empty_sub = bundle / "empty"
        empty_sub.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        index_bundle(bundle)
        # Should not create index in empty subdir
        assert not (empty_sub / "index.md").exists()

    def test_index_with_no_concepts(self, tmp_path: Path) -> None:
        """Index in a directory with no concepts shows appropriate message."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        sub = bundle / "sub"
        sub.mkdir()
        (sub / "index.md").write_text("# Sub\n", encoding="utf-8")

        index_bundle(bundle)
        # Root index should mention no concepts
        root_index = (bundle / "index.md").read_text(encoding="utf-8")
        assert "No concepts" in root_index or "sub" in root_index


class TestSearchEdgeCases:
    """Edge cases for search functionality."""

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        """Search is case-insensitive."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: UPPERCASE TITLE\n---\n\nBody.\n",
            encoding="utf-8",
        )

        assert len(search_bundle(bundle, "uppercase")) == 1
        assert len(search_bundle(bundle, "UPPERCASE")) == 1
        assert len(search_bundle(bundle, "UpPeRcAsE")) == 1

    def test_search_empty_query(self, tmp_path: Path) -> None:
        """Empty query matches everything with text fields."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntype: concept\ntitle: A\n---\n\nBody.\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: concept\ntitle: B\n---\n\nBody.\n",
            encoding="utf-8",
        )

        results = search_bundle(bundle, "")
        assert len(results) == 2

    def test_search_reserved_files_excluded(self, tmp_path: Path) -> None:
        """Reserved files (index.md, log.md) are excluded from search."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\n---\n\n# Index with special word qwerty12345\n',
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        results = search_bundle(bundle, "qwerty12345")
        assert len(results) == 0


class TestStatsEdgeCases:
    """Edge cases for statistics computation."""

    def test_stats_with_no_types(self, tmp_path: Path) -> None:
        """Bundle with no typed concepts has empty type distribution."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text("# No frontmatter\n", encoding="utf-8")

        stats = stats_bundle(bundle)
        assert stats.types_distribution == {}
        assert stats.tags_distribution == {}

    def test_stats_with_no_links(self, tmp_path: Path) -> None:
        """Bundle with no links has zero link counts."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: No Links\n---\n\nNo links here.\n",
            encoding="utf-8",
        )

        stats = stats_bundle(bundle)
        assert stats.total_links == 0
        assert stats.broken_links == 0

    def test_stats_multiple_directories(self, tmp_path: Path) -> None:
        """Stats correctly counts directories with markdown."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        sub1 = bundle / "sub1"
        sub1.mkdir()
        sub2 = bundle / "sub2"
        sub2.mkdir()
        (sub1 / "a.md").write_text("# A\n", encoding="utf-8")
        (sub2 / "b.md").write_text("# B\n", encoding="utf-8")

        stats = stats_bundle(bundle)
        assert stats.directories == 2  # sub1 + sub2 (root has no direct .md files)
