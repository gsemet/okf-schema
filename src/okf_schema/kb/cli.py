"""Click command group for KB (knowledge-base) subcommands.

Provides the ``kb`` group and its ``init`` and ``install`` subcommands,
exposed as ``okf-schema kb`` and the standalone ``okfkb`` entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

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


@kb.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def install(path: str, force: bool) -> None:
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
