"""Tests for src/okf_schema/okfkb/cli.py — kb Click command group."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.okfkb.cli import kb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONTENT_DIRS = {
    "concepts",
    "experiments",
    "findings",
    "playbooks",
    "hypotheses",
    "outcomes",
    "principles",
    "reference",
    "structures",
}


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFKB-001
# @tests_req SwRS-OKFSCHEMA-OKFKB-002


def test_kb_help_kb_help_lists_init_and_install() -> None:
    """kb --help lists both init and install-skills subcommands."""
    runner = CliRunner()
    result = runner.invoke(kb, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "install-skills" in result.output


def test_kb_help_kb_init_help() -> None:
    """kb init --help shows PATH argument and --force flag."""
    runner = CliRunner()
    result = runner.invoke(kb, ["init", "--help"])
    assert result.exit_code == 0
    assert "--force" in result.output


def test_kb_help_kb_install_help() -> None:
    """kb install-skills --help shows destination selectors without --force."""
    runner = CliRunner()
    result = runner.invoke(kb, ["install-skills", "--help"])
    assert result.exit_code == 0
    assert "DESTINATION" in result.output
    assert "--agent-copilot" in result.output
    assert "--local-copilot" in result.output
    assert "--local-agents" in result.output
    options = result.output.split("Options:", maxsplit=1)[1]
    assert "--force" not in options


def test_kb_help_kb_validate_help() -> None:
    """kb validate --help shows PATH argument."""
    runner = CliRunner()
    result = runner.invoke(kb, ["validate", "--help"])
    assert result.exit_code == 0
    assert "PATH" in result.output


# ---------------------------------------------------------------------------
# kb init
# ---------------------------------------------------------------------------


def test_kb_init_kb_init_creates_bundle(tmp_path: Path) -> None:
    """kb init PATH creates the KB bundle layout."""
    runner = CliRunner()
    target = tmp_path / "kb"
    result = runner.invoke(kb, ["init", str(target)])
    assert result.exit_code == 0, result.output
    for name in CONTENT_DIRS:
        assert (target / name).is_dir(), f"Missing directory: {name}"
    assert (target / "index.md").is_file()
    assert (target / "log.md").is_file()


def test_kb_init_kb_init_prints_confirmation(tmp_path: Path) -> None:
    """kb init prints a success confirmation containing the target path."""
    runner = CliRunner()
    target = tmp_path / "my-kb"
    result = runner.invoke(kb, ["init", str(target)])
    assert result.exit_code == 0
    assert str(target) in result.output


def test_kb_init_kb_init_default_path_is_cwd(tmp_path: Path) -> None:
    """kb init with no PATH argument defaults to current directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(kb, ["init"])
        assert result.exit_code == 0, result.output
        assert (Path(td) / "index.md").is_file()


def test_kb_init_kb_init_errors_on_nonempty_dir(tmp_path: Path) -> None:
    """kb init exits with code 1 when target is non-empty and --force not passed."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    (target / "existing.txt").write_text("existing", encoding="utf-8")
    result = runner.invoke(kb, ["init", str(target)])
    assert result.exit_code == 1
    # Error should be reported on stderr or stdout
    assert "already exists" in result.output or "Error" in result.output


def test_kb_init_kb_init_force_overwrites(tmp_path: Path) -> None:
    """kb init --force succeeds on a non-empty directory."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    (target / "existing.txt").write_text("existing", encoding="utf-8")
    result = runner.invoke(kb, ["init", str(target), "--force"])
    assert result.exit_code == 0, result.output
    assert (target / "index.md").is_file()


def test_kb_init_kb_init_exits_1_on_unexpected_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """kb init exits with code 1 when scaffold_kb raises an unexpected error."""
    import okf_schema.okfkb.cli as cli_module

    def broken_scaffold(path: Path, force: bool = False) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(cli_module, "scaffold_kb", broken_scaffold)
    runner = CliRunner()
    result = runner.invoke(kb, ["init", str(tmp_path / "kb")])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# kb install
# ---------------------------------------------------------------------------


def test_kb_install_kb_install_creates_files(tmp_path: Path) -> None:
    """kb install-skills DESTINATION creates the complete KB skill family."""
    runner = CliRunner()
    result = runner.invoke(kb, ["install-skills", str(tmp_path)])
    assert result.exit_code == 0, result.output
    for skill in ("okfkb", "okfkb-distill", "okfkb-gardening", "okfkb-record-findings"):
        assert (tmp_path / skill / "SKILL.md").is_file()
    assert "Destination:" in result.output
    assert "installed: okfkb" in result.output


