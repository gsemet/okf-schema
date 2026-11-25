"""Tests for CLI remaining commands: list, show, index, stats."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
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


# @tests_req SwRS-OKFSCHEMA-CORE-005#S1
def test_list_list_outputs_concepts(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-CORE-005#S1
def test_list_list_sorted_by_path(tmp_path: Path) -> None:
    """list output is sorted by path."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--path", str(bundle)])
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert lines[0].startswith("concept-a.md")
    assert lines[1].startswith("concept-b.md")
    assert lines[2].startswith("subdir/concept-c.md")


# @tests_req SwRS-OKFSCHEMA-CORE-005#S2
def test_list_list_exits_2_on_invalid_bundle(tmp_path: Path) -> None:
    """list exits 2 on nonexistent bundle path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--path", str(tmp_path / "nonexistent")])
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-CORE-005#S1
def test_show_show_outputs_frontmatter_and_body(tmp_path: Path) -> None:
    """show displays frontmatter as YAML followed by body."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])
    assert result.exit_code == 0
    assert "title: Concept A" in result.output
    assert "type: concept" in result.output
    assert "# Concept A" in result.output
    assert "See also" in result.output


# @tests_req SwRS-OKFSCHEMA-CORE-005#S2
def test_show_show_exits_2_on_missing_concept(tmp_path: Path) -> None:
    """show exits 2 when concept not found."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--path", str(bundle), "missing.md"])
    assert result.exit_code == 2


def test_show_show_exits_2_on_invalid_bundle(tmp_path: Path) -> None:
    """show exits 2 on nonexistent bundle path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--path", str(tmp_path / "nonexistent"), "concept-a.md"])
    assert result.exit_code == 2


# @tests_req SwRS-OKFSCHEMA-CORE-005#S3
def test_show_show_accepts_a_name_without_extension(tmp_path: Path) -> None:
    """show prints the same output with and without the .md extension."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    expected = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])
    result = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a"])
    assert result.exit_code == 0
    assert result.output == expected.output


# @tests_req SwRS-OKFSCHEMA-CORE-005#S2
def test_show_show_exits_2_on_directory_without_traceback(tmp_path: Path) -> None:
    """show reports a directory as a concept not found, with no traceback."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--path", str(bundle), "subdir"])
    assert result.exit_code == 2
    assert "Error: Concept not found" in result.output
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)


# @tests_req SwRS-OKFSCHEMA-CORE-010#S1
def test_show_show_exits_2_on_path_outside_the_bundle(tmp_path: Path) -> None:
    """show refuses a path leaving the bundle."""
    bundle = _make_bundle(tmp_path)
    (tmp_path / "outside.md").write_text("# Outside\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--path", str(bundle), "../outside.md"])
    assert result.exit_code == 2
    assert "Error: Concept path is outside the bundle" in result.output
    assert "# Outside" not in result.output


# @tests_req SwRS-OKFSCHEMA-CORE-005#S4
def test_show_show_reads_names_from_the_bundle_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A name, with or without a leading /, starts from the bundle root, from any folder."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    expected = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])

    rooted = runner.invoke(cli, ["show", "--path", str(bundle), "/concept-a"])
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    relative = runner.invoke(cli, ["show", "--path", str(bundle.resolve()), "concept-a"])

    assert rooted.exit_code == 0
    assert rooted.output == expected.output
    assert relative.exit_code == 0
    assert relative.output == expected.output


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------


def test_index_index_creates_missing_index(tmp_path: Path) -> None:
    """index creates missing index.md files."""
    bundle = _make_bundle(tmp_path)
    (bundle / "subdir" / "index.md").unlink()
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--path", str(bundle)])
    assert result.exit_code == 0
    assert (bundle / "subdir" / "index.md").exists()
    assert "updated" in result.output.lower() or "created" in result.output.lower()


def test_index_index_prints_summary(tmp_path: Path) -> None:
    """index prints summary with updated, unchanged, skipped counts."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--path", str(bundle)])
    assert result.exit_code == 0
    assert "updated" in result.output.lower() or "unchanged" in result.output.lower()


def test_index_index_exits_2_on_invalid_bundle(tmp_path: Path) -> None:
    """index exits 2 on nonexistent bundle path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--path", str(tmp_path / "nonexistent")])
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-CORE-005#S1
def test_stats_stats_outputs_summary(tmp_path: Path) -> None:
    """stats outputs a compact summary line."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", "--path", str(bundle)])
    assert result.exit_code == 0
    assert "files" in result.output
    assert "concepts" in result.output
    assert "types" in result.output


def test_stats_stats_includes_types_ranked(tmp_path: Path) -> None:
    """stats includes types ranked by count."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", "--path", str(bundle)])
    assert result.exit_code == 0
    assert "Types:" in result.output
    assert "concept 2" in result.output
    assert "pattern 1" in result.output


