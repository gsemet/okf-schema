"""Tests for the public Python API."""

from __future__ import annotations

from pathlib import Path

import pytest

from okf_schema._internal.models import (
    BundleStats,
    ConceptDetail,
    ConceptSummary,
    IndexUpdate,
    Report,
    SearchResult,
)
from okf_schema.api import (
    format_bundle,
    graph_bundle,
    index_bundle,
    lint_bundle,
    list_bundle,
    search_bundle,
    show_bundle,
    stats_bundle,
    validate_bundle,
)
from okf_schema.formatter import FormattedResult

FIXTURES = Path(__file__).parent / "fixtures"
BUNDLE_FIXTURES = FIXTURES / "bundle"
VALID_BUNDLE = BUNDLE_FIXTURES / "valid"


# ---------------------------------------------------------------------------
# validate_bundle
# ---------------------------------------------------------------------------


class TestValidateBundle:
    """Tests for validate_bundle."""

    def test_returns_report_for_valid_bundle(self) -> None:
        """Returns a conformant Report for a valid bundle."""
        report = validate_bundle(VALID_BUNDLE)
        assert isinstance(report, Report)
        assert report.is_conformant is True

    def test_returns_report_for_invalid_bundle(self) -> None:
        """Returns a non-conformant Report for an invalid bundle."""
        invalid = BUNDLE_FIXTURES / "invalid" / "e1-no-frontmatter"
        report = validate_bundle(invalid)
        assert isinstance(report, Report)
        assert report.is_conformant is False
        assert any(f.code == "E1" for f in report.errors)

    def test_with_schema_db(self) -> None:
        """Loads and applies schema database when provided."""
        schema_db = FIXTURES / "schema"
        report = validate_bundle(VALID_BUNDLE, schema_db=schema_db)
        assert isinstance(report, Report)

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            validate_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            validate_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_accepts_string_path(self) -> None:
        """Accepts str as well as Path."""
        report = validate_bundle(str(VALID_BUNDLE))
        assert isinstance(report, Report)

    def test_empty_bundle(self, tmp_path: Path) -> None:
        """Returns conformant report for empty bundle."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        report = validate_bundle(bundle)
        assert isinstance(report, Report)
        assert report.is_conformant is True


# ---------------------------------------------------------------------------
# format_bundle
# ---------------------------------------------------------------------------


class TestFormatBundle:
    """Tests for format_bundle."""

    def test_returns_list_of_formatted_results(self) -> None:
        """Returns a list of FormattedResult objects."""
        results = format_bundle(VALID_BUNDLE)
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, FormattedResult)

    def test_check_mode_no_changes(self, tmp_path: Path) -> None:
        """Check mode does not modify files."""
        # Copy valid bundle to temp
        import shutil

        bundle = tmp_path / "bundle"
        shutil.copytree(VALID_BUNDLE, bundle)
        original_mtime = (bundle / "subdir" / "concept-a.md").stat().st_mtime

        results = format_bundle(bundle, check=True)
        assert isinstance(results, list)
        # File should not be modified
        assert (bundle / "subdir" / "concept-a.md").stat().st_mtime == original_mtime

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            format_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            format_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_diff_mode(self, tmp_path: Path) -> None:
        """diff mode returns results with diff field."""
        import shutil

        bundle = tmp_path / "bundle"
        shutil.copytree(VALID_BUNDLE, bundle)
        results = format_bundle(bundle, diff=True)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# list_bundle
# ---------------------------------------------------------------------------


class TestListBundle:
    """Tests for list_bundle."""

    def test_returns_sorted_concept_summaries(self) -> None:
        """Returns sorted list of ConceptSummary objects."""
        concepts = list_bundle(VALID_BUNDLE)
        assert isinstance(concepts, list)
        for concept in concepts:
            assert isinstance(concept, ConceptSummary)
            assert concept.path
            assert concept.type
            assert concept.title

    def test_sorted_by_path(self) -> None:
        """Results are sorted by path."""
        concepts = list_bundle(VALID_BUNDLE)
        paths = [c.path for c in concepts]
        assert paths == sorted(paths)

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            list_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            list_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_empty_bundle_returns_empty(self, tmp_path: Path) -> None:
        """Returns empty list for empty bundle."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concepts = list_bundle(bundle)
        assert concepts == []