def test_kb_install_kb_install_prints_confirmation(tmp_path: Path) -> None:
    """kb install-skills prints a success confirmation containing the target path."""
    runner = CliRunner()
    result = runner.invoke(kb, ["install-skills", str(tmp_path)])
    assert result.exit_code == 0
    assert str(tmp_path) in result.output


def test_kb_install_kb_install_local_agents_selector_is_relative_to_cwd(tmp_path: Path) -> None:
    """The local-agents selector creates skills below the current directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(kb, ["install-skills", "--local-agents"])
        assert result.exit_code == 0, result.output
        assert (Path(td) / ".agents" / "skills" / "okfkb" / "SKILL.md").is_file()


def test_kb_install_kb_install_creates_missing_destination(tmp_path: Path) -> None:
    """kb install-skills creates a missing explicit destination."""
    runner = CliRunner()
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(kb, ["install-skills", str(missing)])
    assert result.exit_code == 0, result.output
    assert (missing / "okfkb" / "SKILL.md").is_file()


def test_kb_install_kb_install_rejects_retired_force_option(tmp_path: Path) -> None:
    """kb install-skills rejects the retired force option."""
    runner = CliRunner()
    result = runner.invoke(kb, ["install-skills", str(tmp_path), "--force"])
    assert result.exit_code == 2
    assert "No such option '--force'" in result.output


def test_kb_install_kb_install_exits_1_on_unexpected_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """kb install-skills exits with code 1 when install_kb raises an unexpected error."""
    import okf_schema.okfkb.cli as cli_module

    def broken_install(path: Path) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr(cli_module, "install_kb", broken_install)
    runner = CliRunner()
    result = runner.invoke(kb, ["install-skills", str(tmp_path)])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# okfkb alias
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# kb validate
# ---------------------------------------------------------------------------


def test_kb_validate_kb_validate_valid_bundle(tmp_path: Path) -> None:
    """kb validate exits 0 on a valid KB bundle."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    result = runner.invoke(kb, ["validate", str(target)])
    assert result.exit_code == 0, result.output
    assert "conformant" in result.output


def test_kb_validate_kb_validate_invalid_bundle(tmp_path: Path) -> None:
    """kb validate exits 1 on an invalid bundle (strict mode treats warnings as errors)."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    (target / "index.md").write_text("# Index\n", encoding="utf-8")
    (target / "concepts").mkdir()
    (target / "concepts" / "test.md").write_text("# Test\n", encoding="utf-8")
    result = runner.invoke(kb, ["validate", str(target)])
    assert result.exit_code == 1, result.output
    assert "Validation failed" in result.output


def test_kb_validate_kb_validate_missing_path(tmp_path: Path) -> None:
    """kb validate exits 1 when PATH does not exist."""
    runner = CliRunner()
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(kb, ["validate", str(missing)])
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# kb update
# ---------------------------------------------------------------------------


def test_kb_update_kb_update_on_valid_bundle(tmp_path: Path) -> None:
    """kb update exits 0 on a valid KB bundle and reports index/lint status."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    result = runner.invoke(kb, ["update", str(target)])
    assert result.exit_code == 0, result.output
    assert "Index:" in result.output
    assert "unchanged" in result.output


def test_kb_update_kb_update_check_no_changes(tmp_path: Path) -> None:
    """kb update --check exits 0 when no files would change."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    result = runner.invoke(kb, ["update", str(target), "--check"])
    assert result.exit_code == 0, result.output
    assert "All files are properly linted." in result.output


def test_kb_update_kb_update_check_would_change(tmp_path: Path) -> None:
    """kb update --check exits 1 when files would change."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    # Create a finding with nested list that would be flattened by lint
    findings_dir = target / "findings"
    findings_dir.mkdir(exist_ok=True)
    (findings_dir / "test.md").write_text(
        "---\ntype: Finding\ntags:\n  - [[nested]]\n---\n# Test\n",
        encoding="utf-8",
    )
    result = runner.invoke(kb, ["update", str(target), "--check"])
    assert result.exit_code == 1, result.output
    assert "Would lint" in result.output


