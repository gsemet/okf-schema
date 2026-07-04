"""Tests for okf_schema.kb.finding — new_finding() function and okfkb new-finding CLI."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.kb.cli import kb
from okf_schema.kb.finding import _slugify, new_finding

# ---------------------------------------------------------------------------
# _slugify helper
# ---------------------------------------------------------------------------


class TestSlugify:
    """Slug generation from arbitrary titles."""

    def test_simple_title(self) -> None:
        assert _slugify("HW Failure investigation") == "hw-failure-investigation"

    def test_special_chars_collapsed(self) -> None:
        assert _slugify("foo & bar — baz") == "foo-bar-baz"

    def test_leading_trailing_dashes_stripped(self) -> None:
        slug = _slugify("  hello  ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_max_length_60(self) -> None:
        long_title = "a" * 100
        assert len(_slugify(long_title)) <= 60

    def test_digits_preserved(self) -> None:
        assert _slugify("issue 42 fix") == "issue-42-fix"


# ---------------------------------------------------------------------------
# new_finding() — happy path
# ---------------------------------------------------------------------------


class TestNewFindingHappyPath:
    """new_finding() creates a valid Finding file."""

    def test_creates_file_in_findings_dir(self, tmp_path: Path) -> None:
        """Creates a file inside <kb_path>/findings/."""
        (tmp_path / "findings").mkdir()
        filepath = new_finding(tmp_path, "Something observed")
        assert filepath.parent == tmp_path / "findings"
        assert filepath.exists()

    def test_creates_findings_dir_if_missing(self, tmp_path: Path) -> None:
        """Creates findings/ when it does not exist yet."""
        assert not (tmp_path / "findings").exists()
        filepath = new_finding(tmp_path, "My finding")
        assert (tmp_path / "findings").is_dir()
        assert filepath.exists()

    def test_filename_format(self, tmp_path: Path) -> None:
        """Filename matches YYYY.MM.DD-HH.MM-<slug>.md."""
        filepath = new_finding(tmp_path, "Cache miss rate spike")
        assert re.fullmatch(
            r"\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}-cache-miss-rate-spike\.md",
            filepath.name,
        ), filepath.name

    def test_frontmatter_contains_required_fields(self, tmp_path: Path) -> None:
        """Generated file has all schema-required frontmatter fields."""
        filepath = new_finding(
            tmp_path,
            "Timeout under load",
            confidence="medium",
            context="Observed under 1000 concurrent requests.",
        )
        content = filepath.read_text(encoding="utf-8")
        assert "type: Finding" in content
        assert "title:" in content
        assert "description:" in content
        assert "confidence: medium" in content
        assert "context:" in content
        assert "timestamp:" in content
        assert "links:" in content
        assert "backlinks:" in content
        assert "status: active" in content

    def test_description_defaults_to_title(self, tmp_path: Path) -> None:
        """description mirrors title when not provided."""
        filepath = new_finding(tmp_path, "Memory leak")
        content = filepath.read_text(encoding="utf-8")
        assert "description: Memory leak" in content

    def test_custom_description(self, tmp_path: Path) -> None:
        """Custom description is written to frontmatter."""
        filepath = new_finding(tmp_path, "Memory leak", description="RSS grows unboundedly")
        content = filepath.read_text(encoding="utf-8")
        assert "RSS grows unboundedly" in content

    def test_tags_written(self, tmp_path: Path) -> None:
        """Tags list is embedded in frontmatter."""
        filepath = new_finding(tmp_path, "Network jitter", tags=["network", "latency"])
        content = filepath.read_text(encoding="utf-8")
        assert "network" in content
        assert "latency" in content

    def test_empty_tags_produces_empty_list(self, tmp_path: Path) -> None:
        """No tags → tags: [] in YAML."""
        filepath = new_finding(tmp_path, "No tags")
        content = filepath.read_text(encoding="utf-8")
        assert "tags: []" in content

    def test_body_has_markdown_sections(self, tmp_path: Path) -> None:
        """Generated body includes Observation, Evidence, Implications headings."""
        filepath = new_finding(tmp_path, "With body")
        content = filepath.read_text(encoding="utf-8")
        assert "## Observation" in content
        assert "## Evidence" in content
        assert "## Implications" in content

    def test_h1_contains_title(self, tmp_path: Path) -> None:
        """Body h1 echoes the finding title."""
        filepath = new_finding(tmp_path, "Signal noise")
        content = filepath.read_text(encoding="utf-8")
        assert "# Finding: Signal noise" in content

    def test_file_delimited_by_yaml_fences(self, tmp_path: Path) -> None:
        """File starts and ends YAML block with --- delimiters."""
        filepath = new_finding(tmp_path, "Fence check")
        content = filepath.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "\n---\n" in content


# ---------------------------------------------------------------------------
# new_finding() — confidence levels
# ---------------------------------------------------------------------------


class TestNewFindingConfidence:
    """All valid confidence levels are accepted."""

    @pytest.mark.parametrize("level", ["low", "medium", "high", "confirmed"])
    def test_valid_confidence(self, tmp_path: Path, level: str) -> None:
        filepath = new_finding(tmp_path, f"Finding {level}", confidence=level)
        assert f"confidence: {level}" in filepath.read_text(encoding="utf-8")

    def test_invalid_confidence_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Invalid confidence"):
            new_finding(tmp_path, "Bad conf", confidence="very-sure")


# ---------------------------------------------------------------------------
# new_finding() — error cases
# ---------------------------------------------------------------------------


class TestNewFindingErrors:
    """Error handling in new_finding()."""

    def test_nonexistent_kb_path_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "does-not-exist"
        with pytest.raises(ValueError, match="does not exist"):
            new_finding(missing, "Title")


# ---------------------------------------------------------------------------
# CLI — okfkb new-finding
# ---------------------------------------------------------------------------


class TestKbNewFindingCli:
    """okfkb new-finding CLI command."""

    def test_new_finding_creates_file(self, tmp_path: Path) -> None:
        """new-finding creates a finding file and prints the path."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            ["new-finding", str(tmp_path), "--title", "CLI test finding"],
        )
        assert result.exit_code == 0, result.output
        findings = list((tmp_path / "findings").glob("*.md"))
        assert len(findings) == 1

    def test_new_finding_output_contains_path(self, tmp_path: Path) -> None:
        """Printed output contains the created file path."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            ["new-finding", str(tmp_path), "--title", "Path check"],
        )
        assert result.exit_code == 0
        assert "findings" in result.output

    def test_new_finding_help(self) -> None:
        """new-finding --help exits 0 and shows key options."""
        runner = CliRunner()
        result = runner.invoke(kb, ["new-finding", "--help"])
        assert result.exit_code == 0
        assert "--title" in result.output
        assert "--confidence" in result.output
        assert "--context" in result.output

    def test_new_finding_title_required(self, tmp_path: Path) -> None:
        """Omitting --title exits non-zero."""
        runner = CliRunner()
        result = runner.invoke(kb, ["new-finding", str(tmp_path)])
        assert result.exit_code != 0

    def test_new_finding_confidence_choice(self, tmp_path: Path) -> None:
        """--confidence high is written to the file."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "new-finding",
                str(tmp_path),
                "--title",
                "High conf",
                "--confidence",
                "high",
            ],
        )
        assert result.exit_code == 0
        finding = next((tmp_path / "findings").glob("*.md"))
        assert "confidence: high" in finding.read_text(encoding="utf-8")

    def test_new_finding_invalid_confidence_exits_1(self, tmp_path: Path) -> None:
        """Invalid --confidence value exits non-zero."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            ["new-finding", str(tmp_path), "--title", "Bad", "--confidence", "maybe"],
        )
        assert result.exit_code != 0

    def test_new_finding_tags_written(self, tmp_path: Path) -> None:
        """Comma-separated --tags appear in the generated file."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "new-finding",
                str(tmp_path),
                "--title",
                "Tagged finding",
                "--tags",
                "perf,cache",
            ],
        )
        assert result.exit_code == 0
        finding = next((tmp_path / "findings").glob("*.md"))
        content = finding.read_text(encoding="utf-8")
        assert "perf" in content
        assert "cache" in content

    def test_new_finding_context_written(self, tmp_path: Path) -> None:
        """Custom --context is embedded in the generated file."""
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "new-finding",
                str(tmp_path),
                "--title",
                "Context finding",
                "--context",
                "Observed during load test at 500 RPS.",
            ],
        )
        assert result.exit_code == 0
        finding = next((tmp_path / "findings").glob("*.md"))
        assert "500 RPS" in finding.read_text(encoding="utf-8")

    def test_new_finding_default_path_is_cwd(self, tmp_path: Path) -> None:
        """Omitting PATH defaults to current directory."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(kb, ["new-finding", "--title", "CWD finding"])
            assert result.exit_code == 0, result.output
            assert (Path(td) / "findings").exists()

    def test_new_finding_missing_path_exits_1(self, tmp_path: Path) -> None:
        """Non-existent PATH exits with code 1."""
        runner = CliRunner()
        missing = tmp_path / "no-such-kb"
        result = runner.invoke(kb, ["new-finding", str(missing), "--title", "Fail"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_kb_help_lists_new_finding(self) -> None:
        """kb --help lists new-finding as a subcommand."""
        runner = CliRunner()
        result = runner.invoke(kb, ["--help"])
        assert result.exit_code == 0
        assert "new-finding" in result.output
