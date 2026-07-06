"""Tests for CLI remaining commands: list, show, index, stats."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from okf_schema.cli import cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bundle(path: Path) -> Path:
    """Create a minimal OKF bundle with a few concepts."""
    bundle = path / "bundle"
    bundle.mkdir()

    (bundle / "index.md").write_text(
        '---\nokf_version: "0.1"\n---\n\n# Test Bundle\n',
        encoding="utf-8",
    )
    (bundle / "log.md").write_text("## 2024-01-01\n\n- Entry\n", encoding="utf-8")

    concept_a = bundle / "concept-a.md"
    concept_a.write_text(
        "---\ntitle: Concept A\ndescription: First concept\n"
        "type: concept\ntags: [alpha, beta]\n---\n\n"
        "# Concept A\n\nSee also [Concept B](concept-b.md).\n",
        encoding="utf-8",
    )

    concept_b = bundle / "concept-b.md"
    concept_b.write_text(
        "---\ntitle: Concept B\ndescription: Second concept\n"
        "type: pattern\ntags: [beta, gamma]\n---\n\n"
        "# Concept B\n\nSee also [Concept A](concept-a.md).\n",
        encoding="utf-8",
    )

    subdir = bundle / "subdir"
    subdir.mkdir()
    concept_c = subdir / "concept-c.md"
    concept_c.write_text(
        "---\ntitle: Concept C\ndescription: Third concept\ntype: concept\ntags: [alpha]\n---\n\n"
        "# Concept C\n\nStandalone concept.\n",
        encoding="utf-8",
    )

    (subdir / "index.md").write_text(
        "# subdir\n\n- [Concept C](concept-c.md) — Third concept  [concept]\n",
        encoding="utf-8",
    )

    return bundle


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    """Tests for the list subcommand."""

    def test_list_outputs_concepts(self, tmp_path: Path) -> None:
        """list outputs one concept per line with path, type, title."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(bundle)])
        assert result.exit_code == 0
        lines = [line for line in result.output.splitlines() if line.strip()]
        assert len(lines) == 3
        assert "concept-a.md" in result.output
        assert "concept-b.md" in result.output
        assert "subdir/concept-c.md" in result.output

    def test_list_sorted_by_path(self, tmp_path: Path) -> None:
        """list output is sorted by path."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(bundle)])
        assert result.exit_code == 0
        lines = [line for line in result.output.splitlines() if line.strip()]
        assert lines[0].startswith("concept-a.md")
        assert lines[1].startswith("concept-b.md")
        assert lines[2].startswith("subdir/concept-c.md")

    def test_list_exits_2_on_invalid_bundle(self, tmp_path: Path) -> None:
        """list exits 2 on nonexistent bundle path."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(tmp_path / "nonexistent")])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


class TestShow:
    """Tests for the show subcommand."""

    def test_show_outputs_frontmatter_and_body(self, tmp_path: Path) -> None:
        """show displays frontmatter as YAML followed by body."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])
        assert result.exit_code == 0
        assert "title: Concept A" in result.output
        assert "type: concept" in result.output
        assert "# Concept A" in result.output
        assert "See also" in result.output

    def test_show_exits_2_on_missing_concept(self, tmp_path: Path) -> None:
        """show exits 2 when concept not found."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "--path", str(bundle), "missing.md"])
        assert result.exit_code == 2

    def test_show_exits_2_on_invalid_bundle(self, tmp_path: Path) -> None:
        """show exits 2 on nonexistent bundle path."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["show", "--path", str(tmp_path / "nonexistent"), "concept-a.md"]
        )
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------


class TestIndex:
    """Tests for the index subcommand."""

    def test_index_creates_missing_index(self, tmp_path: Path) -> None:
        """index creates missing index.md files."""
        bundle = _make_bundle(tmp_path)
        (bundle / "subdir" / "index.md").unlink()
        runner = CliRunner()
        result = runner.invoke(cli, ["index", "--path", str(bundle)])
        assert result.exit_code == 0
        assert (bundle / "subdir" / "index.md").exists()
        assert "updated" in result.output.lower() or "created" in result.output.lower()

    def test_index_prints_summary(self, tmp_path: Path) -> None:
        """index prints summary with updated, unchanged, skipped counts."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["index", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "updated" in result.output.lower() or "unchanged" in result.output.lower()

    def test_index_exits_2_on_invalid_bundle(self, tmp_path: Path) -> None:
        """index exits 2 on nonexistent bundle path."""
        runner = CliRunner()
        result = runner.invoke(cli, ["index", "--path", str(tmp_path / "nonexistent")])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


