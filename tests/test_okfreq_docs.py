"""Verify the documented scenario examples against actual reports."""

import json
import re
from pathlib import Path

from parametrization import Parametrization

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml
from okf_schema.okfreq.core import (
    ACCEPTANCE_MODE,
    create_requirement,
    init_requirements,
    report,
    validate_requirements,
    write_markdown_report,
)


@Parametrization.autodetect_parameters()
@Parametrization.case(name="independent", example=1)
@Parametrization.case(name="missing_transition", example=2)
@Parametrization.case(name="undeclared", example=3)
def test_documented_acceptance_examples(tmp_path: Path, example: int) -> None:
    page = Path(__file__).parents[1] / "docs/source/reference/okfreq-acceptance-paths.md"
    blocks = dict(
        re.findall(
            r"```\{code-block\} \w+\n:caption: ([^\n]+)\n\n(.*?)```",
            page.read_text(encoding="utf-8"),
            re.DOTALL,
        )
    )
    prefix = f"Example {example}"
    fixture = make_yaml().load(blocks[f"{prefix} frontmatter"])
    root = init_requirements(tmp_path)
    strs = create_requirement(
        root,
        "StRS",
        "Export",
        "A user can export a report.",
        project="demo",
        scope="default",
        origin="native",
    )
    swrs = create_requirement(
        root,
        "SwRS",
        "Write",
        "The service writes CSV output.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=[strs.stem],
    )
    config = root / "config.yml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "strs_test_coverage_mode: linked-swrs\n",
            f"strs_test_coverage_mode: {ACCEPTANCE_MODE}\n",
        ),
        encoding="utf-8",
    )
    for level, path in (("strs", strs), ("swrs", swrs)):
        frontmatter, body = extract_frontmatter(path.read_text(encoding="utf-8"))
        assert frontmatter is not None
        data = make_yaml().load(frontmatter)
        if level in fixture:
            data["scenarios"] = fixture[level]
        if level == "strs" and "body" in fixture:
            body += "\n" + fixture["body"]
        path.write_text(f"---\n{dump_yaml(data)}---\n{body}", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_export.py").write_text(blocks[f"{prefix} markers"], encoding="utf-8")

    data = report(root)
    stakeholder = next(item for item in data["requirements"] if item["id"] == strs.stem)
    expected = json.loads(blocks[f"{prefix} result"])
    coverage = stakeholder["stakeholder_test_coverage"]
    assert {key: coverage[key] for key in expected} == expected
    destination = tmp_path / "report.md"
    write_markdown_report(root, destination)
    assert blocks[f"{prefix} row"].strip() in destination.read_text(encoding="utf-8")
    if example == 2:
        software = next(item for item in data["requirements"] if item["id"] == swrs.stem)
        assert software["transitions"] == {"tested": ["S1"], "missing": ["S2"]}
    if example == 3:
        findings = validate_requirements(root)
        assert any("W003" in item and "#### Path 1: Export" in item for item in findings)
        assert any("W004" in item for item in findings)
