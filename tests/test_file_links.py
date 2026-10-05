"""Tests for opt-in JSON Schema file-link annotations."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema.api import check_file_links, validate_bundle
from okf_schema.cli import cli
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    graph,
    init_requirements,
    load_schema_database,
    validate_requirements,
)

# @tests_req SwRS-OKFSCHEMA-CORE-007
# @tests_req SwRS-OKFSCHEMA-OKFREQ-005


def _link_schema(resolution: str, syntax: str = "plain") -> dict[str, object]:
    return {"type": "string", "x-okf-link": {"resolution": resolution, "syntax": syntax}}


def test_generic_init_declares_link_defaults(tmp_path: Path) -> None:
    """Generic scaffolds declare local-file semantics on existing link list items."""
    from okf_schema.validator import load_schema_database

    result = CliRunner().invoke(cli, ["init", str(tmp_path / "example")])
    assert result.exit_code == 0, result.output
    schemas = load_schema_database(tmp_path / "example" / "bundle" / "_schema")
    schema = schemas["_base"]
    for field in ("links", "backlinks"):
        items = schema["properties"][field]["items"]
        assert items["type"] == "string"
        assert items["x-okf-link"] == {"resolution": "bundle-relative", "syntax": "plain"}


@Parametrization.autodetect_parameters()
@Parametrization.case("nested", target="findings/2026.10-observation", code=None)
@Parametrization.case("missing", target="findings/missing", code="E10")
@Parametrization.case("escape", target="../outside", code="E10")
@Parametrization.case("absolute", target="/outside", code="E10")
@Parametrization.case("windows_absolute", target="C:/outside", code="E10")
@Parametrization.case(
    "exact_extension_not_stem", target="findings/2026.10-observation.md", code="E10"
)
def test_bundle_relative_stem_checks_exact_markdown_path(
    tmp_path: Path,
    target: str,
    code: str | None,
) -> None:
    """Extensionless bundle paths resolve deterministically and stay within their root."""
    bundle = tmp_path / "knowledge"
    (bundle / "findings").mkdir(parents=True)
    (bundle / "findings" / "2026.10-observation.md").write_text("", encoding="utf-8")
    (tmp_path / "outside.md").write_text("", encoding="utf-8")
    diagnostics = check_file_links(
        {"derived_from": [target]},
        {"properties": {"derived_from": {"items": _link_schema("bundle-relative-stem")}}},
        bundle / "concepts" / "cache.md",
        bundle_root=bundle,
    )
    assert [diagnostic.code for diagnostic in diagnostics] == ([] if code is None else [code])
    if code is not None:
        assert diagnostics[0].field_path == "derived_from[0]"


def test_bundle_relative_stem_wikilinks_and_unavailable_root(tmp_path: Path) -> None:
    """Generic consumers can use wikilinks with extensionless bundle paths."""
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "cache.md").write_text("", encoding="utf-8")
    schema = {"properties": {"design": _link_schema("bundle-relative-stem", "wikilink")}}
    frontmatter = {"design": "[[concepts/cache#Decisions|Cache design]]"}
    assert check_file_links(frontmatter, schema, tmp_path / "source.md", bundle_root=tmp_path) == []
    diagnostics = check_file_links(frontmatter, schema, tmp_path / "source.md")
    assert [diagnostic.code for diagnostic in diagnostics] == ["W15"]
    assert "bundle-relative-stem root is unavailable" in diagnostics[0].message


def test_bundle_relative_remains_exact(tmp_path: Path) -> None:
    """Adding stem resolution does not append extensions to exact bundle links."""
    (tmp_path / "target.md").write_text("", encoding="utf-8")
    diagnostics = check_file_links(
        {"design": "target"},
        {"properties": {"design": _link_schema("bundle-relative")}},
        tmp_path / "source.md",
        bundle_root=tmp_path,
    )
    assert [diagnostic.code for diagnostic in diagnostics] == ["E10"]


def test_bundle_relative_stem_rejects_symlink_escape(tmp_path: Path) -> None:
    """Appending .md never allows a symlink to escape the bundle root."""
    import pytest

    bundle = tmp_path / "knowledge"
    bundle.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("", encoding="utf-8")
    try:
        (bundle / "escape.md").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    diagnostics = check_file_links(
        {"evidence": "escape"},
        {"properties": {"evidence": _link_schema("bundle-relative-stem")}},
        bundle / "source.md",
        bundle_root=bundle,
    )
    assert [diagnostic.code for diagnostic in diagnostics] == ["E10"]
    assert "escapes" in diagnostics[0].message


def test_check_file_links_walks_all_of_and_array_items(tmp_path: Path) -> None:
    """Annotations in composed schemas and array items resolve their targets."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    document = bundle / "requirements" / "SwRS-1.md"
    document.parent.mkdir()
    document.write_text("---\ntype: SwRS\n---\n", encoding="utf-8")
    (bundle / "StRS-1.md").write_text("---\ntype: StRS\n---\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "feature.py").write_text("", encoding="utf-8")

    schema = {
        "allOf": [
            {
                "type": "object",
                "properties": {
                    "derives_from": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "x-okf-link": {
                                "resolution": "filename-stem",
                                "syntax": "plain",
                            },
                        },
                    }
                },
            },
            {
                "type": "object",
                "properties": {
                    "implemented_in_files": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "x-okf-link": {
                                "resolution": "project-relative",
                                "syntax": "plain",
                            },
                        },
                    }
                },
            },
        ]
    }

    assert (
        check_file_links(
            {
                "derives_from": ["StRS-1"],
                "implemented_in_files": ["src/feature.py"],
            },
            schema,
            document,
            bundle_root=bundle,
            project_root=tmp_path,
        )
        == []
    )


