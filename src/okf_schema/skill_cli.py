"""Shared Click wiring for packaged agent-skill installation commands."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import click

from okf_schema.skill_installer import (
    InstallationReport,
    install_skill_family,
    resolve_destination,
)

SkillInstaller = Callable[[Path], InstallationReport]


def _register_install_skills(
    group: click.Group,
    family: str,
    installer: SkillInstaller | None = None,
) -> None:
    """Register the common ``install-skills`` command on a Click group."""

    @group.command("install-skills")
    @click.argument("destination", required=False, type=click.Path())
    @click.option(
        "--agent-copilot",
        is_flag=True,
        help="Install globally under ~/.copilot/skills.",
    )
    @click.option(
        "--local-copilot",
        is_flag=True,
        help="Install locally under .github/skills.",
    )
    @click.option(
        "--local-agents",
        is_flag=True,
        help="Install locally under .agents/skills.",
    )
    def install_skills(
        destination: str | None,
        agent_copilot: bool,
        local_copilot: bool,
        local_agents: bool,
    ) -> None:
        """Install the packaged skill family owned by this command.

        .. versionadded:: 0.12.0

        An explicit ``DESTINATION`` takes precedence over selectors. Without
        either, skills are installed under ``~/.copilot/skills``.

        Examples:
            okf-schema install-skills --local-agents
            okf-schema install-skills ./vendor/agent-skills
        """
        try:
            target = resolve_destination(
                destination,
                agent_copilot=agent_copilot,
                local_copilot=local_copilot,
                local_agents=local_agents,
            )
            if installer is None:
                report = install_skill_family(family, target)
            else:
                report = installer(target)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo(f"Destination: {report.destination}")
        for installation in report.skills:
            click.echo(f"{installation.status}: {installation.skill}")