# ---------------------------------------------------------------------------
# show_bundle
# ---------------------------------------------------------------------------


class TestShowBundle:
    """Tests for show_bundle."""

    def test_returns_concept_detail(self) -> None:
        """Returns ConceptDetail with frontmatter and body."""
        detail = show_bundle(VALID_BUNDLE, "subdir/concept-a.md")
        assert isinstance(detail, ConceptDetail)
        assert isinstance(detail.frontmatter, dict)
        assert "title" in detail.frontmatter
        assert isinstance(detail.body, str)
        assert "# Concept A" in detail.body

    def test_invalid_concept_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent concept path."""
        with pytest.raises(FileNotFoundError):
            show_bundle(VALID_BUNDLE, "does-not-exist.md")

    def test_nonexistent_bundle_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            show_bundle(VALID_BUNDLE / "missing", "concept.md")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when bundle path is a file."""
        with pytest.raises(NotADirectoryError):
            show_bundle(VALID_BUNDLE / "subdir" / "concept-a.md", "concept.md")

    def test_concept_without_frontmatter(self, tmp_path: Path) -> None:
        """Returns empty frontmatter for concept without frontmatter."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "no-fm.md").write_text("# No Frontmatter\n\nBody.\n", encoding="utf-8")
        detail = show_bundle(bundle, "no-fm.md")
        assert detail.frontmatter == {}
        assert "# No Frontmatter" in detail.body


# ---------------------------------------------------------------------------
# index_bundle
# ---------------------------------------------------------------------------


class TestIndexBundle:
    """Tests for index_bundle."""

    def test_returns_index_updates(self) -> None:
        """Returns list of IndexUpdate objects."""
        updates = index_bundle(VALID_BUNDLE)
        assert isinstance(updates, list)
        for update in updates:
            assert isinstance(update, IndexUpdate)
            assert update.action in ("created", "updated", "unchanged")

    def test_creates_missing_index(self, tmp_path: Path) -> None:
        """Creates missing index.md files."""
        import shutil

        bundle = tmp_path / "bundle"
        shutil.copytree(VALID_BUNDLE, bundle)
        # Remove a subdir index
        (bundle / "subdir" / "index.md").unlink()
        assert not (bundle / "subdir" / "index.md").exists()

        updates = index_bundle(bundle)
        assert any(u.action in ("created", "updated") and "subdir" in u.path for u in updates)
        assert (bundle / "subdir" / "index.md").exists()

    def test_preserves_root_frontmatter(self, tmp_path: Path) -> None:
        """Preserves frontmatter in bundle-root index.md."""
        import shutil

        bundle = tmp_path / "bundle"
        shutil.copytree(VALID_BUNDLE, bundle)
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "okf_version" in content

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            index_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            index_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_empty_directory_skipped(self, tmp_path: Path) -> None:
        """Empty subdirectories without markdown are skipped."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "empty_subdir").mkdir()
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n",
            encoding="utf-8",
        )
        updates = index_bundle(bundle)
        # Only root index should be created/updated
        assert any(u.path == "index.md" for u in updates)
        # No index in empty_subdir
        assert not any("empty_subdir" in u.path for u in updates)

    def test_unchanged_when_content_identical(self, tmp_path: Path) -> None:
        """Marks index as unchanged when content is already up-to-date."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n",
            encoding="utf-8",
        )
        # First run creates the index
        updates1 = index_bundle(bundle)
        created = [u for u in updates1 if u.path == "index.md"]
        assert len(created) == 1
        assert created[0].action == "created"
        # Second run with identical content should report unchanged
        updates2 = index_bundle(bundle)
        unchanged = [u for u in updates2 if u.path == "index.md"]
        assert len(unchanged) == 1
        assert unchanged[0].action == "unchanged"

    def test_index_bundle_accepts_string_path(self) -> None:
        """Accepts str as well as Path."""
        updates = index_bundle(str(VALID_BUNDLE))
        assert isinstance(updates, list)
        for update in updates:
            assert isinstance(update, IndexUpdate)

    def test_preserves_existing_descriptions(self, tmp_path: Path) -> None:
        """Preserves custom descriptions from existing index.md."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n",
            encoding="utf-8",
        )
        # Create an index with a custom description
        (bundle / "index.md").write_text(
            "# bundle\n\n- [C](concept.md) — Custom description\n",
            encoding="utf-8",
        )
        updates = index_bundle(bundle)
        updated = [u for u in updates if u.path == "index.md"]
        assert len(updated) == 1
        assert updated[0].action == "updated"
        content = (bundle / "index.md").read_text(encoding="utf-8")
        assert "Custom description" in content

    def test_subdir_description_from_index_body(self, tmp_path: Path) -> None:
        """Extracts subdirectory description from its index.md body."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "subdir"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n",
            encoding="utf-8",
        )
        (subdir / "index.md").write_text(
            "# Subdir\n\nIntro line.\n\n- [C](concept.md) — desc\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "Intro line." in content

    def test_subdir_description_oserror(self, tmp_path: Path) -> None:
        """Falls back to default description when index.md cannot be read."""
        from okf_schema.api import _get_subdir_description

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        index_path = subdir / "index.md"
        index_path.write_text("# S\n", encoding="utf-8")
        # Make file unreadable
        index_path.chmod(0o000)
        try:
            desc = _get_subdir_description(subdir)
            assert "Auto-generated index" in desc
        finally:
            index_path.chmod(0o644)

    def test_generate_index_content_empty(self, tmp_path: Path) -> None:
        """Generates placeholder when no concepts or subdirs exist."""
        from okf_schema.api import _generate_index_content

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        content = _generate_index_content(bundle, bundle)
        assert "No concepts or subdirectories found." in content

    def test_parse_existing_index_no_h1(self) -> None:
        """Parses index without H1 gracefully."""
        from okf_schema.api import _parse_existing_index

        text = "- [Link](target.md) — Description\n"
        result = _parse_existing_index(text)
        assert result["title"] == ""
        assert result["descriptions"] == {"target.md": "Description"}

    def test_parse_existing_index_with_intro(self, tmp_path: Path) -> None:
        """Preserves intro text between H1 and list items."""
        from okf_schema.api import _parse_existing_index

        text = "# Title\n\nIntro paragraph.\n\n- [Link](target.md) — desc\n"
        result = _parse_existing_index(text)
        assert result["title"] == "Title"
        assert result["intro"] == "Intro paragraph."


# ---------------------------------------------------------------------------
# search_bundle
# ---------------------------------------------------------------------------


class TestSearchBundle:
    """Tests for search_bundle."""

    def test_finds_by_title_substring(self) -> None:
        """Finds concepts by title substring (case-insensitive)."""
        results = search_bundle(VALID_BUNDLE, "concept")
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert isinstance(result, SearchResult)

    def test_finds_by_tag_substring(self, tmp_path: Path) -> None:
        """Finds concepts by tag substring."""
        import shutil

        bundle = tmp_path / "bundle"
        shutil.copytree(VALID_BUNDLE, bundle)
        # Add a concept with tags
        concept = bundle / "tagged.md"
        concept.write_text(
            "---\ntitle: Tagged Concept\ntype: concept\ntags: [python, cli]\n---\n\n# Tagged\n",
            encoding="utf-8",
        )
        results = search_bundle(bundle, "python")
        assert any(r.title == "Tagged Concept" for r in results)

    def test_empty_list_for_non_matching(self) -> None:
        """Returns empty list when no concepts match."""
        results = search_bundle(VALID_BUNDLE, "xyznonexistent")
        assert results == []

    def test_case_insensitive(self) -> None:
        """Search is case-insensitive."""
        results_lower = search_bundle(VALID_BUNDLE, "concept")
        results_upper = search_bundle(VALID_BUNDLE, "CONCEPT")
        assert len(results_lower) == len(results_upper)

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            search_bundle(VALID_BUNDLE / "does-not-exist", "query")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            search_bundle(VALID_BUNDLE / "subdir" / "concept-a.md", "query")

    def test_skips_reserved_files(self, tmp_path: Path) -> None:
        """Reserved files (index.md, log.md) are not searched."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            "---\ntitle: Index\ntype: index\n---\n\n# Index\n",
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntitle: Concept\ntype: concept\n---\n\n# Concept\n",
            encoding="utf-8",
        )
        results = search_bundle(bundle, "concept")
        # Should only find concept.md, not index.md
        assert len(results) == 1
        assert results[0].path == "concept.md"

    def test_skips_no_frontmatter(self, tmp_path: Path) -> None:
        """Files without frontmatter are skipped in search."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "no-fm.md").write_text("# No FM\n\nBody.\n", encoding="utf-8")
        results = search_bundle(bundle, "no")
        assert results == []

    def test_skips_unparseable_frontmatter(self, tmp_path: Path) -> None:
        """Files with unparseable frontmatter are skipped in search."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "bad.md").write_text("---\n: bad yaml\n---\n\n# Bad\n", encoding="utf-8")
        results = search_bundle(bundle, "bad")
        assert results == []