def test_check_file_links_parses_wikilink_fragments_and_aliases(tmp_path: Path) -> None:
    """Wikilink fragments and labels do not affect file-target resolution."""
    target = tmp_path / "target.md"
    target.write_text("# Heading\n", encoding="utf-8")
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "wikilink"},
            }
        },
    }

    assert check_file_links({"source": "[[target.md#Heading|read this]]"}, schema, document) == []


def test_check_file_links_supports_all_resolution_modes(tmp_path: Path) -> None:
    """Each resolution mode uses its specified root and exact matching rule."""
    bundle = tmp_path / "bundle"
    document = bundle / "docs" / "source.md"
    document.parent.mkdir(parents=True)
    document.write_text("", encoding="utf-8")
    (bundle / "adjacent.md").write_text("", encoding="utf-8")
    (bundle / "notes").mkdir()
    (bundle / "notes" / "target.md").write_text("", encoding="utf-8")
    (bundle / "Requirement-1.md").write_text("", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "feature.py").write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "document": _link_schema("document-relative"),
            "bundle": _link_schema("bundle-relative"),
            "project": _link_schema("project-relative"),
            "stem": _link_schema("filename-stem"),
        },
    }

    assert (
        check_file_links(
            {
                "document": "../adjacent.md",
                "bundle": "notes/target.md",
                "project": "src/feature.py",
                "stem": "Requirement-1",
            },
            schema,
            document,
            bundle_root=bundle,
            project_root=tmp_path,
        )
        == []
    )


def test_check_file_links_supports_wikilink_labels_and_fragments(tmp_path: Path) -> None:
    """File checks ignore both heading/block fragments and display labels."""
    target = tmp_path / "target.md"
    target.write_text("", encoding="utf-8")
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "links": {
                "type": "array",
                "items": _link_schema("document-relative", "wikilink"),
            }
        },
    }

    assert (
        check_file_links(
            {
                "links": [
                    "[[target.md|label]]",
                    "[[target.md#^block|label]]",
                    "[[target.md#heading]]",
                ]
            },
            schema,
            document,
        )
        == []
    )


def test_check_file_links_traverses_tuple_prefix_and_union_schemas(tmp_path: Path) -> None:
    """Tuple, prefix, and union schema branches all apply their annotations."""
    for name in ("one.md", "two.md", "three.md", "four.md", "five.md"):
        (tmp_path / name).write_text("", encoding="utf-8")
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    link = _link_schema("document-relative")
    schema = {
        "type": "object",
        "properties": {
            "tuple": {"type": "array", "items": [link, link]},
            "prefix": {"type": "array", "prefixItems": [link]},
            "any": {"anyOf": [link, {"type": "string"}]},
            "one": {"oneOf": [{"type": "string"}, link]},
            "ignored": None,
        },
    }

    assert (
        check_file_links(
            {
                "tuple": ["one.md", "two.md"],
                "prefix": ["three.md"],
                "any": "four.md",
                "one": "five.md",
                "ignored": "not checked",
            },
            schema,
            document,
        )
        == []
    )


