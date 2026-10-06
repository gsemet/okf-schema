"""Execute the tutorial's actual code, requirement bodies and harness commands.

Dependency installation is deliberately excluded: the test uses the installed
package and test interpreter. Every captioned executable step is read from the
maintained tutorial, not a second copy of its example implementation.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from okf_schema._internal.yaml import extract_frontmatter
from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import load_requirements

# @tests_req SwRS-OKFSCHEMA-OKFREQ-008


def test_traceability_tutorial_runs_from_existing_feature_to_updated_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Published snippets produce runnable code, linked drafts and fresh CI checks."""
    repository = Path(__file__).parents[1]
    tutorial = repository / "docs/source/tutorials/okfreq-traceability.md"
    blocks = re.findall(
        r"```\{code-block\} (\w+)\n:caption: ([^\n]+)\n\n(.*?)```",
        tutorial.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    project = tmp_path / "demo"
    project.mkdir()
    monkeypatch.chdir(project)
    runner = CliRunner()
    test_outputs: list[str] = []
    just = shutil.which("just")
    assert just, "The repository preflight requires just"

    def run_command(line: str) -> None:
        tokens = shlex.split(line)
        if tokens[0] == "just":
            result = subprocess.run(
                [
                    just,
                    "--color",
                    "never",
                    "--dry-run",
                    "--justfile",
                    str(project / "justfile"),
                    *tokens[1:],
                ],
                cwd=project,
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "NO_COLOR": "1"},
            )
            # Execute the dry-run's real recipe commands through the same
            # offline adapter as direct tutorial commands.
            for command in (result.stdout + result.stderr).splitlines():
                if command.strip():
                    run_command(command)
            return
        assert tokens[:2] == ["uv", "run"], line
        args = tokens[2:]
        if args[0] == "okfreq":
            result = runner.invoke(okfreq, args[1:])
            assert result.exit_code == 0, (line, result.output, result.exception)
        else:
            assert args[:4] == ["python", "-m", "pytest", "tests"], line
            process = subprocess.run(
                [sys.executable, *args[1:]],
                cwd=project,
                capture_output=True,
                text=True,
            )
            assert process.returncode == 0, process.stdout + process.stderr
            test_outputs.append(process.stdout)

    for language, caption, content in blocks:
        if language == "bash":
            for line in content.replace("\\\n", " ").splitlines():
                if line.strip():
                    run_command(line)
        elif language == "python" and "implementation marker for src/export.py" in caption.lower():
            path = project / "src/export.py"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("def export_rows(", content.rstrip() + "\ndef export_rows(", 1),
                encoding="utf-8",
            )
        elif language == "python" and caption == "Test marker for tests/test_export.py":
            path = project / "tests/test_export.py"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "def test_export_rows(", content.rstrip() + "\ndef test_export_rows(", 1
                ),
                encoding="utf-8",
            )
        elif language == "python":
            filename, _, operation = caption.partition(" — ")
            path = project / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if operation == "append":
                path.write_text(
                    path.read_text(encoding="utf-8") + "\n\n" + content, encoding="utf-8"
                )
            else:
                path.write_text(content, encoding="utf-8")
        elif language == "markdown" and caption.endswith(" — body"):
            path = project / caption.removesuffix(" — body")
            frontmatter, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
            assert frontmatter is not None
            path.write_text(f"---\n{frontmatter.rstrip()}\n---\n\n{content}", encoding="utf-8")
        elif caption == "justfile":
            (project / "justfile").write_text(content, encoding="utf-8")
        elif caption == "AGENTS.md — requirements workflow":
            (project / "AGENTS.md").write_text(content, encoding="utf-8")
        else:
            raise AssertionError(f"Unverified tutorial block: {caption}")

    records = load_requirements(project / "requirements")
    assert set(records) == {"StRS-default-001", "SwRS-default-001", "SwRS-default-002"}
    assert all(data["lifecycle"] == "draft" for _, data, _ in records.values())
    for identifier in ("SwRS-default-001", "SwRS-default-002"):
        assert records[identifier][1]["implemented_in_files"] == ["src/export.py"]
        assert records[identifier][1]["tested_in_files"] == ["tests/test_export.py"]
    report_path = project / "dist/requirements-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    schema = json.loads(report_path.with_suffix(".schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(report)
    assert report["execution_evidence"]["status"] == "not_collected"
    assert report["totals"]["fully_traceable"] == 2
    assert report["marker_coverage"]["missing_ids"] == []
    assert any("2 passed" in output for output in test_outputs)
    assert any("3 passed" in output for output in test_outputs)
    assert (project / ".agents/skills/okfreq/references/operations.md").is_file()
