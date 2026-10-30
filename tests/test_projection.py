"""Tests for schema-declared OKF projections, log headings and their CLI surfaces."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema._internal.utils import build_link_graph
from okf_schema.api import lint_bundle, update_bundle, validate_bundle
from okf_schema.cli import cli
from okf_schema.file_links import check_file_links
from okf_schema.okfkb.scaffold import scaffold_kb
from okf_schema.projection import (
    LINKS_END,
    LINKS_START,
    ProjectionError,
    projection_problems,
    replace_links_section,
    schema_projection,
    strip_links_section,
)
from okf_schema.validator import log_heading_findings

# @tests_req SwRS-OKFSCHEMA-CORE-009

SCHEMA = dedent(
    """\
    type: object
    properties:
      type: {type: string}
      state:
        type: string
        enum: [wip, done, gone]
        x-okf-status-projection: {wip: draft, done: stable, gone: deprecated}
      parents:
        type: array
        items:
          type: string
          x-okf-link: {resolution: filename-stem, syntax: plain, link-projection: Parents}
      see:
        type: array
        items:
          type: string
          x-okf-link: {resolution: bundle-relative, syntax: plain, link-projection: See also}
      links:
        type: array
        items:
          type: string
          x-okf-link: {resolution: bundle-relative, syntax: plain}
    """
)


def _bundle(tmp_path: Path, schema: str = SCHEMA) -> Path:
    bundle = tmp_path / "bundle"
    (bundle / "_schema").mkdir(parents=True)
    (bundle / "_schema" / "note.schema.yaml").write_text(schema, encoding="utf-8")
    (bundle / "index.md").write_text("# Notes\n", encoding="utf-8")
    (bundle / "root.md").write_text(
        "---\ntype: note\ntitle: Root note\nstate: done\n---\n\n# Root\n", encoding="utf-8"
    )
    (bundle / "child.md").write_text(
        "---\ntype: note\ntitle: Child\nstate: wip\nparents: [root, missing]\n"
        "see: [root.md]\n---\n\n# Child\n\nSee [root](root.md).\n",
        encoding="utf-8",
    )
    return bundle


def test_schema_projection_reads_links_in_schema_order_and_the_status_mapping() -> None:
    base = {
        "properties": {
            "up": {
                "items": {"x-okf-link": {"resolution": "filename-stem", "link-projection": "Up"}}
            }
        }
    }
    schema = {
        "allOf": [base],
        "properties": {
            "state": {"x-okf-status-projection": {"a": "draft"}},
            "across": {
                "x-okf-link": {
                    "resolution": "bundle-relative-stem",
                    "syntax": "wikilink",
                    "link-projection": " Across ",
                }
            },
            "files": {
                "items": {
                    "x-okf-link": {"resolution": "project-relative", "link-projection": "Files"}
                }
            },
            "plain": {"items": {"x-okf-link": {"resolution": "filename-stem"}}},
        },
    }

    projection = schema_projection(schema)

    assert [(link.field, link.label, link.syntax) for link in projection.links] == [
        ("up", "Up", "plain"),
        ("across", "Across", "wikilink"),
    ]
    assert (projection.status_field, projection.status_map) == ("state", {"a": "draft"})
    assert schema_projection(None).links == ()


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="empty_label",
    prop={"items": {"x-okf-link": {"resolution": "filename-stem", "link-projection": " "}}},
    expected="x-okf-link link-projection must be a non-empty string",
)
@Parametrization.case(
    name="outside_the_bundle",
    prop={"items": {"x-okf-link": {"resolution": "project-relative", "link-projection": "F"}}},
    expected="needs a resolution inside the bundle",
)
@Parametrization.case(
    name="status_not_a_mapping",
    prop={"x-okf-status-projection": ["draft"]},
    expected="must map each field value to an OKF status",
)
@Parametrization.case(
    name="status_outside_okf",
    prop={"x-okf-status-projection": {"a": "retired"}},
    expected="maps a to retired; expected one of draft, stable, deprecated",
)
@Parametrization.case(
    name="incomplete_status_mapping",
    prop={"enum": ["a", "b"], "x-okf-status-projection": {"a": "draft"}},
    expected="has no OKF status for b",
)
def test_projection_problems_report_malformed_annotations(prop: dict, expected: str) -> None:
    problems = projection_problems({"properties": {"field": prop}})

    assert len(problems) == 1
    assert problems[0].startswith("field: ")
    assert expected in problems[0]


@Parametrization.autodetect_parameters()
@Parametrization.case(name="empty", label="", expected="must be a non-empty string")
@Parametrization.case(name="not_a_string", label=3, expected="must be a non-empty string")
def test_file_link_parser_rejects_a_malformed_link_projection(
    tmp_path: Path, label: object, expected: str
) -> None:
    (tmp_path / "a.md").write_text("---\ntype: x\n---\n", encoding="utf-8")
    schema = {
        "properties": {
            "to": {
                "x-okf-link": {
                    "resolution": "filename-stem",
                    "syntax": "plain",
                    "link-projection": label,
                }
            }
        }
    }

    diagnostics = check_file_links({"to": "a"}, schema, tmp_path / "b.md", bundle_root=tmp_path)

    assert [diagnostic.code for diagnostic in diagnostics] == ["E10"]
    assert expected in diagnostics[0].message


def test_file_link_parser_rejects_a_link_projection_leaving_the_bundle(tmp_path: Path) -> None:
    schema = {
        "properties": {
            "to": {
                "x-okf-link": {
                    "resolution": "project-relative",
                    "syntax": "plain",
                    "link-projection": "To",
                }
            }
        }
    }

    diagnostics = check_file_links({"to": "a.py"}, schema, tmp_path / "b.md", project_root=tmp_path)

    assert "needs a resolution inside the bundle" in diagnostics[0].message


def test_lint_generates_links_and_status_from_schema_annotations(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)

    changed = [result.path.name for result in lint_bundle(bundle, links=True) if result.changed]

    child = (bundle / "child.md").read_text(encoding="utf-8")
    assert sorted(changed) == ["child.md", "root.md"]
    assert "state: wip\nstatus: draft\n" in child
    assert "status: stable" in (bundle / "root.md").read_text(encoding="utf-8")
    assert child.endswith(
        "See [root](root.md).\n\n"
        f"{LINKS_START}\n### Links\n\n"
        "<!-- Generated from the frontmatter relations; edit them instead. -->\n\n"
        "- Parents:\n  - [root](root.md): Root note\n  - `missing`\n"
        "- See also:\n  - [root.md](root.md): Root note\n"
        f"{LINKS_END}\n"
    )
    assert LINKS_START not in (bundle / "root.md").read_text(encoding="utf-8")
    assert not any(result.changed for result in lint_bundle(bundle, check=True, links=True))


def test_link_graph_skips_the_generated_links_section(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    lint_bundle(bundle, links=True)

    outgoing, _ = build_link_graph(bundle)

    assert outgoing == {"child.md": ["root.md"]}
    assert "links: [root.md]" in (bundle / "child.md").read_text(encoding="utf-8")


def test_renaming_then_removing_an_annotation_updates_every_links_section(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    lint_bundle(bundle)
    schema = bundle / "_schema" / "note.schema.yaml"

    schema.write_text(SCHEMA.replace("link-projection: Parents", "link-projection: Up"), "utf-8")
    assert [r.path.name for r in lint_bundle(bundle, check=True) if r.changed] == ["child.md"]
    lint_bundle(bundle)
    assert "- Up:\n" in (bundle / "child.md").read_text(encoding="utf-8")

    schema.write_text(
        SCHEMA.replace(", link-projection: Parents", "").replace(", link-projection: See also", ""),
        "utf-8",
    )
    lint_bundle(bundle)
    child = (bundle / "child.md").read_text(encoding="utf-8")
    assert LINKS_START not in child
    assert child.endswith("See [root](root.md).\n")


def test_lint_without_projection_or_schemas_leaves_bodies_unchanged(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    assert not any(r.changed for r in lint_bundle(bundle, projection=False))

    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "a.md").write_text("---\ntype: x\n---\n\nBody\n", encoding="utf-8")
    assert not any(r.changed for r in lint_bundle(plain))


@Parametrization.autodetect_parameters()
@Parametrization.case(name="start_only", body=f"Body\n{LINKS_START}\n")
@Parametrization.case(name="reversed", body=f"{LINKS_END}\n{LINKS_START}\n")
@Parametrization.case(name="repeated", body=f"{LINKS_START}{LINKS_END}{LINKS_START}{LINKS_END}")
def test_a_malformed_links_section_is_refused(body: str) -> None:
    with pytest.raises(ProjectionError, match="one complete generated Links section"):
        replace_links_section(body, "")
    assert strip_links_section(body) == body


def test_replace_links_section_keeps_text_after_the_section() -> None:
    body = f"Intro\n\n{LINKS_START}\nold\n{LINKS_END}\n\nOutro\n"

    assert replace_links_section(body, "NEW") == "Intro\n\nOutro\n\nNEW\n"
    assert replace_links_section(f"{LINKS_START}{LINKS_END}", "") == ""
    assert replace_links_section("", "NEW") == "NEW\n"


def test_cli_lint_reports_a_malformed_links_section(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (bundle / "root.md").write_text(
        f"---\ntype: note\nstate: done\n---\n\n{LINKS_START}\n", encoding="utf-8"
    )

    result = CliRunner().invoke(cli, ["lint", "--path", str(bundle)])

    assert result.exit_code == 1
    assert "one complete generated Links section" in result.output


def test_validate_reports_malformed_projection_annotations(tmp_path: Path) -> None:
    bundle = _bundle(
        tmp_path,
        SCHEMA.replace("resolution: filename-stem", "resolution: project-relative").replace(
            "gone: deprecated", "gone: retired"
        ),
    )

    report = validate_bundle(bundle)

    messages = [finding.message for finding in report.errors if finding.code == "E11"]
    assert len(messages) == 2
    assert any("parents: x-okf-link link-projection needs a resolution" in m for m in messages)
    assert any("state: x-okf-status-projection maps gone to retired" in m for m in messages)


@Parametrization.autodetect_parameters()
@Parametrization.case(
    name="conforming", text="## 2026-10-28\n\n### Topic\n\n## 2026-10-25\n", codes=[]
)
@Parametrization.case(name="topic_in_heading", text="## 2026-10-25 (topic)\n", codes=["W5"])
@Parametrization.case(
    name="not_a_date", text="## 2026-02-30\n\n## June 1, 2026\n", codes=["W5", "W5"]
)
@Parametrization.case(name="oldest_first", text="## 2026-10-25\n\n## 2026-10-28\n", codes=["W18"])
@Parametrization.case(name="repeated", text="## 2026-10-28\n\n## 2026-10-28\n", codes=["W18"])
def test_log_heading_findings(tmp_path: Path, text: str, codes: list[str]) -> None:
    log = tmp_path / "log.md"
    log.write_text(f"# Log\n\n{text}", encoding="utf-8")

    assert [finding.code for finding in log_heading_findings(log)] == codes


def test_cli_lint_check_fails_on_a_non_conforming_log_heading(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "log.md").write_text("# Log\n\n## 2026-10-28\n", encoding="utf-8")
    runner = CliRunner()

    assert runner.invoke(cli, ["lint", "--path", str(bundle), "--check"]).exit_code == 0
    (bundle / "log.md").write_text("# Log\n\n## 2026-10-25 (topic)\n", encoding="utf-8")
    result = runner.invoke(cli, ["lint", "--path", str(bundle), "--check"])

    assert result.exit_code == 1
    assert "[W5]" in result.output and "'### Topic' sub-heading" in result.output


# @tests_req SwRS-OKFSCHEMA-OKFKB-006
def test_okfkb_update_projects_derivations_as_markdown_links(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    scaffold_kb(kb)
    (kb / "findings").mkdir(exist_ok=True)
    (kb / "concepts").mkdir(exist_ok=True)
    (kb / "findings" / "raw.md").write_text(
        "---\ntype: Finding\ntitle: Raw observation\n---\n\nObserved.\n", encoding="utf-8"
    )
    (kb / "concepts" / "idea.md").write_text(
        "---\ntype: Concept\ntitle: Idea\nderived_from: [findings/raw]\n---\n\nIdea.\n",
        encoding="utf-8",
    )

    update_bundle(kb)

    idea = (kb / "concepts" / "idea.md").read_text(encoding="utf-8")
    raw = (kb / "findings" / "raw.md").read_text(encoding="utf-8")
    assert "- Derived from:\n  - [findings/raw](../findings/raw.md): Raw observation\n" in idea
    assert "- Derives to:\n  - [concepts/idea](../concepts/idea.md): Idea\n" in raw
    assert raw.startswith("---\ntype: Finding\ntitle: Raw observation\n")
    assert "links: []" in raw