def test_check_file_links_applies_items_only_after_prefix_items(tmp_path: Path) -> None:
    """Draft 2020 ``items`` applies only to values after ``prefixItems``."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    (tmp_path / "existing.md").write_text("", encoding="utf-8")
    schema = {
        "type": "array",
        "prefixItems": [{"type": "integer"}],
        "items": _link_schema("document-relative"),
    }

    assert check_file_links([7, "existing.md"], schema, document) == []


def test_check_file_links_only_traverses_applicable_union_branches(tmp_path: Path) -> None:
    """An annotated string branch does not inspect a value accepted as an integer."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "anyOf": [
                    {"type": "integer"},
                    _link_schema("document-relative"),
                ]
            }
        },
    }

    assert check_file_links({"value": 42}, schema, document) == []
    diagnostics = check_file_links({"value": "missing.md"}, schema, document)

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E10"


def test_check_file_links_follows_local_refs_through_recursive_schemas(tmp_path: Path) -> None:
    """Local definitions apply annotations at nested recursive values."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    (tmp_path / "target.md").write_text("", encoding="utf-8")
    schema = {
        "$defs": {
            "link": _link_schema("document-relative"),
            "node": {
                "type": "object",
                "properties": {
                    "target": {"$ref": "#/$defs/link"},
                    "next": {"$ref": "#/$defs/node"},
                },
            },
        },
        "$ref": "#/$defs/node",
    }

    diagnostics = check_file_links(
        {"target": "target.md", "next": {"target": "missing.md"}},
        schema,
        document,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].field_path == "next.target"
    assert diagnostics[0].code == "E10"

    cyclic_schema = {"$defs": {"node": {"$ref": "#/$defs/node"}}, "$ref": "#/$defs/node"}
    assert check_file_links({}, cyclic_schema, document) == []

    deep_defs: dict[str, object] = {"link-129": _link_schema("document-relative")}
    for index in range(129):
        deep_defs[f"link-{index}"] = {"$ref": f"#/$defs/link-{index + 1}"}
    deep_schema = {"$defs": deep_defs, "$ref": "#/$defs/link-0"}
    assert check_file_links("target.md", deep_schema, document) == []
    deep_missing = check_file_links("missing.md", deep_schema, document)
    assert len(deep_missing) == 1
    assert deep_missing[0].code == "E10"
    assert "missing.md" in deep_missing[0].message


def test_check_file_links_deduplicates_composed_link_diagnostics(tmp_path: Path) -> None:
    """Repeated annotations in composed profiles report a missing target once."""
    schema = {
        "type": "object",
        "allOf": [
            {"properties": {"target": _link_schema("document-relative")}},
            {"properties": {"target": _link_schema("document-relative")}},
        ],
    }

    diagnostics = check_file_links({"target": "missing.md"}, schema, tmp_path / "source.md")

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E10"
    assert diagnostics[0].field_path == "target"


def test_check_file_links_rejects_absolute_filename_stems(tmp_path: Path) -> None:
    """A filename-stem annotation does not permit an absolute target."""
    schema = {"properties": {"target": _link_schema("filename-stem")}}

    diagnostics = check_file_links(
        {"target": str(tmp_path / "Target")},
        schema,
        tmp_path / "source.md",
        bundle_root=tmp_path,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E10"
    assert "absolute target" in diagnostics[0].message


def test_check_file_links_skips_unresolvable_roots(tmp_path: Path, monkeypatch) -> None:
    """Filesystem resolution errors leave explicit unavailable-root diagnostics."""
    schema = {
        "properties": {
            "bundle": _link_schema("bundle-relative"),
            "project": _link_schema("project-relative"),
        }
    }

    def unavailable_path(path: Path, *args, **kwargs) -> Path:
        raise OSError("Filesystem is unavailable")

    monkeypatch.setattr(Path, "resolve", unavailable_path)
    diagnostics = check_file_links(
        {"bundle": "target.md", "project": "src/target.py"},
        schema,
        tmp_path / "source.md",
        bundle_root=tmp_path,
        project_root=tmp_path,
    )

    assert len(diagnostics) == 2
    assert all(diagnostic.code == "W15" for diagnostic in diagnostics)
    assert all("root is unavailable" in diagnostic.message for diagnostic in diagnostics)


def test_check_file_links_skips_unresolvable_stem_candidates(tmp_path: Path, monkeypatch) -> None:
    """A stem whose candidate cannot be resolved is not reported as checked."""
    target = tmp_path / "Target.md"
    target.write_text("", encoding="utf-8")
    original_resolve = Path.resolve

    def resolve_candidate(path: Path, *args, **kwargs) -> Path:
        if path == target:
            raise OSError("Candidate is unavailable")
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_candidate)
    schema = {"properties": {"target": _link_schema("filename-stem")}}
    diagnostics = check_file_links(
        {"target": "Target"}, schema, tmp_path / "source.md", bundle_root=tmp_path
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "W15"
    assert "workspace may be unavailable" in diagnostics[0].message


def test_check_file_links_reports_invalid_annotations_and_values(tmp_path: Path) -> None:
    """Invalid metadata, values, wikilinks, and empty wikilinks are errors."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "resolution": {
                "type": "string",
                "x-okf-link": {"resolution": "unknown", "syntax": "plain"},
            },
            "syntax": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "unknown"},
            },
            "resolution_type": {
                "type": "string",
                "x-okf-link": {"resolution": [], "syntax": "plain"},
            },
            "syntax_type": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": {}},
            },
            "value": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "plain"},
            },
            "malformed": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "wikilink"},
            },
            "empty": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "wikilink"},
            },
        },
    }

    diagnostics = check_file_links(
        {
            "resolution": "target.md",
            "syntax": "target.md",
            "resolution_type": "target.md",
            "syntax_type": "target.md",
            "value": 42,
            "malformed": "target.md",
            "empty": "[[]]",
        },
        schema,
        document,
    )

    assert len(diagnostics) == 7
    assert all(diagnostic.code == "E10" for diagnostic in diagnostics)
    assert "resolution must be one of" in diagnostics[0].message
    assert "syntax must be one of" in diagnostics[1].message
    assert "resolution must be one of" in diagnostics[2].message
    assert "syntax must be one of" in diagnostics[3].message
    assert "value must be a string" in diagnostics[4].message
    assert "wikilink value must use" in diagnostics[5].message
    assert "wikilink target is empty" in diagnostics[6].message


