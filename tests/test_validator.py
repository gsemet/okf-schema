"""Tests for the OKF bundle validator."""

from __future__ import annotations

from pathlib import Path

from okf_schema.validator import (
    _has_block_lists,
    _has_nested_lists,
    load_schema_database,
    validate_against_schema,
    validate_bundle,
    validate_concept,
    validate_index,
    validate_log,
)

FIXTURES = Path(__file__).parent / "fixtures"
BUNDLE_FIXTURES = FIXTURES / "bundle"
SCHEMA_FIXTURES = FIXTURES / "schema"


# ---------------------------------------------------------------------------
# load_schema_database
# ---------------------------------------------------------------------------


class TestLoadSchemaDatabase:
    """Tests for load_schema_database."""

    def test_loads_json_schema(self) -> None:
        """Loads .schema.json files."""
        schemas = load_schema_database(SCHEMA_FIXTURES)
        assert "concept" in schemas
        assert schemas["concept"]["type"] == "object"

    def test_loads_yaml_schema(self) -> None:
        """Loads .schema.yaml files."""
        schemas = load_schema_database(SCHEMA_FIXTURES)
        assert "pattern" in schemas
        assert schemas["pattern"]["type"] == "object"

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Returns empty dict for empty directory."""
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        """Returns empty dict for non-existent directory."""
        schemas = load_schema_database(tmp_path / "missing")
        assert schemas == {}

    def test_skips_non_schema_files(self, tmp_path: Path) -> None:
        """Ignores files without .schema.{json,yaml} suffix."""
        (tmp_path / "random.txt").write_text("hello")
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_skips_invalid_json(self, tmp_path: Path) -> None:
        """Skips files with invalid JSON."""
        (tmp_path / "bad.schema.json").write_text("not json")
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_skips_invalid_json5(self, tmp_path: Path) -> None:
        """Skips files with invalid JSON5."""
        (tmp_path / "bad.schema.json5").write_text("not json5")
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_skips_invalid_yaml(self, tmp_path: Path) -> None:
        """Skips files with invalid YAML."""
        (tmp_path / "bad.schema.yaml").write_text("{not yaml")
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_skips_non_dict_yaml(self, tmp_path: Path) -> None:
        """Skips YAML files that parse to non-dict."""
        (tmp_path / "bad.schema.yaml").write_text("- a\n- b\n")
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_skips_oserror(self, tmp_path: Path) -> None:
        """Skips files that raise OSError on read."""
        # Create a directory with .schema.json suffix (not a file)
        (tmp_path / "bad.schema.json").mkdir()
        schemas = load_schema_database(tmp_path)
        assert schemas == {}

    def test_resolves_json_ref(self, tmp_path: Path) -> None:
        """Inlines a $ref pointing to a JSON file."""
        base = tmp_path / "base.json"
        base.write_text('{"type": "object", "properties": {"name": {"type": "string"}}}')
        schema_file = tmp_path / "concept.schema.json"
        schema_file.write_text('{"$ref": "base.json", "required": ["name"]}')
        schemas = load_schema_database(tmp_path)
        assert "concept" in schemas
        assert schemas["concept"]["type"] == "object"
        assert "properties" in schemas["concept"]
        assert "required" in schemas["concept"]

    def test_resolves_yaml_ref(self, tmp_path: Path) -> None:
        """Inlines a $ref pointing to a YAML file."""
        base = tmp_path / "common.yaml"
        base.write_text("type: object\nproperties:\n  id:\n    type: integer\n")
        schema_file = tmp_path / "item.schema.yaml"
        schema_file.write_text("$ref: common.yaml\n")
        schemas = load_schema_database(tmp_path)
        assert "item" in schemas
        assert schemas["item"]["type"] == "object"
        assert "properties" in schemas["item"]

    def test_resolves_nested_ref(self, tmp_path: Path) -> None:
        """Inlines $ref nested inside properties."""
        base = tmp_path / "defs.json"
        base.write_text('{"type": "string", "minLength": 1}')
        schema_file = tmp_path / "doc.schema.json"
        schema_file.write_text('{"type": "object", "properties": {"title": {"$ref": "defs.json"}}}')
        schemas = load_schema_database(tmp_path)
        assert "doc" in schemas
        assert schemas["doc"]["properties"]["title"]["type"] == "string"

    def test_keeps_unresolvable_ref(self, tmp_path: Path) -> None:
        """Preserves $ref when the target file does not exist."""
        schema_file = tmp_path / "concept.schema.json"
        schema_file.write_text('{"$ref": "missing.json"}')
        schemas = load_schema_database(tmp_path)
        assert "concept" in schemas
        assert schemas["concept"]["$ref"] == "missing.json"

    def test_resolves_ref_in_array_items(self, tmp_path: Path) -> None:
        """Inlines $ref inside array items."""
        base = tmp_path / "tag.yaml"
        base.write_text("type: string\nminLength: 1\n")
        schema_file = tmp_path / "doc.schema.yaml"
        schema_file.write_text(
            "type: object\nproperties:\n  tags:\n    type: array\n"
            "    items:\n      $ref: tag.yaml\n"
        )
        schemas = load_schema_database(tmp_path)
        assert "doc" in schemas
        assert schemas["doc"]["properties"]["tags"]["items"]["type"] == "string"

    def test_resolves_extensionless_ref(self, tmp_path: Path) -> None:
        """Discovers $ref target when no extension is given."""
        base = tmp_path / "common.yaml"
        base.write_text("type: object\nproperties:\n  name:\n    type: string\n")
        schema_file = tmp_path / "doc.schema.json"
        schema_file.write_text('{"$ref": "common", "required": ["name"]}')
        schemas = load_schema_database(tmp_path)
        assert "doc" in schemas
        assert schemas["doc"]["type"] == "object"
        assert "required" in schemas["doc"]

    def test_resolves_extensionless_ref_json5(self, tmp_path: Path) -> None:
        """Discovers $ref target as .json5 when no extension is given."""
        base = tmp_path / "defs.json5"
        base.write_text('{type: "string", minLength: 1}')
        schema_file = tmp_path / "doc.schema.json"
        schema_file.write_text('{"$ref": "defs", "required": ["id"]}')
        schemas = load_schema_database(tmp_path)
        assert "doc" in schemas
        assert schemas["doc"]["type"] == "string"
        assert "required" in schemas["doc"]

    def test_resolves_extensionless_ref_yml(self, tmp_path: Path) -> None:
        """Discovers $ref target as .yml when no extension is given."""
        base = tmp_path / "common.yml"
        base.write_text("type: object\nproperties:\n  id:\n    type: integer\n")
        schema_file = tmp_path / "doc.schema.json"
        schema_file.write_text('{"$ref": "common", "required": ["id"]}')
        schemas = load_schema_database(tmp_path)
        assert "doc" in schemas
        assert schemas["doc"]["type"] == "object"
        assert "required" in schemas["doc"]

    def test_loads_schema_yml_extension(self, tmp_path: Path) -> None:
        """Loads .schema.yml files alongside .schema.yaml."""
        (tmp_path / "item.schema.yml").write_text(
            "type: object\nproperties:\n  id:\n    type: integer\n"
        )
        schemas = load_schema_database(tmp_path)
        assert "item" in schemas
        assert schemas["item"]["type"] == "object"


# ---------------------------------------------------------------------------
# validate_against_schema
# ---------------------------------------------------------------------------


class TestValidateAgainstSchema:
    """Tests for validate_against_schema."""

    def test_valid_frontmatter(self) -> None:
        """Returns empty list for conformant frontmatter."""
        schema = {
            "type": "object",
            "properties": {"type": {"type": "string"}},
            "required": ["type"],
        }
        errors = validate_against_schema({"type": "concept"}, schema, "concept")
        assert errors == []

    def test_missing_required_field(self) -> None:
        """Reports missing required field."""
        schema = {
            "type": "object",
            "properties": {"type": {"type": "string"}},
            "required": ["type"],
        }
        errors = validate_against_schema({}, schema, "concept")
        assert len(errors) == 1
        assert "type" in errors[0]

    def test_wrong_type(self) -> None:
        """Reports type mismatch."""
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
        }
        errors = validate_against_schema({"count": "not an int"}, schema, "test")
        assert len(errors) == 1
        assert "integer" in errors[0]

    def test_validator_exception(self) -> None:
        """Handles exception from Draft202012Validator."""
        # Invalid schema (not a dict) will cause validator construction to fail
        errors = validate_against_schema({}, "not-a-schema", "test")
        assert len(errors) == 1
        assert "Schema validator error" in errors[0]


# ---------------------------------------------------------------------------
# _has_nested_lists
# ---------------------------------------------------------------------------


class TestHasNestedLists:
    """Tests for _has_nested_lists helper."""

    def test_flat_list(self) -> None:
        """Flat list is not nested."""
        assert _has_nested_lists(["a", "b", "c"]) is False

    def test_nested_list(self) -> None:
        """Nested list is detected."""
        assert _has_nested_lists([["a", "b"], "c"]) is True

    def test_deeply_nested(self) -> None:
        """Deeply nested list is detected."""
        assert _has_nested_lists({"tags": [["a"], "b"]}) is True

    def test_dict_without_lists(self) -> None:
        """Dict with scalar values is fine."""
        assert _has_nested_lists({"title": "Test", "count": 5}) is False

    def test_dict_with_flat_list(self) -> None:
        """Dict with flat list is fine."""
        assert _has_nested_lists({"tags": ["a", "b"]}) is False

    def test_scalar(self) -> None:
        """Scalar values are fine."""
        assert _has_nested_lists("hello") is False
        assert _has_nested_lists(42) is False


# ---------------------------------------------------------------------------
# _has_block_lists
# ---------------------------------------------------------------------------


class TestHasBlockLists:
    """Tests for _has_block_lists helper."""

    def test_inline_list(self) -> None:
        """Inline list is not block-style."""
        fm = "tags: [a, b, c]\n"
        assert _has_block_lists(fm) is False

    def test_block_list(self) -> None:
        """Block list is detected."""
        fm = "tags:\n  - a\n  - b\n"
        assert _has_block_lists(fm) is True

    def test_mixed_inline_and_block(self) -> None:
        """Mixed: block list is detected even with inline present."""
        fm = "tags:\n  - a\n  - b\nother: [x, y]\n"
        assert _has_block_lists(fm) is True

    def test_no_lists(self) -> None:
        """No lists at all."""
        fm = "title: Test\ncount: 5\n"
        assert _has_block_lists(fm) is False

    def test_invalid_yaml(self) -> None:
        """Invalid YAML returns False (graceful)."""
        fm = "title: : bad:\n"
        assert _has_block_lists(fm) is False


# ---------------------------------------------------------------------------
# validate_concept
# ---------------------------------------------------------------------------


class TestValidateConcept:
    """Tests for validate_concept."""

    def test_valid_concept_no_warnings(self, tmp_path: Path) -> None:
        """Valid concept produces no errors or warnings."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "# Test\n"
        )
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert report.is_conformant is True
        assert report.warnings == []

    def test_e1_no_frontmatter(self, tmp_path: Path) -> None:
        """E1: file without frontmatter."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("# No Frontmatter\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "E1" for f in report.errors)

    def test_e1_unparseable_yaml(self, tmp_path: Path) -> None:
        """E1: unparseable YAML frontmatter."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: : bad:\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "E1" for f in report.errors)

    def test_e2_missing_type(self, tmp_path: Path) -> None:
        """E2: missing type field."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "E2" for f in report.errors)

    def test_e2_empty_type(self, tmp_path: Path) -> None:
        """E2: empty type field."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text('---\ntitle: Test\ntype: ""\n---\n\n# Body\n')
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "E2" for f in report.errors)

    def test_e4_schema_validation_failure(self, tmp_path: Path) -> None:
        """E4: frontmatter fails schema validation."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\n---\n\n# Body\n")
        schemas = {
            "concept": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "const": "concept"},
                    "required_field": {"type": "string"},
                },
                "required": ["required_field"],
            }
        }
        report = Report()
        validate_concept(path, report, tmp_path, schemas)
        assert any(f.code == "E4" for f in report.errors)

    def test_e5_unflatten_list(self, tmp_path: Path) -> None:
        """E5: nested lists in frontmatter."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text(
            "---\ntitle: Test\ntype: concept\ntags:\n  - [a, b]\n  - c\n---\n\n# Body\n"
        )
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "E5" for f in report.errors)

    def test_w1_missing_title(self, tmp_path: Path) -> None:
        """W1: missing title field."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ndescription: A desc\ntype: concept\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "W1" and "title" in f.message for f in report.warnings)

    def test_w1_missing_description(self, tmp_path: Path) -> None:
        """W1: missing description field."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "W1" and "description" in f.message for f in report.warnings)

    def test_w2_broken_link(self, tmp_path: Path) -> None:
        """W2: broken internal link."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\n---\n\n[link](./missing.md)\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "W2" for f in report.warnings)

    def test_w3_missing_timestamp(self, tmp_path: Path) -> None:
        """W3: missing timestamp field."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "W3" for f in report.warnings)

    def test_w6_missing_schema(self, tmp_path: Path) -> None:
        """W6: type declared but no schema found."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: unknown\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, {})
        assert any(f.code == "W6" for f in report.warnings)

    def test_no_w6_when_schemas_none(self, tmp_path: Path) -> None:
        """W6 is not emitted when schemas is None."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert not any(f.code == "W6" for f in report.warnings)

    def test_w7_block_list(self, tmp_path: Path) -> None:
        """W7: block-style list in frontmatter."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "tags:\n"
            "  - alpha\n"
            "  - beta\n"
            "---\n\n"
            "# Body\n"
        )
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert any(f.code == "W7" for f in report.warnings)

    def test_no_w7_inline_list(self, tmp_path: Path) -> None:
        """W7 is not emitted for inline lists."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "tags: [alpha, beta]\n"
            "---\n\n"
            "# Body\n"
        )
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert not any(f.code == "W7" for f in report.warnings)

    def test_no_w7_no_lists(self, tmp_path: Path) -> None:
        """W7 is not emitted when there are no lists at all."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: Test\ntype: concept\ntimestamp: 2024-01-01\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        assert not any(f.code == "W7" for f in report.warnings)

    def test_no_w7_invalid_yaml(self, tmp_path: Path) -> None:
        """W7 is not emitted when frontmatter YAML is invalid."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\ntitle: : bad:\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        # E1 is emitted for invalid YAML, not W7
        assert any(f.code == "E1" for f in report.errors)
        assert not any(f.code == "W7" for f in report.warnings)

    def test_no_w7_non_dict_yaml(self, tmp_path: Path) -> None:
        """W7 is not emitted when frontmatter parses to non-dict."""
        from okf_schema._internal.models import Report

        path = tmp_path / "concept.md"
        path.write_text("---\n- a\n- b\n---\n\n# Body\n")
        report = Report()
        validate_concept(path, report, tmp_path, None)
        # E1 is emitted for non-dict frontmatter, not W7
        assert any(f.code == "E1" for f in report.errors)
        assert not any(f.code == "W7" for f in report.warnings)


