"""Install KB skills and guidelines into a target project.

Copies the bundled ``record-finding`` and ``consolidate-knowledge-base`` skills
together with ``knowledge-base.guidelines.md`` into the target project's agent
configuration directory, then creates or patches ``AGENTS.md`` with a reference
to the installed guideline.
"""

from __future__ import annotations

import shutil
from importlib.resources import as_file, files
from pathlib import Path

import click

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GUIDELINE_NAME = "knowledge-base.guidelines.md"
_SKILL_NAMES: tuple[str, ...] = (
    "consolidate-knowledge-base",
    "record-finding",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_base(target: Path) -> tuple[Path, bool]:
    """Detect the agent configuration base directory inside *target*.

    Prefers ``.agents/``; falls back to ``.github/``.  Creates ``.agents/``
    when neither directory exists.

    Args:
        target: Root directory of the target project.

    Returns:
        A ``(base, created)`` tuple where *base* is the resolved base
        directory and *created* is ``True`` when a new directory was created.
    """
    agents_dir = target / ".agents"
    github_dir = target / ".github"

    if agents_dir.exists():
        return agents_dir, False
    if github_dir.exists():
        return github_dir, False

    agents_dir.mkdir(parents=True)
    return agents_dir, True


def _copy_guideline(
    base: Path,
    force: bool,
    installed: list[str],
    skipped: list[str],
) -> None:
    """Copy the bundled guideline file into *base*/guidelines/.

    Args:
        base: Agent configuration base directory (``.agents/`` or
            ``.github/``).
        force: When ``True``, overwrite existing files.
        installed: Accumulator list for installed file paths (mutated).
        skipped: Accumulator list for skipped file paths (mutated).
    """
    dst_dir = base / "guidelines"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / _GUIDELINE_NAME

    if dst.exists() and not force:
        click.echo(f"  warning  skipped (already exists): {dst.relative_to(base.parent)}")
        skipped.append(str(dst.relative_to(base.parent)))
        return

    guideline_pkg = files("okf_schema.data.kb").joinpath("guidelines").joinpath(_GUIDELINE_NAME)
    with as_file(guideline_pkg) as src:
        shutil.copy2(src, dst)

    installed.append(str(dst.relative_to(base.parent)))


def _copy_skills(
    base: Path,
    force: bool,
    installed: list[str],
    skipped: list[str],
) -> None:
    """Copy all bundled skill directories into *base*/skills/.

    Args:
        base: Agent configuration base directory (``.agents/`` or
            ``.github/``).
        force: When ``True``, overwrite existing skill directories.
        installed: Accumulator list for installed paths (mutated).
        skipped: Accumulator list for skipped paths (mutated).
    """
    dst_skills_dir = base / "skills"
    dst_skills_dir.mkdir(parents=True, exist_ok=True)

    skills_pkg = files("okf_schema.data.kb").joinpath("skills")
    for skill_name in _SKILL_NAMES:
        dst = dst_skills_dir / skill_name

        if dst.exists() and not force:
            click.echo(f"  warning  skipped (already exists): {dst.relative_to(base.parent)}")
            skipped.append(str(dst.relative_to(base.parent)))
            continue

        if dst.exists() and force:
            shutil.rmtree(dst)

        skill_src = skills_pkg.joinpath(skill_name)
        with as_file(skill_src) as src_dir:
            shutil.copytree(src_dir, dst)

        installed.append(str(dst.relative_to(base.parent)))


def _patch_agents_md(target: Path, base: Path) -> None:
    """Create or patch ``AGENTS.md`` with the guideline reference.

    The reference line is appended only once (idempotent).  If ``AGENTS.md``
    does not exist a minimal file is created with a project stub heading and
    the reference line.

    Args:
        target: Root directory of the target project.
        base: Agent configuration base directory — used to build the correct
            relative path for the reference line.
    """
    # Build a relative path from the project root to the installed guideline
    rel_base = base.relative_to(target)
    guideline_rel = f"{rel_base}/guidelines/{_GUIDELINE_NAME}"
    ref_line = f"- [Knowledge Base Guidelines]({guideline_rel})"

    agents_md = target / "AGENTS.md"
    if agents_md.exists():
        content = agents_md.read_text(encoding="utf-8")
        if ref_line in content:
            return  # idempotent — already present
        agents_md.write_text(content.rstrip("\n") + "\n" + ref_line + "\n", encoding="utf-8")
    else:
        agents_md.write_text(
            "# AGENTS.md\n\n"
            "This project uses the OKF Knowledge Base tooling.\n\n"
            "## Guidelines\n\n"
            f"{ref_line}\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def install_kb(target: Path, force: bool = False) -> None:
    """Install KB skills and guidelines into the *target* project.

    Detects whether *target*/.agents/ or *target*/.github/ exists and selects
    the appropriate base directory (`.agents/` is preferred).  Creates
    ``.agents/`` if neither directory exists.  Copies the bundled
    ``record-finding`` and ``consolidate-knowledge-base`` skills into
    ``<base>/skills/`` and ``knowledge-base.guidelines.md`` into
    ``<base>/guidelines/``.  Creates or patches ``AGENTS.md`` at the project
    root with a reference to the installed guideline.

    Args:
        target: Root directory of the target project.  Must exist.
        force: When ``True``, overwrite existing files; otherwise skip them
            with a warning.

    Raises:
        RuntimeError: If *target* does not exist.
    """
    if not target.exists():
        raise RuntimeError(
            f"Target directory does not exist: '{target}'.\n"
            "Create the directory first or supply a valid path."
        )

    base, _created = _detect_base(target)

    installed: list[str] = []
    skipped: list[str] = []

    _copy_guideline(base, force, installed, skipped)
    _copy_skills(base, force, installed, skipped)
    _patch_agents_md(target, base)

    # --- summary -----------------------------------------------------------
    click.echo(f"Installed KB tooling into '{target}':")
    for path in installed:
        click.echo(f"  installed  {path}")
    for _path in skipped:
        pass  # warnings already printed inline
    click.echo(f"  {len(installed)} installed, {len(skipped)} skipped")