def test_check_file_links_reports_missing_exact_targets(tmp_path: Path) -> None:
    """A missing target is an error when its root is available."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {"type": "object", "properties": {"target": _link_schema("document-relative")}}

    diagnostics = check_file_links({"target": "missing.md"}, schema, document)

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "E10"
    assert "does not resolve to a file" in diagnostics[0].message


def test_check_file_links_skips_unavailable_roots_and_unresolved_stems(tmp_path: Path) -> None:
    """Unavailable workspace roots produce explicit warnings instead of errors."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "bundle": _link_schema("bundle-relative"),
            "project": _link_schema("project-relative"),
            "stem": _link_schema("filename-stem"),
        },
    }

    diagnostics = check_file_links(
        {"bundle": "missing.md", "project": "src/missing.py", "stem": "Unknown"},
        schema,
        document,
    )

    assert len(diagnostics) == 3
    assert all(diagnostic.code == "W15" for diagnostic in diagnostics)
    assert all(diagnostic.severity == "warning" for diagnostic in diagnostics)
    assert all("Skipped file-link check" in diagnostic.message for diagnostic in diagnostics)


def test_check_file_links_reports_ambiguous_and_case_sensitive_stems(tmp_path: Path) -> None:
    """Stem lookup is recursive, case-sensitive, and rejects ambiguity."""
    bundle = tmp_path / "bundle"
    (bundle / "one").mkdir(parents=True)
    (bundle / "two").mkdir()
    (bundle / "one" / "Target.md").write_text("", encoding="utf-8")
    (bundle / "two" / "Target.md").write_text("", encoding="utf-8")
    document = bundle / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {"type": "object", "properties": {"target": _link_schema("filename-stem")}}

    ambiguous = check_file_links({"target": "Target"}, schema, document, bundle_root=bundle)
    case_mismatch = check_file_links({"target": "target"}, schema, document, bundle_root=bundle)

    assert ambiguous[0].code == "E10"
    assert "ambiguous" in ambiguous[0].message
    assert case_mismatch[0].code == "W15"

    (bundle / "outside.md").symlink_to(tmp_path / "outside.md")
    (tmp_path / "outside.md").write_text("", encoding="utf-8")
    escaped = check_file_links({"target": "outside"}, schema, document, bundle_root=bundle)

    assert escaped[0].code == "W15"