# ---------------------------------------------------------------------------
# validate_index
# ---------------------------------------------------------------------------


class TestValidateIndex:
    """Tests for validate_index."""

    def test_root_index_with_frontmatter_ok(self, tmp_path: Path) -> None:
        """Root index.md may have frontmatter."""
        from okf_schema._internal.models import Report

        path = tmp_path / "index.md"
        path.write_text("---\nokf_version: '0.1'\n---\n\n# Index\n")
        report = Report()
        validate_index(path, report, tmp_path)
        assert report.errors == []

    def test_non_root_index_with_frontmatter_e3(self, tmp_path: Path) -> None:
        """Non-root index.md with frontmatter triggers E3."""
        from okf_schema._internal.models import Report

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        path = subdir / "index.md"
        path.write_text("---\ntitle: Bad\n---\n\n# Index\n")
        report = Report()
        validate_index(path, report, tmp_path)
        assert any(f.code == "E3" for f in report.errors)

    def test_non_root_index_without_frontmatter_ok(self, tmp_path: Path) -> None:
        """Non-root index.md without frontmatter is fine."""
        from okf_schema._internal.models import Report

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        path = subdir / "index.md"
        path.write_text("# Index\n")
        report = Report()
        validate_index(path, report, tmp_path)
        assert report.errors == []


