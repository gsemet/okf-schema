"""Tests for src/okf_schema/kb/install.py — install_kb()."""

from __future__ import annotations

from pathlib import Path

import pytest

from okf_schema.kb.install import install_kb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GUIDELINE_NAME = "knowledge-base.guidelines.md"
_SKILL_NAMES = ("consolidate-knowledge-base", "record-finding")


def _agents_guideline(base: Path) -> Path:
    return base / "guidelines" / _GUIDELINE_NAME


def _agents_skill(base: Path, skill: str) -> Path:
    return base / "skills" / skill


# ---------------------------------------------------------------------------
# Base directory detection
# ---------------------------------------------------------------------------


class TestBaseDirectoryDetection:
    """install_kb picks the right base directory."""

    def test_creates_dot_agents_when_neither_exists(self, tmp_path: Path) -> None:
        """Creates .agents/ when neither .agents/ nor .github/ exists."""
        install_kb(tmp_path)
        assert (tmp_path / ".agents").is_dir()

    def test_prefers_dot_agents_over_dot_github(self, tmp_path: Path) -> None:
        """Uses .agents/ when both .agents/ and .github/ exist."""
        (tmp_path / ".agents").mkdir()
        (tmp_path / ".github").mkdir()
        install_kb(tmp_path)
        assert _agents_guideline(tmp_path / ".agents").is_file()

    def test_falls_back_to_dot_github(self, tmp_path: Path) -> None:
        """Uses .github/ when only .github/ exists."""
        (tmp_path / ".github").mkdir()
        install_kb(tmp_path)
        assert _agents_guideline(tmp_path / ".github").is_file()

    def test_dot_agents_does_not_create_dot_github(self, tmp_path: Path) -> None:
        """Does not create .github/ when .agents/ is used."""
        install_kb(tmp_path)
        assert not (tmp_path / ".github").exists()


# ---------------------------------------------------------------------------
# File installation
# ---------------------------------------------------------------------------


class TestFileInstallation:
    """install_kb copies skills and guideline."""

    def test_installs_guideline(self, tmp_path: Path) -> None:
        """Copies knowledge-base.guidelines.md into <base>/guidelines/."""
        install_kb(tmp_path)
        assert _agents_guideline(tmp_path / ".agents").is_file()

    def test_installs_all_skills(self, tmp_path: Path) -> None:
        """Copies all bundled skill directories into <base>/skills/."""
        install_kb(tmp_path)
        for skill in _SKILL_NAMES:
            assert _agents_skill(tmp_path / ".agents", skill).is_dir(), (
                f"Skill directory missing: {skill}"
            )

    def test_skill_directory_has_skill_md(self, tmp_path: Path) -> None:
        """Each skill directory contains SKILL.md."""
        install_kb(tmp_path)
        for skill in _SKILL_NAMES:
            skill_md = _agents_skill(tmp_path / ".agents", skill) / "SKILL.md"
            assert skill_md.is_file(), f"SKILL.md missing in {skill}"

    def test_installs_into_dot_github_fallback(self, tmp_path: Path) -> None:
        """Skills and guideline land under .github/ when only .github/ exists."""
        (tmp_path / ".github").mkdir()
        install_kb(tmp_path)
        assert _agents_guideline(tmp_path / ".github").is_file()
        for skill in _SKILL_NAMES:
            assert _agents_skill(tmp_path / ".github", skill).is_dir()


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------