def test_check_file_links_does_not_fall_back_to_frontmatter_ids(tmp_path: Path) -> None:
    """A frontmatter ID cannot satisfy an unresolved filename stem."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    target = bundle / "Readable title.md"
    target.write_text("---\nid: REQ-1\n---\n", encoding="utf-8")
    document = bundle / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {"type": "object", "properties": {"target": _link_schema("filename-stem")}}

    diagnostics = check_file_links({"target": "REQ-1"}, schema, document, bundle_root=bundle)

    assert diagnostics[0].code == "W15"
    assert "REQ-1" in diagnostics[0].message


def test_check_file_links_rejects_absolute_and_root_escaping_targets(tmp_path: Path) -> None:
    """Bundle/project roots reject absolute paths, ``..`` escapes, and symlink escapes."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("", encoding="utf-8")
    (bundle / "linked.txt").symlink_to(outside)
    document = bundle / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {
            "absolute": _link_schema("bundle-relative"),
            "windows": _link_schema("bundle-relative"),
            "parent": _link_schema("bundle-relative"),
            "symlink": _link_schema("bundle-relative"),
        },
    }

    diagnostics = check_file_links(
        {
            "absolute": str(outside),
            "windows": r"C:\outside.txt",
            "parent": "../outside.txt",
            "symlink": "linked.txt",
        },
        schema,
        document,
        bundle_root=bundle,
    )

    assert len(diagnostics) == 4
    assert all(diagnostic.code == "E10" for diagnostic in diagnostics)
    assert sum("absolute target" in diagnostic.message for diagnostic in diagnostics) == 2
    assert sum("escapes" in diagnostic.message for diagnostic in diagnostics) == 2


def test_check_file_links_skips_document_relative_check_for_missing_parent(tmp_path: Path) -> None:
    """A standalone document outside an available directory reports W15."""
    schema = {
        "type": "object",
        "properties": {"target": _link_schema("document-relative")},
    }

    diagnostics = check_file_links(
        {"target": "target.md"},
        schema,
        tmp_path / "missing" / "source.md",
    )

    assert diagnostics[0].code == "W15"


def test_check_file_links_uses_git_root_but_not_current_working_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Project links use the document's Git root and never an unrelated cwd."""
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    (repository / "src").mkdir()
    (repository / "src" / "feature.py").write_text("", encoding="utf-8")
    document = repository / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {"type": "object", "properties": {"target": _link_schema("project-relative")}}

    assert check_file_links({"target": "src/feature.py"}, schema, document) == []

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    (unrelated / "src").mkdir()
    (unrelated / "src" / "feature.py").write_text("", encoding="utf-8")
    monkeypatch.chdir(unrelated)
    external_document = tmp_path / "external" / "source.md"
    external_document.parent.mkdir()
    external_document.write_text("", encoding="utf-8")
    diagnostics = check_file_links({"target": "src/feature.py"}, schema, external_document)

    assert diagnostics[0].code == "W15"


def test_check_file_links_reports_malformed_annotations(tmp_path: Path) -> None:
    """Malformed schema metadata is diagnosed instead of raising or passing."""
    document = tmp_path / "source.md"
    document.write_text("", encoding="utf-8")
    schema = {
        "type": "object",
        "properties": {"target": {"type": "string", "x-okf-link": None}},
    }

    diagnostics = check_file_links({"target": "target.md"}, schema, document)

    assert diagnostics[0].code == "E10"
    assert "must be an object" in diagnostics[0].message


def test_normal_schema_validation_ignores_file_link_annotation() -> None:
    """The annotation remains non-validating when optional checking is disabled."""
    from okf_schema.validator import validate_against_schema

    schema = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "x-okf-link": {"resolution": "document-relative", "syntax": "plain"},
            }
        },
    }

    assert validate_against_schema({"target": "missing.md"}, schema, "concept") == []


