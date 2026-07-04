"""Click command group for KB (knowledge-base) subcommands.

Provides the ``kb`` group and its ``init``, ``install-skills``, and
``new-finding`` subcommands, exposed as ``okf-schema kb`` and the standalone
``okfkb`` entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from okf_schema.kb.finding import new_finding as _new_finding
from okf_schema.kb.install import install_kb
from okf_schema.kb.scaffold import scaffold_kb


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def kb() -> None:
    """Knowledge base management commands."""


@kb.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def init(path: str, force: bool) -> None:
    """Scaffold a new knowledge-base bundle at PATH.

    PATH defaults to the current directory when omitted.
    """
    target = Path(path)
    try:
        scaffold_kb(target, force=force)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Created knowledge base at {target}.")


@kb.command("install-skills")
@click.argument("path", default=".", type=click.Path())
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def install_skills(path: str, force: bool) -> None:
    """Install KB skills and guidelines into a project at PATH.

    PATH defaults to the current directory when omitted.
    """
    target = Path(path)
    try:
        install_kb(target, force=force)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Installed KB tooling at {target}.")


@kb.command("new-finding")
@click.argument("path", default=".", type=click.Path())
@click.option("--title", "-t", required=True, help="Short title for the finding.")
@click.option(
    "--description",
    "-d",
    default=None,
    help="One-line summary (defaults to title when omitted).",
)
@click.option(
    "--confidence",
    "-c",
    default="low",
    type=click.Choice(["low", "medium", "high", "confirmed"]),
    show_default=True,
    help="Confidence level at the time of recording.",
)
@click.option(
    "--context",
    default="No additional context recorded.",
    show_default=True,
    help="Background and assumptions at the time of recording.",
)
@click.option(
    "--tags",
    default="",
    help="Comma-separated keyword tags.",
)
def new_finding(
    path: str,
    title: str,
    description: str | None,
    confidence: str,
    context: str,
    tags: str,
) -> None:
    """Record a new Finding in the KB bundle at PATH.

    PATH defaults to the current directory when omitted.
    Creates findings/YYYY.MM.DD-HH.MM-<slug>.md with valid OKF frontmatter.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    target = Path(path)
    try:
        filepath = _new_finding(
            target,
            title,
            description=description,
            confidence=confidence,
            context=context,
            tags=tag_list,
        )
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Created {filepath}")
