"""Tests for the public Python API."""

from __future__ import annotations

from pathlib import Path

import pytest

from okf_schema._internal.models import (
    BacklinkResult,
    BundleStats,
    ConceptDetail,
    ConceptSummary,
    IndexUpdate,
    Report,
    SearchResult,
)
from okf_schema.api import (
    _get_subdir_description,
    backlinks_bundle,
    format_bundle,
    graph_bundle,
    index_bundle,
    lint_bundle,
    list_bundle,
    search_bundle,
    show_bundle,
    stats_bundle,
    validate_bundle,
    validate_markdown_files,
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
# validate_markdown_files
# ---------------------------------------------------------------------------


class TestValidateMarkdownFiles:
    """Tests for validate_markdown_files."""

    def test_returns_report_for_valid_files(self, tmp_path: Path) -> None:
        """Returns a Report for valid markdown files."""

        # Create test file with valid frontmatter
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: concept\ntitle: Test\n---\n\n# Test Content\n",
            encoding="utf-8",
        )

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)

    def test_single_input_pattern(self, tmp_path: Path) -> None:
        """Accepts single input pattern as string."""

        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: concept\ntitle: Test\n---\n\n# Test\n",
            encoding="utf-8",
        )

        report = validate_markdown_files(str(test_file))
        assert isinstance(report, Report)

    def test_multiple_input_patterns(self, tmp_path: Path) -> None:
        """Accepts multiple input patterns."""

        file1 = tmp_path / "file1.md"
        file1.write_text("---\ntype: concept\ntitle: Test1\n---\n\nContent\n", encoding="utf-8")
        file2 = tmp_path / "file2.md"
        file2.write_text("---\ntype: concept\ntitle: Test2\n---\n\nContent\n", encoding="utf-8")

        report = validate_markdown_files([str(file1), str(file2)])
        assert isinstance(report, Report)

    def test_glob_pattern_support(self, tmp_path: Path) -> None:
        """Supports glob patterns including **."""

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.md"
        file1.write_text("---\ntype: concept\ntitle: Test1\n---\n\nContent\n", encoding="utf-8")
        file2 = subdir / "file2.md"
        file2.write_text("---\ntype: concept\ntitle: Test2\n---\n\nContent\n", encoding="utf-8")

        pattern = str(tmp_path / "**" / "*.md")
        report = validate_markdown_files([pattern], schemas_dir=None)
        assert isinstance(report, Report)

    def test_error_detection_no_frontmatter(self, tmp_path: Path) -> None:
        """Detects missing frontmatter (E1 error)."""

        test_file = tmp_path / "test.md"
        test_file.write_text("# No Frontmatter\n\nContent without YAML.\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert any(f.code == "E1" for f in report.errors)

    def test_error_detection_missing_type(self, tmp_path: Path) -> None:
        """Detects missing type field (E2 error)."""

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntitle: Test\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert any(f.code == "E2" for f in report.errors)

    def test_no_files_found_returns_empty_report(self) -> None:
        """Returns empty report when no files match patterns."""

        report = validate_markdown_files(["nonexistent_dir_xyz/**/*.md"])
        assert isinstance(report, Report)
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_unparseable_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Detects unparseable YAML frontmatter (E1 error)."""

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ninvalid: [yaml: content\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert any(f.code == "E1" for f in report.errors)

    def test_missing_title_and_description_warnings(self, tmp_path: Path) -> None:
        """Detects missing title and description (W1 warnings)."""

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert sum(1 for f in report.warnings if f.code == "W1") >= 2

    def test_missing_timestamp_warning(self, tmp_path: Path) -> None:
        """Detects missing timestamp (W3 warning)."""

        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: concept\ntitle: Test\ndescription: Test\n---\n\n# Test\n",
            encoding="utf-8",
        )

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert any(f.code == "W3" for f in report.warnings)

    def test_block_style_lists_warning(self, tmp_path: Path) -> None:
        """Detects block-style lists (W7 warning)."""

        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - tag1\n  - tag2\n---\n\n# Test\n",
            encoding="utf-8",
        )

        report = validate_markdown_files([str(test_file)])
        assert isinstance(report, Report)
        assert any(f.code == "W7" for f in report.warnings)

    def test_schema_validation_error(self, tmp_path: Path) -> None:
        """Detects schema validation errors (E4 error)."""
        from okf_schema.api import validate_markdown_files

        # Create schemas directory with a schema requiring specific field
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", '
            '"properties": {'
            '"type": {"type": "string"}, '
            '"title": {"type": "string"}}, '
            '"required": ["type", "title"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        # File with missing required title
        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)], schemas_dir=str(schemas_dir))
        assert isinstance(report, Report)
        assert any(f.code == "E4" for f in report.errors)

    def test_no_schema_warning(self, tmp_path: Path) -> None:
        """Detects when no schema is found for type (W6 warning)."""
        from okf_schema.api import validate_markdown_files

        # Create schemas directory
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", "properties": {"type": {"type": "string"}}, "required": ["type"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        # File with unknown type
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: unknown_type\ntitle: Test\n---\n\n# Test\n", encoding="utf-8"
        )

        report = validate_markdown_files([str(test_file)], schemas_dir=str(schemas_dir))
        assert isinstance(report, Report)
        assert any(f.code == "W6" for f in report.warnings)

    def test_accepts_path_objects(self, tmp_path: Path) -> None:
        """Accepts Path objects as well as strings."""

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([test_file])
        assert isinstance(report, Report)

    def test_with_schemas_dir(self, tmp_path: Path) -> None:
        """Accepts schemas_dir parameter for schema validation."""
        from okf_schema.api import validate_markdown_files

        # Create schemas directory
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", '
            '"properties": {'
            '"type": {"type": "string"}, '
            '"title": {"type": "string"}}, '
            '"required": ["type"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n\n# Test\n", encoding="utf-8")

        report = validate_markdown_files([str(test_file)], schemas_dir=str(schemas_dir))
        assert isinstance(report, Report)

    def test_nonexistent_schemas_dir_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when schemas_dir does not exist."""
        from okf_schema.api import validate_markdown_files

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n\n# Test\n", encoding="utf-8")

        nonexistent_schemas = tmp_path / "nonexistent" / "schemas"
        with pytest.raises(FileNotFoundError):
            validate_markdown_files([str(test_file)], schemas_dir=str(nonexistent_schemas))

    def test_schemas_dir_is_file_raises(self, tmp_path: Path) -> None:
        """Raises NotADirectoryError when schemas_dir is a file."""
        from okf_schema.api import validate_markdown_files

        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n\n# Test\n", encoding="utf-8")

        file_as_dir = tmp_path / "file.txt"
        file_as_dir.write_text("not a directory", encoding="utf-8")

        with pytest.raises(NotADirectoryError):
            validate_markdown_files([str(test_file)], schemas_dir=str(file_as_dir))

    def test_nested_glob_patterns(self, tmp_path: Path) -> None:
        """Handles nested directory glob patterns correctly."""
        from okf_schema.api import validate_markdown_files

        # Create nested structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "api").mkdir()
        (tmp_path / "docs" / "guides").mkdir()

        file1 = tmp_path / "docs" / "api" / "overview.md"
        file1.write_text("---\ntype: concept\ntitle: API\n---\n# API", encoding="utf-8")

        file2 = tmp_path / "docs" / "guides" / "tutorial.md"
        file2.write_text("---\ntype: concept\ntitle: Tutorial\n---\n# Tutorial", encoding="utf-8")

        # Use nested glob pattern
        report = validate_markdown_files([f"{tmp_path}/docs/**/*.md"])
        assert len(report.errors) == 0
        assert len(report.warnings) <= 4  # Could have W1, W3 warnings

    def test_pattern_with_no_matches(self, tmp_path: Path) -> None:
        """Returns empty report when pattern matches no files."""
        from okf_schema.api import validate_markdown_files

        report = validate_markdown_files([str(tmp_path / "nonexistent" / "*.md")])
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_absolute_path_with_wildcard(self, tmp_path: Path) -> None:
        """Handles absolute paths with wildcard patterns."""
        from okf_schema.api import validate_markdown_files

        # Create files in tmp_path
        file1 = tmp_path / "test1.md"
        file1.write_text("---\ntype: concept\ntitle: Test\n---\n# Test\n", encoding="utf-8")

        file2 = tmp_path / "test2.md"
        file2.write_text(
            "---\ntype: concept\ntitle: Test\ndescription: Test\n---\n# Test\n",
            encoding="utf-8",
        )

        # Use absolute pattern with wildcard
        pattern = str(tmp_path / "test*.md")
        report = validate_markdown_files([pattern])
        assert len(report.errors) == 0

    def test_absolute_directory_path(self, tmp_path: Path) -> None:
        """Handles absolute directory paths with recursive glob."""
        from okf_schema.api import validate_markdown_files

        # Create nested directory structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "api").mkdir()

        file1 = tmp_path / "docs" / "api" / "test.md"
        file1.write_text(
            "---\ntype: concept\ntitle: Test\ndescription: Test\n---\n# Test\n",
            encoding="utf-8",
        )

        # Use absolute directory path
        report = validate_markdown_files([str(tmp_path / "docs")])
        assert len(report.errors) == 0


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

    def test_schema_aware_subdir_heading(self, tmp_path: Path) -> None:
        """Subdirectory index uses schema title as heading."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        (schema_dir / "myconcept.schema.json").write_text(
            '{"title": "MyConcept", "x-okf-summary": "Short summary."}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        subdir_index = subdir / "index.md"
        content = subdir_index.read_text(encoding="utf-8")
        assert "# MyConcept" in content

    def test_schema_aware_subdir_intro(self, tmp_path: Path) -> None:
        """Subdirectory index includes schema description as intro."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        (schema_dir / "myconcept.schema.json").write_text(
            '{"title": "MyConcept", "description": "Full description here.",'
            ' "x-okf-summary": "Short summary."}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        subdir_index = subdir / "index.md"
        content = subdir_index.read_text(encoding="utf-8")
        assert "Full description here." in content

    def test_schema_aware_root_descriptions(self, tmp_path: Path) -> None:
        """Root index uses x-okf-summary for folder descriptions."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        (schema_dir / "myconcept.schema.json").write_text(
            '{"title": "MyConcept", "x-okf-summary": "Short summary."}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "Short summary." in content
        assert "Auto-generated index" not in content

    def test_schema_aware_fallback_to_description(self, tmp_path: Path) -> None:
        """When x-okf-summary is missing, falls back to description."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        (schema_dir / "myconcept.schema.json").write_text(
            '{"title": "MyConcept", "description": "Fallback description."}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "Fallback description." in content

    def test_mixed_types_use_generic_fallback(self, tmp_path: Path) -> None:
        """Mixed-type folders keep generic fallback."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        (schema_dir / "typea.schema.json").write_text(
            '{"title": "TypeA", "x-okf-summary": "Summary A."}',
            encoding="utf-8",
        )
        (schema_dir / "typeb.schema.json").write_text(
            '{"title": "TypeB", "x-okf-summary": "Summary B."}',
            encoding="utf-8",
        )
        subdir = bundle / "mixed"
        subdir.mkdir()
        (subdir / "a.md").write_text(
            "---\ntitle: A\ntype: typea\n---\n\n# A\n",
            encoding="utf-8",
        )
        (subdir / "b.md").write_text(
            "---\ntitle: B\ntype: typeb\n---\n\n# B\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "Auto-generated index for concepts in `mixed`." in content

    def test_no_schema_info_preserves_existing(self, tmp_path: Path) -> None:
        """When no schema info available, existing custom text is preserved."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        # Create existing index with custom intro
        (subdir / "index.md").write_text(
            "# concepts\n\nCustom intro text.\n\n- [C](concept.md) — desc\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        subdir_index = subdir / "index.md"
        content = subdir_index.read_text(encoding="utf-8")
        assert "Custom intro text." in content

    def test_schema_aware_long_description_truncated(self, tmp_path: Path) -> None:
        """Long descriptions are truncated to 120 characters."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        long_desc = "A" * 150
        (schema_dir / "myconcept.schema.json").write_text(
            f'{{"title": "MyConcept", "description": "{long_desc}"}}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        root_index = bundle / "index.md"
        content = root_index.read_text(encoding="utf-8")
        assert "A" * 117 + "..." in content
        assert "A" * 118 not in content

    def test_schema_aware_subdir_long_description_full(self, tmp_path: Path) -> None:
        """Subdirectory index keeps full schema description (not truncated)."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        long_desc = "B" * 150
        (schema_dir / "myconcept.schema.json").write_text(
            f'{{"title": "MyConcept", "description": "{long_desc}"}}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        index_bundle(bundle)
        subdir_index = subdir / "index.md"
        content = subdir_index.read_text(encoding="utf-8")
        assert "B" * 150 in content

    def test_get_subdir_description_truncates_long_desc(self, tmp_path: Path) -> None:
        """_get_subdir_description truncates descriptions over 120 chars."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()
        long_desc = "C" * 150
        (schema_dir / "myconcept.schema.json").write_text(
            f'{{"title": "MyConcept", "description": "{long_desc}"}}',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntitle: C\ntype: myconcept\n---\n\n# C\n",
            encoding="utf-8",
        )
        schema_info = {"myconcept": {"description": long_desc}}
        result = _get_subdir_description(subdir, schema_info)
        assert result == "C" * 117 + "..."


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
# backlinks_bundle
# ---------------------------------------------------------------------------


class TestBacklinksBundle:
    """Tests for backlinks_bundle."""

    def test_returns_backlink_results(self, tmp_path: Path) -> None:
        """Returns BacklinkResult records for linked concepts."""
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
        results = backlinks_bundle(bundle, ["a.md"])
        assert len(results) == 1
        assert isinstance(results[0], BacklinkResult)
        assert results[0].target == "a.md"
        assert results[0].source == "b.md"

    def test_multiple_targets(self, tmp_path: Path) -> None:
        """Can query backlinks for multiple targets at once."""
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
        (bundle / "c.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n\nLink to [A](a.md) and [B](b.md)\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["a.md", "b.md"])
        assert len(results) == 4
        targets = [r.target for r in results]
        assert targets.count("a.md") == 2  # b.md and c.md
        assert targets.count("b.md") == 2  # a.md and c.md

    def test_no_backlinks_returns_empty(self, tmp_path: Path) -> None:
        """Returns empty list when no backlinks exist."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["a.md"])
        assert results == []

    def test_skips_external_links(self, tmp_path: Path) -> None:
        """External URLs do not produce backlinks."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[External](https://example.com)\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["https://example.com"])
        assert results == []

    def test_skips_reserved_files(self, tmp_path: Path) -> None:
        """Reserved files are not included as backlink sources."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            "---\ntitle: Index\ntype: index\n---\n\n# Index\n\n[Link](concept.md)\n",
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntitle: C\ntype: concept\n---\n\n# C\n", encoding="utf-8"
        )
        results = backlinks_bundle(bundle, ["concept.md"])
        assert results == []

    def test_self_link_excluded(self, tmp_path: Path) -> None:
        """Links to self do not produce backlinks."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[Self](a.md)\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["a.md"])
        assert results == []

    def test_link_outside_bundle_excluded(self, tmp_path: Path) -> None:
        """Links outside the bundle do not produce backlinks."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[Outside](/outside.md)\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["/outside.md"])
        assert results == []

    def test_sorted_by_target_then_source(self, tmp_path: Path) -> None:
        """Results are sorted by (target, source)."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\nLink to [C](c.md)\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntitle: B\ntype: concept\n---\n\n# B\n\nLink to [C](c.md)\n",
            encoding="utf-8",
        )
        results = backlinks_bundle(bundle, ["c.md"])
        assert len(results) == 2
        assert results[0].source == "a.md"
        assert results[1].source == "b.md"

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        with pytest.raises(FileNotFoundError):
            backlinks_bundle(VALID_BUNDLE / "does-not-exist", ["a.md"])

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        with pytest.raises(NotADirectoryError):
            backlinks_bundle(VALID_BUNDLE / "subdir" / "concept-a.md", ["a.md"])


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


# ---------------------------------------------------------------------------
# update_bundle
# ---------------------------------------------------------------------------


class TestUpdateBundle:
    """Tests for update_bundle (index + lint)."""

    def test_returns_update_result(self, tmp_path: Path) -> None:
        """update_bundle returns an UpdateResult with index and lint data."""
        from okf_schema.api import UpdateResult, update_bundle

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = update_bundle(bundle)
        assert isinstance(result, UpdateResult)
        assert len(result.index_updates) >= 1
        assert len(result.lint_results) >= 1
        assert any(r.changed for r in result.lint_results)

    def test_creates_index_and_lints(self, tmp_path: Path) -> None:
        """update_bundle creates index.md and lints frontmatter."""
        from okf_schema.api import update_bundle

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        update_bundle(bundle)
        assert (bundle / "index.md").exists()
        text = (bundle / "concept.md").read_text(encoding="utf-8")
        assert "tags: [a, b]" in text

    def test_check_mode_no_changes(self, tmp_path: Path) -> None:
        """update_bundle with check=True does not modify files."""
        from okf_schema.api import update_bundle

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        original = "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n"
        (bundle / "concept.md").write_text(original, encoding="utf-8")
        result = update_bundle(bundle, check=True)
        assert (bundle / "concept.md").read_text(encoding="utf-8") == original
        assert result.lint_results[0].changed is True

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        from okf_schema.api import update_bundle

        with pytest.raises(FileNotFoundError):
            update_bundle(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        from okf_schema.api import update_bundle

        with pytest.raises(NotADirectoryError):
            update_bundle(VALID_BUNDLE / "subdir" / "concept-a.md")


# ---------------------------------------------------------------------------
# rewrite_superseded_links
# ---------------------------------------------------------------------------


class TestRewriteSupersededLinks:
    """Tests for rewrite_superseded_links."""

    def test_no_superseded_docs_returns_empty(self, tmp_path: Path) -> None:
        """Returns empty lists when no superseded documents exist."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntype: Finding\ntitle: A\nstatus: active\n---\n\n# A\n\n[B](b.md)\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: Finding\ntitle: B\nstatus: active\n---\n\n# B\n",
            encoding="utf-8",
        )
        rewrites, deferred = rewrite_superseded_links(bundle)
        assert rewrites == []
        assert deferred == []

    def test_rewrites_link_to_superseded_doc(self, tmp_path: Path) -> None:
        """Rewrites a body link from superseded doc to its replacement."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (bundle / "source.md").write_text(
            "---\ntype: Finding\ntitle: Source\n---\n\n# Source\n\nSee [Old](old.md).\n",
            encoding="utf-8",
        )
        rewrites, deferred = rewrite_superseded_links(bundle)
        assert len(rewrites) == 1
        assert rewrites[0].source == "source.md"
        assert rewrites[0].old_target == "old.md"
        assert rewrites[0].new_target == "new.md"
        text = (bundle / "source.md").read_text(encoding="utf-8")
        assert "[Old](new.md)" in text
        assert "old.md" not in text

    def test_deferred_when_no_superseded_by(self, tmp_path: Path) -> None:
        """Defers superseded doc without superseded_by field."""
        from okf_schema.api import DeferredRewrite, rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n---\n\n# Old\n",
            encoding="utf-8",
        )
        rewrites, deferred = rewrite_superseded_links(bundle)
        assert rewrites == []
        assert len(deferred) == 1
        assert isinstance(deferred[0], DeferredRewrite)
        assert deferred[0].superseded_doc == "old.md"
        assert deferred[0].reason == "no_superseded_by"

    def test_deferred_when_replacement_missing(self, tmp_path: Path) -> None:
        """Defers superseded doc when replacement path does not exist."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [nonexistent.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        rewrites, deferred = rewrite_superseded_links(bundle)
        assert rewrites == []
        assert len(deferred) == 1
        assert "replacement_not_found" in deferred[0].reason

    def test_check_mode_does_not_modify_files(self, tmp_path: Path) -> None:
        """check=True reports rewrites without modifying files."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        original = "---\ntype: Finding\ntitle: Source\n---\n\n# Source\n\nSee [Old](old.md).\n"
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (bundle / "source.md").write_text(original, encoding="utf-8")
        rewrites, _ = rewrite_superseded_links(bundle, check=True)
        assert len(rewrites) == 1
        assert (bundle / "source.md").read_text(encoding="utf-8") == original

    def test_rewrites_link_in_subdirectory(self, tmp_path: Path) -> None:
        """Computes correct relative path for cross-directory links."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        findings = bundle / "findings"
        findings.mkdir()
        concepts = bundle / "concepts"
        concepts.mkdir()
        (findings / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [findings/new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (findings / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (concepts / "concept.md").write_text(
            "---\ntype: Concept\ntitle: Concept\n---\n\n# Concept\n"
            "\nSee [Old](../findings/old.md).\n",
            encoding="utf-8",
        )
        rewrites, _ = rewrite_superseded_links(bundle)
        assert len(rewrites) == 1
        text = (concepts / "concept.md").read_text(encoding="utf-8")
        assert "../findings/new.md" in text
        assert "../findings/old.md" not in text

    def test_nonexistent_path_raises(self) -> None:
        """Raises FileNotFoundError for nonexistent bundle path."""
        from okf_schema.api import rewrite_superseded_links

        with pytest.raises(FileNotFoundError):
            rewrite_superseded_links(VALID_BUNDLE / "does-not-exist")

    def test_not_a_directory_raises(self) -> None:
        """Raises NotADirectoryError when path is a file."""
        from okf_schema.api import rewrite_superseded_links

        with pytest.raises(NotADirectoryError):
            rewrite_superseded_links(VALID_BUNDLE / "subdir" / "concept-a.md")


class TestUpdateBundleSuperseded:
    """Tests for update_bundle superseded-rewrite integration."""

    def test_update_result_includes_rewrite_fields(self, tmp_path: Path) -> None:
        """UpdateResult has superseded_rewrites and deferred_rewrites fields."""
        from okf_schema.api import UpdateResult, update_bundle

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: Concept\ntitle: C\n---\n\n# C\n",
            encoding="utf-8",
        )
        result = update_bundle(bundle)
        assert isinstance(result, UpdateResult)
        assert hasattr(result, "superseded_rewrites")
        assert hasattr(result, "deferred_rewrites")
        assert isinstance(result.superseded_rewrites, list)
        assert isinstance(result.deferred_rewrites, list)

    def test_update_rewrites_superseded_then_lints(self, tmp_path: Path) -> None:
        """update_bundle rewrites superseded links before linting."""
        from okf_schema.api import update_bundle

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (bundle / "source.md").write_text(
            "---\ntype: Finding\ntitle: Source\n---\n\n# Source\n\nSee [Old](old.md).\n",
            encoding="utf-8",
        )
        result = update_bundle(bundle)
        assert len(result.superseded_rewrites) == 1
        assert result.deferred_rewrites == []
        text = (bundle / "source.md").read_text(encoding="utf-8")
        assert "[Old](new.md)" in text

    def test_rewrite_skips_reserved_files_as_source(self, tmp_path: Path) -> None:
        """Reserved files (index.md) are not processed as link sources."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (bundle / "index.md").write_text(
            "# Index\n\n[Old](old.md)\n",
            encoding="utf-8",
        )
        rewrites, _ = rewrite_superseded_links(bundle)
        # index.md should not have been processed as a source
        assert all(r.source != "index.md" for r in rewrites)
        index_text = (bundle / "index.md").read_text(encoding="utf-8")
        assert "old.md" in index_text  # unchanged

    def test_rewrite_source_without_frontmatter(self, tmp_path: Path) -> None:
        """Source docs without frontmatter have their body links rewritten."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        # Source doc with no frontmatter but has a link
        (bundle / "source.md").write_text(
            "# Source\n\nSee [Old](old.md).\n",
            encoding="utf-8",
        )
        rewrites, _ = rewrite_superseded_links(bundle)
        assert len(rewrites) == 1
        text = (bundle / "source.md").read_text(encoding="utf-8")
        assert "[Old](new.md)" in text

    def test_rewrite_body_with_non_matching_links(self, tmp_path: Path) -> None:
        """Non-superseded links in body are preserved unchanged."""
        from okf_schema.api import rewrite_superseded_links

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "old.md").write_text(
            "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
            "superseded_by: [new.md]\n---\n\n# Old\n",
            encoding="utf-8",
        )
        (bundle / "new.md").write_text(
            "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
            encoding="utf-8",
        )
        (bundle / "other.md").write_text(
            "---\ntype: Finding\ntitle: Other\nstatus: active\n---\n\n# Other\n",
            encoding="utf-8",
        )
        (bundle / "source.md").write_text(
            "---\ntype: Finding\ntitle: Source\n---\n\n# Source\n"
            "\n[Old](old.md) and [Other](other.md).\n",
            encoding="utf-8",
        )
        rewrites, _ = rewrite_superseded_links(bundle)
        assert len(rewrites) == 1
        assert rewrites[0].old_target == "old.md"
        text = (bundle / "source.md").read_text(encoding="utf-8")
        assert "[Old](new.md)" in text
        assert "[Other](other.md)" in text  # preserved