class TestStats:
    """Tests for the stats subcommand."""

    def test_stats_outputs_summary(self, tmp_path: Path) -> None:
        """stats outputs a compact summary line."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "files" in result.output
        assert "concepts" in result.output
        assert "types" in result.output

    def test_stats_includes_types_ranked(self, tmp_path: Path) -> None:
        """stats includes types ranked by count."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "Types:" in result.output
        assert "concept 2" in result.output
        assert "pattern 1" in result.output

    def test_stats_includes_tags_ranked(self, tmp_path: Path) -> None:
        """stats includes tags ranked by frequency."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "Tags:" in result.output
        assert "alpha 2" in result.output
        assert "beta 2" in result.output
        assert "gamma 1" in result.output

    def test_stats_includes_health_score(self, tmp_path: Path) -> None:
        """stats includes a health score."""
        bundle = _make_bundle(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "Health:" in result.output
        assert "all clear" in result.output

    def test_stats_shows_broken_links_in_health(self, tmp_path: Path) -> None:
        """stats health score reflects broken links."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntitle: A\ntype: concept\n---\n\n# A\n\n[B](broken.md)\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "Health:" in result.output
        assert "1 broken link" in result.output

    def test_stats_exits_2_on_invalid_bundle(self, tmp_path: Path) -> None:
        """stats exits 2 on nonexistent bundle path."""
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", str(tmp_path / "nonexistent")])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# Error handling coverage (mock-based for defensive branches)
# ---------------------------------------------------------------------------


class TestDefensiveErrorHandling:
    """Mock-based tests for defensive exception branches in CLI commands."""

    def test_list_exits_2_on_api_error(self, tmp_path: Path) -> None:
        """list exits 2 when list_bundle raises FileNotFoundError."""
        bundle = _make_bundle(tmp_path)
        with patch("okf_schema.cli.list_bundle", side_effect=FileNotFoundError("boom")):
            runner = CliRunner()
            result = runner.invoke(cli, ["list", "--path", str(bundle)])
        assert result.exit_code == 2
        assert "boom" in result.output

    def test_show_exits_2_on_api_error(self, tmp_path: Path) -> None:
        """show exits 2 when show_bundle raises NotADirectoryError."""
        bundle = _make_bundle(tmp_path)
        with patch("okf_schema.cli.show_bundle", side_effect=NotADirectoryError("boom")):
            runner = CliRunner()
            result = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])
        assert result.exit_code == 2
        assert "boom" in result.output

    def test_index_exits_2_on_api_error(self, tmp_path: Path) -> None:
        """index exits 2 when index_bundle raises FileNotFoundError."""
        bundle = _make_bundle(tmp_path)
        with patch("okf_schema.cli.index_bundle", side_effect=FileNotFoundError("boom")):
            runner = CliRunner()
            result = runner.invoke(cli, ["index", "--path", str(bundle)])
        assert result.exit_code == 2
        assert "boom" in result.output

    def test_stats_exits_2_on_api_error(self, tmp_path: Path) -> None:
        """stats exits 2 when stats_bundle raises NotADirectoryError."""
        bundle = _make_bundle(tmp_path)
        with patch("okf_schema.cli.stats_bundle", side_effect=NotADirectoryError("boom")):
            runner = CliRunner()
            result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 2
        assert "boom" in result.output


# ---------------------------------------------------------------------------
# validate-md
# ---------------------------------------------------------------------------


