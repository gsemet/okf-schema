"""Click command-line interface for standalone requirements management.

The :func:`okfreq` command group initializes requirement bundles, creates
stakeholder and software requirements, validates their structure, scans
traceability markers, updates generated coverage fields, and writes reports.

Examples:
    Invoke the command through the installed console script::

        okfreq --help
        okfreq validate requirements --prose
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from okf_schema.okfreq.core import (
    RequirementError,
    bundle_path,
    create_requirement,
    graph,
    init_requirements,
    load_requirements,
    marker_scan,
    merge_config,
    update_coverage,
    validate_requirements,
    write_json_report,
    write_markdown_report,
    write_report_schema,
)
from okf_schema.skill_cli import _register_install_skills


class _HelpCommand(click.Command):
    """Click command with the short and long help options enabled."""

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a command and add default help option names."""
        context_settings = kwargs.setdefault("context_settings", {})
        context_settings.setdefault("help_option_names", ["-h", "--help"])
        super().__init__(*args, **kwargs)


class _HelpGroup(click.Group):
    """Click group whose commands consistently accept ``-h`` and ``--help``."""

    command_class = _HelpCommand


def _root(path: str) -> Path:
    """Resolve a command-line path to its requirements bundle root."""
    return bundle_path(Path(path).resolve())


def _fail(exc: RequirementError) -> click.ClickException:
    """Convert a domain error into a Click command error."""
    return click.ClickException(str(exc))


