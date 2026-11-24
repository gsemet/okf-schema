"""The worked examples of the acceptance-paths reference page match the real runtime."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from okf_schema.okfreq.core import (
    init_requirements,
    report,
    validate_requirements,
    write_markdown_report,
)

PAGE = Path(__file__).resolve().parents[1] / "docs/source/reference/okfreq-acceptance-paths.md"
BLOCK = re.compile(
    r"```\{code-block\} (?P<lang>\w+)\n:caption: (?P<caption>[^\n]+)\n\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def _blocks() -> dict[str, str]:
    """Map the caption of every code block of the page to its text."""
    return {
        match["caption"]: match["body"]
        for match in BLOCK.finditer(PAGE.read_text(encoding="utf-8"))
    }


def _materialize(tmp_path: Path, files: dict[str, str]) -> Path:
    """Run the page's setup, then write the captioned frontmatter and test blocks."""
    blocks = _blocks()
    root = init_requirements(tmp_path / "requirements")
    assert isinstance(root, Path)
    config = root / "config.yml"
    old = "strs_test_coverage_mode: linked-swrs\n"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            old, blocks["Setup: mode in requirements/config.yml"] + "\n"
        ),
        encoding="utf-8",
    )
    for caption, name in files.items():
        text = blocks[caption]
        if name.startswith("tiers/") and not caption.endswith("(frontmatter and body)"):
            title = re.search(r"^title: (.+)$", text, re.MULTILINE)
            description = re.search(r"^description: (.+)$", text, re.MULTILINE)
            assert title and description
            text += f"\n\n## {title[1]}\n\n### Normative behavior\n\n{description[1]}\n"
        target = (root if name.startswith("tiers/") else tmp_path) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
    return root


def _record(root: Path, identifier: str) -> dict[str, Any]:
    return next(item for item in report(root)["requirements"] if item["id"] == identifier)


def _assert_markdown(root: Path, tmp_path: Path, caption: str) -> None:
    destination = tmp_path / "summary.md"
    write_markdown_report(root, destination)
    actual = destination.read_text(encoding="utf-8").splitlines()
    shown = [line for line in _blocks()[caption].splitlines() if line.strip()]
    assert shown
    assert all(line in actual for line in shown), shown


def _errors(root: Path) -> list[str]:
    return [item for item in validate_requirements(root) if not re.match(r"[WI]\d{3} ", item)]


def test_page_captions_the_blocks_of_the_three_worked_examples() -> None:
    examples = {caption.split(":")[0] for caption in _blocks() if caption.startswith("Example ")}
    assert examples == {"Example 1", "Example 2", "Example 3"}
    assert _blocks()["Setup: mode in requirements/config.yml"].strip() == (
        "strs_test_coverage_mode: linked-swrs-and-acceptance-paths"
    )


# @tests_req SwRS-OKFSCHEMA-OKFREQ-015#S1
def test_example_1_three_paths_tested_two_accepted_one(tmp_path: Path) -> None:
    root = _materialize(
        tmp_path,
        {
            "Example 1: frontmatter of StRS-default-001": "tiers/strs/StRS-default-001.md",
            "Example 1: frontmatter of SwRS-default-001": "tiers/swrs/SwRS-default-001.md",
            "Example 1: tests/test_export.py": "tests/test_export.py",
            "Example 1: tests/test_acceptance_export.py": "tests/test_acceptance_export.py",
        },
    )
    assert _errors(root) == []
    excerpt = json.loads(_blocks()["Example 1: JSON excerpt"])
    assert _record(root, "StRS-default-001")["stakeholder_test_coverage"] == excerpt
    _assert_markdown(root, tmp_path, "Example 1: Markdown row")


def test_example_2_a_swrs_with_an_untested_transition(tmp_path: Path) -> None:
    root = _materialize(
        tmp_path,
        {
            "Example 1: frontmatter of StRS-default-001": "tiers/strs/StRS-default-001.md",
            "Example 2: frontmatter of SwRS-default-002": "tiers/swrs/SwRS-default-002.md",
            "Example 2: tests/test_csv.py": "tests/test_csv.py",
        },
    )
    assert _errors(root) == []
    excerpt = json.loads(_blocks()["Example 2: JSON excerpt"])
    record = _record(root, "SwRS-default-002")
    assert {key: record[key] for key in excerpt} == excerpt
    assert _record(root, "StRS-default-001")["stakeholder_test_coverage"]["linked_swrs"] == [
        {"id": "SwRS-default-002", "status": "missing"}
    ]
    _assert_markdown(root, tmp_path, "Example 2: Markdown row")


def test_example_3_a_strs_without_scenarios_gets_w003_and_w004(tmp_path: Path) -> None:
    root = _materialize(
        tmp_path,
        {
            "Example 3: StRS-default-003 (frontmatter and body)": "tiers/strs/StRS-default-003.md",
            "Example 3: tests/test_review.py": "tests/test_review.py",
        },
    )
    assert _errors(root) == []
    shown = _blocks()["Example 3: okfreq validate output (W003 and W004)"]
    findings = [item for item in validate_requirements(root) if item.startswith(("W003", "W004"))]
    assert [item.replace(f"{tmp_path}/", "") for item in findings] == re.split(
        r"\n(?=W00\d )", shown
    )
    excerpt = json.loads(_blocks()["Example 3: JSON excerpt"])
    assert _record(root, "StRS-default-003")["stakeholder_test_coverage"] == excerpt
    _assert_markdown(root, tmp_path, "Example 3: Markdown row")