class TestValidateMd:
    """Tests for the validate-md subcommand."""

    def test_validate_md_exits_0_for_valid_files(self, tmp_path: Path) -> None:
        """validate-md exits 0 for valid markdown files."""
        test_file = tmp_path / "test.md"
        content = (
            "---\ntype: concept\ntitle: Test\ndescription: Test\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\n# Test\n"
        )
        test_file.write_text(content, encoding="utf-8")

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", "properties": {"type": {"type": "string"}}, "required": ["type"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 0
        assert "All files validated successfully" in result.output

    def test_validate_md_exits_1_for_invalid_files(self, tmp_path: Path) -> None:
        """validate-md exits 1 for files with errors."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# No Frontmatter\n\nContent\n", encoding="utf-8")

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 1
        assert "E1" in result.output or "error" in result.output.lower()

    def test_validate_md_multiple_inputs(self, tmp_path: Path) -> None:
        """validate-md accepts multiple --input flags."""
        file1 = tmp_path / "file1.md"
        content1 = (
            "---\ntype: concept\ntitle: Test1\ndescription: Desc\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\nContent\n"
        )
        file1.write_text(content1, encoding="utf-8")
        file2 = tmp_path / "file2.md"
        content2 = (
            "---\ntype: concept\ntitle: Test2\ndescription: Desc\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\nContent\n"
        )
        file2.write_text(content2, encoding="utf-8")

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", "properties": {"type": {"type": "string"}}, "required": ["type"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(file1),
                "--input",
                str(file2),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 0
        assert "All files validated successfully" in result.output

    def test_validate_md_strict_mode(self, tmp_path: Path) -> None:
        """validate-md --strict exits 1 for warnings."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "---\ntype: concept\n---\n\n# Test\n",
            encoding="utf-8",
        )

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(schemas_dir),
                "--strict",
            ],
        )
        assert result.exit_code == 1

    def test_validate_md_glob_pattern(self, tmp_path: Path) -> None:
        """validate-md supports glob patterns."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.md"
        content1 = (
            "---\ntype: concept\ntitle: Test1\ndescription: Desc\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\nContent\n"
        )
        file1.write_text(content1, encoding="utf-8")
        file2 = subdir / "file2.md"
        content2 = (
            "---\ntype: concept\ntitle: Test2\ndescription: Desc\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\nContent\n"
        )
        file2.write_text(content2, encoding="utf-8")

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema_file = schemas_dir / "concept.schema.json"
        schema_text = (
            '{"type": "object", "properties": {"type": {"type": "string"}}, "required": ["type"]}'
        )
        schema_file.write_text(schema_text, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(tmp_path / "**" / "*.md"),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 0
        assert "All files validated successfully" in result.output

    def test_validate_md_schema_validation(self, tmp_path: Path) -> None:
        """validate-md validates against schemas."""
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

        # File missing required title
        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\n---\n\n# Test\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 1
        assert "E4" in result.output or "error" in result.output.lower()

    def test_validate_md_nonexistent_schemas_dir(self, tmp_path: Path) -> None:
        """validate-md exits with error for nonexistent schemas directory."""
        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n# Test\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(tmp_path / "nonexistent"),
            ],
        )
        assert result.exit_code != 0

    def test_validate_md_schemas_dir_is_file(self, tmp_path: Path) -> None:
        """validate-md exits with error when schemas-dir is a file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("---\ntype: concept\ntitle: Test\n---\n# Test\n", encoding="utf-8")

        file_as_dir = tmp_path / "file.txt"
        file_as_dir.write_text("not a directory", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(test_file),
                "--schemas-dir",
                str(file_as_dir),
            ],
        )
        assert result.exit_code != 0

    def test_validate_md_no_files_matched(self, tmp_path: Path) -> None:
        """validate-md handles pattern with no matches gracefully."""
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate-md",
                "--input",
                str(tmp_path / "nonexistent" / "*.md"),
                "--schemas-dir",
                str(schemas_dir),
            ],
        )
        assert result.exit_code == 0
        assert "All files validated successfully" in result.output
