"""Acceptance tests of the generic ``okf-schema`` capability, run on the installed wheel.

Each test walks one main path of a StRS of scope ``core`` through the installed console script
or, for the navigation path, through the installed Python API, in a subprocess whose
environment holds no source checkout.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from tests.acceptance_support import InstalledProduct, combined_output

_CONCEPT_SCHEMA = textwrap.dedent(
    """\
    type: object
    properties:
      type: {type: string}
      title: {type: string}
      description: {type: string}
    required: [type, title, description]
    """
)

_CLOCK = textwrap.dedent(
    """\
    ---
    type: concept
    title: Clock
    description: The system clock.
    generated:
      at: "2026-01-01T00:00:00Z"
      by: bot:test
    ---

    The clock ticks. See [the timer](timer.md).
    """
)

_TIMER = textwrap.dedent(
    """\
    ---
    type: concept
    title: Timer
    description: The timer counts ticks.
    generated:
      at: "2026-01-01T00:00:00Z"
      by: bot:test
    ---

    A timer counts.
    """
)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _initialize_bundle(product: InstalledProduct, workspace: Path) -> Path:
    product.run("okf-schema", "init", "notes", cwd=workspace, check=True)
    bundle = workspace / "notes" / "bundle"
    (bundle / "_schema" / "concept.schema.yaml").write_text(_CONCEPT_SCHEMA, encoding="utf-8")
    return bundle


def _write_concepts(bundle: Path) -> None:
    (bundle / "concepts").mkdir(exist_ok=True)
    (bundle / "concepts" / "clock.md").write_text(_CLOCK, encoding="utf-8")
    (bundle / "concepts" / "timer.md").write_text(_TIMER, encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
def test_validate_reports_a_conforming_bundle_without_violation(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """A conforming bundle validates with no violation and a success status, even in strict mode."""
    bundle = _initialize_bundle(installed_product, tmp_path)
    _write_concepts(bundle)
    installed_product.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True)

    result = installed_product.run(
        "okf-schema", "validate", "--path", str(bundle), "--strict", cwd=tmp_path
    )

    assert result.returncode == 0, combined_output(result)
    assert "Bundle is conformant (0 errors, 0 warnings)" in combined_output(result)
    assert "ERROR" not in combined_output(result)
    assert "WARNING" not in combined_output(result)


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
def test_validate_reports_a_non_conforming_bundle_without_changing_it(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """An invalid document is reported readably with a failure status; nothing is written."""
    bundle = _initialize_bundle(installed_product, tmp_path)
    _write_concepts(bundle)
    installed_product.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True)
    invalid = bundle / "concepts" / "broken.md"
    invalid.write_text("---\ntype: concept\ndescription: No title.\n---\n\nBody.\n", "utf-8")
    before = _snapshot(tmp_path)

    result = installed_product.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)

    output = combined_output(result)
    assert result.returncode == 1, output
    assert "ERROR" in output
    assert "broken.md" in output
    assert "title" in output
    assert "Validation failed: 1 error(s)" in output
    assert _snapshot(tmp_path) == before


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
def test_init_then_new_creates_a_valid_bundle_that_keeps_the_authored_concept(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """A bundle is initialized, a concept is added and authored, and both validate and survive."""
    bundle = _initialize_bundle(installed_product, tmp_path)
    created = installed_product.run(
        "okf-schema",
        *("new", "--path", str(bundle), "--name", "concepts/clock", "--title", "Clock"),
        cwd=tmp_path,
        check=True,
    )
    concept = bundle / "concepts" / "clock.md"
    assert concept.is_file()
    assert "Created concept" in created.stdout
    authored = _CLOCK
    concept.write_text(authored, encoding="utf-8")
    installed_product.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True)

    validated = installed_product.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)
    shown = installed_product.run(
        "okf-schema", "show", "--path", str(bundle), "concepts/clock.md", cwd=tmp_path, check=True
    )

    assert validated.returncode == 0, validated.stdout + validated.stderr
    assert "Bundle is conformant" in validated.stdout
    assert concept.read_text(encoding="utf-8") == authored
    assert "title: Clock" in shown.stdout
    assert "The clock ticks." in shown.stdout


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_lint_and_index_are_deterministic_and_preserve_authored_content(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Formatting and indexing are idempotent, and comments, metadata and body survive."""
    bundle = _initialize_bundle(installed_product, tmp_path)
    _write_concepts(bundle)
    clock = bundle / "concepts" / "clock.md"
    clock.write_text(
        textwrap.dedent(
            """\
            ---
            type: concept
            title: Clock
            description: The system clock.
            # keep this comment
            tags:
              - time
              - hardware
            owner: team-a   # unknown metadata
            generated:
              at: "2026-01-01T00:00:00Z"
              by: bot:test
            ---

            The clock ticks. See [the timer](timer.md).
            """
        ),
        encoding="utf-8",
    )

    def format_and_index() -> None:
        installed_product.run(
            "okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True
        )
        installed_product.run("okf-schema", "lint", "--path", str(bundle), cwd=tmp_path, check=True)

    format_and_index()
    first = _snapshot(tmp_path)
    format_and_index()
    second = _snapshot(tmp_path)
    check = installed_product.run(
        "okf-schema", "lint", "--path", str(bundle), "--check", cwd=tmp_path
    )

    assert first == second
    assert check.returncode == 0, check.stdout + check.stderr
    formatted = clock.read_text(encoding="utf-8")
    assert "tags: [time, hardware]" in formatted
    assert "# keep this comment" in formatted
    assert "owner: team-a   # unknown metadata" in formatted
    assert formatted.endswith("\nThe clock ticks. See [the timer](timer.md).\n")
    index = (bundle / "concepts" / "index.md").read_text(encoding="utf-8")
    assert "- [Clock](clock.md) — The system clock." in index
    assert "- [Timer](timer.md) — The timer counts ticks." in index


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_inspection_reports_matching_concepts_and_changes_no_file(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Searching, listing, showing, trust and backlinks report on concepts and write nothing."""
    bundle = _initialize_bundle(installed_product, tmp_path)
    _write_concepts(bundle)
    installed_product.run("okf-schema", "lint", "--path", str(bundle), cwd=tmp_path, check=True)
    installed_product.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True)
    before = _snapshot(tmp_path)

    def inspect(*args: str) -> str:
        result = installed_product.run("okf-schema", *args, cwd=tmp_path, check=True)
        return result.stdout

    found = inspect("kb", "search", "clock", str(bundle), "--format", "paths")
    listed = inspect("list", "--path", str(bundle))
    shown = inspect("show", "--path", str(bundle), "concepts/clock.md")
    shown_by_name = inspect("show", "--path", str(bundle), "concepts/clock")
    trusted = inspect("trust", "--path", str(bundle), "concepts/clock")
    backlinks = inspect("backlinks", "--path", str(bundle), "concepts/timer")
    statistics = inspect("stats", "--path", str(bundle))

    assert found.split() == ["concepts/clock.md"]
    assert "concepts/clock.md" in listed
    assert "concepts/timer.md" in listed
    assert shown == (bundle / "concepts" / "clock.md").read_text(encoding="utf-8")
    assert "trust:" not in shown
    assert "The clock ticks." in shown_by_name
    assert trusted.splitlines() == ["trust: unverified"]
    assert "concepts/timer.md ← concepts/clock.md" in backlinks
    assert "2 concepts" in statistics
    assert _snapshot(tmp_path) == before


_NAVIGATION_SCRIPT = textwrap.dedent(
    """\
    import json
    import sys
    from pathlib import Path

    from okf_schema.api import inspect_file_links, show_bundle
    from okf_schema.validator import load_schema_database

    bundle = Path(sys.argv[1])
    schema = load_schema_database(bundle / "_schema")["concept"]
    frontmatter = show_bundle(bundle, "concepts/cache.md").frontmatter
    authored = json.dumps(frontmatter, sort_keys=True)
    results = inspect_file_links(
        frontmatter,
        schema,
        bundle / "concepts" / "cache.md",
        bundle_root=bundle,
        project_root=bundle.parent,
    )
    print(
        json.dumps(
            {
                "links": [
                    {
                        "field_path": result.field_path,
                        "resolution": result.resolution,
                        "target": result.target,
                        "status": result.status,
                        "resolved": str(result.resolved_path),
                    }
                    for result in results
                ],
                "value_types": {
                    "design": type(frontmatter["design"]).__name__,
                    "sources": type(frontmatter["sources"]).__name__,
                    "source_items": sorted(
                        {type(item).__name__ for item in frontmatter["sources"]}
                    ),
                },
                "authored_unchanged": json.dumps(frontmatter, sort_keys=True) == authored,
            }
        )
    )
    """
)


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
def test_api_navigates_single_and_list_file_links_without_changing_values(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """The installed API returns each target with its root, and values stay strings and lists."""
    bundle = tmp_path / "project" / "bundle"
    (bundle / "_schema").mkdir(parents=True)
    (bundle / "concepts").mkdir()
    (bundle / "design").mkdir()
    (bundle / "design" / "cache.md").write_text("# Cache design\n", encoding="utf-8")
    (tmp_path / "project" / "src").mkdir()
    for name in ("cache.py", "eviction.py"):
        (tmp_path / "project" / "src" / name).write_text("", encoding="utf-8")
    (bundle / "_schema" / "concept.schema.yaml").write_text(
        textwrap.dedent(
            """\
            type: object
            properties:
              type: {type: string}
              design:
                type: string
                x-okf-link: {resolution: bundle-relative, syntax: plain}
              sources:
                type: array
                items:
                  type: string
                  x-okf-link: {resolution: project-relative, syntax: plain}
            """
        ),
        encoding="utf-8",
    )
    (bundle / "concepts" / "cache.md").write_text(
        "---\ntype: concept\ntitle: Cache\ndescription: Cache.\n"
        "design: design/cache.md\nsources: [src/cache.py, src/eviction.py]\n---\n\nBody.\n",
        encoding="utf-8",
    )

    completed = installed_product.run_python(
        _NAVIGATION_SCRIPT, str(bundle), cwd=tmp_path, check=False
    )

    assert completed.returncode == 0, completed.stderr
    outcome = json.loads(completed.stdout)
    assert [
        (link["field_path"], link["resolution"], link["target"]) for link in outcome["links"]
    ] == [
        ("design", "bundle-relative", "design/cache.md"),
        ("sources[0]", "project-relative", "src/cache.py"),
        ("sources[1]", "project-relative", "src/eviction.py"),
    ]
    assert all(link["status"] == "valid" for link in outcome["links"])
    assert outcome["links"][0]["resolved"] == str((bundle / "design" / "cache.md").resolve())
    assert outcome["value_types"] == {"design": "str", "sources": "list", "source_items": ["str"]}
    assert outcome["authored_unchanged"] is True


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
def test_validate_checks_declared_file_links_only_on_request_and_reports_skipped_checks(
    installed_product: InstalledProduct, tmp_path: Path
) -> None:
    """Link checking is opt-in; a missing target is an error and an impossible check is skipped."""
    bundle = tmp_path / "bundle"
    (bundle / "_schema").mkdir(parents=True)
    (bundle / "concepts").mkdir()
    (bundle / "_schema" / "concept.schema.yaml").write_text(
        textwrap.dedent(
            """\
            type: object
            properties:
              type: {type: string}
              design:
                type: string
                x-okf-link: {resolution: bundle-relative, syntax: plain}
              sources:
                type: array
                items:
                  type: string
                  x-okf-link: {resolution: project-relative, syntax: plain}
            """
        ),
        encoding="utf-8",
    )
    (bundle / "concepts" / "cache.md").write_text(
        "---\ntype: concept\ntitle: Cache\ndescription: Cache.\n"
        "generated:\n  at: '2026-01-01T00:00:00Z'\n  by: bot:test\n"
        "design: concepts/missing.md\nsources: [src/cache.py]\n---\n\nBody.\n",
        encoding="utf-8",
    )
    installed_product.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path, check=True)
    before = _snapshot(tmp_path)

    default = installed_product.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)
    checked = installed_product.run(
        "okf-schema", "validate", "--path", str(bundle), "--check-links", cwd=tmp_path
    )

    assert default.returncode == 0, combined_output(default)
    assert "E10" not in combined_output(default)
    output = combined_output(checked)
    assert checked.returncode == 1, output
    assert "E10" in output
    assert "concepts/missing.md" in output
    assert "W15" in output
    assert "project-relative root is unavailable" in output
    assert _snapshot(tmp_path) == before
