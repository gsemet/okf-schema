"""Compatibility facade for installing the complete ``okfkb`` skill family.

The reusable implementation lives in :mod:`okf_schema.skill_installer`.
Command entry points use that module directly as they migrate to the shared
destination contract.
"""

from __future__ import annotations

from pathlib import Path

from okf_schema.skill_installer import InstallationReport, install_skill_family

# @implements_req SwRS-OKFSCHEMA-OKFKB-002


def install_kb(target: Path) -> InstallationReport:
    """Install the packaged ``okfkb`` skill family into *target*.

    .. versionchanged:: 0.12.0
        The legacy guideline, project-file mutation, inference, skip, and
        force behavior is no longer part of this installer.

    Args:
        target:
            Destination directory containing the installed skills.

    Returns:
        Per-skill installation results from the shared installer.
    """
    return install_skill_family("okfkb", target)
