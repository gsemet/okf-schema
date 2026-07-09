"""Click command group for KB (knowledge-base) subcommands.

Provides the ``kb`` group and its ``init``, ``install-skills``,
``new-finding``, and ``update`` subcommands, exposed as
``okf-schema kb`` and the standalone ``okfkb`` entry point.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from okf_schema.api import update_bundle, validate_bundle
from okf_schema.kb import navigate
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


@kb.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--check", is_flag=True, help="Check if files would change; do not modify.")
@click.option("--diff", is_flag=True, help="Show unified diff without modifying files.")
@click.option(
    "--links/--no-links",
    is_flag=True,
    default=True,
    help="Update links and backlinks frontmatter fields from markdown body.",
)
def update(
    path: str,
    check: bool,
    diff: bool,
    links: bool,
) -> None:
    """Regenerate indexes and lint frontmatter in a knowledge base.

    This is equivalent to running ``okf-schema index`` followed by
    ``okf-schema lint`` — the recommended workflow after editing
    concepts in a knowledge base.
    """
    target = Path(path)
    try:
        result = update_bundle(target, check=check, diff=diff, links=links)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    # Report superseded-link rewrites
    if result.superseded_rewrites:
        click.echo(f"Superseded links rewritten: {len(result.superseded_rewrites)}")
        for rw in result.superseded_rewrites:
            click.echo(f"  {rw.source}: {rw.old_target} → {rw.new_target}")
    if result.deferred_rewrites:
        click.echo(
            f"Superseded links deferred (needs manual review): {len(result.deferred_rewrites)}"
        )
        for dr in result.deferred_rewrites:
            click.echo(f"  {dr.superseded_doc}: {dr.reason}", err=True)

    # Report index updates
    updated = sum(1 for u in result.index_updates if u.action == "updated")
    created = sum(1 for u in result.index_updates if u.action == "created")
    unchanged = sum(1 for u in result.index_updates if u.action == "unchanged")
    skipped = sum(1 for u in result.index_updates if u.action == "skipped")
    click.echo(
        f"Index: {updated} updated, {created} created, {unchanged} unchanged, {skipped} skipped"
    )

    # Report lint results
    changed = [r for r in result.lint_results if r.changed]

    if diff:
        for r in changed:
            if r.diff:
                click.echo(r.diff)
        return

    if check:
        if changed:
            for r in changed:
                click.echo(f"Would lint: {r.path}")
            sys.exit(1)
        click.echo("All files are properly linted.")
        return

    if changed:
        for r in changed:
            click.echo(f"Linted: {r.path}")
        click.echo(f"Linted {len(changed)} file(s).")
    else:
        click.echo("All files are already linted.")


@kb.command()
@click.argument("path", default=".", type=click.Path())
def validate(path: str) -> None:
    """Validate a knowledge base with strict mode (warnings as errors).

    This is equivalent to running ``okf-schema validate --strict``.
    """
    target = Path(path)
    try:
        report = validate_bundle(target)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if report.is_conformant and not report.warnings:
        click.echo("Bundle is conformant (0 errors, 0 warnings).")
        return

    by_file: dict[str, dict[str, list[str]]] = {}
    for finding in report.errors:
        path_str = str(finding.path) if finding.path else "<bundle>"
        by_file.setdefault(path_str, {"errors": [], "warnings": []})
        by_file[path_str]["errors"].append(f"[{finding.code}] {finding.message}")
    for finding in report.warnings:
        path_str = str(finding.path) if finding.path else "<bundle>"
        by_file.setdefault(path_str, {"errors": [], "warnings": []})
        by_file[path_str]["warnings"].append(f"[{finding.code}] {finding.message}")

    for path_str in sorted(by_file):
        click.echo(f"\n{path_str}")
        for msg in by_file[path_str]["errors"]:
            click.echo(f"  ERROR   {msg}", err=True)
        for msg in by_file[path_str]["warnings"]:
            click.echo(f"  WARNING {msg}", err=True)

    error_count = len(report.errors)
    warning_count = len(report.warnings)
    if error_count:
        click.echo(
            f"\nValidation failed: {error_count} error(s), {warning_count} warning(s).",
            err=True,
        )
        sys.exit(1)
    elif warning_count:
        click.echo(
            f"\nValidation failed: {error_count} error(s), "
            f"{warning_count} warning(s) (strict mode).",
            err=True,
        )
        sys.exit(1)


def _node_to_dict(node: navigate.KbNode) -> dict:
    """Serialise a :class:`KbNode` to a JSON-friendly dict."""
    return {
        "path": node.path,
        "tier": node.tier,
        "type": node.type,
        "title": node.title,
        "confidence": node.confidence,
        "status": node.status,
        "tags": node.tags,
        "timestamp": node.timestamp,
    }


def _echo_node_table(nodes: list[navigate.KbNode]) -> None:
    """Print a compact table of nodes (tier, confidence, status, title)."""
    if not nodes:
        click.echo("No matching nodes.")
        return
    for node in nodes:
        conf = node.confidence or "-"
        status = node.status or "-"
        click.echo(f"{node.tier:<11} {conf:<9} {status:<12} {node.title}")
        click.echo(f"            {node.path}")


@kb.command()
@click.argument("text")
@click.argument("path", default=".", type=click.Path())
@click.option(
    "--tier",
    "tiers",
    multiple=True,
    help="Restrict search to a tier (repeatable), e.g. --tier findings.",
)
@click.option("--limit", default=10, show_default=True, help="Maximum results.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "paths"]),
    default="table",
    show_default=True,
    help="Output format.",
)
def search(
    text: str,
    path: str,
    tiers: tuple[str, ...],
    limit: int,
    output_format: str,
) -> None:
    """Ranked keyword search across the KB bundle at PATH.

    Matches TEXT against titles, tags, type, context, and body.
    """
    target = Path(path)
    try:
        hits = navigate.search(target, text, tiers=list(tiers) or None, limit=limit)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(
            json.dumps(
                [{**_node_to_dict(h.node), "score": h.score} for h in hits],
                indent=2,
            )
        )
        return
    if output_format == "paths":
        for hit in hits:
            click.echo(hit.node.path)
        return
    _echo_node_table([h.node for h in hits])


@kb.command()
@click.argument("node_id")
@click.argument("path", default=".", type=click.Path())
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json", "frontmatter"]),
    default="md",
    show_default=True,
    help="What to print.",
)
def get(node_id: str, path: str, output_format: str) -> None:
    """Fetch a single node by id or bundle-relative path from PATH."""
    target = Path(path)
    try:
        node = navigate.get(target, node_id)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps({**_node_to_dict(node), "body": node.body}, indent=2))
        return
    if output_format == "frontmatter":
        click.echo(json.dumps(node.frontmatter, indent=2, default=str))
        return
    click.echo(f"# {node.title}  ({node.path})\n")
    click.echo(node.body.strip())


@kb.command()
@click.argument("tier")
@click.argument("path", default=".", type=click.Path())
@click.option("--status", default=None, help="Only include nodes with this status.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "frontmatter", "titles"]),
    default="md",
    show_default=True,
    help="Output format.",
)
def read(tier: str, path: str, status: str | None, output_format: str) -> None:
    """Read a whole stable TIER at once from the KB bundle at PATH."""
    target = Path(path)
    try:
        nodes = navigate.read_tier(target, tier, status=status)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not nodes:
        click.echo("No matching nodes.")
        return

    if output_format == "titles":
        for node in nodes:
            click.echo(f"{node.path}\t{node.title}")
        return
    if output_format == "frontmatter":
        click.echo(json.dumps([_node_to_dict(n) for n in nodes], indent=2, default=str))
        return
    for node in nodes:
        click.echo(f"# {node.title}  ({node.path})\n")
        click.echo(node.body.strip())
        click.echo("\n---\n")


@kb.command()
@click.argument("expr")
@click.argument("path", default=".", type=click.Path())
@click.option("--limit", default=None, type=int, help="Maximum results.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "paths"]),
    default="table",
    show_default=True,
    help="Output format.",
)
def query(expr: str, path: str, limit: int | None, output_format: str) -> None:
    """Run a structured query over the KB bundle at PATH.

    EXPR is either a filter expression (e.g.
    "type:finding confidence:>=high tag:pll") or an arrow-traversal path
    (e.g. "finding[tag=pll] -> concept -> principle").
    """
    target = Path(path)
    try:
        nodes = navigate.query(target, expr, limit=limit)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps([_node_to_dict(n) for n in nodes], indent=2))
        return
    if output_format == "paths":
        for node in nodes:
            click.echo(node.path)
        return
    _echo_node_table(nodes)