@click.group(
    cls=_HelpGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def okfreq() -> None:
    """Create, validate, trace, and maintain OKF requirements."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-001


_register_install_skills(okfreq, "okfreq")


@okfreq.command("init")
@click.argument("path", default=".", type=click.Path())
@click.option("--force", is_flag=True, help="Merge without replacing existing files.")
def init(path: str, force: bool) -> None:
    """Initialize a requirements bundle below PATH.

    Args:
        path:
            Project or requirements-bundle path.
        force:
            Merge into a non-empty directory without replacing files.
    """
    try:
        click.echo(
            f"Created requirements bundle at {init_requirements(Path(path).resolve(), force)}"
        )
    except RequirementError as exc:
        raise _fail(exc) from exc


@okfreq.group()
def new() -> None:
    """Create a native requirement."""


def _register_new(level: str, name: str) -> None:
    """Register a level-specific requirement creation command."""

    @new.command(name)
    @click.argument("title")
    @click.option(
        "--description",
        required=True,
        help="Normative EARS behavior containing one observable SHALL response.",
    )
    @click.option("--project", required=True)
    @click.option("--scope", "scope_name", default="default", show_default=True)
    @click.option("--origin", default="native", show_default=True)
    @click.option("--derives-from", multiple=True)
    @click.option(
        "--user-need",
        help="Stakeholder need for StRS only; rejected for derived levels such as SwRS.",
    )
    @click.option("--path", default=".", type=click.Path())
    def create(
        title: str,
        description: str,
        project: str,
        scope_name: str,
        origin: str,
        derives_from: tuple[str, ...],
        user_need: str | None,
        path: str,
    ) -> None:
        """Create one requirement of the registered level.

        Args:
            title:
                Concise statement of the requirement's subject.
            description:
                Normative EARS behavior containing a ``SHALL`` response.
            project:
                Owning project code.
            scope_name:
                Configured scope used for allocation and marker scanning.
            origin:
                Producer or source of the requirement.
            derives_from:
                Parent requirement IDs.
            user_need:
                Stakeholder need accepted only for an StRS.
            path:
                Project or requirements-bundle path.

        Examples:
            Create a stakeholder requirement::

                okfreq new strs "Readable reports" \
                    --description "The tool SHALL produce readable reports." \
                    --project example \
                    --user-need "Users need to review requirement coverage."
        """
        try:
            target = create_requirement(
                _root(path),
                level,
                title,
                description,
                project=project,
                scope=scope_name,
                origin=origin,
                derives_from=list(derives_from),
                user_need=user_need,
            )
            click.echo(f"Created {target}")
            if level == "StRS":
                click.echo(
                    "Complete the generated stakeholder need and constraint gaps before review."
                )
            else:
                click.echo("Complete the generated scenarios and verification gaps before review.")
        except RequirementError as exc:
            raise _fail(exc) from exc


_register_new("StRS", "strs")
_register_new("SwRS", "swrs")


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--json", "as_json", is_flag=True)
@click.option("--prose", is_flag=True, help="Enable optional prose warnings.")
def validate(
    path: str,
    as_json: bool,
    prose: bool,
) -> None:
    """Validate requirements, configuration, and derivation graph.

    Advisory prose warnings are reported separately and never change the exit
    status; only structural errors do.

    Args:
        path:
            Project or requirements-bundle path.
        as_json:
            Emit a structured JSON result.
        prose:
            Include advisory EARS prose warnings.

    Examples:
        Validate a bundle and include prose diagnostics::

            okfreq validate requirements --prose
    """
    try:
        findings = validate_requirements(_root(path), prose=prose)
    except RequirementError as exc:
        raise _fail(exc) from exc
    warnings = [finding for finding in findings if finding.startswith("W")]
    errors = [finding for finding in findings if not finding.startswith("W")]
    result = {
        "errors": errors,
        "warnings": warnings,
        "requirements": len(load_requirements(_root(path))),
    }
    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(
            f"{result['requirements']} requirements, {len(errors)} errors, {len(warnings)} warnings"
        )
        for warning in warnings:
            click.echo(warning)
    if errors:
        raise click.exceptions.Exit(1)


def _run_validation(path: str) -> None:
    """Run validation for commands that only need an exit status."""
    root = _root(path)
    errors = validate_requirements(root)
    if errors:
        raise click.ClickException("\n".join(errors))


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--prose", is_flag=True, help="Also report advisory EARS prose warnings.")
def lint(path: str, prose: bool) -> None:
    """Run structural checks, optionally with advisory prose warnings.

    Args:
        path:
            Project or requirements-bundle path.
        prose:
            Print advisory EARS prose warnings before structural validation.
    """
    if prose:
        for finding in validate_requirements(_root(path), prose=True):
            if finding.startswith("W"):
                click.echo(finding)
    _run_validation(path)


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
def index(path: str) -> None:
    """Print stable requirement IDs.

    Args:
        path:
            Project or requirements-bundle path.
    """
    for identifier in sorted(load_requirements(_root(path))):
        click.echo(identifier)


@okfreq.command()
@click.argument("query")
@click.argument("path", default=".", type=click.Path())
def search(query: str, path: str) -> None:
    """Search requirement IDs, titles, and descriptions.

    Args:
        query:
            Case-insensitive text to find.
        path:
            Project or requirements-bundle path.
    """
    query_lower = query.casefold()
    for identifier, (_, data, _) in load_requirements(_root(path)).items():
        haystack = " ".join(str(data.get(key, "")) for key in ("id", "title", "description"))
        if query_lower in haystack.casefold():
            click.echo(identifier)


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--json", "as_json", is_flag=True)
def trace(path: str, as_json: bool) -> None:
    """Scan configured source and test directories for markers.

    Args:
        path:
            Project or requirements-bundle path.
        as_json:
            Emit marker locations and diagnostics as JSON.
    """
    result = marker_scan(_root(path))
    summary = (
        f"implemented: {len(result['implemented'])}; "
        f"tested: {len(result['tested'])}; "
        f"missing IDs: {len(result['missing_ids'])}"
    )
    click.echo(json.dumps(result, indent=2) if as_json else summary)


@okfreq.command("in-file")
@click.argument("file", type=click.Path(exists=True))
def in_file(file: str) -> None:
    """Show a requirement file.

    Args:
        file:
            Existing requirement-document path.
    """
    click.echo(Path(file).read_text(encoding="utf-8"))


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
def status(path: str) -> None:
    """Print lifecycle counts and health.

    Args:
        path:
            Project or requirements-bundle path.
    """
    root = _root(path)
    requirements = load_requirements(root)
    lifecycle: dict[str, int] = {}
    for _, data, _ in requirements.values():
        value = str(data.get("lifecycle", "invalid"))
        lifecycle[value] = lifecycle.get(value, 0) + 1
    click.echo(
        json.dumps(
            {
                "requirements": len(requirements),
                "lifecycle": lifecycle,
                "errors": len(validate_requirements(root)),
            },
            indent=2,
        )
    )


@okfreq.command()
@click.argument("path", default=".", type=click.Path())
def scope(path: str) -> None:
    """Print configured scope mappings.

    Args:
        path:
            Project or requirements-bundle path.
    """
    from okf_schema.okfreq.core import load_config

    click.echo(json.dumps(load_config(_root(path)).get("scopes", {}), indent=2))


@okfreq.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("--path", default=".", type=click.Path())
def import_config(source: str, path: str) -> None:
    """Import a configuration explicitly, preserving conflicts and unknown keys.

    Args:
        source:
            Existing YAML configuration to import.
        path:
            Project or requirements-bundle path.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-006
    try:
        conflicts = merge_config(_root(path), Path(source))
    except RequirementError as exc:
        raise _fail(exc) from exc
    click.echo(f"Configuration imported; conflicts: {len(conflicts)}")
    for conflict in conflicts:
        click.echo(f"  conflict: {conflict}", err=True)


@okfreq.command("config-merge")
@click.argument("source", type=click.Path(exists=True))
@click.option("--path", default=".", type=click.Path())
def config_merge(source: str, path: str) -> None:
    """Explicitly merge SOURCE into the project configuration.

    Args:
        source:
            Existing YAML configuration to merge.
        path:
            Project or requirements-bundle path.
    """
    try:
        conflicts = merge_config(_root(path), Path(source))
    except RequirementError as exc:
        raise _fail(exc) from exc
    click.echo(f"Configuration merged; conflicts: {len(conflicts)}")
    for conflict in conflicts:
        click.echo(f"  conflict: {conflict}", err=True)


@okfreq.command("update-coverage")
@click.argument("path", default=".", type=click.Path())
@click.option("--check", is_flag=True, help="Preview and do not write.")
@click.option("--diff", "show_diff", is_flag=True, help="Print unified diffs and do not write.")
def coverage(
    path: str,
    check: bool,
    show_diff: bool,
) -> None:
    """Explicitly update generated coverage fields.

    Args:
        path:
            Project or requirements-bundle path.
        check:
            Preview the changed-file count without writing.
        show_diff:
            Print unified diffs without writing.

    Examples:
        Preview generated coverage changes::

            okfreq update-coverage requirements --check
    """
    changed = update_coverage(_root(path), check=check, show_diff=show_diff)
    click.echo(f"{len(changed)} files {'would change' if check or show_diff else 'updated'}")


@okfreq.command("graph")
@click.argument("path", default=".", type=click.Path())
@click.option("--json", "as_json", is_flag=True)
def graph_command(path: str, as_json: bool) -> None:
    """Show authored and computed derivation links.

    Args:
        path:
            Project or requirements-bundle path.
        as_json:
            Include errors and both edge directions in the JSON output.
    """
    result = graph(_root(path))
    click.echo(
        json.dumps(result, indent=2) if as_json else json.dumps(result["derived_by"], indent=2)
    )
    if result["errors"]:
        raise click.exceptions.Exit(1)


@okfreq.command("generate-report")
@click.argument("path", default=".", type=click.Path())
@click.option(
    "--output-json", type=click.Path(), help="Write the detailed JSON report to this path."
)
@click.option(
    "--output-summary-md", type=click.Path(), help="Write the Markdown summary to this path."
)
def generate_report(
    path: str,
    output_json: str | None,
    output_summary_md: str | None,
) -> None:
    """Generate detailed JSON and summary Markdown traceability reports.

    Args:
        path:
            Project or requirements-bundle path.
        output_json:
            Optional path for the detailed JSON report.
        output_summary_md:
            Optional path for the Markdown summary.

    Examples:
        Write both report formats to explicit destinations::

            okfreq generate-report requirements \
                --output-json dist/requirements.json \
                --output-summary-md dist/requirements.md
    """
    root = _root(path)
    destinations = []
    if output_json:
        json_destination = Path(output_json)
        schema_destination = json_destination.with_suffix(".schema.json")
        destinations.extend([json_destination, schema_destination])
        write_json_report(root, json_destination)
        write_report_schema(schema_destination)
    if output_summary_md:
        destinations.append(Path(output_summary_md))
        write_markdown_report(root, Path(output_summary_md))
    if not destinations:
        json_destination = root.parent / "dist" / "requirements-report.json"
        schema_destination = root.parent / "dist" / "requirements-report.schema.json"
        markdown_destination = root.parent / "dist" / "requirements-report.md"
        json_destination.parent.mkdir(parents=True, exist_ok=True)
        destinations = [json_destination, schema_destination, markdown_destination]
        write_json_report(root, json_destination)
        write_report_schema(schema_destination)
        write_markdown_report(root, markdown_destination)
    click.echo("Generated: " + ", ".join(str(destination) for destination in destinations))


@okfreq.command()
@click.argument("target")
@click.option("--path", default=".", type=click.Path())
@click.option("--yes", is_flag=True, help="Confirm the explicit lifecycle change.")
def archive(
    target: str,
    path: str,
    yes: bool,
) -> None:
    """Mark TARGET deprecated without deleting it.

    Args:
        target:
            Stable ID of the requirement to deprecate.
        path:
            Project or requirements-bundle path.
        yes:
            Confirm the lifecycle change.

    Examples:
        Confirm and archive one requirement::

            okfreq archive SwRS-example-001 --path requirements --yes
    """
    if not yes:
        raise click.ClickException("archive is destructive to lifecycle state; pass --yes")
    _change_lifecycle(_root(path), target, "deprecated")


@okfreq.command()
@click.argument("target")
@click.argument("replacement")
@click.option("--path", default=".", type=click.Path())
@click.option("--yes", is_flag=True)
def supersede(
    target: str,
    replacement: str,
    path: str,
    yes: bool,
) -> None:
    """Mark TARGET superseded by REPLACEMENT.

    Args:
        target:
            Stable ID of the requirement to supersede.
        replacement:
            Stable ID of its replacement requirement.
        path:
            Project or requirements-bundle path.
        yes:
            Confirm the lifecycle change.

    Examples:
        Confirm a replacement relationship::

            okfreq supersede SwRS-old-001 SwRS-new-001 \
                --path requirements --yes
    """
    if not yes:
        raise click.ClickException("supersede requires explicit confirmation with --yes")
    requirements = load_requirements(_root(path))
    if replacement not in requirements:
        raise click.ClickException(f"unknown replacement requirement: {replacement}")
    if replacement == target:
        raise click.ClickException("a requirement cannot supersede itself")
    _change_lifecycle(_root(path), target, "superseded", {"superseded_by": replacement})


def _change_lifecycle(
    root: Path,
    target: str,
    lifecycle: str,
    extra: dict[str, str] | None = None,
) -> None:
    """Change one requirement's lifecycle after explicit confirmation."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-007
    from okf_schema.okfreq.core import _atomic_write, _render_frontmatter

    requirements = load_requirements(root)
    if target not in requirements:
        raise click.ClickException(f"unknown requirement: {target}")
    file, _, text = requirements[target]
    _atomic_write(file, _render_frontmatter(text, {"lifecycle": lifecycle, **(extra or {})}))
    click.echo(f"Updated {target}")
