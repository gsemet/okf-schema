"""Tests for src/okf_schema/kb/cli.py — kb Click command group."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.kb.cli import kb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONTENT_DIRS = {
    "concepts",
    "experiments",
    "findings",
    "guides",
    "ideas",
    "principles",
    "reference",
    "structures",
}


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------


class TestKbHelp:
    """The kb group help output lists all subcommands."""

    def test_kb_help_lists_init_and_install(self) -> None:
        """kb --help lists both init and install-skills subcommands."""
        runner = CliRunner()
        result = runner.invoke(kb, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "install-skills" in result.output

    def test_kb_init_help(self) -> None:
        """kb init --help shows PATH argument and --force flag."""
        runner = CliRunner()
        result = runner.invoke(kb, ["init", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output

    def test_kb_install_help(self) -> None:
        """kb install-skills --help shows PATH argument and --force flag."""
        runner = CliRunner()
        result = runner.invoke(kb, ["install-skills", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output


# ---------------------------------------------------------------------------
# kb init
# ---------------------------------------------------------------------------


class TestKbInit:
    """kb init scaffolds a KB bundle at the given path."""

    def test_kb_init_creates_bundle(self, tmp_path: Path) -> None:
        """kb init PATH creates the KB bundle layout."""
        runner = CliRunner()
        target = tmp_path / "kb"
        result = runner.invoke(kb, ["init", str(target)])
        assert result.exit_code == 0, result.output
        for name in CONTENT_DIRS:
            assert (target / name).is_dir(), f"Missing directory: {name}"
        assert (target / "index.md").is_file()
        assert (target / "log.md").is_file()

    def test_kb_init_prints_confirmation(self, tmp_path: Path) -> None:
        """kb init prints a success confirmation containing the target path."""
        runner = CliRunner()
        target = tmp_path / "my-kb"
        result = runner.invoke(kb, ["init", str(target)])
        assert result.exit_code == 0
        assert str(target) in result.output

    def test_kb_init_default_path_is_cwd(self, tmp_path: Path) -> None:
        """kb init with no PATH argument defaults to current directory."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(kb, ["init"])
            assert result.exit_code == 0, result.output
            assert (Path(td) / "index.md").is_file()

    def test_kb_init_errors_on_nonempty_dir(self, tmp_path: Path) -> None:
        """kb init exits with code 1 when target is non-empty and --force not passed."""
        runner = CliRunner()
        target = tmp_path / "kb"
        target.mkdir()
        (target / "existing.txt").write_text("existing", encoding="utf-8")
        result = runner.invoke(kb, ["init", str(target)])
        assert result.exit_code == 1
        # Error should be reported on stderr or stdout
        assert "already exists" in result.output or "Error" in result.output

    def test_kb_init_force_overwrites(self, tmp_path: Path) -> None:
        """kb init --force succeeds on a non-empty directory."""
        runner = CliRunner()
        target = tmp_path / "kb"
        target.mkdir()
        (target / "existing.txt").write_text("existing", encoding="utf-8")
        result = runner.invoke(kb, ["init", str(target), "--force"])
        assert result.exit_code == 0, result.output
        assert (target / "index.md").is_file()

    def test_kb_init_exits_1_on_unexpected_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """kb init exits with code 1 when scaffold_kb raises an unexpected error."""
        import okf_schema.kb.cli as cli_module

        def broken_scaffold(path: Path, force: bool = False) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(cli_module, "scaffold_kb", broken_scaffold)
        runner = CliRunner()
        result = runner.invoke(kb, ["init", str(tmp_path / "kb")])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# kb install
# ---------------------------------------------------------------------------


class TestKbInstall:
    """kb install-skills deploys KB skills and guidelines into a project."""

    def test_kb_install_creates_files(self, tmp_path: Path) -> None:
        """kb install-skills PATH creates skills and guideline files."""
        runner = CliRunner()
        result = runner.invoke(kb, ["install-skills", str(tmp_path)])
        assert result.exit_code == 0, result.output
        # Should create .agents/ or .github/ with skills and guidelines
        agents_dir = tmp_path / ".agents"
        assert agents_dir.exists()
        assert (agents_dir / "guidelines" / "knowledge-base.guidelines.md").is_file()

    def test_kb_install_prints_confirmation(self, tmp_path: Path) -> None:
        """kb install-skills prints a success confirmation containing the target path."""
        runner = CliRunner()
        result = runner.invoke(kb, ["install-skills", str(tmp_path)])
        assert result.exit_code == 0
        assert str(tmp_path) in result.output

    def test_kb_install_default_path_is_cwd(self, tmp_path: Path) -> None:
        """kb install-skills with no PATH argument defaults to current directory."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(kb, ["install-skills"])
            assert result.exit_code == 0, result.output
            assert (Path(td) / ".agents").exists()

    def test_kb_install_errors_when_target_missing(self, tmp_path: Path) -> None:
        """kb install-skills exits with code 1 when PATH does not exist."""
        runner = CliRunner()
        missing = tmp_path / "does-not-exist"
        result = runner.invoke(kb, ["install-skills", str(missing)])
        assert result.exit_code == 1
        assert "Error" in result.output or "does not exist" in result.output

    def test_kb_install_force_overwrites(self, tmp_path: Path) -> None:
        """kb install-skills --force overwrites existing files."""
        runner = CliRunner()
        # First install
        runner.invoke(kb, ["install-skills", str(tmp_path)])
        # Second install with --force should succeed
        result = runner.invoke(kb, ["install-skills", str(tmp_path), "--force"])
        assert result.exit_code == 0, result.output

    def test_kb_install_exits_1_on_unexpected_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """kb install-skills exits with code 1 when install_kb raises an unexpected error."""
        import okf_schema.kb.cli as cli_module

        def broken_install(path: Path, force: bool = False) -> None:
            raise OSError("permission denied")

        monkeypatch.setattr(cli_module, "install_kb", broken_install)
        runner = CliRunner()
        result = runner.invoke(kb, ["install-skills", str(tmp_path)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# okfkb alias
# ---------------------------------------------------------------------------


class TestOkfkbAlias:
    """The okfkb entry point resolves to the kb Click group."""

    def test_okfkb_alias_is_importable(self) -> None:
        """okfkb entry point resolves: kb group is importable from okf_schema.kb.cli."""
        from okf_schema.kb.cli import kb as okfkb

        assert okfkb is not None
        assert okfkb.name == "kb"

    def test_okfkb_alias_has_init_and_install(self) -> None:
        """The kb group (okfkb alias) exposes both init and install-skills subcommands."""
        from okf_schema.kb.cli import kb as okfkb

        commands = list(okfkb.commands.keys())
        assert "init" in commands
        assert "install-skills" in commands

    def test_okfkb_alias_invokable_via_runner(self, tmp_path: Path) -> None:
        """okfkb install-skills can be invoked directly through the kb group."""
        from okf_schema.kb.cli import kb as okfkb

        runner = CliRunner()
        result = runner.invoke(okfkb, ["install-skills", str(tmp_path)])
        assert result.exit_code == 0, result.output
