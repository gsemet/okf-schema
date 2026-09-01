"""Tests for the shared packaged-skill installer."""

# @tests_req SwRS-OKFSCHEMA-OKFKB-002

from __future__ import annotations

import os
from pathlib import Path

import pytest

import okf_schema.skill_installer as installer
from okf_schema.skill_installer import (
    SKILL_FAMILIES,
    InstallationError,
    install_skill_family,
    resolve_destination,
)


def _snapshot(root: Path) -> dict[Path, bytes | None]:
    """Capture directory entries and file bytes below *root*."""
    snapshot: dict[Path, bytes | None] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            snapshot[relative] = None
        elif path.is_file():
            snapshot[relative] = path.read_bytes()
        else:
            snapshot[relative] = None
    return snapshot


def test_skill_families_are_exact_and_immutable() -> None:
    """Each command owns its complete, fixed family of packaged skills."""
    assert dict(SKILL_FAMILIES) == {
        "okf-schema": ("okf-schema",),
        "okfkb": (
            "okfkb",
            "okfkb-distill",
            "okfkb-gardening",
            "okfkb-record-findings",
        ),
        "okfreq": ("okfreq", "okfreq-gardening"),
    }
    with pytest.raises(TypeError):
        SKILL_FAMILIES["other"] = ("other",)  # type: ignore[index]


def test_resolve_destination_defaults_to_global_copilot(tmp_path: Path) -> None:
    """The implicit destination is the user's global Copilot skill directory."""
    assert resolve_destination(cwd=tmp_path) == (Path.home() / ".copilot" / "skills").resolve()


def test_resolve_destination_supports_agent_copilot_selector(tmp_path: Path) -> None:
    """The explicit global Copilot selector resolves to the home directory."""
    assert (
        resolve_destination(agent_copilot=True, cwd=tmp_path)
        == (Path.home() / ".copilot" / "skills").resolve()
    )


def test_resolve_destination_supports_local_copilot_selector(tmp_path: Path) -> None:
    """The local Copilot selector resolves relative to the current directory."""
    assert (
        resolve_destination(local_copilot=True, cwd=tmp_path)
        == (tmp_path / ".github" / "skills").resolve()
    )


def test_resolve_destination_supports_local_agents_selector(tmp_path: Path) -> None:
    """The local agents selector resolves relative to the current directory."""
    assert (
        resolve_destination(local_agents=True, cwd=tmp_path)
        == (tmp_path / ".agents" / "skills").resolve()
    )


def test_resolve_destination_resolves_relative_explicit_path(tmp_path: Path) -> None:
    """A relative explicit destination is anchored to the current directory."""
    assert (
        resolve_destination("custom/skills", cwd=tmp_path)
        == (tmp_path / "custom" / "skills").resolve()
    )


def test_resolve_destination_explicit_path_precedes_selector(tmp_path: Path) -> None:
    """An explicit destination wins even when a selector is also supplied."""
    explicit = tmp_path / "authoritative" / "skills"
    assert resolve_destination(explicit, local_agents=True, cwd=tmp_path) == explicit.resolve()


def test_resolve_destination_rejects_conflicting_selectors(tmp_path: Path) -> None:
    """Multiple selectors without an explicit path fail clearly."""
    with pytest.raises(InstallationError, match="only one"):
        resolve_destination(local_copilot=True, local_agents=True, cwd=tmp_path)


def test_install_skill_family_creates_parents_and_reports_installed(tmp_path: Path) -> None:
    """A new destination creates parents and reports every family member as installed."""
    destination = tmp_path / "missing" / "nested" / "skills"

    report = install_skill_family("okfkb", destination)

    assert report.destination == destination.resolve()
    assert {entry.skill for entry in report.skills} == set(SKILL_FAMILIES["okfkb"])
    assert {entry.status for entry in report.skills} == {"installed"}
    assert all((destination / skill / "SKILL.md").is_file() for skill in SKILL_FAMILIES["okfkb"])


