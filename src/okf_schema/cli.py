"""Command-line interface for creating and maintaining OKF bundles.

The :func:`cli` Click group exposes bundle creation, validation, linting,
indexing, inspection, and knowledge-base commands. OKF means Open Knowledge
Format; commands accept filesystem paths and report failures through Click
exit codes.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Any

import click

from okf_schema import __version__
from okf_schema._internal.models import BundleStats
from okf_schema._internal.yaml import make_yaml
from okf_schema.api import (
    backlinks_bundle,
    index_bundle,
    lint_bundle,
    list_bundle,
    show_bundle,
    stats_bundle,
    validate_bundle,
    validate_markdown_files,
)
from okf_schema.okfkb.cli import kb
from okf_schema.okfkb.patterns import INIT_PATTERNS, list_patterns


class _HelpCommand(click.Command):
    """Click command with the short and long help options enabled."""

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        context_settings = kwargs.setdefault("context_settings", {})
        context_settings.setdefault("help_option_names", ["-h", "--help"])
        super().__init__(*args, **kwargs)


class _HelpGroup(click.Group):
    """Click group whose commands consistently accept ``-h`` and ``--help``."""

    command_class = _HelpCommand


# Force UTF-8 output so Unicode characters (e.g. backlink arrows)
# print correctly on Windows consoles that default to cp1252.
_stdout: Any = sys.stdout
if hasattr(_stdout, "reconfigure"):
    _stdout.reconfigure(encoding="utf-8")
_stderr: Any = sys.stderr
if hasattr(_stderr, "reconfigure"):
    _stderr.reconfigure(encoding="utf-8")


@click.group(
    cls=_HelpGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="okf-schema")
@click.option("--verbose", "-v", count=True, help="Increase verbosity (up to 3).")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output.")
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    quiet: bool,
) -> None:
    """Manage Open Knowledge Format bundles from the command line.

    Args:
        ctx:
            Active Click command context.
        verbose:
            Number of requested verbosity increases.
        quiet:
            Whether to suppress non-error output.

    Examples:
        okf-schema --help
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-001
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
@click.option("--pattern", default=None, help="Init pattern to use (e.g. 'kb').")
@click.pass_context
def init(
    ctx: click.Context,
    name: str,
    pattern: str | None,
) -> None:
    """Create a new OKF bundle directory structure.

    Args:
        ctx:
            Active Click command context.
        name:
            Destination directory for the new bundle.
        pattern:
            Optional registered initialization pattern.

    Examples:
        okf-schema init notes
        okf-schema init knowledge --pattern kb
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-002
    if pattern is not None:
        if pattern not in INIT_PATTERNS:
            available = ", ".join(list_patterns()) or "none"
            click.echo(
                f"Error: Unknown pattern '{pattern}'. Available patterns: {available}.",
                err=True,
            )
            ctx.exit(1)
            return
        INIT_PATTERNS[pattern](Path(name), False)
        _echo(ctx, f"Created OKF bundle '{name}' using pattern '{pattern}'.")
        return

    path = Path(name)
    if path.exists():
        click.echo(f"Error: '{name}' already exists.", err=True)
        ctx.exit(1)

    bundle_dir = path / "bundle"
    schema_dir = bundle_dir / "_schema"
    bundle_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)

    index_path = bundle_dir / "index.md"
    index_path.write_text('---\nokf_version: "0.2"\n---\n\n', encoding="utf-8")

    log_path = bundle_dir / "log.md"
    today = datetime.date.today().isoformat()
    log_path.write_text(f"## {today}\n\n", encoding="utf-8")

    base_schema_path = schema_dir / "_base.schema.yaml"
    base_schema_path.write_text(
        '$schema: "https://json-schema.org/draft/2020-12/schema"\n'
        "type: object\n"
        "properties:\n"
        "  type:\n"
        "    type: string\n"
        "    description: >-\n"
        "      A short string identifying the kind of concept.\n"
        "      Consumers use this for routing, filtering, and presentation.\n"
        "  title:\n"
        "    type: string\n"
        "    description: >-\n"
        "      Human-readable display name. If omitted, consumers MAY\n"
        "      derive a title from the filename.\n"
        "  description:\n"
        "    type: string\n"
        "    description: >-\n"
        "      A single sentence summarizing the concept. Used by\n"
        "      index.md generators, search snippets, and previews.\n"
        "  resource:\n"
        "    type: string\n"
        "    description: >-\n"
        "      A URI that uniquely identifies the underlying asset the\n"
        "      concept describes. Absent for concepts that describe\n"
        "      abstract ideas rather than physical resources.\n"
        "  tags:\n"
        "    type: array\n"
        "    items:\n"
        "      type: string\n"
        "    description: >-\n"
        "      A YAML list of short strings for cross-cutting\n"
        "      categorization.\n"
        "  timestamp:\n"
        "    type: string\n"
        "    format: date-time\n"
        "    description: >-\n"
        "      ISO 8601 datetime of last meaningful change.\n"
        "  links:\n"
        "    type: array\n"
        "    items:\n"
        "      type: string\n"
        "    description: >-\n"
        "      Bundle-relative paths of concepts this file links to.\n"
        "      Automatically maintained by ``okf-schema lint --links``.\n"
        "  backlinks:\n"
        "    type: array\n"
        "    items:\n"
        "      type: string\n"
        "    description: >-\n"
        "      Bundle-relative paths of concepts that link to this file.\n"
        "      Automatically maintained by ``okf-schema lint --links``.\n"
        "required:\n"
        "  - type\n"
        "additionalProperties: true\n",
        encoding="utf-8",
    )

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
    """Create a new OKF concept file with a frontmatter template.

    Args:
        ctx:
            Active Click command context.
        root_path:
            Root directory in which to create the concept.
        name:
            Concept path relative to ``root_path``, without the ``.md`` suffix.
        concept_type:
            Frontmatter type assigned to the concept.
        concept_title:
            Optional display title; defaults to the final path component.

    Examples:
        okf-schema new --path bundle/concepts --name clock --title "Clock"
    """
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
    """Validate an OKF bundle.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to validate.
        schema_db:
            Optional directory containing schemas that override the bundle schemas.
        strict:
            Whether warnings should cause validation to fail.

    Examples:
        okf-schema validate --path bundle
        okf-schema validate --path bundle --strict
    """
    try:
        report = validate_bundle(bundle_path, schema_db=schema_db)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
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
# validate-md
# ---------------------------------------------------------------------------


@cli.command("validate-md")
@click.option(
    "--input",
    "input_patterns",
    multiple=True,
    required=True,
    help="Glob pattern(s) for markdown files to validate (e.g., '**/*.md'). "
    "Supports ** for recursive matching. Can be specified multiple times.",
)
@click.option(
    "--schemas-dir",
    required=True,
    help="Directory containing JSON/YAML schema files (named <type>.schema.{json|json5|yaml|yml}).",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors (exit 1 if any warning is present).",
)
@click.pass_context
def validate_md(
    ctx: click.Context,
    input_patterns: tuple[str, ...],
    schemas_dir: str,
    strict: bool,
) -> None:
    """Validate standalone markdown files against JSON schemas.

    Validates one or more markdown files with frontmatter against provided schemas.
    This is useful for validating markdown outside of a full OKF bundle.

    Args:
        ctx:
            Active Click command context.
        input_patterns:
            Glob patterns selecting Markdown files to validate.
        schemas_dir:
            Directory containing the JSON or YAML schemas.
        strict:
            Whether warnings should cause validation to fail.

    Examples:
        okf-schema validate-md --input 'notes/**/*.md' --schemas-dir ./schemas
        okf-schema validate-md --input '*.md' --input 'docs/**/*.md' --schemas-dir ./schemas
    """
    try:
        report = validate_markdown_files(list(input_patterns), schemas_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)

    if report.is_conformant and not report.warnings:
        _echo(ctx, "All files validated successfully (0 errors, 0 warnings).")
        ctx.exit(0)

    # Group findings by file
    by_file: dict[str, dict[str, list[str]]] = {}
    for finding in report.errors:
        path_str = str(finding.path) if finding.path else "<unknown>"
        by_file.setdefault(path_str, {"errors": [], "warnings": []})
        by_file[path_str]["errors"].append(f"[{finding.code}] {finding.message}")
    for finding in report.warnings:
        path_str = str(finding.path) if finding.path else "<unknown>"
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
        _echo(ctx, f"\nValidation passed: {warning_count} warning(s).")
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
@click.option(
    "--links/--no-links",
    is_flag=True,
    default=True,
    help="Update links and backlinks frontmatter fields from markdown body.",
)
@click.pass_context
def lint(
    ctx: click.Context,
    bundle_path: str,
    check: bool,
    diff: bool,
    links: bool,
) -> None:
    """Lint frontmatter: flatten nested lists and convert block-style to inline.

    Normalizes YAML frontmatter by flattening nested lists and converting
    block-style (multi-line) lists to inline notation.  This keeps
    frontmatter compact, which is important for coding agents that load
    only the first *n* lines of a file.

    With ``--links/--no-links`` (default: ``--links``), also updates ``links``
    (outgoing) and ``backlinks`` (incoming) frontmatter fields
    based on internal markdown links found in each concept's body.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to lint.
        check:
            Whether to report changes without writing them.
        diff:
            Whether to print a unified diff without writing changes.
        links:
            Whether to synchronize link metadata from Markdown bodies.

    Examples:
        okf-schema lint --path bundle
        okf-schema lint --path bundle --check --no-links
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-003
    try:
        results = lint_bundle(bundle_path, check=check, diff=diff, links=links)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
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
    """List all concepts in an OKF bundle.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to list.
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-005
    try:
        concepts = list_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    for concept in concepts:
        stale_marker = " [STALE]" if concept.stale else ""
        click.echo(f"{concept.path}  {concept.type}  {concept.title}{stale_marker}")


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
def show(
    ctx: click.Context,
    bundle_path: str,
    concept_path: str,
) -> None:
    """Show a single concept's frontmatter and body.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle containing the concept.
        concept_path:
            Bundle-relative path of the concept to display.

    Examples:
        okf-schema show --path bundle concepts/clock.md
    """
    try:
        detail = show_bundle(bundle_path, concept_path)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    import io

    from okf_schema._internal.yaml import make_yaml

    y = make_yaml()
    buf = io.StringIO()
    y.dump(detail.frontmatter, buf)
    fm_yaml = buf.getvalue().rstrip("\n")
    click.echo(f"---\n{fm_yaml}\n---")
    # OKF 0.2: show derived trust tier and staleness
    click.echo(f"trust: {detail.trust_tier}")
    if detail.stale:
        click.echo("stale: true")
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
    """Regenerate all index.md files in an OKF bundle.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to index.
    """
    # @implements_req SwRS-OKFSCHEMA-CORE-004
    try:
        updates = index_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
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
    """Show compact statistics for an OKF bundle.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to summarize.
    """
    try:
        s = stats_bundle(bundle_path)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
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
        click.echo("  Types:")
        for name, count in sorted_types:
            click.echo(f"    {name} {count}")

    # Tags (ranked by frequency, skip if empty)
    if s.tags_distribution:
        sorted_tags = sorted(s.tags_distribution.items(), key=lambda x: (-x[1], x[0]))
        click.echo("  Tags:")
        for tag, count in sorted_tags:
            click.echo(f"    {tag} {count}")

    # Health score
    score, issues = _health_score(s)
    if issues:
        click.echo(f"  Health: {score}% — {', '.join(issues)}")
    else:
        click.echo(f"  Health: {score}% — all clear")


# ---------------------------------------------------------------------------
# backlinks
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--path",
    "bundle_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory of the OKF bundle.",
)
@click.argument("targets", nargs=-1, required=True)
@click.pass_context
def backlinks(
    ctx: click.Context,
    bundle_path: str,
    targets: tuple[str, ...],
) -> None:
    """List all concepts that link to the given target concept(s).

    One line is printed per backlink in the form ``target ← source``.
    Multiple target paths may be provided.  The ``.md`` extension is
    optional and will be added automatically if omitted.

    Args:
        ctx:
            Active Click command context.
        bundle_path:
            Root directory of the bundle to inspect.
        targets:
            Bundle-relative target paths whose backlinks should be listed.

    Examples:
        okf-schema backlinks --path bundle concepts/clock
    """
    target_list = [t if t.endswith(".md") else f"{t}.md" for t in targets]
    try:
        results = backlinks_bundle(bundle_path, target_list)
    except (FileNotFoundError, NotADirectoryError) as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(2)

    # Group backlinks by target for ordered output
    by_target: dict[str, list[str]] = {t: [] for t in target_list}
    for r in results:
        by_target[r.target].append(r.source)

    for target in target_list:
        sources = by_target[target]
        if sources:
            for source in sources:
                click.echo(f"{target} ← {source}")
        else:
            click.echo(f"{target} ← ❌")


# Register the kb subcommand group
cli.add_command(kb)
