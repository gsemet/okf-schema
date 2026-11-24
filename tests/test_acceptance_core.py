"""Installed-product acceptance paths for core OKF operations."""

import subprocess
from collections.abc import Callable
from pathlib import Path


def create_bundle(run: Callable[..., subprocess.CompletedProcess[str]]) -> None:
    run("okf-schema", "init", "knowledge")
    run("okf-schema", "new", "--path", "knowledge/bundle", "--name", "clock", "--title", "Clock")


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
# @tests_req SwRS-OKFSCHEMA-CORE-001#S1
def test_validate_conforming_bundle(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    create_bundle(run_installed)
    document = tmp_path / "knowledge" / "bundle" / "clock.md"
    before = document.read_bytes()
    result = run_installed("okf-schema", "validate", "--path", "knowledge/bundle")
    assert result.returncode == 0
    assert document.read_bytes() == before


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
# @tests_req SwRS-OKFSCHEMA-CORE-001#S2
def test_validation_reports_invalid_bundle_without_mutation(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    run_installed("okf-schema", "init", "knowledge")
    document = tmp_path / "knowledge" / "bundle" / "invalid.md"
    document.write_text("Missing frontmatter\n", encoding="utf-8")
    before = document.read_bytes()
    result = run_installed("okf-schema", "validate", "--path", "knowledge/bundle", check=False)
    assert result.returncode != 0
    assert "E1" in result.stdout + result.stderr
    assert document.read_bytes() == before


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
# @tests_req SwRS-OKFSCHEMA-CORE-002#S1
def test_create_bundle_and_author_concept(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    create_bundle(run_installed)
    assert "Clock" in (tmp_path / "knowledge" / "bundle" / "clock.md").read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_normalize_and_index_bundle(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    create_bundle(run_installed)
    document = tmp_path / "knowledge" / "bundle" / "clock.md"
    before = document.read_text(encoding="utf-8")
    run_installed("okf-schema", "lint", "--path", "knowledge/bundle")
    run_installed("okf-schema", "index", "--path", "knowledge/bundle")
    assert "Clock" in document.read_text(encoding="utf-8")
    assert "Clock" in before
    assert "clock.md" in (tmp_path / "knowledge" / "bundle" / "index.md").read_text(
        encoding="utf-8"
    )


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_inspect_bundle_without_mutation(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    create_bundle(run_installed)
    document = tmp_path / "knowledge" / "bundle" / "clock.md"
    before = document.read_bytes()
    result = run_installed("okf-schema", "show", "--path", "knowledge/bundle", "clock.md")
    assert "Clock" in result.stdout
    assert document.read_bytes() == before


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
# @tests_req SwRS-OKFSCHEMA-CORE-007#S1
def test_navigate_declared_links_with_installed_api(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    (tmp_path / "source.md").write_text("Source", encoding="utf-8")
    (tmp_path / "target.md").write_text("Target", encoding="utf-8")
    code = (
        "from pathlib import Path; from okf_schema.file_links import inspect_file_links; "
        "schema={'type':'object','properties':{'link':{'type':'string',"
        "'x-okf-link':{'resolution':'document-relative','syntax':'plain'}}}}; "
        "r=inspect_file_links({'link':'target.md'},schema,Path('source.md')); "
        "print(r[0].status, r[0].resolved_path)"
    )
    result = run_installed("python", "-c", code)
    assert "valid" in result.stdout
    assert str(tmp_path / "target.md") in result.stdout


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
# @tests_req SwRS-OKFSCHEMA-CORE-007#S2
def test_check_declared_links_when_requested(
    tmp_path: Path, run_installed: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "concept.schema.yaml").write_text(
        "type: object\nproperties:\n  link:\n    type: string\n"
        "    x-okf-link: {resolution: document-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    document = tmp_path / "source.md"
    document.write_text("---\ntype: concept\nlink: missing.md\n---\n\nBody\n", encoding="utf-8")
    before = document.read_bytes()
    result = run_installed(
        "okf-schema",
        "validate-md",
        "--input",
        "source.md",
        "--schemas-dir",
        "schemas",
        "--check-links",
        check=False,
    )
    assert result.returncode != 0
    assert "E10" in result.stdout + result.stderr
    assert document.read_bytes() == before