def test_install_skill_family_resolves_relative_destination_from_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A relative installer destination is anchored to the current directory."""
    monkeypatch.chdir(tmp_path)

    report = install_skill_family("okf-schema", Path("skills"))

    assert report.destination == (tmp_path / "skills").resolve()
    assert (tmp_path / "skills" / "okf-schema" / "SKILL.md").is_file()


def test_install_skill_family_replaces_owned_directory_and_preserves_unrelated_content(
    tmp_path: Path,
) -> None:
    """An update removes stale owned files while preserving unrelated destination content."""
    destination = tmp_path / "skills"
    install_skill_family("okf-schema", destination)
    owned = destination / "okf-schema"
    unrelated = destination / "okfreq"
    stale = owned / "stale.txt"
    unrelated.mkdir()
    (unrelated / "keep.txt").write_text("keep", encoding="utf-8")
    stale.write_text("stale", encoding="utf-8")

    report = install_skill_family("okf-schema", destination)

    assert report.skills[0].status == "updated"
    assert not stale.exists()
    assert (unrelated / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_install_skill_family_rejects_owned_symlink_without_following_it(tmp_path: Path) -> None:
    """An owned symlink fails without changing the link or its target."""
    destination = tmp_path / "skills"
    outside = tmp_path / "outside"
    destination.mkdir()
    outside.mkdir()
    (outside / "sentinel.txt").write_text("outside", encoding="utf-8")
    link = destination / "okfkb-distill"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(InstallationError, match="symbolic link.*okfkb-distill"):
        install_skill_family("okfkb", destination)

    assert link.is_symlink()
    assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "outside"


def test_install_skill_family_stages_complete_family_before_mutation(tmp_path: Path) -> None:
    """A family staging failure leaves all existing destination bytes unchanged."""
    destination = tmp_path / "skills"
    destination.mkdir()
    for skill in SKILL_FAMILIES["okfkb"]:
        skill_directory = destination / skill
        skill_directory.mkdir()
        (skill_directory / "sentinel.txt").write_bytes(skill.encode("utf-8"))
    (destination / "unrelated.txt").write_bytes(b"unrelated")
    before = _snapshot(destination)

    def fail_staging(skill_names: tuple[str, ...], staging_root: Path) -> None:
        assert skill_names == SKILL_FAMILIES["okfkb"]
        assert not staging_root.exists()
        raise RuntimeError("missing packaged resource")

    with pytest.raises(InstallationError, match="Unable to stage skill family"):
        install_skill_family("okfkb", destination, stage_family=fail_staging)

    assert _snapshot(destination) == before


def test_install_skill_family_rejects_unknown_family(tmp_path: Path) -> None:
    """An unknown command family fails before resource preparation."""
    with pytest.raises(InstallationError, match="Unknown skill family"):
        install_skill_family("unknown", tmp_path / "skills")


def test_install_skill_family_rejects_incomplete_staging(tmp_path: Path) -> None:
    """A staging callback must produce every owned skill directory."""
    destination = tmp_path / "skills"

    def incomplete_staging(skill_names: tuple[str, ...], staging_root: Path) -> None:
        staging_root.mkdir()
        (staging_root / skill_names[0]).mkdir()

    with pytest.raises(InstallationError, match="Unable to stage skill family"):
        install_skill_family("okfkb", destination, stage_family=incomplete_staging)

    assert not destination.exists()


def test_install_skill_family_uses_valid_packaged_resource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A complete package resource is copied without consulting the source checkout."""
    packaged_root = tmp_path / "packaged"
    packaged_skill = packaged_root / "okf-schema"
    packaged_skill.mkdir(parents=True)
    (packaged_skill / "SKILL.md").write_text("packaged", encoding="utf-8")
    monkeypatch.setattr(installer, "files", lambda _: packaged_root)

    destination = tmp_path / "destination"
    install_skill_family("okf-schema", destination)

    assert (destination / "okf-schema" / "SKILL.md").read_text(encoding="utf-8") == "packaged"


