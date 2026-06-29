"""Click CLI entry point for okf-schema."""

from __future__ import annotations

import datetime
from pathlib import Path

import click

from okf_schema import __version__
from okf_schema._internal.models import BundleStats
from okf_schema._internal.yaml import make_yaml
from okf_schema.api import (
    index_bundle,
    lint_bundle,
    list_bundle,
    show_bundle,
    stats_bundle,
    validate_bundle,
)


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="okf-schema")
@click.option("--verbose", "-v", count=True, help="Increase verbosity (up to 3).")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output.")
@click.pass_context
def cli(ctx: click.Context, verbose: int, quiet: bool) -> None:
    """CLI tool and Python library for OKF bundle management."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _echo(ctx: click.Context, message: str) -> None:
    """Echo *message* unless --quiet is set."""
    if not ctx.obj.get("quiet"):
        click.echo(message)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("name")
@click.pass_context
def init(ctx: click.Context, name: str) -> None:
    """Create a new OKF bundle directory structure."""
    path = Path(name)
    if path.exists():
        click.echo(f"Error: '{name}' already exists.", err=True)
        ctx.exit(1)

    bundle_dir = path / "bundle"
    schema_dir = bundle_dir / "_schema"
    bundle_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)

    index_path = bundle_dir / "index.md"
    index_path.write_text('---\nokf_version: "0.1"\n---\n\n', encoding="utf-8")

    log_path = bundle_dir / "log.md"
    today = datetime.date.today().isoformat()
    log_path.write_text(f"## {today}\n\n", encoding="utf-8")

    _echo(ctx, f"Created OKF bundle '{name}'.")


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--path", "root_path", required=True, help="Root directory for the new concept.")
@click.option("--name", required=True, help="Relative path of the concept (without .md).")
@click.option("--type", "concept_type", default="concept", help="Concept type.")
@click.option("--title", "concept_title", default=None, help="Concept title.")
@click.pass_context
def new(
    ctx: click.Context,
    root_path: str,
    name: str,
    concept_type: str,
    concept_title: str | None,
) -> None:
    """Create a new OKF concept file with frontmatter template."""
    root = Path(root_path)
    file_path = root / f"{name}.md"

    if file_path.exists():
        click.echo(f"Error: '{file_path}' already exists.", err=True)
        ctx.exit(1)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    title = concept_title if concept_title is not None else Path(name).name

    y = make_yaml()
    data = {
        "type": concept_type,
        "title": title,
        "description": "",
        "tags": [],
    }
    import io

    buf = io.StringIO()
    y.dump(data, buf)
    fm = buf.getvalue().rstrip("\n")
    content = f"---\n{fm}\n---\n\n"

    file_path.write_text(content, encoding="utf-8")
    _echo(ctx, f"Created concept '{file_path}'.")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.option(
    "--schema-db",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Override the built-in _schema directory inside the bundle.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors (exit 1 if any warning is present).",
)
@click.pass_context
def validate(
    ctx: click.Context,
    bundle_path: str,
    schema_db: str | None,
    strict: bool,
) -> None:
    """Validate an OKF bundle."""
    try:
        report = validate_bundle(bundle_path, schema_db=schema_db)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)

    if report.is_conformant and not report.warnings:
        _echo(ctx, "Bundle is conformant (0 errors, 0 warnings).")
        ctx.exit(0)

    # Group findings by file
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
        _echo(ctx, f"\n{path_str}")
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
        ctx.exit(1)
    elif strict and warning_count:
        msg = (
            f"\nValidation failed: {error_count} error(s), "
            f"{warning_count} warning(s) (strict mode)."
        )
        click.echo(msg, err=True)
        ctx.exit(1)
    else:
        _echo(ctx, f"\nBundle is conformant ({warning_count} warning(s)).")
        ctx.exit(0)


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.option("--check", is_flag=True, help="Check if files would change; do not modify.")
@click.option("--diff", is_flag=True, help="Show unified diff without modifying files.")
@click.pass_context
def lint(
    ctx: click.Context,
    bundle_path: str,
    check: bool,
    diff: bool,
) -> None:
    """Lint frontmatter: flatten nested lists and convert block-style to inline.

    Normalizes YAML frontmatter by flattening nested lists and converting
    block-style (multi-line) lists to inline notation.  This keeps
    frontmatter compact, which is important for coding agents that load
    only the first *n* lines of a file.
    """
    try:
        results = lint_bundle(bundle_path, check=check, diff=diff)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)

    changed = [r for r in results if r.changed]

    if diff:
        for r in changed:
            if r.diff:
                click.echo(r.diff)
        ctx.exit(0)

    if check:
        if changed:
            for r in changed:
                _echo(ctx, f"Would lint: {r.path}")
            ctx.exit(1)
        _echo(ctx, "All files are properly linted.")
        ctx.exit(0)

    # In-place mode
    if changed:
        for r in changed:
            _echo(ctx, f"Linted: {r.path}")
        _echo(ctx, f"Linted {len(changed)} file(s).")
    else:
        _echo(ctx, "All files are already linted.")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@cli.command(name="list")
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.pass_context
def list_cmd(ctx: click.Context, bundle_path: str) -> None:
    """List all concepts in an OKF bundle."""
    try:
        concepts = list_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    for concept in concepts:
        click.echo(f"{concept.path}  {concept.type}  {concept.title}")


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.argument("concept_path")
@click.pass_context
def show(ctx: click.Context, bundle_path: str, concept_path: str) -> None:
    """Show a single concept's frontmatter and body."""
    try:
        detail = show_bundle(bundle_path, concept_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    import io

    from okf_schema._internal.yaml import make_yaml

    y = make_yaml()
    buf = io.StringIO()
    y.dump(detail.frontmatter, buf)
    fm_yaml = buf.getvalue().rstrip("\n")
    click.echo(f"---\n{fm_yaml}\n---")
    if detail.body.strip():
        click.echo(detail.body)


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.pass_context
def index(ctx: click.Context, bundle_path: str) -> None:
    """Regenerate all index.md files in an OKF bundle."""
    try:
        updates = index_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    updated = sum(1 for u in updates if u.action == "updated")
    created = sum(1 for u in updates if u.action == "created")
    unchanged = sum(1 for u in updates if u.action == "unchanged")
    skipped = sum(1 for u in updates if u.action == "skipped")

    _echo(ctx, f"{updated} updated, {created} created, {unchanged} unchanged, {skipped} skipped")


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


def _health_score(s: BundleStats) -> tuple[int, list[str]]:
    """Return a health score (0-100) and a list of issue strings."""
    score = 100
    issues: list[str] = []

    if s.broken_links:
        penalty = min(10 * s.broken_links, 30)
        score -= penalty
        issues.append(f"{s.broken_links} broken link{'s' if s.broken_links > 1 else ''}")

    if s.files_without_frontmatter:
        penalty = min(10 * s.files_without_frontmatter, 30)
        score -= penalty
        plural = "s" if s.files_without_frontmatter > 1 else ""
        issues.append(f"{s.files_without_frontmatter} file{plural} without frontmatter")

    return max(score, 0), issues


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.pass_context
def stats(ctx: click.Context, bundle_path: str) -> None:
    """Show compact statistics for an OKF bundle."""
    try:
        s = stats_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    # Summary line
    type_count = len(s.types_distribution)
    summary = (
        f"{s.total_files} file{'s' if s.total_files != 1 else ''} · "
        f"{s.total_concepts} concept{'s' if s.total_concepts != 1 else ''} · "
        f"{type_count} type{'s' if type_count != 1 else ''} · "
        f"{s.total_size:,} bytes"
    )
    click.echo(summary)

    # Frontmatter / links line (only if there is anything to report)
    if s.files_without_frontmatter or s.total_links:
        parts: list[str] = []
        if s.files_without_frontmatter:
            parts.append(f"{s.files_without_frontmatter} without frontmatter")
        if s.total_links:
            link_summary = f"{s.total_links} link{'s' if s.total_links != 1 else ''}"
            if s.broken_links:
                link_summary += f" ({s.broken_links} broken)"
            parts.append(link_summary)
        click.echo("  " + " · ".join(parts))

    # Types (skip if empty or only one type)
    if len(s.types_distribution) > 1:
        sorted_types = sorted(s.types_distribution.items(), key=lambda x: (-x[1], x[0]))
        type_parts = [f"{name} {count}" for name, count in sorted_types]
        click.echo("  Types: " + "  ·  ".join(type_parts))

    # Tags (ranked by frequency, skip if empty)
    if s.tags_distribution:
        sorted_tags = sorted(s.tags_distribution.items(), key=lambda x: (-x[1], x[0]))
        tag_parts = [f"{tag} {count}" for tag, count in sorted_tags]
        click.echo("  Tags:  " + "  ·  ".join(tag_parts))

    # Health score
    score, issues = _health_score(s)
    if issues:
        click.echo(f"  Health: {score}% — {', '.join(issues)}")
    else:
        click.echo(f"  Health: {score}% — all clear")