# ---------------------------------------------------------------------------
# validate_log
# ---------------------------------------------------------------------------


class TestValidateLog:
    """Tests for validate_log."""

    def test_log_with_frontmatter_e3(self, tmp_path: Path) -> None:
        """log.md with frontmatter triggers E3."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("---\ntitle: Bad\n---\n\n# Log\n")
        report = Report()
        validate_log(path, report)
        assert any(f.code == "E3" for f in report.errors)

    def test_log_without_frontmatter_ok(self, tmp_path: Path) -> None:
        """log.md without frontmatter is fine."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("# Log\n\n## 2024-01-15\n\n- Entry\n")
        report = Report()
        validate_log(path, report)
        assert report.errors == []

    def test_log_bad_date_w5(self, tmp_path: Path) -> None:
        """log.md with non-ISO date headings triggers W5."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("# Log\n\n## 2024/01/15\n\n- Entry\n")
        report = Report()
        validate_log(path, report)
        assert any(f.code == "W5" for f in report.warnings)

    def test_log_good_date_no_w5(self, tmp_path: Path) -> None:
        """log.md with ISO date headings does not trigger W5."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("# Log\n\n## 2024-01-15\n\n- Entry\n")
        report = Report()
        validate_log(path, report)
        assert not any(f.code == "W5" for f in report.warnings)

    def test_log_no_date_headings_no_w5(self, tmp_path: Path) -> None:
        """log.md without ## headings does not trigger W5."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("# Log\n\n- Entry\n")
        report = Report()
        validate_log(path, report)
        assert not any(f.code == "W5" for f in report.warnings)

    def test_log_valid_dates_no_w5(self, tmp_path: Path) -> None:
        """log.md with valid ISO dates has no W5."""
        from okf_schema._internal.models import Report

        path = tmp_path / "log.md"
        path.write_text("# Log\n\n## 2024-01-15\n\n- Entry\n\n## 2024-02-20\n\n- Entry 2\n")
        report = Report()
        validate_log(path, report)
        assert not any(f.code == "W5" for f in report.warnings)


# ---------------------------------------------------------------------------
# validate_bundle — fixture-based integration tests
# ---------------------------------------------------------------------------


class TestValidateBundleValid:
    """Tests with the valid bundle fixture."""

    def test_valid_bundle_is_conformant(self) -> None:
        """Valid bundle has no errors and no warnings."""
        bundle = BUNDLE_FIXTURES / "valid"
        report = validate_bundle(bundle)
        assert report.is_conformant is True
        assert report.errors == []
        assert report.warnings == []


class TestValidateBundleE1:
    """E1 tests using fixtures."""

    def test_e1_no_frontmatter(self) -> None:
        """E1 triggered when concept has no frontmatter."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e1-no-frontmatter"
        report = validate_bundle(bundle)
        assert any(f.code == "E1" for f in report.errors)

    def test_e1_unparseable_yaml(self) -> None:
        """E1 triggered when frontmatter YAML is unparseable."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e1-unparseable-yaml"
        report = validate_bundle(bundle)
        assert any(f.code == "E1" for f in report.errors)


class TestValidateBundleE2:
    """E2 tests using fixtures."""

    def test_e2_missing_type(self) -> None:
        """E2 triggered when type field is missing."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e2-missing-type"
        report = validate_bundle(bundle)
        assert any(f.code == "E2" for f in report.errors)

    def test_e2_empty_type(self) -> None:
        """E2 triggered when type field is empty."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e2-empty-type"
        report = validate_bundle(bundle)
        assert any(f.code == "E2" for f in report.errors)


class TestValidateBundleE3:
    """E3 tests using fixtures."""

    def test_e3_index_frontmatter(self) -> None:
        """E3 triggered when non-root index.md has frontmatter."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e3-index-frontmatter"
        report = validate_bundle(bundle)
        assert any(f.code == "E3" for f in report.errors)

    def test_e3_log_frontmatter(self) -> None:
        """E3 triggered when log.md has frontmatter."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e3-log-frontmatter"
        report = validate_bundle(bundle)
        assert any(f.code == "E3" for f in report.errors)


class TestValidateBundleE4:
    """E4 tests using fixtures."""

    def test_e4_schema_fail(self) -> None:
        """E4 triggered when frontmatter fails schema validation."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e4-schema-fail"
        schemas = load_schema_database(SCHEMA_FIXTURES)
        report = validate_bundle(bundle, schemas)
        assert any(f.code == "E4" for f in report.errors)