def test_validate_bundle_checks_links_only_when_opted_in(tmp_path: Path) -> None:
    """The generic API exposes opt-in checking without changing default validation."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "source.md").write_text(
        "---\ntype: concept\ntitle: Source\ndescription: Source\ntarget: missing.md\n---\n",
        encoding="utf-8",
    )
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\nproperties:\n  type: {type: string}\n  target:\n"
        "    type: string\n    x-okf-link: {resolution: document-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    assert not any(finding.code == "E10" for finding in validate_bundle(bundle, schemas).errors)
    report = validate_bundle(bundle, schemas, check_links=True)

    assert any(finding.code == "E10" for finding in report.errors)


def test_malformed_link_annotation_is_reported_by_api_and_cli(tmp_path: Path) -> None:
    """Malformed annotation choices produce E10 instead of an unhashable-value crash."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    document = bundle / "source.md"
    document.write_text(
        "---\ntype: concept\ntitle: Source\ndescription: Source\ntarget: target.md\n---\n",
        encoding="utf-8",
    )
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\nproperties:\n  type: {type: string}\n  target:\n"
        "    type: string\n    x-okf-link:\n      resolution: []\n      syntax: plain\n",
        encoding="utf-8",
    )

    report = validate_bundle(bundle, schemas, check_links=True)
    result = CliRunner().invoke(
        cli,
        [
            "validate-md",
            "--input",
            str(document),
            "--schemas-dir",
            str(schemas),
            "--check-links",
        ],
    )

    assert any(finding.code == "E10" for finding in report.errors)
    assert result.exit_code == 1
    assert "E10" in result.output
    assert "unhashable" not in result.output


def test_local_link_refs_work_through_generic_api_and_cli(tmp_path: Path) -> None:
    """Generic schema loading preserves local link annotations for API and CLI checks."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    document = bundle / "source.md"
    document.write_text(
        "---\ntype: concept\ntitle: Source\ndescription: Source\ntarget: missing.md\n---\n",
        encoding="utf-8",
    )
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\n$defs:\n  link:\n    type: string\n    x-okf-link:\n"
        "      resolution: document-relative\n      syntax: plain\nproperties:\n"
        "  type: {type: string}\n  target:\n    $ref: '#/$defs/link'\n",
        encoding="utf-8",
    )

    report = validate_bundle(bundle, schemas, check_links=True)
    result = CliRunner().invoke(
        cli,
        [
            "validate-md",
            "--input",
            str(document),
            "--schemas-dir",
            str(schemas),
            "--check-links",
        ],
    )

    assert any(finding.code == "E10" for finding in report.errors)
    assert result.exit_code == 1
    assert "E10" in result.output


def test_array_pointer_link_refs_work_through_generic_api_and_cli(tmp_path: Path) -> None:
    """API and CLI checks follow refs through arrays and escaped pointer tokens."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    document = bundle / "source.md"
    document.write_text(
        "---\ntype: concept\ntitle: Source\ndescription: Source\ntarget: missing.md\n---\n",
        encoding="utf-8",
    )
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\n$defs:\n  'link/name~v':\n    allOf:\n"
        "      - type: string\n        x-okf-link: {resolution: document-relative, syntax: plain}\n"
        "properties:\n  type: {type: string}\n  target:\n"
        "    $ref: '#/$defs/link~1name~0v/allOf/0'\n",
        encoding="utf-8",
    )

    report = validate_bundle(bundle, schemas, check_links=True)
    result = CliRunner().invoke(
        cli,
        [
            "validate-md",
            "--input",
            str(document),
            "--schemas-dir",
            str(schemas),
            "--check-links",
        ],
    )

    assert any(finding.code == "E10" for finding in report.errors)
    assert result.exit_code == 1
    assert "E10" in result.output


def test_generic_validate_md_cli_accepts_link_check_options(tmp_path: Path) -> None:
    """The generic CLI can opt into target checking and report link errors."""
    document = tmp_path / "source.md"
    document.write_text(
        "---\ntype: concept\ntitle: Source\ndescription: Source\ntarget: missing.md\n---\n",
        encoding="utf-8",
    )
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\nproperties:\n  type: {type: string}\n  target:\n"
        "    type: string\n    x-okf-link: {resolution: document-relative, syntax: plain}\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "validate-md",
            "--input",
            str(document),
            "--schemas-dir",
            str(schemas),
            "--check-links",
        ],
    )

    assert result.exit_code == 1
    assert "E10" in result.output


