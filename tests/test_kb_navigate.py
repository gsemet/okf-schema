"""Tests for src/okf_schema/kb/navigate.py and the kb navigation CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.kb import navigate
from okf_schema.kb.cli import kb

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FINDING_PLL = """\
---
type: Finding
title: PLL lock time increases at low temperature
confidence: high
context: Measured via logic analyzer; 200us at 25C, 950us at -10C.
timestamp: 2026-07-03T14:20:00Z
tags: [pll, oscillator, temperature]
links: []
backlinks: []
status: active
---
# Finding
PLL lock drifts with temperature.
"""

_FINDING_TEMP = """\
---
type: Finding
title: Boot timeout more frequent at 0C
confidence: medium
context: Thermal sweep; 40% failures at 0C.
timestamp: 2026-07-02T11:00:00Z
tags: [boot, temperature]
links: []
backlinks: []
status: active
---
# Finding
Temperature correlation.
"""

_CONCEPT = """\
---
type: Concept
title: Boot PLL startup margin
confidence: high
status: resolved
promoted_from: [findings/2026.07.03-14.20-pll-temp-drift.md]
links: [principles/firmware-timeouts-must-be-polled.md]
backlinks: []
tags: [pll, boot]
---
# Concept
Hardcoded wait too short at low temp.
"""

_PRINCIPLE = """\
---
type: Principle
title: Firmware timeouts must be polled
status: active
links: []
backlinks: [concepts/boot-pll-startup-margin.md]
---
# Principle
Poll readiness signals.
"""


@pytest.fixture
def kb_bundle(tmp_path: Path) -> Path:
    """Create a minimal KB bundle with linked findings/concepts/principles."""
    for tier in ("findings", "concepts", "principles"):
        (tmp_path / tier).mkdir(parents=True)
    (tmp_path / "findings" / "2026.07.03-14.20-pll-temp-drift.md").write_text(
        _FINDING_PLL, encoding="utf-8"
    )
    (tmp_path / "findings" / "2026.07.02-11.00-temp-sensitivity.md").write_text(
        _FINDING_TEMP, encoding="utf-8"
    )
    (tmp_path / "concepts" / "boot-pll-startup-margin.md").write_text(_CONCEPT, encoding="utf-8")
    (tmp_path / "principles" / "firmware-timeouts-must-be-polled.md").write_text(
        _PRINCIPLE, encoding="utf-8"
    )
    (tmp_path / "index.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "log.md").write_text("# Log\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# normalize_tier / load_nodes
# ---------------------------------------------------------------------------


class TestTierNormalization:
    def test_plural_and_singular_map_to_folder(self) -> None:
        assert navigate.normalize_tier("finding") == "findings"
        assert navigate.normalize_tier("findings") == "findings"
        assert navigate.normalize_tier("Concept") == "concepts"
        assert navigate.normalize_tier("hypothesis") == "hypotheses"
        assert navigate.normalize_tier("ref") == "reference"

    def test_unknown_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tier"):
            navigate.normalize_tier("nonsense")


class TestLoadNodes:
    def test_loads_content_nodes_and_skips_reserved(self, kb_bundle: Path) -> None:
        nodes = navigate.load_nodes(kb_bundle)
        paths = {n.path for n in nodes}
        assert "index.md" not in paths
        assert "log.md" not in paths
        assert "concepts/boot-pll-startup-margin.md" in paths
        assert len(nodes) == 4

    def test_node_fields_parsed(self, kb_bundle: Path) -> None:
        node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin.md")
        assert node.tier == "concepts"
        assert node.type == "Concept"
        assert node.confidence == "high"
        assert node.status == "resolved"
        assert "pll" in node.tags
        assert node.links() == ["principles/firmware-timeouts-must-be-polled.md"]
        assert node.promoted_from() == ["findings/2026.07.03-14.20-pll-temp-drift.md"]


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_ranks_title_and_tags(self, kb_bundle: Path) -> None:
        hits = navigate.search(kb_bundle, "pll")
        assert hits, "expected at least one hit"
        # The finding with 'PLL' in title + tag should outrank others.
        assert hits[0].node.path == "findings/2026.07.03-14.20-pll-temp-drift.md"

    def test_search_tier_filter(self, kb_bundle: Path) -> None:
        hits = navigate.search(kb_bundle, "pll", tiers=["concepts"])
        assert all(h.node.tier == "concepts" for h in hits)

    def test_search_limit(self, kb_bundle: Path) -> None:
        hits = navigate.search(kb_bundle, "temperature", limit=1)
        assert len(hits) == 1

    def test_empty_query_returns_nothing(self, kb_bundle: Path) -> None:
        assert navigate.search(kb_bundle, "   ") == []


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_by_full_path(self, kb_bundle: Path) -> None:
        node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin.md")
        assert node.title == "Boot PLL startup margin"

    def test_get_without_extension(self, kb_bundle: Path) -> None:
        node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin")
        assert node.tier == "concepts"

    def test_get_by_stem(self, kb_bundle: Path) -> None:
        node = navigate.get(kb_bundle, "boot-pll-startup-margin")
        assert node.tier == "concepts"

    def test_get_missing_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(FileNotFoundError):
            navigate.get(kb_bundle, "does-not-exist")


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


class TestRead:
    def test_read_tier(self, kb_bundle: Path) -> None:
        nodes = navigate.read_tier(kb_bundle, "findings")
        assert len(nodes) == 2
        assert all(n.tier == "findings" for n in nodes)
        # Sorted by path (chronological due to dated filenames).
        assert nodes[0].path.endswith("temp-sensitivity.md")

    def test_read_status_filter(self, kb_bundle: Path) -> None:
        nodes = navigate.read_tier(kb_bundle, "concepts", status="resolved")
        assert len(nodes) == 1
        assert navigate.read_tier(kb_bundle, "concepts", status="active") == []

    def test_read_unknown_tier_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Unknown tier"):
            navigate.read_tier(kb_bundle, "bogus")


# ---------------------------------------------------------------------------
# query — filter DSL
# ---------------------------------------------------------------------------


class TestQueryFilter:
    def test_filter_by_type_and_tag(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "type:finding tag:pll")
        assert [n.path for n in nodes] == ["findings/2026.07.03-14.20-pll-temp-drift.md"]

    def test_confidence_ordinal_range(self, kb_bundle: Path) -> None:
        high = navigate.query(kb_bundle, "type:finding confidence:>=high")
        assert [n.title for n in high] == ["PLL lock time increases at low temperature"]
        atleast_medium = navigate.query(kb_bundle, "type:finding confidence:>=medium")
        assert len(atleast_medium) == 2

    def test_status_and_title_regex(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "type:concept title:~boot status:resolved")
        assert len(nodes) == 1

    def test_since_until(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "type:finding since:2026-07-03")
        assert len(nodes) == 1
        assert nodes[0].timestamp.startswith("2026-07-03")

    def test_not_equal(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "type:finding confidence:!=high")
        assert [n.confidence for n in nodes] == ["medium"]

    def test_empty_expr_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Empty query"):
            navigate.query(kb_bundle, "   ")

    def test_malformed_term_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Invalid filter term"):
            navigate.query(kb_bundle, "bareword")


# ---------------------------------------------------------------------------
# query — arrow traversal
# ---------------------------------------------------------------------------


class TestQueryTraversal:
    def test_links_hop(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "concept[tag=pll] -> principle")
        assert [n.path for n in nodes] == ["principles/firmware-timeouts-must-be-polled.md"]

    def test_backlinks_hop(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "principle <- concept")
        assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]

    def test_promotion_hop(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "finding[tag=pll] ^ concept")
        assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]

    def test_multi_hop(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "finding[tag=pll] ^ concept -> principle")
        assert [n.path for n in nodes] == ["principles/firmware-timeouts-must-be-polled.md"]

    def test_bare_tier_start_set(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "finding")
        assert len(nodes) == 2

    def test_inline_filter_operators(self, kb_bundle: Path) -> None:
        nodes = navigate.query(kb_bundle, "finding[confidence>=high]")
        assert len(nodes) == 1

    def test_invalid_node_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Unknown tier"):
            navigate.query(kb_bundle, "bogus[tag=x] -> concept")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestNavigationCli:
    def test_search_command_table(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["search", "pll", str(kb_bundle)])
        assert result.exit_code == 0, result.output
        assert "PLL lock time" in result.output

    def test_search_command_json(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["search", "pll", str(kb_bundle), "--format", "json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload[0]["score"] >= 1

    def test_get_command_frontmatter(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "get",
                "concepts/boot-pll-startup-margin.md",
                str(kb_bundle),
                "--format",
                "frontmatter",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Boot PLL startup margin" in result.output

    def test_get_command_missing_exits_1(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["get", "nope", str(kb_bundle)])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_read_command_titles(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["read", "findings", str(kb_bundle), "--format", "titles"])
        assert result.exit_code == 0, result.output
        assert "Boot timeout more frequent at 0C" in result.output

    def test_read_command_unknown_tier_exits_1(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["read", "bogus", str(kb_bundle)])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_query_filter_paths(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "query",
                "type:finding confidence:>=high tag:pll",
                str(kb_bundle),
                "--format",
                "paths",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip() == "findings/2026.07.03-14.20-pll-temp-drift.md"

    def test_query_traversal_json(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            kb,
            [
                "query",
                "finding[tag=pll] ^ concept -> principle",
                str(kb_bundle),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload[0]["path"] == "principles/firmware-timeouts-must-be-polled.md"

    def test_query_bad_expr_exits_1(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["query", "bareword", str(kb_bundle)])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_kb_help_lists_navigation_commands(self) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["--help"])
        assert result.exit_code == 0
        for cmd in ("search", "get", "read", "query"):
            assert cmd in result.output


# ---------------------------------------------------------------------------
# Edge-case coverage
# ---------------------------------------------------------------------------

_SCALAR_LINKS = """\
---
type: Outcome
title: Fix bootloader PLL polling
description: Uniquetoken pollingfix deliverable.
status: planned
priority: 2
links: concepts/boot-pll-startup-margin.md
promoted_from:
tags: fix
---
# Outcome
Scalar (non-list) frontmatter values.
"""

_LOW_FINDING = """\
---
type: Finding
title: Sporadic recovery observed
confidence: low
context: Watch dog note only.
timestamp: 2026-07-01T09:30:00Z
tags: [boot]
links: [findings/ghost.md]
status: active
---
# Finding
Body mentions oscilloscope evidence.
"""


@pytest.fixture
def kb_bundle_extra(kb_bundle: Path) -> Path:
    """Augment the base bundle with scalar-valued and low-confidence nodes."""
    (kb_bundle / "outcomes").mkdir()
    (kb_bundle / "outcomes" / "fix-bootloader-pll-polling.md").write_text(
        _SCALAR_LINKS, encoding="utf-8"
    )
    (kb_bundle / "findings" / "2026.07.01-09.30-sporadic.md").write_text(
        _LOW_FINDING, encoding="utf-8"
    )
    # A schema file (must be skipped by the loader).
    (kb_bundle / "_schema").mkdir()
    (kb_bundle / "_schema" / "Finding.schema.yaml").write_text("type: object\n", encoding="utf-8")
    # A node without a frontmatter title (title falls back to the file stem).
    (kb_bundle / "guides").mkdir()
    (kb_bundle / "guides" / "untitled-note.md").write_text(
        "---\ntype: Guide\nstatus: active\n---\n# Note\n", encoding="utf-8"
    )
    return kb_bundle


class TestAsStrList:
    def test_scalar_string_coerced_to_list(self, kb_bundle_extra: Path) -> None:
        node = navigate.get(kb_bundle_extra, "outcomes/fix-bootloader-pll-polling.md")
        assert node.links() == ["concepts/boot-pll-startup-margin.md"]
        assert node.tags == ["fix"]

    def test_none_value_is_empty(self, kb_bundle_extra: Path) -> None:
        node = navigate.get(kb_bundle_extra, "outcomes/fix-bootloader-pll-polling.md")
        assert node.promoted_from() == []


class TestSearchScoringBranches:
    def test_body_only_match(self, kb_bundle_extra: Path) -> None:
        hits = navigate.search(kb_bundle_extra, "oscilloscope")
        assert [h.node.tier for h in hits] == ["findings"]

    def test_context_match(self, kb_bundle_extra: Path) -> None:
        hits = navigate.search(kb_bundle_extra, "watch dog")
        assert hits and hits[0].node.title == "Sporadic recovery observed"

    def test_no_limit_returns_all(self, kb_bundle_extra: Path) -> None:
        hits = navigate.search(kb_bundle_extra, "boot", limit=0)
        assert len(hits) >= 3


class TestCompareBranches:
    def test_type_fuzzy_match(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:~find")
        assert all(n.tier == "findings" for n in nodes)
        assert len(nodes) == 3

    def test_scalar_links_traversal(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "outcome -> concept")
        assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]

    def test_numeric_frontmatter_comparison(self, kb_bundle_extra: Path) -> None:
        assert navigate.query(kb_bundle_extra, "type:outcome priority:>=2")
        assert navigate.query(kb_bundle_extra, "type:outcome priority:<1") == []

    def test_confidence_unknown_value_ordered_false(self, kb_bundle_extra: Path) -> None:
        # Ordered comparison against a non-ordinal value yields no matches.
        assert navigate.query(kb_bundle_extra, "type:finding confidence:>=bogus") == []

    def test_string_ordered_comparison(self, kb_bundle_extra: Path) -> None:
        # status is a plain string; ordered ops fall back to lexical compare.
        nodes = navigate.query(kb_bundle_extra, "type:outcome status:>=planned")
        assert len(nodes) == 1

    def test_since_without_timestamp_excluded(self, kb_bundle_extra: Path) -> None:
        # Outcome has no timestamp, so a since-filter excludes it.
        assert navigate.query(kb_bundle_extra, "type:outcome since:2020-01-01") == []


class TestReadAndGetMarkdown:
    def test_read_md_format_cli(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["read", "principles", str(kb_bundle)])
        assert result.exit_code == 0, result.output
        assert "Poll readiness signals." in result.output

    def test_get_md_format_cli(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["get", "concepts/boot-pll-startup-margin.md", str(kb_bundle)])
        assert result.exit_code == 0, result.output
        assert "Hardcoded wait too short" in result.output

    def test_query_table_no_matches(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["query", "type:guide", str(kb_bundle)])
        assert result.exit_code == 0, result.output
        assert "No matching nodes." in result.output

    def test_read_empty_tier(self, kb_bundle: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(kb, ["read", "guides", str(kb_bundle)])
        assert result.exit_code == 0, result.output
        assert "No matching nodes." in result.output


class TestOperatorBranches:
    def test_confidence_less_than(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:finding confidence:<medium")
        assert [n.confidence for n in nodes] == ["low"]

    def test_confidence_less_equal(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:finding confidence:<=medium")
        assert {n.confidence for n in nodes} == {"low", "medium"}

    def test_confidence_greater_than(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:finding confidence:>medium")
        assert [n.confidence for n in nodes] == ["high"]

    def test_confidence_equal(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:finding confidence:medium")
        assert [n.confidence for n in nodes] == ["medium"]

    def test_numeric_less_equal_and_greater(self, kb_bundle_extra: Path) -> None:
        assert navigate.query(kb_bundle_extra, "type:outcome priority:<=2")
        assert navigate.query(kb_bundle_extra, "type:outcome priority:>1")
        assert navigate.query(kb_bundle_extra, "type:outcome priority:>5") == []

    def test_string_less_than(self, kb_bundle_extra: Path) -> None:
        # 'active' < 'planned' lexically.
        nodes = navigate.query(kb_bundle_extra, "type:finding status:<planned")
        assert nodes and all(n.status == "active" for n in nodes)

    def test_invalid_regex_falls_back_to_substring(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:concept title:~(boot")
        # Invalid regex '(boot' falls back to substring, which will not match.
        assert nodes == []

    def test_generic_list_field_membership(self, kb_bundle: Path) -> None:
        nodes = navigate.query(
            kb_bundle,
            "type:concept links:principles/firmware-timeouts-must-be-polled.md",
        )
        assert len(nodes) == 1

    def test_get_by_bare_filename(self, kb_bundle_extra: Path) -> None:
        node = navigate.get(kb_bundle_extra, "2026.07.01-09.30-sporadic.md")
        assert node.tier == "findings"

    def test_dangling_link_hop_skipped(self, kb_bundle_extra: Path) -> None:
        # The low finding links to a non-existent ghost.md; the hop yields nothing.
        nodes = navigate.query(kb_bundle_extra, "finding[confidence=low] -> finding")
        assert nodes == []

    def test_schema_files_skipped(self, kb_bundle_extra: Path) -> None:
        paths = {n.path for n in navigate.load_nodes(kb_bundle_extra)}
        assert not any(p.startswith("_schema/") for p in paths)

    def test_description_scoring(self, kb_bundle_extra: Path) -> None:
        hits = navigate.search(kb_bundle_extra, "pollingfix")
        assert [h.node.tier for h in hits] == ["outcomes"]

    def test_title_fallback_to_stem(self, kb_bundle_extra: Path) -> None:
        nodes = navigate.query(kb_bundle_extra, "type:guide title:~untitled")
        assert [n.path for n in nodes] == ["guides/untitled-note.md"]

    def test_list_field_ordered_op_is_false(self, kb_bundle: Path) -> None:
        # An ordered operator on a list field yields no matches.
        assert navigate.query(kb_bundle, "type:concept links:>a") == []

    def test_invalid_inline_filter_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Invalid inline filter"):
            navigate.query(kb_bundle, "finding[justword]")

    def test_invalid_node_expression_raises(self, kb_bundle: Path) -> None:
        with pytest.raises(ValueError, match="Invalid node expression"):
            navigate.query(kb_bundle, "finding -> 9bad")