class TestValidateBundleE5:
    """E5 tests using fixtures."""

    def test_e5_unflatten_list(self) -> None:
        """E5 triggered when frontmatter has nested lists."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e5-unflatten-list"
        report = validate_bundle(bundle)
        assert any(f.code == "E5" for f in report.errors)


class TestValidateBundleE6:
    """E6 tests using fixtures."""

    def test_e6_log_outside_root(self) -> None:
        """E6 triggered when log.md is not at bundle root."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e6-log-outside-root"
        report = validate_bundle(bundle)
        assert any(f.code == "E6" for f in report.errors)


class TestValidateBundleE7:
    """E7 tests using fixtures."""

    def test_e7_loose_root_file(self) -> None:
        """E7 triggered when a non-reserved .md file is at bundle root."""
        bundle = BUNDLE_FIXTURES / "invalid" / "e7-loose-root-file"
        report = validate_bundle(bundle)
        assert any(f.code == "E7" for f in report.errors)
        e7 = next(f for f in report.errors if f.code == "E7")
        assert "loose-concept.md" in e7.message


class TestValidateBundleW1:
    """W1 tests using fixtures."""

    def test_w1_missing_title(self) -> None:
        """W1 triggered when title is missing."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w1-missing-title"
        report = validate_bundle(bundle)
        assert any(f.code == "W1" and "title" in f.message for f in report.warnings)

    def test_w1_missing_description(self) -> None:
        """W1 triggered when description is missing."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w1-missing-description"
        report = validate_bundle(bundle)
        assert any(f.code == "W1" and "description" in f.message for f in report.warnings)


