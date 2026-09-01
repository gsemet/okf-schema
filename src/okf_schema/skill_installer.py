"""Install complete agent-skill families from packaged resources.

The installer resolves global, local, and explicit destinations, stages every
skill in a family through :mod:`importlib.resources`, and replaces owned
directories without touching unrelated destination entries.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.machinery import PathFinder
from importlib.resources import as_file, files
from importlib.util import module_from_spec
from pathlib import Path
from types import MappingProxyType
from typing import Literal

# @implements_req SwRS-OKFSCHEMA-OKFKB-002

SkillStatus = Literal["installed", "updated"]
StageFamily = Callable[[tuple[str, ...], Path], None]

SKILL_FAMILIES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "okf-schema": ("okf-schema",),
        "okfkb": (
            "okfkb",
            "okfkb-distill",
            "okfkb-gardening",
            "okfkb-record-findings",
        ),
        "okfreq": ("okfreq", "okfreq-gardening"),
    }
)


def _absolute_path(path: Path) -> Path:
    """Normalize a path lexically without following symbolic links."""
    return Path(os.path.abspath(path))


class InstallationError(RuntimeError):
    """Raised when a skill family cannot be safely installed.

    .. versionadded:: 0.12.0
    """


@dataclass(frozen=True, slots=True)
class SkillInstallation:
    """Describe the result for one installed skill.

    .. versionadded:: 0.12.0
    """

    skill: str
    status: SkillStatus


@dataclass(frozen=True, slots=True)
class InstallationReport:
    """Report the destination and per-skill results of an installation.

    .. versionadded:: 0.12.0
    """

    destination: Path
    skills: tuple[SkillInstallation, ...]


def resolve_destination(
    destination: str | Path | None = None,
    *,
    agent_copilot: bool = False,
    local_copilot: bool = False,
    local_agents: bool = False,
    cwd: Path | None = None,
) -> Path:
    """Resolve an explicit path or supported installation selector.

    .. versionadded:: 0.12.0

    Explicit destinations take precedence over selectors. Relative paths and
    local selectors are resolved against *cwd*, or the process working
    directory when it is omitted.

    Args:
        destination:
            Optional explicit installation directory.
        agent_copilot:
            Select the global ``~/.copilot/skills`` directory.
        local_copilot:
            Select the current directory's ``.github/skills`` directory.
        local_agents:
            Select the current directory's ``.agents/skills`` directory.
        cwd:
            Working directory used for relative paths and local selectors.

    Returns:
        The normalized absolute destination path.

    Raises:
        InstallationError:
            If more than one selector is supplied without an explicit path.

    Examples:
        >>> destination = resolve_destination(local_copilot=True, cwd=Path.cwd())
        >>> destination.name
        'skills'
    """
    working_directory = _absolute_path((cwd if cwd is not None else Path.cwd()).expanduser())

    if destination is not None:
        explicit_path = Path(destination).expanduser()
        if not explicit_path.is_absolute():
            explicit_path = working_directory / explicit_path
        return _absolute_path(explicit_path)

    selectors = sum((agent_copilot, local_copilot, local_agents))
    if selectors > 1:
        raise InstallationError("Select only one skill installation destination")

    if local_copilot:
        selected_path = working_directory / ".github" / "skills"
    elif local_agents:
        selected_path = working_directory / ".agents" / "skills"
    else:
        selected_path = Path.home() / ".copilot" / "skills"

    return _absolute_path(selected_path.expanduser())


def install_skill_family(
    family: str,
    destination: str | Path,
    *,
    stage_family: StageFamily | None = None,
) -> InstallationReport:
    """Install all packaged skills owned by *family* into *destination*.

    .. versionadded:: 0.12.0

    The complete family is staged before the destination is created or any
    owned directory is replaced. Existing normal directories are replaced in
    the destination's parent directory, while unrelated entries are retained.

    Args:
        family:
            Command family key from :data:`SKILL_FAMILIES`.
        destination:
            Installation directory, which may not be a symbolic link.
        stage_family:
            Optional staging function for controlled resource preparation and
            failure testing. It receives the immutable skill names and an
            initially absent temporary directory to populate.

    Returns:
        Per-skill installation statuses and the normalized destination.

    Raises:
        InstallationError:
            If the family is unknown, resources cannot be staged, the
            destination is invalid, or an owned path is a symbolic link.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     report = install_skill_family("okf-schema", Path(directory))
        ...     report.skills[0].status
        'installed'
    """
    try:
        skill_names = SKILL_FAMILIES[family]
    except KeyError as exc:
        raise InstallationError(f"Unknown skill family: {family}") from exc

    destination_path = Path(destination).expanduser()
    if not destination_path.is_absolute():
        destination_path = Path.cwd() / destination_path
    if destination_path.is_symlink():
        raise InstallationError(f"Destination is a symbolic link: {destination_path}")
    destination_path = _absolute_path(destination_path)
    staging_function = stage_family or _stage_packaged_family

    with tempfile.TemporaryDirectory(prefix="okf-schema-skills-") as temporary_root:
        staging_root = Path(temporary_root) / "family"
        try:
            staging_function(skill_names, staging_root)
            _validate_staged_family(skill_names, staging_root)
        except Exception as exc:
            raise InstallationError(f"Unable to stage skill family '{family}': {exc}") from exc

        _validate_destination(destination_path, skill_names)
        try:
            destination_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise InstallationError(
                f"Unable to create installation destination '{destination_path}': {exc}"
            ) from exc

        installations = tuple(
            _replace_skill(
                staged_skill=staging_root / skill_name,
                destination_skill=destination_path / skill_name,
            )
            for skill_name in skill_names
        )

    return InstallationReport(destination=destination_path, skills=installations)


def _stage_packaged_family(skill_names: tuple[str, ...], staging_root: Path) -> None:
    """Copy a complete packaged family into a temporary staging directory."""
    staging_root.mkdir(parents=True)
    try:
        resource_root = files("okf_schema.skills")
    except ModuleNotFoundError:
        source_root = Path(__file__).resolve().parents[2]
        source_spec = PathFinder.find_spec("skills", [os.fspath(source_root)])
        if source_spec is None:
            raise ModuleNotFoundError("No module named 'skills'") from None
        resource_root = files(module_from_spec(source_spec))
    for skill_name in skill_names:
        resource = resource_root.joinpath(skill_name)
        staged_skill = staging_root / skill_name
        if resource.is_dir() and resource.joinpath("SKILL.md").is_file():
            with as_file(resource) as source:
                shutil.copytree(source, staged_skill)
            continue

        raise InstallationError(f"Packaged skill is not a directory: {skill_name}")


def _validate_staged_family(skill_names: tuple[str, ...], staging_root: Path) -> None:
    """Ensure staging produced one normal directory for every family member."""
    for skill_name in skill_names:
        staged_skill = staging_root / skill_name
        if staged_skill.is_symlink() or not staged_skill.is_dir():
            raise InstallationError(f"Staged skill is not a directory: {skill_name}")


def _validate_destination(destination: Path, skill_names: tuple[str, ...]) -> None:
    """Reject destination links and invalid owned paths before mutation."""
    if destination.is_symlink():
        raise InstallationError(f"Installation destination is a symbolic link: {destination}")
    if destination.exists() and not destination.is_dir():
        raise InstallationError(f"Installation destination is not a directory: {destination}")

    for skill_name in skill_names:
        destination_skill = destination / skill_name
        if destination_skill.is_symlink():
            raise InstallationError(f"Owned skill path is a symbolic link: {skill_name}")
        if destination_skill.exists() and not destination_skill.is_dir():
            raise InstallationError(f"Owned skill path is not a directory: {skill_name}")


def _replace_skill(staged_skill: Path, destination_skill: Path) -> SkillInstallation:
    """Copy one staged skill into a same-parent replacement path."""
    status: SkillStatus = "updated" if destination_skill.exists() else "installed"
    candidate = Path(
        tempfile.mkdtemp(prefix=f".{destination_skill.name}-", dir=destination_skill.parent)
    )
    shutil.rmtree(candidate)

    try:
        shutil.copytree(staged_skill, candidate)
    except OSError as exc:
        if candidate.exists():
            shutil.rmtree(candidate)
        raise InstallationError(
            f"Unable to prepare replacement for skill '{destination_skill.name}': {exc}"
        ) from exc

    backup: Path | None = None
    destination_moved = False
    try:
        if status == "updated":
            backup = Path(
                tempfile.mkdtemp(
                    prefix=f".{destination_skill.name}-backup-",
                    dir=destination_skill.parent,
                )
            )
            shutil.rmtree(backup)
            os.replace(destination_skill, backup)
            destination_moved = True
        os.replace(candidate, destination_skill)
    except OSError as exc:
        if destination_moved and (destination_skill.exists() or destination_skill.is_symlink()):
            _remove_directory(destination_skill)
        if backup is not None and backup.exists():
            os.replace(backup, destination_skill)
        if candidate.exists():
            shutil.rmtree(candidate)
        raise InstallationError(
            f"Unable to replace skill '{destination_skill.name}': {exc}"
        ) from exc

    if backup is not None and backup.exists():
        shutil.rmtree(backup)

    return SkillInstallation(skill=destination_skill.name, status=status)


def _remove_directory(path: Path) -> None:
    """Remove a normal temporary or owned directory without following links."""
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
