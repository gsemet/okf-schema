"""Tests for the standalone okfreq skill-installation command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from okf_schema.okfreq.cli import okfreq
from okf_schema.skill_installer import SKILL_FAMILIES


def test_install_skills_help_matches_shared_destination_contract() -> None:
    """okfreq install-skills exposes the common destination selectors."""
    runner = CliRunner()
    result = runner.invoke(okfreq, ["install-skills", "--help"])

    assert result.exit_code == 0
    assert "DESTINATION" in result.output
    for option in ("--agent-copilot", "--local-copilot", "--local-agents"):
        assert option in result.output
    assert "--force" not in result.output


def test_install_skills_installs_only_requirements_family(tmp_path: Path) -> None:
    """okfreq install-skills installs the base and companion requirements skills."""
    runner = CliRunner()
    destination = tmp_path / "skills"

    result = runner.invoke(okfreq, ["install-skills", str(destination)])

    assert result.exit_code == 0, result.output
    assert result.output.startswith(f"Destination: {destination.resolve()}\n")
    assert [line.split(": ")[-1] for line in result.output.splitlines()[1:]] == list(
        SKILL_FAMILIES["okfreq"]
    )
    for skill in SKILL_FAMILIES["okfreq"]:
        assert (destination / skill / "SKILL.md").is_file()
    assert not (destination / "okfkb" / "SKILL.md").exists()


def test_install_skills_local_copilot_selector_resolves_from_working_directory(
    tmp_path: Path,
) -> None:
    """The local Copilot selector uses the command working directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as working_directory:
        result = runner.invoke(okfreq, ["install-skills", "--local-copilot"])

    assert result.exit_code == 0, result.output
    assert (Path(working_directory) / ".github" / "skills" / "okfreq" / "SKILL.md").is_file()


def test_install_skills_relative_destination_resolves_from_working_directory(
    tmp_path: Path,
) -> None:
    """An explicit relative destination is resolved from the command directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as working_directory:
        result = runner.invoke(okfreq, ["install-skills", "vendor/skills"])

    destination = Path(working_directory) / "vendor" / "skills"
    assert result.exit_code == 0, result.output
    assert f"Destination: {destination}" in result.output
    assert (destination / "okfreq" / "SKILL.md").is_file()


def test_install_skills_agent_copilot_selector_matches_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The explicit global selector targets the same location as the default."""
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    runner = CliRunner()

    result = runner.invoke(okfreq, ["install-skills", "--agent-copilot"])

    destination = home / ".copilot" / "skills"
    assert result.exit_code == 0, result.output
    assert (destination / "okfreq" / "SKILL.md").is_file()