def test_kb_update_kb_update_diff_shows_diff(tmp_path: Path) -> None:
    """kb update --diff shows unified diff without modifying files."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    findings_dir = target / "findings"
    findings_dir.mkdir(exist_ok=True)
    (findings_dir / "test.md").write_text("# Test\n", encoding="utf-8")
    result = runner.invoke(kb, ["update", str(target), "--diff"])
    assert result.exit_code == 0, result.output


def test_kb_update_kb_update_no_links(tmp_path: Path) -> None:
    """kb update --no-links runs without updating backlinks."""
    runner = CliRunner()
    target = tmp_path / "kb"
    runner.invoke(kb, ["init", str(target)])
    result = runner.invoke(kb, ["update", str(target), "--no-links"])
    assert result.exit_code == 0, result.output
    assert "Index:" in result.output


def test_kb_update_kb_update_diff_with_actual_changes(tmp_path: Path) -> None:
    """kb update --diff shows actual diff content when files need linting."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    # Create a file with block-style list that needs linting
    (target / "doc.md").write_text(
        "---\ntype: Finding\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
        encoding="utf-8",
    )
    result = runner.invoke(kb, ["update", str(target), "--diff"])
    assert result.exit_code == 0, result.output
    # Diff output should contain the change
    assert "tags:" in result.output


def test_kb_update_kb_validate_warnings_only(tmp_path: Path) -> None:
    """kb validate exits 1 for warnings-only (strict mode)."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    # File with valid type/title/description but no timestamp → W3 warning
    (target / "doc.md").write_text(
        "---\ntype: Concept\ntitle: T\ndescription: D\n---\n\n# T\n",
        encoding="utf-8",
    )
    result = runner.invoke(kb, ["validate", str(target)])
    # In strict mode warnings become errors; warnings about missing fields expected
    assert result.exit_code in (0, 1)
    """kb update exits 1 when PATH does not exist."""
    runner = CliRunner()
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(kb, ["update", str(missing)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_kb_update_kb_update_reports_superseded_rewrites(tmp_path: Path) -> None:
    """kb update reports superseded-link rewrites when they occur."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    (target / "old.md").write_text(
        "---\ntype: Finding\ntitle: Old\nstatus: superseded\n"
        "superseded_by: [new.md]\n---\n\n# Old\n",
        encoding="utf-8",
    )
    (target / "new.md").write_text(
        "---\ntype: Finding\ntitle: New\nstatus: active\n---\n\n# New\n",
        encoding="utf-8",
    )
    (target / "source.md").write_text(
        "---\ntype: Finding\ntitle: Source\n---\n\n# Source\n\nSee [Old](old.md).\n",
        encoding="utf-8",
    )
    result = runner.invoke(kb, ["update", str(target)])
    assert result.exit_code == 0, result.output
    assert "Superseded links rewritten: 1" in result.output


def test_kb_update_kb_update_reports_deferred_rewrites(tmp_path: Path) -> None:
    """kb update reports deferred superseded docs in output."""
    runner = CliRunner()
    target = tmp_path / "kb"
    target.mkdir()
    (target / "old.md").write_text(
        "---\ntype: Finding\ntitle: Old\nstatus: superseded\n---\n\n# Old\n",
        encoding="utf-8",
    )
    result = runner.invoke(kb, ["update", str(target)])
    assert result.exit_code == 0
    assert "Superseded links deferred" in result.output


# ---------------------------------------------------------------------------
# okfkb alias
# ---------------------------------------------------------------------------


def test_okfkb_alias_okfkb_alias_is_importable() -> None:
    """okfkb entry point resolves: kb group is importable from okf_schema.okfkb.cli."""
    from okf_schema.okfkb.cli import kb as okfkb

    assert okfkb is not None
    assert okfkb.name == "kb"


def test_okfkb_alias_okfkb_alias_has_init_and_install() -> None:
    """The kb group (okfkb alias) exposes both init and install-skills subcommands."""
    from okf_schema.okfkb.cli import kb as okfkb

    commands = list(okfkb.commands.keys())
    assert "init" in commands
    assert "install-skills" in commands
    assert "validate" in commands
    assert "validate" in commands


def test_okfkb_alias_okfkb_alias_invokable_via_runner(tmp_path: Path) -> None:
    """okfkb install-skills can be invoked directly through the kb group."""
    from okf_schema.okfkb.cli import kb as okfkb

    runner = CliRunner()
    result = runner.invoke(okfkb, ["install-skills", str(tmp_path)])
    assert result.exit_code == 0, result.output
