"""Acceptance paths for the core product, exercised through an installed wheel."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run(
    runtime: dict[str, Any], command: str, *arguments: str, cwd: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(runtime["bin"] / command), *arguments],
        cwd=cwd,
        env=runtime["env"],
        check=False,
        capture_output=True,
        text=True,
    )


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
def test_accepts_validation_of_conforming_bundle(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "index.md").write_text("---\nokf_version: '0.2'\n---\n\n# Bundle\n", encoding="utf-8")
    completed = _run(
        installed_runtime, "okf-schema", "validate", "--path", str(bundle), cwd=tmp_path
    )
    assert completed.returncode == 0, completed.stderr
    assert "conformant" in completed.stdout.lower()
    assert "0 errors, 0 warnings" in completed.stdout


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
def test_accepts_nonconforming_report_without_mutation(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    target = bundle / "broken.md"
    original = "content without metadata\n"
    target.write_text(original, encoding="utf-8")
    completed = _run(
        installed_runtime, "okf-schema", "validate", "--path", str(bundle), cwd=tmp_path
    )
    assert completed.returncode != 0
    assert "frontmatter" in completed.stderr.lower() or "frontmatter" in completed.stdout.lower()
    assert target.read_text(encoding="utf-8") == original


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
def test_accepts_bundle_creation_and_authorship(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = tmp_path / "knowledge"
    initialized = _run(installed_runtime, "okf-schema", "init", str(bundle), cwd=tmp_path)
    assert initialized.returncode == 0, initialized.stderr
    created = _run(
        installed_runtime,
        "okf-schema",
        "new",
        "--path",
        str(bundle / "concepts"),
        "--name",
        "portable-export",
        "--title",
        "Portable export",
        cwd=tmp_path,
    )
    assert created.returncode == 0, created.stderr
    concept = bundle / "concepts/portable-export.md"
    assert concept.is_file()
    assert "title: Portable export" in concept.read_text(encoding="utf-8")
    assert "type: concept" in concept.read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_accepts_normalize_and_index(installed_runtime: dict[str, Any], tmp_path: Path) -> None:
    bundle = tmp_path / "knowledge"
    assert _run(installed_runtime, "okf-schema", "init", str(bundle), cwd=tmp_path).returncode == 0
    (bundle / "concepts").mkdir()
    (bundle / "concepts/export.md").write_text(
        "---\ntype: concept\ntitle: Export rows\ndescription: Export selected rows.\n---\n\n"
        "# Export rows\n",
        encoding="utf-8",
    )
    indexed = _run(installed_runtime, "okf-schema", "index", "--path", str(bundle), cwd=tmp_path)
    assert indexed.returncode == 0, indexed.stderr
    generated = (bundle / "concepts/index.md").read_text(encoding="utf-8")
    assert "[Export rows](export.md)" in generated
    second = _run(installed_runtime, "okf-schema", "index", "--path", str(bundle), cwd=tmp_path)
    assert second.returncode == 0, second.stderr
    assert (bundle / "concepts/index.md").read_text(encoding="utf-8") == generated


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_accepts_read_only_bundle_inspection(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    bundle = tmp_path / "knowledge"
    assert _run(installed_runtime, "okf-schema", "init", str(bundle), cwd=tmp_path).returncode == 0
    (bundle / "concepts").mkdir()
    (bundle / "concepts/clock.md").write_text(
        "---\ntype: concept\ntitle: Stable clock\ndescription: Clock observations.\n---\n\n"
        "# Stable clock\n\nThe clock remains observable.\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(bundle): path.read_bytes() for path in bundle.rglob("*") if path.is_file()
    }
    listed = _run(installed_runtime, "okf-schema", "list", "--path", str(bundle), cwd=tmp_path)
    assert listed.returncode == 0, listed.stderr
    assert "Stable clock" in listed.stdout
    shown = _run(
        installed_runtime,
        "okf-schema",
        "show",
        "--path",
        str(bundle),
        "concepts/clock.md",
        cwd=tmp_path,
    )
    assert shown.returncode == 0, shown.stderr
    assert "The clock remains observable." in shown.stdout
    after = {
        path.relative_to(bundle): path.read_bytes() for path in bundle.rglob("*") if path.is_file()
    }
    assert after == before


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
def test_accepts_installed_navigation_api(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    target = tmp_path / "evidence/report.csv"
    target.parent.mkdir()
    target.write_text("name,value\nAda,1\n", encoding="utf-8")
    source = tmp_path / "requirement.md"
    source.write_text("---\nid: demo\nreport: evidence/report.csv\n---\n", encoding="utf-8")
    script = (
        "from pathlib import Path; from okf_schema.api import inspect_file_links; "
        f"p=Path({str(source)!r}); "
        "schema={'type':'object','properties':{'report':{'type':'string','x-okf-link':"
        "{'resolution':'project-relative','syntax':'plain'}}}}; "
        f"result=inspect_file_links({{'report':'evidence/report.csv'}},schema,p,"
        f"project_root=Path({str(tmp_path)!r})); "
        "assert len(result)==1 and result[0].status=='valid'; "
        "print(result[0].resolved_path)"
    )
    completed = subprocess.run(
        [str(installed_runtime["python"]), "-c", script],
        cwd=tmp_path,
        env=installed_runtime["env"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(target.resolve())


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
def test_accepts_link_checking_through_installed_command(
    installed_runtime: dict[str, Any], tmp_path: Path
) -> None:
    requirements = Path(__file__).parents[1] / "requirements"
    completed = _run(
        installed_runtime,
        "okfreq",
        "validate",
        str(requirements),
        "--check-links",
        "--project-root",
        str(Path(__file__).parents[1]),
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stderr
    assert "0 errors" in completed.stdout