def test_stats_stats_includes_tags_ranked(tmp_path: Path) -> None:
    """stats includes tags ranked by frequency."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", "--path", str(bundle)])
    assert result.exit_code == 0
    assert "Tags:" in result.output
    assert "alpha 2" in result.output
    assert "beta 2" in result.output
    assert "gamma 1" in result.output


def test_stats_stats_includes_health_score(tmp_path: Path) -> None:
    """stats includes a health score."""
    bundle = _make_bundle(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", "--path", str(bundle)])
    assert result.exit_code == 0
    assert "Health:" in result.output
    assert "all clear" in result.output


def test_stats_stats_shows_broken_links_in_health(tmp_path: Path) -> None:
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


# @tests_req SwRS-OKFSCHEMA-CORE-005#S1
def test_stats_ignores_anchors_and_encoding_of_valid_links(tmp_path: Path) -> None:
    """Anchored and percent-encoded links to existing files cost no health points."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for name in ("other.md", "my file.md"):
        (bundle / name).write_text("---\ntitle: T\ntype: concept\n---\n\n# T\n", encoding="utf-8")
    (bundle / "a.md").write_text(
        "---\ntitle: A\ntype: concept\n---\n\n# A\n\n"
        "[a](other.md#part) [t](#top) [b](my%20file.md)\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["stats", "--path", str(bundle)])

    assert result.exit_code == 0
    assert "all clear" in result.output
    assert "broken link" not in result.output
    assert "broken)" not in result.output


# @tests_req SwRS-OKFSCHEMA-CORE-005#S2
def test_stats_stats_exits_2_on_invalid_bundle(tmp_path: Path) -> None:
    """stats exits 2 on nonexistent bundle path."""
    runner = CliRunner()
    result = runner.invoke(cli, ["stats", str(tmp_path / "nonexistent")])
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# Error handling coverage (mock-based for defensive branches)
# ---------------------------------------------------------------------------


def test_defensive_error_handling_list_exits_2_on_api_error(tmp_path: Path) -> None:
    """list exits 2 when list_bundle raises FileNotFoundError."""
    bundle = _make_bundle(tmp_path)
    with patch("okf_schema.cli.list_bundle", side_effect=FileNotFoundError("boom")):
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(bundle)])
    assert result.exit_code == 2
    assert "boom" in result.output


def test_defensive_error_handling_show_exits_2_on_api_error(tmp_path: Path) -> None:
    """show exits 2 when show_bundle raises NotADirectoryError."""
    bundle = _make_bundle(tmp_path)
    with patch("okf_schema.cli.show_bundle", side_effect=NotADirectoryError("boom")):
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "--path", str(bundle), "concept-a.md"])
    assert result.exit_code == 2
    assert "boom" in result.output


def test_defensive_error_handling_index_exits_2_on_api_error(tmp_path: Path) -> None:
    """index exits 2 when index_bundle raises FileNotFoundError."""
    bundle = _make_bundle(tmp_path)
    with patch("okf_schema.cli.index_bundle", side_effect=FileNotFoundError("boom")):
        runner = CliRunner()
        result = runner.invoke(cli, ["index", "--path", str(bundle)])
    assert result.exit_code == 2
    assert "boom" in result.output


def test_defensive_error_handling_stats_exits_2_on_api_error(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_exits_0_for_valid_files(tmp_path: Path) -> None:
    """validate-md exits 0 for valid markdown files."""
    test_file = tmp_path / "test.md"
    content = (
        "---\ntype: concept\ntitle: Test\ndescription: Test\n"
        'generated:\n  at: "2024-01-01T00:00:00Z"\n  by: bot:test\n'
        "---\n\n# Test\n"
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


# @tests_req SwRS-OKFSCHEMA-CORE-006#S5
def test_validate_md_strict_accepts_producer_version_actor(tmp_path: Path) -> None:
    """validate-md --strict raises no W10 for a `<producer>/<version>` verification actor."""
    test_file = tmp_path / "test.md"
    content = (
        "---\ntype: concept\ntitle: Test\ndescription: Test\n"
        'generated: {at: "2024-01-01T00:00:00Z", by: reference_agent/gemini-2.5-pro}\n'
        'verified: [{by: reference_agent/gemini-2.5-pro, at: "2024-01-02T00:00:00Z"}]\n'
        "---\n\n# Test\n"
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
            "--strict",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "W10" not in result.output


def test_validate_md_validate_md_exits_1_for_invalid_files(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_multiple_inputs(tmp_path: Path) -> None:
    """validate-md accepts multiple --input flags."""
    file1 = tmp_path / "file1.md"
    content1 = (
        "---\ntype: concept\ntitle: Test1\ndescription: Desc\n"
        'generated:\n  at: "2024-01-01T00:00:00Z"\n  by: bot:test\n'
        "---\n\nContent\n"
    )
    file1.write_text(content1, encoding="utf-8")
    file2 = tmp_path / "file2.md"
    content2 = (
        "---\ntype: concept\ntitle: Test2\ndescription: Desc\n"
        'generated:\n  at: "2024-01-01T00:00:00Z"\n  by: bot:test\n'
        "---\n\nContent\n"
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


def test_validate_md_validate_md_strict_mode(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_glob_pattern(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_schema_validation(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_nonexistent_schemas_dir(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_schemas_dir_is_file(tmp_path: Path) -> None:
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


def test_validate_md_validate_md_no_files_matched(tmp_path: Path) -> None:
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
