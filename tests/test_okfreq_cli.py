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


def test_acceptance_paths_cli_surface(tmp_path: Path) -> None:
    """CLI commands enforce acceptance paths, W003/W004, trace, report, new, and retire."""
    runner = CliRunner()
    req_dir = tmp_path / "requirements"
    assert runner.invoke(okfreq, ["init", str(req_dir)]).exit_code == 0

    cfg = req_dir / "config.yml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs",
            "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
        ),
        encoding="utf-8",
    )

    new_strs = runner.invoke(
        okfreq,
        [
            "new",
            "strs",
            "Export CSV",
            "--path",
            str(req_dir),
            "--project",
            "demo",
            "--user-need",
            "Users export CSV.",
            "--description",
            "The tool SHALL export CSV.",
        ],
    )
    assert new_strs.exit_code == 0, new_strs.output
    strs_file = next((req_dir / "tiers" / "strs").rglob("StRS-*.md"))
    assert "### Main paths" in strs_file.read_text(encoding="utf-8")

    # W004 warning exits 0 and prints W004
    val_warn = runner.invoke(okfreq, ["validate", str(req_dir)])
    assert val_warn.exit_code == 0, val_warn.output
    assert "W004" in val_warn.output

    # Add @accepts_req marker -> trace prints accepted:, retire refuses draft
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_acc.py").write_text("# @accepts_req StRS-default-001#S1\n", encoding="utf-8")
    traced = runner.invoke(okfreq, ["trace", str(req_dir)])
    assert traced.exit_code == 0, traced.output
    assert "accepted:" in traced.output

    retired = runner.invoke(okfreq, ["retire", "StRS-default-001", "--path", str(req_dir), "--yes"])
    assert retired.exit_code != 0
    assert "test_acc.py" in retired.output

    # update-coverage writes accepted_in_files on StRS; generate-report writes Markdown columns
    upd = runner.invoke(okfreq, ["update-coverage", str(req_dir)])
    assert upd.exit_code == 0, upd.output
    assert "accepted_in_files:" in strs_file.read_text(encoding="utf-8")

    rep_md = tmp_path / "report.md"
    gen = runner.invoke(
        okfreq,
        ["generate-report", str(req_dir), "--output-summary-md", str(rep_md)],
    )
    assert gen.exit_code == 0, gen.output
    assert "Accepted" in rep_md.read_text(encoding="utf-8")
