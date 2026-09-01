"""Tests for the shared installer facade in ``okf_schema.okfkb.install``."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from okf_schema.okfkb.install import install_kb
from okf_schema.skill_installer import SKILL_FAMILIES, InstallationError, resolve_destination

# @tests_req SwRS-OKFSCHEMA-OKFKB-002


def test_install_kb_installs_exact_family_at_supplied_destination(tmp_path: Path) -> None:
    """The compatibility facade installs all and only the packaged okfkb family."""
    destination = tmp_path / "skills"

    report = install_kb(destination)

    assert report.destination == destination.resolve()
    assert {entry.skill for entry in report.skills} == set(SKILL_FAMILIES["okfkb"])
    assert all((destination / skill / "SKILL.md").is_file() for skill in SKILL_FAMILIES["okfkb"])


def test_install_kb_updates_owned_directory_and_preserves_unrelated_content(
    tmp_path: Path,
) -> None:
    """A repeated install updates owned files without deleting unrelated entries."""
    destination = tmp_path / "skills"
    install_kb(destination)
    owned = destination / "okfkb-record-findings"
    unrelated = destination / "other-skill"
    (owned / "stale.txt").write_text("stale", encoding="utf-8")
    unrelated.mkdir()
    (unrelated / "keep.txt").write_text("keep", encoding="utf-8")

    report = install_kb(destination)

    assert {entry.status for entry in report.skills} == {"updated"}
    assert not (owned / "stale.txt").exists()
    assert (unrelated / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_install_kb_does_not_mutate_guidelines_or_agents_file(tmp_path: Path) -> None:
    """The retired guideline and AGENTS.md mutations are absent from the facade."""
    destination = tmp_path / "skills"

    install_kb(destination)

    assert not (tmp_path / "AGENTS.md").exists()
    assert not (destination / "guidelines").exists()


def test_install_kb_no_longer_exposes_force_parameter() -> None:
    """The retired force option is absent from the installer API."""
    assert "force" not in inspect.signature(install_kb).parameters


def test_install_kb_rejects_retired_force_keyword(tmp_path: Path) -> None:
    """The facade rejects the retired force keyword instead of ignoring it."""
    with pytest.raises(TypeError):
        install_kb(tmp_path / "skills", force=True)


def test_install_kb_rejects_owned_symbolic_link(tmp_path: Path) -> None:
    """The facade preserves the shared installer's symlink safety contract."""
    destination = tmp_path / "skills"
    destination.mkdir()
    target = tmp_path / "outside"
    target.mkdir()
    link = destination / "okfkb-gardening"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(InstallationError, match="symbolic link.*okfkb-gardening"):
        install_kb(destination)

    assert link.is_symlink()


def test_install_kb_rejects_explicit_destination_symlink_after_resolution(
    tmp_path: Path,
) -> None:
    """Public destination resolution must preserve a symlink for rejection."""
    destination = tmp_path / "skills"
    target = tmp_path / "outside"
    target.mkdir()
    destination.symlink_to(target, target_is_directory=True)

    resolved_destination = resolve_destination(destination, cwd=tmp_path)

    with pytest.raises(InstallationError, match="symbolic link"):
        install_kb(resolved_destination)

    assert destination.is_symlink()
    assert not (target / "okfkb").exists()