class TestValidateBundleW2:
    """W2 tests using fixtures."""

    def test_w2_broken_link(self) -> None:
        """W2 triggered when internal link is broken."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w2-broken-link"
        report = validate_bundle(bundle)
        assert any(f.code == "W2" for f in report.warnings)


class TestValidateBundleW3:
    """W3 tests using fixtures."""

    def test_w3_missing_timestamp(self) -> None:
        """W3 triggered when timestamp is missing."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w3-missing-timestamp"
        report = validate_bundle(bundle)
        assert any(f.code == "W3" for f in report.warnings)


class TestValidateBundleW4:
    """W4 tests using fixtures."""

    def test_w4_missing_index(self) -> None:
        """W4 triggered when directory has no index.md."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w4-missing-index"
        report = validate_bundle(bundle)
        assert any(f.code == "W4" for f in report.warnings)


class TestValidateBundleW5:
    """W5 tests using fixtures."""

    def test_w5_bad_date(self) -> None:
        """W5 triggered when log.md has non-ISO date headings."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w5-bad-date"
        report = validate_bundle(bundle)
        assert any(f.code == "W5" for f in report.warnings)


class TestValidateBundleW6:
    """W6 tests using fixtures."""

    def test_w6_missing_schema(self) -> None:
        """W6 triggered when type has no matching schema."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w6-missing-schema"
        schemas = load_schema_database(SCHEMA_FIXTURES)
        report = validate_bundle(bundle, schemas)
        assert any(f.code == "W6" for f in report.warnings)


class TestValidateBundleW7:
    """W7 tests using fixtures."""

    def test_w7_block_list(self) -> None:
        """W7 triggered when frontmatter has block-style lists."""
        bundle = BUNDLE_FIXTURES / "invalid" / "w7-block-list"
        report = validate_bundle(bundle)
        assert any(f.code == "W7" for f in report.warnings)


# ---------------------------------------------------------------------------
# validate_bundle — edge cases
# ---------------------------------------------------------------------------


class TestValidateBundleEdgeCases:
    """Edge case tests for validate_bundle."""

    def test_empty_bundle(self, tmp_path: Path) -> None:
        """Empty bundle is conformant with no errors or warnings."""
        report = validate_bundle(tmp_path)
        assert report.is_conformant is True
        assert report.errors == []
        assert report.warnings == []

    def test_bundle_not_a_directory(self, tmp_path: Path) -> None:
        """Non-directory path triggers E0."""
        file_path = tmp_path / "not-a-dir.txt"
        file_path.write_text("hello")
        report = validate_bundle(file_path)
        assert not report.is_conformant
        assert any(f.code == "E0" for f in report.errors)

    def test_bundle_with_external_links(self, tmp_path: Path) -> None:
        """External links do not trigger W2."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "index.md").write_text("# subdir\n")
        path = subdir / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "[external](https://example.com)\n"
        )
        report = validate_bundle(tmp_path)
        assert report.is_conformant is True
        assert not any(f.code == "W2" for f in report.warnings)

    def test_bundle_root_may_lack_index(self, tmp_path: Path) -> None:
        """Bundle root without index.md does not trigger W4."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "index.md").write_text("# subdir\n")
        path = subdir / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "# Test\n"
        )
        report = validate_bundle(tmp_path)
        assert report.is_conformant is True
        assert not any(f.code == "W4" for f in report.warnings)

    def test_missing_schema_db(self, tmp_path: Path) -> None:
        """Missing schema db does not cause errors."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        path = subdir / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "# Test\n"
        )
        report = validate_bundle(tmp_path, None)
        assert report.is_conformant is True

    def test_e7_root_concept_triggers_error(self, tmp_path: Path) -> None:
        """E7 triggered when a concept .md is placed at bundle root."""
        path = tmp_path / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "# Test\n"
        )
        report = validate_bundle(tmp_path)
        assert not report.is_conformant
        assert any(f.code == "E7" for f in report.errors)
        e7 = next(f for f in report.errors if f.code == "E7")
        assert "concept.md" in e7.message

    def test_e7_multiple_root_files(self, tmp_path: Path) -> None:
        """E7 triggered for each non-reserved .md at bundle root."""
        (tmp_path / "a.md").write_text("---\ntitle: A\ntype: concept\n---\n\n# A\n")
        (tmp_path / "b.md").write_text("---\ntitle: B\ntype: concept\n---\n\n# B\n")
        report = validate_bundle(tmp_path)
        e7s = [f for f in report.errors if f.code == "E7"]
        assert len(e7s) == 2

    def test_no_e7_for_reserved_root_files(self, tmp_path: Path) -> None:
        """index.md and log.md at root do not trigger E7."""
        (tmp_path / "index.md").write_text("---\nokf_version: '0.1'\n---\n\n# Index\n")
        (tmp_path / "log.md").write_text("# Log\n\n## 2024-01-15\n\n- Entry\n")
        report = validate_bundle(tmp_path)
        assert not any(f.code == "E7" for f in report.errors)

    def test_no_e7_for_subdir_concepts(self, tmp_path: Path) -> None:
        """Concepts in subdirectories do not trigger E7."""
        subdir = tmp_path / "concepts"
        subdir.mkdir()
        path = subdir / "concept.md"
        path.write_text(
            "---\n"
            "title: Test\n"
            "description: A test\n"
            "type: concept\n"
            "timestamp: 2024-01-01\n"
            "---\n\n"
            "# Test\n"
        )
        report = validate_bundle(tmp_path)
        assert not any(f.code == "E7" for f in report.errors)