class TestConflictResolution:
    """install_kb skips existing files unless --force."""

    def test_skips_existing_guideline(self, tmp_path: Path) -> None:
        """Does not overwrite existing guideline when force=False."""
        base = tmp_path / ".agents"
        (base / "guidelines").mkdir(parents=True)
        sentinel = "ORIGINAL_CONTENT"
        (base / "guidelines" / _GUIDELINE_NAME).write_text(sentinel, encoding="utf-8")

        install_kb(tmp_path, force=False)

        content = (base / "guidelines" / _GUIDELINE_NAME).read_text(encoding="utf-8")
        assert content == sentinel

    def test_skips_existing_skill(self, tmp_path: Path) -> None:
        """Does not overwrite existing skill directory when force=False."""
        base = tmp_path / ".agents"
        skill_dir = base / "skills" / "record-finding"
        skill_dir.mkdir(parents=True)
        sentinel_file = skill_dir / "custom.txt"
        sentinel_file.write_text("sentinel", encoding="utf-8")

        install_kb(tmp_path, force=False)

        assert sentinel_file.exists(), "Sentinel file was removed during skip"

    def test_force_overwrites_guideline(self, tmp_path: Path) -> None:
        """Overwrites existing guideline when force=True."""
        base = tmp_path / ".agents"
        (base / "guidelines").mkdir(parents=True)
        (base / "guidelines" / _GUIDELINE_NAME).write_text("OLD", encoding="utf-8")

        install_kb(tmp_path, force=True)

        content = (base / "guidelines" / _GUIDELINE_NAME).read_text(encoding="utf-8")
        assert content != "OLD"

    def test_force_overwrites_skill(self, tmp_path: Path) -> None:
        """Overwrites existing skill directory when force=True."""
        base = tmp_path / ".agents"
        skill_dir = base / "skills" / "record-finding"
        skill_dir.mkdir(parents=True)
        extra_file = skill_dir / "extra.txt"
        extra_file.write_text("extra", encoding="utf-8")

        install_kb(tmp_path, force=True)

        # After force overwrite the skill dir exists and has SKILL.md
        assert (skill_dir / "SKILL.md").is_file()


# ---------------------------------------------------------------------------
# AGENTS.md patching
# ---------------------------------------------------------------------------


class TestAgentsMdPatching:
    """install_kb creates or patches AGENTS.md."""

    def test_creates_agents_md_when_missing(self, tmp_path: Path) -> None:
        """Creates AGENTS.md when it does not exist."""
        install_kb(tmp_path)
        assert (tmp_path / "AGENTS.md").is_file()

    def test_created_agents_md_contains_guideline_ref(self, tmp_path: Path) -> None:
        """Created AGENTS.md references the installed guideline."""
        install_kb(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert _GUIDELINE_NAME in content

    def test_created_agents_md_has_project_stub(self, tmp_path: Path) -> None:
        """Created AGENTS.md has at least a minimal heading/stub."""
        install_kb(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "AGENTS" in content or "#" in content

    def test_appends_ref_to_existing_agents_md(self, tmp_path: Path) -> None:
        """Appends guideline reference to existing AGENTS.md."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# AGENTS.md\n\nexisting content\n", encoding="utf-8")
        install_kb(tmp_path)
        content = agents_md.read_text(encoding="utf-8")
        assert _GUIDELINE_NAME in content
        assert "existing content" in content

    def test_idempotent_agents_md_patch(self, tmp_path: Path) -> None:
        """Running install_kb twice does not duplicate the guideline reference."""
        install_kb(tmp_path)
        install_kb(tmp_path, force=True)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert content.count(_GUIDELINE_NAME) == 1

    def test_no_duplicate_on_existing_ref(self, tmp_path: Path) -> None:
        """Does not append ref when it already exists in AGENTS.md."""
        base = tmp_path / ".agents"
        base.mkdir()
        ref_line = f"- [Knowledge Base Guidelines](.agents/guidelines/{_GUIDELINE_NAME})"
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(f"# AGENTS.md\n\n{ref_line}\n", encoding="utf-8")
        install_kb(tmp_path)
        content = agents_md.read_text(encoding="utf-8")
        assert content.count(_GUIDELINE_NAME) == 1

    def test_agents_md_ref_uses_dot_github_path_when_applicable(self, tmp_path: Path) -> None:
        """AGENTS.md reference path reflects .github/ when that is the base."""
        (tmp_path / ".github").mkdir()
        install_kb(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert ".github/guidelines" in content


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """install_kb raises on invalid target."""

    def test_errors_when_target_missing(self, tmp_path: Path) -> None:
        """Raises RuntimeError when target path does not exist."""
        missing = tmp_path / "does_not_exist"
        with pytest.raises((RuntimeError, SystemExit)):
            install_kb(missing)


# ---------------------------------------------------------------------------
# Summary output
# ---------------------------------------------------------------------------


class TestSummaryOutput:
    """install_kb prints a summary."""

    def test_prints_summary(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Prints at least one installed/skipped line."""
        install_kb(tmp_path)
        captured = capsys.readouterr()
        assert captured.out  # non-empty output