def test_okfreq_cli_accepts_link_check_options(tmp_path: Path) -> None:
    """The okfreq validator exposes opt-in link checking without fatal skips."""
    root = init_requirements(tmp_path)
    (root / "tiers" / "strs" / "StRS-default-001.md").write_text(
        "---\ntype: StRS\nid: StRS-default-001\nuuid: "
        "00000000-0000-4000-8000-000000000001\ntitle: Parent\ndescription: Parent\n"
        "project: demo\nscope: default\nlifecycle: draft\norigin: native\ntier: StRS\n"
        "user_need: Need\n---\n\nThe parent SHALL exist.\n",
        encoding="utf-8",
    )
    (root / "tiers" / "swrs" / "SwRS-default-001.md").write_text(
        "---\ntype: SwRS\nid: SwRS-default-001\nuuid: "
        "00000000-0000-4000-8000-000000000002\ntitle: Child\ndescription: Child\n"
        "project: demo\nscope: default\nlifecycle: draft\norigin: native\ntier: SwRS\n"
        "derives_from: [StRS-default-001]\nannotation_exemption: false\n"
        "implemented_in_files: [src/missing.py]\ntested_in_files: []\n---\n"
        "\nThe child SHALL exist.\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    without_check = runner.invoke(okfreq, ["validate", str(root)])
    with_check = runner.invoke(
        okfreq,
        [
            "validate",
            str(root),
            "--json",
            "--check-links",
            "--project-root",
            str(tmp_path),
        ],
    )
    lint_with_unavailable_root = runner.invoke(okfreq, ["lint", str(root), "--check-links"])

    assert without_check.exit_code == 0, without_check.output
    assert with_check.exit_code == 1
    assert "E10" in with_check.output
    assert lint_with_unavailable_root.exit_code == 0, lint_with_unavailable_root.output
    assert "W15" in lint_with_unavailable_root.output


def test_generated_okfreq_schemas_and_link_check_preserve_requirement_semantics(
    tmp_path: Path,
) -> None:
    """The live initializer annotates relationships and source/test arrays."""
    root = init_requirements(tmp_path)
    schemas = load_schema_database(root / "tiers" / "_schema")
    base = schemas["base"]["properties"]
    swrs = schemas["swrs"]["allOf"][1]["properties"]

    assert base["derives_from"]["items"]["x-okf-link"] == {
        "resolution": "filename-stem",
        "syntax": "plain",
    }
    assert swrs["implemented_in_files"]["items"]["x-okf-link"] == {
        "resolution": "project-relative",
        "syntax": "plain",
    }
    assert "external_id" not in base

    (root / "tiers" / "strs" / "StRS-default-001.md").write_text(
        "---\ntype: StRS\nid: StRS-default-001\nuuid: "
        "00000000-0000-4000-8000-000000000001\ntitle: Parent\ndescription: Parent\n"
        "project: demo\nscope: default\nlifecycle: draft\norigin: native\ntier: StRS\n"
        "user_need: Need\nexternal_id: EXT-1\n---\n\nThe parent SHALL exist.\n",
        encoding="utf-8",
    )
    swrs = root / "tiers" / "swrs" / "SwRS-default-001.md"
    swrs.write_text(
        "---\ntype: SwRS\nid: SwRS-default-001\nuuid: "
        "00000000-0000-4000-8000-000000000002\ntitle: Child\ndescription: Child\n"
        "project: demo\nscope: default\nlifecycle: draft\norigin: native\ntier: SwRS\n"
        "derives_from: [StRS-default-001]\nannotation_exemption: false\n"
        "implemented_in_files: [src/feature.py]\ntested_in_files: [tests/test_feature.py]\n"
        "external_id: EXT-2\n---\n\nThe child SHALL exist.\n",
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "feature.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "test_feature.py").write_text("", encoding="utf-8")

    assert validate_requirements(root, check_links=True, project_root=tmp_path) == []
    assert graph(root)["derives_from"]["SwRS-default-001"] == ["StRS-default-001"]
    assert "EXT-2" in swrs.read_text(encoding="utf-8")
