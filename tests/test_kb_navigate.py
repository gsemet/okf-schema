"""Tests for src/okf_schema/okfkb/navigate.py and the kb navigation CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from okf_schema.okfkb import navigate
from okf_schema.okfkb.cli import kb

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
kb_status: active
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
kb_status: active
---
# Finding
Temperature correlation.
"""

_CONCEPT = """\
---
type: Concept
title: Boot PLL startup margin
confidence: high
kb_status: deprecated
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
kb_status: active
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


def test_tier_normalization_plural_and_singular_map_to_folder() -> None:
    assert navigate.normalize_tier("finding") == "findings"
    assert navigate.normalize_tier("findings") == "findings"
    assert navigate.normalize_tier("Concept") == "concepts"
    assert navigate.normalize_tier("hypothesis") == "hypotheses"
    assert navigate.normalize_tier("ref") == "reference"


def test_tier_normalization_unknown_tier_raises() -> None:
    with pytest.raises(ValueError, match="Unknown tier"):
        navigate.normalize_tier("nonsense")


def test_load_nodes_loads_content_nodes_and_skips_reserved(kb_bundle: Path) -> None:
    nodes = navigate.load_nodes(kb_bundle)
    paths = {n.path for n in nodes}
    assert "index.md" not in paths
    assert "log.md" not in paths
    assert "concepts/boot-pll-startup-margin.md" in paths
    assert len(nodes) == 4


def test_load_nodes_node_fields_parsed(kb_bundle: Path) -> None:
    node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin.md")
    assert node.tier == "concepts"
    assert node.type == "Concept"
    assert node.confidence == "high"
    assert node.status == "deprecated"
    assert "pll" in node.tags
    assert node.links() == ["principles/firmware-timeouts-must-be-polled.md"]
    assert node.promoted_from() == ["findings/2026.07.03-14.20-pll-temp-drift.md"]


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFKB-004


def test_search_search_ranks_title_and_tags(kb_bundle: Path) -> None:
    hits = navigate.search(kb_bundle, "pll")
    assert hits, "expected at least one hit"
    # The finding with 'PLL' in title + tag should outrank others.
    assert hits[0].node.path == "findings/2026.07.03-14.20-pll-temp-drift.md"


def test_search_search_tier_filter(kb_bundle: Path) -> None:
    hits = navigate.search(kb_bundle, "pll", tiers=["concepts"])
    assert all(h.node.tier == "concepts" for h in hits)


def test_search_search_limit(kb_bundle: Path) -> None:
    hits = navigate.search(kb_bundle, "temperature", limit=1)
    assert len(hits) == 1


def test_search_empty_query_returns_nothing(kb_bundle: Path) -> None:
    assert navigate.search(kb_bundle, "   ") == []


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_get_by_full_path(kb_bundle: Path) -> None:
    node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin.md")
    assert node.title == "Boot PLL startup margin"


def test_get_get_without_extension(kb_bundle: Path) -> None:
    node = navigate.get(kb_bundle, "concepts/boot-pll-startup-margin")
    assert node.tier == "concepts"


def test_get_get_by_stem(kb_bundle: Path) -> None:
    node = navigate.get(kb_bundle, "boot-pll-startup-margin")
    assert node.tier == "concepts"


def test_get_get_missing_raises(kb_bundle: Path) -> None:
    with pytest.raises(FileNotFoundError):
        navigate.get(kb_bundle, "does-not-exist")


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


def test_read_read_tier(kb_bundle: Path) -> None:
    nodes = navigate.read_tier(kb_bundle, "findings")
    assert len(nodes) == 2
    assert all(n.tier == "findings" for n in nodes)
    # Raw findings are returned most recent first.
    assert nodes[0].path.endswith("pll-temp-drift.md")


def test_read_read_status_filter(kb_bundle: Path) -> None:
    nodes = navigate.read_tier(kb_bundle, "concepts", status="deprecated")
    assert len(nodes) == 1
    assert navigate.read_tier(kb_bundle, "concepts", status="active") == []


def test_read_read_unknown_tier_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Unknown tier"):
        navigate.read_tier(kb_bundle, "bogus")


# ---------------------------------------------------------------------------
# query — filter DSL
# ---------------------------------------------------------------------------


def test_query_filter_filter_by_type_and_tag(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "type:finding tag:pll")
    assert [n.path for n in nodes] == ["findings/2026.07.03-14.20-pll-temp-drift.md"]


def test_query_filter_confidence_ordinal_range(kb_bundle: Path) -> None:
    high = navigate.query(kb_bundle, "type:finding confidence:>=high")
    assert [n.title for n in high] == ["PLL lock time increases at low temperature"]
    atleast_medium = navigate.query(kb_bundle, "type:finding confidence:>=medium")
    assert len(atleast_medium) == 2


def test_query_filter_status_and_title_regex(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "type:concept title:~boot status:deprecated")
    assert len(nodes) == 1


def test_query_filter_since_until(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "type:finding since:2026-07-03")
    assert len(nodes) == 1
    assert nodes[0].timestamp.startswith("2026-07-03")


def test_query_filter_not_equal(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "type:finding confidence:!=high")
    assert [n.confidence for n in nodes] == ["medium"]


def test_query_filter_empty_expr_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Empty query"):
        navigate.query(kb_bundle, "   ")


def test_query_filter_malformed_term_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Invalid filter term"):
        navigate.query(kb_bundle, "bareword")


# ---------------------------------------------------------------------------
# query — arrow traversal
# ---------------------------------------------------------------------------


def test_query_traversal_links_hop(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "concept[tag=pll] -> principle")
    assert [n.path for n in nodes] == ["principles/firmware-timeouts-must-be-polled.md"]


def test_query_traversal_backlinks_hop(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "principle <- concept")
    assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]


def test_query_traversal_promotion_hop(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "finding[tag=pll] ^ concept")
    assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]


def test_query_traversal_multi_hop(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "finding[tag=pll] ^ concept -> principle")
    assert [n.path for n in nodes] == ["principles/firmware-timeouts-must-be-polled.md"]


def test_query_traversal_bare_tier_start_set(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "finding")
    assert len(nodes) == 2


def test_query_traversal_inline_filter_operators(kb_bundle: Path) -> None:
    nodes = navigate.query(kb_bundle, "finding[confidence>=high]")
    assert len(nodes) == 1


def test_query_traversal_invalid_node_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Unknown tier"):
        navigate.query(kb_bundle, "bogus[tag=x] -> concept")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_navigation_cli_search_command_table(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["search", "pll", str(kb_bundle)])
    assert result.exit_code == 0, result.output
    assert "PLL lock time" in result.output


def test_navigation_cli_search_command_json(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["search", "pll", str(kb_bundle), "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload[0]["score"] >= 1


def test_navigation_cli_get_command_frontmatter(kb_bundle: Path) -> None:
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


def test_navigation_cli_get_command_missing_exits_1(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["get", "nope", str(kb_bundle)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_navigation_cli_read_command_titles(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["read", "findings", str(kb_bundle), "--format", "titles"])
    assert result.exit_code == 0, result.output
    assert "Boot timeout more frequent at 0C" in result.output


def test_navigation_cli_read_command_unknown_tier_exits_1(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["read", "bogus", str(kb_bundle)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_navigation_cli_query_filter_paths(kb_bundle: Path) -> None:
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


def test_navigation_cli_query_traversal_json(kb_bundle: Path) -> None:
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


def test_navigation_cli_query_bad_expr_exits_1(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["query", "bareword", str(kb_bundle)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_navigation_cli_kb_help_lists_navigation_commands() -> None:
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


def test_as_str_list_scalar_string_coerced_to_list(kb_bundle_extra: Path) -> None:
    node = navigate.get(kb_bundle_extra, "outcomes/fix-bootloader-pll-polling.md")
    assert node.links() == ["concepts/boot-pll-startup-margin.md"]
    assert node.tags == ["fix"]


def test_as_str_list_none_value_is_empty(kb_bundle_extra: Path) -> None:
    node = navigate.get(kb_bundle_extra, "outcomes/fix-bootloader-pll-polling.md")
    assert node.promoted_from() == []


def test_search_scoring_branches_body_only_match(kb_bundle_extra: Path) -> None:
    hits = navigate.search(kb_bundle_extra, "oscilloscope")
    assert [h.node.tier for h in hits] == ["findings"]


def test_search_scoring_branches_context_match(kb_bundle_extra: Path) -> None:
    hits = navigate.search(kb_bundle_extra, "watch dog")
    assert hits and hits[0].node.title == "Sporadic recovery observed"


def test_search_scoring_branches_no_limit_returns_all(kb_bundle_extra: Path) -> None:
    hits = navigate.search(kb_bundle_extra, "boot", limit=0)
    assert len(hits) >= 3


def test_compare_branches_type_fuzzy_match(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:~find")
    assert all(n.tier == "findings" for n in nodes)
    assert len(nodes) == 3


def test_compare_branches_scalar_links_traversal(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "outcome -> concept")
    assert [n.path for n in nodes] == ["concepts/boot-pll-startup-margin.md"]


def test_compare_branches_numeric_frontmatter_comparison(kb_bundle_extra: Path) -> None:
    assert navigate.query(kb_bundle_extra, "type:outcome priority:>=2")
    assert navigate.query(kb_bundle_extra, "type:outcome priority:<1") == []


def test_compare_branches_confidence_unknown_value_ordered_false(kb_bundle_extra: Path) -> None:
    # Ordered comparison against a non-ordinal value yields no matches.
    assert navigate.query(kb_bundle_extra, "type:finding confidence:>=bogus") == []


def test_compare_branches_string_ordered_comparison(kb_bundle_extra: Path) -> None:
    # status is a plain string; ordered ops fall back to lexical compare.
    nodes = navigate.query(kb_bundle_extra, "type:outcome status:>=planned")
    assert len(nodes) == 1


def test_compare_branches_since_without_timestamp_excluded(kb_bundle_extra: Path) -> None:
    # Outcome has no timestamp, so a since-filter excludes it.
    assert navigate.query(kb_bundle_extra, "type:outcome since:2020-01-01") == []


def test_read_and_get_markdown_read_md_format_cli(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["read", "principles", str(kb_bundle)])
    assert result.exit_code == 0, result.output
    assert "Poll readiness signals." in result.output


def test_read_and_get_markdown_get_md_format_cli(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["get", "concepts/boot-pll-startup-margin.md", str(kb_bundle)])
    assert result.exit_code == 0, result.output
    assert "Hardcoded wait too short" in result.output


def test_read_and_get_markdown_query_table_no_matches(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["query", "type:guide", str(kb_bundle)])
    assert result.exit_code == 0, result.output
    assert "No matching nodes." in result.output


def test_read_and_get_markdown_read_empty_tier(kb_bundle: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(kb, ["read", "guides", str(kb_bundle)])
    assert result.exit_code == 0, result.output
    assert "No matching nodes." in result.output


def test_operator_branches_confidence_less_than(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:finding confidence:<medium")
    assert [n.confidence for n in nodes] == ["low"]


def test_operator_branches_confidence_less_equal(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:finding confidence:<=medium")
    assert {n.confidence for n in nodes} == {"low", "medium"}


def test_operator_branches_confidence_greater_than(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:finding confidence:>medium")
    assert [n.confidence for n in nodes] == ["high"]


def test_operator_branches_confidence_equal(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:finding confidence:medium")
    assert [n.confidence for n in nodes] == ["medium"]


def test_operator_branches_numeric_less_equal_and_greater(kb_bundle_extra: Path) -> None:
    assert navigate.query(kb_bundle_extra, "type:outcome priority:<=2")
    assert navigate.query(kb_bundle_extra, "type:outcome priority:>1")
    assert navigate.query(kb_bundle_extra, "type:outcome priority:>5") == []


def test_operator_branches_string_less_than(kb_bundle_extra: Path) -> None:
    # 'active' < 'planned' lexically.
    nodes = navigate.query(kb_bundle_extra, "type:finding status:<planned")
    assert nodes and all(n.status == "active" for n in nodes)


def test_operator_branches_invalid_regex_falls_back_to_substring(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:concept title:~(boot")
    # Invalid regex '(boot' falls back to substring, which will not match.
    assert nodes == []


def test_operator_branches_generic_list_field_membership(kb_bundle: Path) -> None:
    nodes = navigate.query(
        kb_bundle,
        "type:concept links:principles/firmware-timeouts-must-be-polled.md",
    )
    assert len(nodes) == 1


def test_operator_branches_get_by_bare_filename(kb_bundle_extra: Path) -> None:
    node = navigate.get(kb_bundle_extra, "2026.07.01-09.30-sporadic.md")
    assert node.tier == "findings"


def test_operator_branches_dangling_link_hop_skipped(kb_bundle_extra: Path) -> None:
    # The low finding links to a non-existent ghost.md; the hop yields nothing.
    nodes = navigate.query(kb_bundle_extra, "finding[confidence=low] -> finding")
    assert nodes == []


def test_operator_branches_schema_files_skipped(kb_bundle_extra: Path) -> None:
    paths = {n.path for n in navigate.load_nodes(kb_bundle_extra)}
    assert not any(p.startswith("_schema/") for p in paths)


def test_operator_branches_description_scoring(kb_bundle_extra: Path) -> None:
    hits = navigate.search(kb_bundle_extra, "pollingfix")
    assert [h.node.tier for h in hits] == ["outcomes"]


def test_operator_branches_title_fallback_to_stem(kb_bundle_extra: Path) -> None:
    nodes = navigate.query(kb_bundle_extra, "type:guide title:~untitled")
    assert [n.path for n in nodes] == ["guides/untitled-note.md"]


def test_operator_branches_list_field_ordered_op_is_false(kb_bundle: Path) -> None:
    # An ordered operator on a list field yields no matches.
    assert navigate.query(kb_bundle, "type:concept links:>a") == []


def test_operator_branches_invalid_inline_filter_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Invalid inline filter"):
        navigate.query(kb_bundle, "finding[justword]")


def test_operator_branches_invalid_node_expression_raises(kb_bundle: Path) -> None:
    with pytest.raises(ValueError, match="Invalid node expression"):
        navigate.query(kb_bundle, "finding -> 9bad")