# ---------------------------------------------------------------------------
# graph_bundle
# ---------------------------------------------------------------------------


class TestGraphBundle:
    """Tests for graph_bundle."""

    def test_returns_adjacency_dict(self) -> None:
        """Returns dict mapping concept paths to linked concepts."""
        graph = graph_bundle(VALID_BUNDLE)
        assert isinstance(graph, dict)

    def test_cross_linked_concepts(self, tmp_path: Path) -> None:
        """Correctly maps cross-linked concepts."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\nLink to [B](b.md)\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntitle: B\ntype: concept\n---\n\n# B\n\nLink to [A](a.md)\n",
            encoding="utf-8",
        )
        graph = graph_bundle(bundle)
        assert "a.md" in graph
        assert "b.md" in graph["a.md"]
        assert "a.md" in graph["b.md"]

    def test_skips_external_links(self, tmp_path: Path) -> None:
        """External URLs are not included in the graph."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[External](https://example.com)\n",
            encoding="utf-8",
        )
        graph = graph_bundle(bundle)
        assert graph == {} or "https://example.com" not in str(graph)

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            graph_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            graph_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_skips_reserved_files(self, tmp_path: Path) -> None:
        """Reserved files are not included in the graph."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            "---\ntitle: Index\ntype: index\n---\n\n# Index\n\n[Link](concept.md)\n",
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n", encoding="utf-8"
        )
        graph = graph_bundle(bundle)
        assert "index.md" not in graph

    def test_self_link_excluded(self, tmp_path: Path) -> None:
        """Links to self are not included in graph."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[Self](a.md)\n",
            encoding="utf-8",
        )
        graph = graph_bundle(bundle)
        assert "a.md" not in graph or "a.md" not in graph.get("a.md", [])

    def test_link_outside_bundle_excluded(self, tmp_path: Path) -> None:
        """Links outside the bundle are not included."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[Outside](/outside.md)\n",
            encoding="utf-8",
        )
        graph = graph_bundle(bundle)
        assert graph == {} or "/outside.md" not in str(graph)


# ---------------------------------------------------------------------------
# stats_bundle
# ---------------------------------------------------------------------------


class TestStatsBundle:
    """Tests for stats_bundle."""

    def test_returns_bundle_stats(self) -> None:
        """Returns BundleStats with correct metrics."""
        stats = stats_bundle(VALID_BUNDLE)
        assert isinstance(stats, BundleStats)
        assert stats.total_concepts >= 0
        assert stats.total_links >= 0
        assert stats.broken_links >= 0
        assert isinstance(stats.types_distribution, dict)
        assert isinstance(stats.tags_distribution, dict)
        assert stats.directories >= 0

    def test_counts_concepts_correctly(self, tmp_path: Path) -> None:
        """Counts total concepts accurately."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntitle: B\ntype: pattern\n---\n\n# B\n",
            encoding="utf-8",
        )
        stats = stats_bundle(bundle)
        assert stats.total_concepts == 2
        assert stats.types_distribution == {"concept": 1, "pattern": 1}

    def test_counts_tags(self, tmp_path: Path) -> None:
        """Counts tags distribution accurately."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\ntags: [python, cli]\n---\n\n# A\n",
            encoding="utf-8",
        )
        stats = stats_bundle(bundle)
        assert stats.tags_distribution == {"python": 1, "cli": 1}

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            stats_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            stats_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")

    def test_counts_files_without_frontmatter(self, tmp_path: Path) -> None:
        """Counts files without frontmatter correctly."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "no-fm.md").write_text("# No FM\n\nBody.\n", encoding="utf-8")
        stats = stats_bundle(bundle)
        assert stats.total_files == 1
        assert stats.total_concepts == 1
        assert stats.files_without_frontmatter == 1

    def test_counts_reserved_files(self, tmp_path: Path) -> None:
        """Reserved files count toward total_files but not total_concepts."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text("# Index\n", encoding="utf-8")
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n", encoding="utf-8"
        )
        stats = stats_bundle(bundle)
        assert stats.total_files == 2
        assert stats.total_concepts == 1

    def test_counts_directories(self, tmp_path: Path) -> None:
        """Counts directories with markdown files."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "subdir"
        subdir.mkdir()
        (subdir / "a.md").write_text("---\ntitle: A\ntype: concept\n---\n\n# A\n", encoding="utf-8")
        (bundle / "b.md").write_text("---\ntitle: B\ntype: concept\n---\n\n# B\n", encoding="utf-8")
        stats = stats_bundle(bundle)
        assert stats.directories == 2  # bundle root + subdir

    def test_counts_broken_links(self, tmp_path: Path) -> None:
        """Counts broken internal links."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[Broken](missing.md)\n",
            encoding="utf-8",
        )
        stats = stats_bundle(bundle)
        assert stats.total_links == 1
        assert stats.broken_links == 1

    def test_no_tags_means_empty_distribution(self, tmp_path: Path) -> None:
        """Empty tags_distribution when no tags present."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text("---\ntitle: A\ntype: concept\n---\n\n# A\n", encoding="utf-8")
        stats = stats_bundle(bundle)
        assert stats.tags_distribution == {}


# ---------------------------------------------------------------------------
# lint_bundle
# ---------------------------------------------------------------------------


class TestLintBundleAPI:
    """Tests for lint_bundle via the public API."""

    def test_converts_block_lists(self, tmp_path: Path) -> None:
        """lint_bundle converts block-style lists to inline."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        results = lint_bundle(bundle)
        assert len(results) == 1
        assert results[0].changed is True
        text = (bundle / "concept.md").read_text(encoding="utf-8")
        assert "tags: [a, b]" in text

    def test_check_mode(self, tmp_path: Path) -> None:
        """lint_bundle with check=True does not modify files."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        original = "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n"
        (bundle / "concept.md").write_text(original, encoding="utf-8")
        results = lint_bundle(bundle, check=True)
        assert len(results) == 1
        assert results[0].changed is True
        assert (bundle / "concept.md").read_text(encoding="utf-8") == original

    def test_no_changes_when_inline(self, tmp_path: Path) -> None:
        """lint_bundle returns changed=False when lists are already inline."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags: [a, b]\n---\n\n# Test\n",
            encoding="utf-8",
        )
        results = lint_bundle(bundle)
        assert len(results) == 1
        assert results[0].changed is False