def test_install_skill_family_rejects_non_directory_packaged_skill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A packaged family member must be represented by a directory resource."""
    monkeypatch.setattr(installer, "files", lambda _: tmp_path)

    with pytest.raises(InstallationError, match="Packaged skill is not a directory"):
        install_skill_family("okf-schema", tmp_path / "skills")


def test_install_skill_family_rejects_invalid_destination(tmp_path: Path) -> None:
    """An existing file cannot become an installation directory."""
    destination = tmp_path / "skills"
    destination.write_text("not a directory", encoding="utf-8")

    with pytest.raises(InstallationError, match="not a directory"):
        install_skill_family("okf-schema", destination)


def test_install_skill_family_rejects_symbolic_link_destination(tmp_path: Path) -> None:
    """The destination itself cannot be a symbolic link."""
    destination = tmp_path / "skills"
    target = tmp_path / "target"
    target.mkdir()
    destination.symlink_to(target, target_is_directory=True)

    with pytest.raises(InstallationError, match="Destination is a symbolic link"):
        install_skill_family("okf-schema", destination)


def test_install_skill_family_rechecks_destination_link_after_staging(tmp_path: Path) -> None:
    """A destination that becomes a symlink while staging is rejected before mutation."""
    destination = tmp_path / "skills"
    target = tmp_path / "target"
    target.mkdir()

    def stage_then_link(skill_names: tuple[str, ...], staging_root: Path) -> None:
        staging_root.mkdir()
        for skill_name in skill_names:
            (staging_root / skill_name).mkdir()
        destination.symlink_to(target, target_is_directory=True)

    with pytest.raises(InstallationError, match="Installation destination is a symbolic link"):
        install_skill_family("okf-schema", destination, stage_family=stage_then_link)

    assert destination.is_symlink()
    assert not (target / "okf-schema").exists()


def test_install_skill_family_reports_destination_creation_error(tmp_path: Path) -> None:
    """A parent file produces a clear destination-creation error."""
    parent = tmp_path / "parent-file"
    parent.write_text("not a directory", encoding="utf-8")

    with pytest.raises(InstallationError, match="Unable to create installation destination"):
        install_skill_family("okf-schema", parent / "skills")


def test_install_skill_family_rejects_owned_file(tmp_path: Path) -> None:
    """An owned file is rejected before any other owned path is replaced."""
    destination = tmp_path / "skills"
    destination.mkdir()
    (destination / "okfkb").write_text("not a directory", encoding="utf-8")

    with pytest.raises(InstallationError, match="Owned skill path.*okfkb"):
        install_skill_family("okfkb", destination)


def test_install_skill_family_reports_replacement_copy_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure preparing a replacement is reported without removing the old directory."""
    destination = tmp_path / "skills"
    install_skill_family("okf-schema", destination)

    def prepare_staging(skill_names: tuple[str, ...], staging_root: Path) -> None:
        staging_root.mkdir()
        for skill_name in skill_names:
            (staging_root / skill_name).mkdir()

    def fail_copy(source: Path, target: Path) -> None:
        target.mkdir()
        raise OSError("disk full")

    monkeypatch.setattr(installer.shutil, "copytree", fail_copy)

    with pytest.raises(InstallationError, match="Unable to prepare replacement"):
        install_skill_family("okf-schema", destination, stage_family=prepare_staging)

    assert (destination / "okf-schema" / "SKILL.md").is_file()


def test_install_skill_family_restores_directory_after_replacement_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed final rename restores the existing owned directory."""
    destination = tmp_path / "skills"
    install_skill_family("okf-schema", destination)
    original_skill = destination / "okf-schema"
    original_content = (original_skill / "SKILL.md").read_bytes()
    real_replace = installer.os.replace
    replace_calls = 0

    def fail_second_replace(
        source: str | os.PathLike[str],
        target: str | os.PathLike[str],
    ) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("rename failed")
        real_replace(source, target)

    monkeypatch.setattr(installer.os, "replace", fail_second_replace)
    with pytest.raises(InstallationError, match="Unable to replace skill"):
        install_skill_family("okf-schema", destination)

    assert (original_skill / "SKILL.md").read_bytes() == original_content


def test_install_skill_family_preserves_directory_when_backup_rename_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed backup rename leaves the original owned directory untouched."""
    destination = tmp_path / "skills"
    install_skill_family("okf-schema", destination)
    original_skill = destination / "okf-schema"
    original_content = (original_skill / "SKILL.md").read_bytes()

    def fail_backup_rename(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        raise OSError("rename failed")

    monkeypatch.setattr(installer.os, "replace", fail_backup_rename)
    with pytest.raises(InstallationError, match="Unable to replace skill"):
        install_skill_family("okf-schema", destination)

    assert (original_skill / "SKILL.md").read_bytes() == original_content
