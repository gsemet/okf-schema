"""Tests for okf_schema.okfkb.finding — new_finding() function and okfkb new-finding CLI."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema.okfkb.cli import kb
from okf_schema.okfkb.finding import _slugify, new_finding

# ---------------------------------------------------------------------------
# _slugify helper
# ---------------------------------------------------------------------------


def test_slugify_simple_title() -> None:
    assert _slugify("HW Failure investigation") == "hw-failure-investigation"


def test_slugify_special_chars_collapsed() -> None:
    assert _slugify("foo & bar — baz") == "foo-bar-baz"


def test_slugify_leading_trailing_dashes_stripped() -> None:
    slug = _slugify("  hello  ")
    assert not slug.startswith("-")
    assert not slug.endswith("-")


def test_slugify_max_length_60() -> None:
    long_title = "a" * 100
    assert len(_slugify(long_title)) <= 60


def test_slugify_digits_preserved() -> None:
    assert _slugify("issue 42 fix") == "issue-42-fix"


# ---------------------------------------------------------------------------
# new_finding() — happy path
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFKB-003


def test_new_finding_happy_path_creates_file_in_findings_dir(tmp_path: Path) -> None:
    """Creates a file inside <kb_path>/findings/."""
    (tmp_path / "findings").mkdir()
    filepath = new_finding(tmp_path, "Something observed")
    assert filepath.parent == tmp_path / "findings"
    assert filepath.exists()


def test_new_finding_happy_path_creates_findings_dir_if_missing(tmp_path: Path) -> None:
    """Creates findings/ when it does not exist yet."""
    assert not (tmp_path / "findings").exists()
    filepath = new_finding(tmp_path, "My finding")
    assert (tmp_path / "findings").is_dir()
    assert filepath.exists()


def test_new_finding_happy_path_filename_format(tmp_path: Path) -> None:
    """Filename matches YYYY.MM.DD-HH.MM-<slug>.md."""
    filepath = new_finding(tmp_path, "Cache miss rate spike")
    assert re.fullmatch(
        r"\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}-cache-miss-rate-spike\.md",
        filepath.name,
    ), filepath.name


def test_new_finding_happy_path_frontmatter_contains_required_fields(tmp_path: Path) -> None:
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
    assert "generated:" in content
    assert "links:" in content
    assert "backlinks:" in content
    assert "kb_status: active" in content


def test_new_finding_happy_path_description_defaults_to_title(tmp_path: Path) -> None:
    """description mirrors title when not provided."""
    filepath = new_finding(tmp_path, "Memory leak")
    content = filepath.read_text(encoding="utf-8")
    assert "description: Memory leak" in content


def test_new_finding_happy_path_custom_description(tmp_path: Path) -> None:
    """Custom description is written to frontmatter."""
    filepath = new_finding(tmp_path, "Memory leak", description="RSS grows unboundedly")
    content = filepath.read_text(encoding="utf-8")
    assert "RSS grows unboundedly" in content


def test_new_finding_happy_path_tags_written(tmp_path: Path) -> None:
    """Tags list is embedded in frontmatter."""
    filepath = new_finding(tmp_path, "Network jitter", tags=["network", "latency"])
    content = filepath.read_text(encoding="utf-8")
    assert "network" in content
    assert "latency" in content


def test_new_finding_happy_path_empty_tags_produces_empty_list(tmp_path: Path) -> None:
    """No tags → tags: [] in YAML."""
    filepath = new_finding(tmp_path, "No tags")
    content = filepath.read_text(encoding="utf-8")
    assert "tags: []" in content


def test_new_finding_happy_path_body_has_markdown_sections(tmp_path: Path) -> None:
    """Generated body includes Observation, Evidence, Implications headings."""
    filepath = new_finding(tmp_path, "With body")
    content = filepath.read_text(encoding="utf-8")
    assert "## Observation" in content
    assert "## Evidence" in content
    assert "## Implications" in content


def test_new_finding_happy_path_h1_contains_title(tmp_path: Path) -> None:
    """Body h1 echoes the finding title."""
    filepath = new_finding(tmp_path, "Signal noise")
    content = filepath.read_text(encoding="utf-8")
    assert "# Finding: Signal noise" in content


def test_new_finding_happy_path_file_delimited_by_yaml_fences(tmp_path: Path) -> None:
    """File starts and ends YAML block with --- delimiters."""
    filepath = new_finding(tmp_path, "Fence check")
    content = filepath.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "\n---\n" in content


# ---------------------------------------------------------------------------
# new_finding() — confidence levels
# ---------------------------------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(name="low", level="low")
@Parametrization.case(name="medium", level="medium")
@Parametrization.case(name="high", level="high")
@Parametrization.case(name="confirmed", level="confirmed")
def test_new_finding_confidence_valid_confidence(tmp_path: Path, level: str) -> None:
    filepath = new_finding(tmp_path, f"Finding {level}", confidence=level)
    assert f"confidence: {level}" in filepath.read_text(encoding="utf-8")


def test_new_finding_confidence_invalid_confidence_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid confidence"):
        new_finding(tmp_path, "Bad conf", confidence="very-sure")


# ---------------------------------------------------------------------------
# new_finding() — error cases
# ---------------------------------------------------------------------------


def test_new_finding_errors_nonexistent_kb_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(ValueError, match="does not exist"):
        new_finding(missing, "Title")


# ---------------------------------------------------------------------------
# CLI — okfkb new-finding
# ---------------------------------------------------------------------------


def test_kb_new_finding_cli_new_finding_creates_file(tmp_path: Path) -> None:
    """new-finding creates a finding file and prints the path."""
    runner = CliRunner()
    result = runner.invoke(
        kb,
        ["new-finding", str(tmp_path), "--title", "CLI test finding"],
    )
    assert result.exit_code == 0, result.output
    findings = list((tmp_path / "findings").glob("*.md"))
    assert len(findings) == 1


def test_kb_new_finding_cli_new_finding_output_contains_path(tmp_path: Path) -> None:
    """Printed output contains the created file path."""
    runner = CliRunner()
    result = runner.invoke(
        kb,
        ["new-finding", str(tmp_path), "--title", "Path check"],
    )
    assert result.exit_code == 0
    assert "findings" in result.output


def test_kb_new_finding_cli_new_finding_help() -> None:
    """new-finding --help exits 0 and shows key options."""
    runner = CliRunner()
    result = runner.invoke(kb, ["new-finding", "--help"])
    assert result.exit_code == 0
    assert "--title" in result.output
    assert "--confidence" in result.output
    assert "--context" in result.output


def test_kb_new_finding_cli_new_finding_title_required(tmp_path: Path) -> None:
    """Omitting --title exits non-zero."""
    runner = CliRunner()
    result = runner.invoke(kb, ["new-finding", str(tmp_path)])
    assert result.exit_code != 0


def test_kb_new_finding_cli_new_finding_confidence_choice(tmp_path: Path) -> None:
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


def test_kb_new_finding_cli_new_finding_invalid_confidence_exits_1(tmp_path: Path) -> None:
    """Invalid --confidence value exits non-zero."""
    runner = CliRunner()
    result = runner.invoke(
        kb,
        ["new-finding", str(tmp_path), "--title", "Bad", "--confidence", "maybe"],
    )
    assert result.exit_code != 0


def test_kb_new_finding_cli_new_finding_tags_written(tmp_path: Path) -> None:
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


def test_kb_new_finding_cli_new_finding_context_written(tmp_path: Path) -> None:
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


def test_kb_new_finding_cli_new_finding_default_path_is_cwd(tmp_path: Path) -> None:
    """Omitting PATH defaults to current directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(kb, ["new-finding", "--title", "CWD finding"])
        assert result.exit_code == 0, result.output
        assert (Path(td) / "findings").exists()


def test_kb_new_finding_cli_new_finding_missing_path_exits_1(tmp_path: Path) -> None:
    """Non-existent PATH exits with code 1."""
    runner = CliRunner()
    missing = tmp_path / "no-such-kb"
    result = runner.invoke(kb, ["new-finding", str(missing), "--title", "Fail"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_kb_new_finding_cli_kb_help_lists_new_finding() -> None:
    """kb --help lists new-finding as a subcommand."""
    runner = CliRunner()
    result = runner.invoke(kb, ["--help"])
    assert result.exit_code == 0
    assert "new-finding" in result.output
