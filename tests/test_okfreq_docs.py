"""Keep the acceptance-paths reference page and ``okfreq`` from drifting.

The three worked examples of
``docs/source/reference/okfreq-acceptance-paths.md`` carry ``{code-block}``
directives whose caption is ``example <n> — <topic>``. A block whose topic is a
project-relative path is a file of the example project; the topics ``report
excerpt``, ``Markdown row`` and ``findings`` are the results the page promises.
This module builds each example bundle from those files and asserts the promised
results, so a change in the page or in the code fails here.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from okf_schema.okfreq.core import (
    initialize_bundle,
    report,
    validate_requirements,
    write_markdown_report,
)

_PAGE = Path(__file__).parents[1] / "docs/source/reference/okfreq-acceptance-paths.md"

_BLOCK = re.compile(
    r"^```\{code-block\} (?P<language>\w+)\n:caption: (?P<caption>[^\n]+)\n\n(?P<content>.*?)^```$",
    re.MULTILINE | re.DOTALL,
)

_RESULT_TOPICS = frozenset({"report excerpt", "Markdown row", "findings"})

_CONFIG = """version: 1
tiers:
  StRS: {folder: strs, prefix: StRS, derives_from: [], approval_lock: true}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}
id_policy: scope-prefix-sequence
strs_test_coverage_mode: linked-swrs-and-acceptance-paths
lifecycle:
  field: req_lifecycle
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  accepts: '@accepts_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, supersedes, implemented_in_files, tested_in_files,
  accepted_in_files, default_owner_email, status, verified]
retired_ids: []
scopes:
  core: {source_dirs: [src], test_dirs: [tests]}
"""


def _captioned_blocks(page: Path) -> dict[str, dict[str, str]]:
    """Return the page's worked examples, keyed by example number then by topic."""
    examples: dict[str, dict[str, str]] = {}
    for match in _BLOCK.finditer(page.read_text(encoding="utf-8")):
        caption = match.group("caption")
        number, separator, topic = caption.partition(" — ")
        assert separator == " — ", f"unexpected caption: {caption}"
        assert number.startswith("example "), f"unexpected caption: {caption}"
        examples.setdefault(number.removeprefix("example "), {})[topic] = match.group("content")
    return examples


def _build_example(tmp_path: Path, blocks: dict[str, str]) -> tuple[Path, Path]:
    """Write the example's files into a fresh bundle and return project and bundle roots."""
    project = tmp_path / "project"
    project.mkdir()
    bundle = project / "requirements"
    initialize_bundle(bundle)
    (bundle / "config.yml").write_text(_CONFIG, encoding="utf-8")
    for topic, content in blocks.items():
        if topic in _RESULT_TOPICS:
            continue
        path = project / topic
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return project, bundle


def _assert_markdown_lines(root: Path, destination: Path, expected: str) -> None:
    """Assert every non-empty line of ``expected`` appears in the Markdown report."""
    write_markdown_report(root, destination)
    written = destination.read_text(encoding="utf-8").splitlines()
    for line in expected.splitlines():
        if line.strip():
            assert line in written, f"missing Markdown line: {line}"


def _report_parts(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the per-StRS coverage entries and the per-SwRS transitions of a report."""
    coverage: dict[str, Any] = {}
    transitions: dict[str, Any] = {}
    for record in report(root)["requirements"]:
        if "stakeholder_test_coverage" in record:
            coverage[record["id"]] = record["stakeholder_test_coverage"]
        if "transitions" in record:
            transitions[record["id"]] = record["transitions"]
    return coverage, transitions


def test_examples_have_their_expected_topics() -> None:
    """The page's captions carry the three worked examples this module replays."""
    examples = _captioned_blocks(_PAGE)
    assert set(examples) == {"1", "2", "3"}
    assert {"report excerpt", "Markdown row"} <= set(examples["1"])
    assert {"report excerpt", "Markdown row"} <= set(examples["2"])
    assert "findings" in examples["3"]


def test_example_1_three_paths_tested_and_accepted(tmp_path: Path) -> None:
    """A path can be accepted without being tested; both columns show a fraction."""
    blocks = _captioned_blocks(_PAGE)["1"]
    project, bundle = _build_example(tmp_path, blocks)
    assert validate_requirements(bundle, prose=True) == []
    expected = json.loads(blocks["report excerpt"])
    coverage, transitions = _report_parts(bundle)
    assert transitions == {}
    assert set(expected) == set(coverage)
    assert coverage == expected
    _assert_markdown_lines(bundle, project / "report.md", blocks["Markdown row"])


def test_example_2_missing_swrs_transition_keeps_parent_uncovered(tmp_path: Path) -> None:
    """An untested declared transition is reported and keeps the linked StRS missing."""
    blocks = _captioned_blocks(_PAGE)["2"]
    project, bundle = _build_example(tmp_path, blocks)
    assert validate_requirements(bundle, prose=True) == []
    expected = json.loads(blocks["report excerpt"])
    coverage, transitions = _report_parts(bundle)
    assert set(expected) == set(coverage) | set(transitions)
    assert coverage == {key: value for key, value in expected.items() if key in coverage}
    assert transitions == {key: value for key, value in expected.items() if key in transitions}
    assert transitions["SwRS-CORE-001"] == {"tested": ["S1"], "missing": ["S2"]}
    _assert_markdown_lines(bundle, project / "report.md", blocks["Markdown row"])


def test_example_3_no_scenarios_prints_w003_and_w004(tmp_path: Path) -> None:
    """A fragmentless test marker counts, and the two warnings tell how to close the gap."""
    blocks = _captioned_blocks(_PAGE)["3"]
    _project, bundle = _build_example(tmp_path, blocks)
    findings = [
        finding.replace(str(bundle), "<bundle>").replace(os.sep, "/")
        for finding in validate_requirements(bundle, prose=True)
    ]
    assert "\n".join(findings) == blocks["findings"].strip()
    coverage, _transitions = _report_parts(bundle)
    assert coverage["StRS-CORE-001"]["paths"] == {"total": 0, "tested": 0, "accepted": 0}
    assert coverage["StRS-CORE-001"]["tested"] is True
    assert coverage["StRS-CORE-001"]["accepted"] is False
