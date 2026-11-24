"""Verify the executable acceptance-path examples stay aligned with the runtime."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

from okf_schema._internal.yaml import make_yaml, parse_yaml
from okf_schema.okfreq.core import (
    create_requirement,
    initialize_bundle,
    report,
    validate_requirements,
    write_markdown_report,
)


def _blocks(document: str) -> dict[str, str]:
    matches = re.finditer(
        r"```\{code-block\} \w+\n:caption: ([^\n]+)\n(.*?)\n```",
        document,
        re.DOTALL,
    )
    return {match.group(1): match.group(2) for match in matches}


def _set_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = text.split("---", 2)[1:]
    data = make_yaml().load(frontmatter)
    for key, value in updates.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    buffer = io.StringIO()
    make_yaml().dump(data, buffer)
    path.write_text(f"---\n{buffer.getvalue()}---{body}")


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return all(
            key in actual and _contains(actual[key], value) for key, value in expected.items()
        )
    return actual == expected


def test_worked_acceptance_path_examples_are_executable(tmp_path: Path) -> None:
    """Every captioned worked example reproduces its JSON, Markdown and warnings."""
    page = (
        Path(__file__).parents[1] / "docs/source/reference/okfreq-acceptance-paths.md"
    ).read_text(encoding="utf-8")
    blocks = _blocks(page)
    for index in range(1, 4):
        assert f"Example {index} frontmatter" in blocks
        assert f"Example {index} JSON result" in blocks
        assert f"Example {index} Markdown row" in blocks

    def build(number: int) -> tuple[Path, str, dict[str, Any]]:
        project = tmp_path / f"example-{number}"
        project.mkdir()
        root, _ = initialize_bundle(project / "requirements")
        config = root / "config.yml"
        config.write_text(
            config.read_text(encoding="utf-8").replace(
                "strs_test_coverage_mode: linked-swrs",
                "strs_test_coverage_mode: linked-swrs-and-acceptance-paths",
            )
        )
        stakeholder = create_requirement(
            root,
            "StRS",
            "Export rows" if number < 3 else "Publish a report",
            "The stakeholder SHALL receive the documented outcome.",
            project="docs",
            scope="export",
            origin="native",
            user_need="Review the outcome.",
            lifecycle="proposed",
        )
        allocated_stakeholder_id = parse_yaml(stakeholder.read_text().split("---", 2)[1])["id"]
        software = (
            create_requirement(
                root,
                "SwRS",
                "Export rows",
                "The tool SHALL export rows.",
                project="docs",
                scope="export",
                origin="native",
                derives_from=[allocated_stakeholder_id],
                lifecycle="proposed",
            )
            if number in (1, 2)
            else None
        )
        stakeholder_data = parse_yaml(blocks[f"Example {number} frontmatter"])
        stakeholder_id = str(stakeholder_data["id"])
        if number == 2:
            stakeholder_id = "StRS-EXPORT-001"
            stakeholder_data = {
                "id": stakeholder_id,
                "type": "StRS",
                "title": "Export rows",
                "scenarios": [{"id": "S1", "title": "Export rows"}],
            }
        _set_frontmatter(
            stakeholder,
            {
                **stakeholder_data,
                **({"title": stakeholder_data["title"]} if "title" in stakeholder_data else {}),
                "scope": "export",
                **({"scenarios": None} if number == 3 else {}),
            },
        )
        (project / "src").mkdir()
        (project / "tests").mkdir()
        marker_label = f"Example {number} marker"
        if number == 1:
            marker_label = "Example 1 markers"
        markers = blocks[marker_label]
        (project / "tests/example.py").write_text(markers + "\n", encoding="utf-8")

        if software is not None:
            if number == 1:
                _set_frontmatter(
                    software,
                    {
                        "id": "SwRS-EXPORT-001",
                        "scope": "export",
                        "derives_from": [stakeholder_id],
                    },
                )
                (project / "tests/example.py").write_text(
                    markers + "\n# @tests_req SwRS-EXPORT-001\n",
                    encoding="utf-8",
                )
            else:
                _set_frontmatter(
                    software,
                    {
                        **parse_yaml(blocks["Example 2 frontmatter"]),
                        "scope": "export",
                        "derives_from": [stakeholder_id],
                    },
                )
            (project / "src/example.py").write_text(
                "# @implements_req SwRS-EXPORT-001\n", encoding="utf-8"
            )
        return root, stakeholder_id, json.loads(blocks[f"Example {number} JSON result"])

    warning_root: Path | None = None
    for number in range(1, 4):
        root, stakeholder_id, expected = build(number)
        if number == 3:
            warning_root = root
        payload = report(root)
        record = next(item for item in payload["requirements"] if item["id"] == stakeholder_id)
        if number == 2:
            actual = next(
                item for item in payload["requirements"] if item["id"] == "SwRS-EXPORT-001"
            )
        else:
            actual = record["stakeholder_test_coverage"]
        assert _contains(actual, expected)
        destination = root.parent / "report.md"
        write_markdown_report(root, destination)
        assert blocks[f"Example {number} Markdown row"] in destination.read_text(encoding="utf-8")

    assert warning_root is not None
    findings = validate_requirements(warning_root)
    assert any(finding.startswith("W003 ") for finding in findings)
    assert any(finding.startswith("W004 ") for finding in findings)
