"""Execute the consolidated OKFKB tutorial against its actual schemas and CLI."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from click.testing import CliRunner

from okf_schema._internal.yaml import extract_frontmatter, parse_yaml
from okf_schema.cli import cli
from okf_schema.okfkb.cli import kb

# @tests_req SwRS-OKFSCHEMA-OKFKB-003
# @tests_req SwRS-OKFSCHEMA-OKFKB-004


def test_knowledge_tutorial_preserves_evidence_and_builds_a_navigable_synthesis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Actual tutorial snippets yield valid provenance, backlinks and stable Finding bodies."""
    repository = Path(__file__).parents[1]
    tutorial = repository / "docs/source/tutorials/okfkb-workflow.md"
    blocks = re.findall(
        r"```\{code-block\} (\w+)\n:caption: ([^\n]+)\n\n(.*?)```",
        tutorial.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    substitutions: dict[str, str] = {}
    aliases = {
        "Capture PLL timing": "PLL_FINDING_STEM",
        "Capture bootloader wait": "WAIT_FINDING_STEM",
    }
    frozen: dict[Path, str] = {}

    def replace_stems(text: str) -> str:
        for placeholder, stem in substitutions.items():
            text = text.replace(placeholder, stem)
        return text

    def run_command(command: str, caption: str) -> None:
        tokens = shlex.split(command)
        assert tokens[:2] == ["uv", "run"]
        args = tokens[2:]
        before = set(Path("knowledge/findings").glob("*.md"))
        result = runner.invoke(kb if args[0] == "okfkb" else cli, args[1:])
        assert result.exit_code == 0, (command, result.output, result.exception)
        if args[1] == "new-finding":
            added = set(Path("knowledge/findings").glob("*.md")) - before
            assert len(added) == 1
            substitutions[aliases[caption]] = added.pop().stem
        if args[:2] == ["okfkb", "update"]:
            for path in Path("knowledge/findings").glob("*.md"):
                if path.name == "index.md":
                    continue
                _, body = extract_frontmatter(path.read_text(encoding="utf-8"))
                if path in frozen:
                    assert body == frozen[path]
                else:
                    frozen[path] = body

    for language, caption, content in blocks:
        content = replace_stems(content)
        if language == "bash":
            for line in content.replace("\\\n", " ").splitlines():
                if line.strip():
                    run_command(line, caption)
        elif language == "markdown":
            filename, _, operation = replace_stems(caption).partition(" — ")
            path = Path(filename)
            if operation == "body":
                fm, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
                assert fm is not None
                path.write_text(f"---\n{fm.rstrip()}\n---\n\n{content}", encoding="utf-8")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        elif language == "make":
            # Execute the actual recipes through the installed CLI, without
            # resolving a second uv environment or installing dependencies.
            for line in content.splitlines():
                if line.startswith("    "):
                    run_command(line.strip(), caption)
        else:
            raise AssertionError(f"Unverified snippet: {caption}")

    assert len(frozen) == 2
    concept_path = Path("knowledge/concepts/cold-pll-wait.md")
    fm, _ = extract_frontmatter(concept_path.read_text(encoding="utf-8"))
    concept = parse_yaml(fm)
    assert concept["derived_from"] == [
        f"findings/{substitutions['PLL_FINDING_STEM']}",
        f"findings/{substitutions['WAIT_FINDING_STEM']}",
    ]
    assert concept["derives_to"] == ["outcomes/bounded-pll-polling"]
    for path in frozen:
        fm, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
        data = parse_yaml(fm)
        assert data["derives_to"] == ["concepts/cold-pll-wait"]
    pll_path = Path(f"knowledge/findings/{substitutions['PLL_FINDING_STEM']}.md")
    fm, _ = extract_frontmatter(pll_path.read_text(encoding="utf-8"))
    assert parse_yaml(fm)["backlinks"] == sorted(
        [
            "concepts/cold-pll-wait.md",
            f"findings/{substitutions['WAIT_FINDING_STEM']}.md",
        ]
    )
    result = runner.invoke(
        kb, ["query", "finding[tag=pll] ^ concept", "knowledge", "--format", "paths"]
    )
    assert result.exit_code == 0 and result.output.strip() == "concepts/cold-pll-wait.md"
    result = runner.invoke(
        kb, ["get", "outcomes/bounded-pll-polling", "knowledge", "--format", "json"]
    )
    assert json.loads(result.output)["status"] == "planned"
    assert not list(Path("knowledge/principles").glob("*.md")) or all(
        path.name == "index.md" for path in Path("knowledge/principles").glob("*.md")
    )
    assert Path(".agents/skills/okfkb/references/consolidation-judgment.md").is_file()
