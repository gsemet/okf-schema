"""Check the worked examples of the acceptance-paths reference page against okfreq.

Each example's captioned blocks are read from the published page, built into a
bundle in mode ``linked-swrs-and-acceptance-paths``, and the JSON excerpt, the
Markdown rows and the ``okfreq validate`` output the page shows are compared with
what okfreq produces, so the page and the code cannot drift.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import (
    create_requirement,
    init_requirements,
    project_path,
    report,
    tiers_path,
    write_markdown_report,
)

PAGE = Path(__file__).parents[1] / "docs/source/reference/okfreq-acceptance-paths.md"
BLOCK = re.compile(r"```\{code-block\} (\w+)\n:caption: ([^\n]+)\n\n(.*?)```", re.DOTALL)


def example_blocks(number: int) -> dict[str, str]:
    """Return the captioned blocks of one worked example, by caption without its prefix."""
    prefix = f"Example {number}: "
    blocks = {
        caption.removeprefix(prefix): content
        for _, caption, content in BLOCK.findall(PAGE.read_text(encoding="utf-8"))
        if caption.startswith(prefix)
    }
    assert blocks, f"no captioned block for example {number} in {PAGE.name}"
    return blocks


def set_frontmatter(file: Path, **updates: Any) -> None:
    """Set (or remove, with ``None``) frontmatter keys of a requirement, keeping its body."""
    frontmatter, body = extract_frontmatter(file.read_text(encoding="utf-8"))
    assert frontmatter is not None
    data = make_yaml().load(frontmatter)
    for key, value in updates.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    file.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")


def build_example(tmp_path: Path, blocks: dict[str, str]) -> Path:
    """Build the bundle and test files an example shows; return the bundle root."""
    root = init_requirements(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs\n",
            "strs_test_coverage_mode: linked-swrs-and-acceptance-paths\n",
        ),
        encoding="utf-8",
    )
    project = project_path(root)
    (project / "src").mkdir()
    for caption, content in blocks.items():
        if caption.startswith("frontmatter of "):
            data = make_yaml().load(content)
            file = create_requirement(
                root,
                data["type"],
                data["title"],
                data["description"],
                project="shop",
                scope="default",
                origin="native",
                derives_from=list(data.get("derives_from") or []) or None,
            )
            assert file.stem == data["id"]
            scenarios = data.get("scenarios")
            set_frontmatter(file, scenarios=[dict(entry) for entry in scenarios or []] or None)
        elif caption.startswith("body of "):
            identifier = caption.removeprefix("body of ").split()[0]
            file = next(tiers_path(root).rglob(f"{identifier}.md"))
            text = file.read_text(encoding="utf-8")
            updated = re.sub(
                r"### Main paths\n.*?(?=### Preserved stakeholder intent)",
                lambda _, body=content: body + "\n",
                text,
                flags=re.DOTALL,
            )
            assert updated != text
            file.write_text(updated, encoding="utf-8")
        elif caption.startswith("tests/"):
            test_file = project / caption
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(content, encoding="utf-8")
    return root


def assert_excerpt(expected: Any, actual: Any, where: str = "report") -> None:
    """Assert that every key the excerpt shows has the shown value in ``actual``."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), where
        for key, value in expected.items():
            assert key in actual, f"{where}.{key} missing"
            assert_excerpt(value, actual[key], f"{where}.{key}")
    else:
        assert actual == expected, where


@Parametrization.autodetect_parameters()
@Parametrization.case(name="tested_and_accepted_paths", number=1)
@Parametrization.case(name="missing_swrs_transition", number=2)
@Parametrization.case(name="strs_without_scenarios", number=3)
def test_worked_example_matches_okfreq(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, number: int
) -> None:
    blocks = example_blocks(number)
    root = build_example(tmp_path, blocks)

    built = report(root)
    excerpt = json.loads(blocks["report JSON excerpt"])
    records = {record["id"]: record for record in built["requirements"]}
    for record in excerpt.pop("requirements", []):
        assert_excerpt(record, records[record["id"]], record["id"])
    assert_excerpt(excerpt, built)

    summary = tmp_path / "requirements-report.md"
    write_markdown_report(root, summary)
    lines = summary.read_text(encoding="utf-8").splitlines()
    for line in blocks["Markdown report rows"].splitlines():
        assert not line.strip() or line in lines, line

    project = project_path(root).resolve()
    monkeypatch.chdir(project)
    result = CliRunner().invoke(okfreq, ["validate", "."])
    output = result.output.replace(f"{project}{os.sep}", "").replace("\\", "/")
    assert blocks["okfreq validate output"].strip() in output
    assert result.exit_code == 0
    if number == 3:
        assert "\nW003 " in output
        assert "\nW004 " in output
