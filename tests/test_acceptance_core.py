"""Installed-wheel acceptance tests for core StRS main paths."""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import InstalledWheelEnv


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
def test_accepts_core_001_s1_validate_conforming_bundle(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema validates a conforming bundle with exit code 0 and no mutations."""
    project = tmp_path / "project"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    installed_wheel_env.run(
        "okf-schema",
        "new",
        "--path",
        str(bundle),
        "--name",
        "overview",
        "--type",
        "concept",
        "--title",
        "Overview",
        cwd=tmp_path,
    )
    before = _snapshot(bundle)
    result = installed_wheel_env.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)
    assert result.returncode == 0
    assert _snapshot(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
def test_accepts_core_001_s2_report_nonconforming_bundle_without_changing_it(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema exits non-zero on a broken bundle without mutating any file."""
    project = tmp_path / "broken-project"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    bad_doc = bundle / "broken.md"
    bad_doc.write_text("No frontmatter at all.\n", encoding="utf-8")
    before = _snapshot(bundle)

    result = installed_wheel_env.run(
        "okf-schema", "validate", "--path", str(bundle), cwd=tmp_path, check=False
    )
    assert result.returncode != 0
    assert "broken.md" in (result.stdout + result.stderr)
    assert _snapshot(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
def test_accepts_core_002_s1_create_bundle_and_author_concept(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema initializes a bundle, creates a concept, and validates cleanly."""
    project = tmp_path / "authored"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    installed_wheel_env.run(
        "okf-schema",
        "new",
        "--path",
        str(bundle),
        "--name",
        "architecture",
        "--type",
        "concept",
        "--title",
        "Architecture",
        cwd=tmp_path,
    )
    assert (bundle / "index.md").is_file()
    created = list(bundle.rglob("*architecture*.md"))
    assert len(created) == 1
    installed_wheel_env.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_accepts_core_002_s2_normalize_and_index_bundle(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema lints frontmatter and regenerates indexes while keeping prose."""
    project = tmp_path / "normalize"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    topic = bundle / "topics"
    topic.mkdir()
    doc = topic / "note.md"
    doc.write_text(
        "---\ntype: concept\ntitle: Note\ntags: [[alpha], beta]\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n  by: human:tester\n---\n\n'
        "Authored prose that must survive.\n",
        encoding="utf-8",
    )
    installed_wheel_env.run("okf-schema", "lint", "--path", str(bundle), cwd=tmp_path)
    installed_wheel_env.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path)
    assert "Authored prose that must survive." in doc.read_text(encoding="utf-8")
    assert (topic / "index.md").is_file()
    assert "note.md" in (topic / "index.md").read_text(encoding="utf-8")
    installed_wheel_env.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_accepts_core_002_s3_inspect_bundle_knowledge_read_only(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema list, stats, and backlinks inspect a bundle without mutating it."""
    project = tmp_path / "inspect"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    (bundle / "alpha.md").write_text(
        "---\ntype: concept\ntitle: Alpha\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n  by: human:tester\n---\n\nAlpha body.\n',
        encoding="utf-8",
    )
    (bundle / "beta.md").write_text(
        "---\ntype: concept\ntitle: Beta\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n  by: human:tester\n---\n\n'
        "Links to [Alpha](alpha.md).\n",
        encoding="utf-8",
    )
    before = _snapshot(bundle)

    list_out = installed_wheel_env.run("okf-schema", "list", "--path", str(bundle), cwd=tmp_path)
    stats_out = installed_wheel_env.run("okf-schema", "stats", "--path", str(bundle), cwd=tmp_path)
    backlinks_out = installed_wheel_env.run(
        "okf-schema", "backlinks", "--path", str(bundle), "alpha", cwd=tmp_path
    )
    assert "alpha" in list_out.stdout.lower()
    assert stats_out.stdout.strip()
    assert "beta" in backlinks_out.stdout.lower()
    assert _snapshot(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
def test_accepts_core_003_s1_navigate_declared_file_links(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed wheel Python API resolves schema-declared x-okf-link targets in isolation."""
    bundle = tmp_path / "links"
    bundle.mkdir()
    target = bundle / "target.md"
    target.write_text("# Target\n", encoding="utf-8")
    doc = bundle / "source.md"
    doc.write_text("---\ntype: note\nref: target.md\n---\n", encoding="utf-8")

    script = (
        "import json\n"
        "from pathlib import Path\n"
        "from okf_schema.file_links import inspect_file_links\n"
        f"bundle = Path({str(bundle)!r})\n"
        f"doc = Path({str(doc)!r})\n"
        "schema = {'properties': {'ref': {'type': 'string', "
        "'x-okf-link': {'resolution': 'document-relative', 'syntax': 'plain'}}}}\n"
        "results = inspect_file_links({'ref': 'target.md'}, schema, doc, bundle_root=bundle)\n"
        "print(json.dumps([{'status': r.status, 'resolved': str(r.resolved_path)} "
        "for r in results]))\n"
    )
    completed = installed_wheel_env.run("python", "-c", script, cwd=tmp_path)
    payload = json.loads(completed.stdout)
    assert len(payload) == 1
    assert payload[0]["status"] == "valid"
    assert Path(payload[0]["resolved"]).resolve() == target.resolve()


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
def test_accepts_core_003_s2_check_declared_file_links_on_request(
    tmp_path: Path,
    installed_wheel_env: InstalledWheelEnv,
) -> None:
    """Installed okf-schema skips link checks by default and reports E10 with --check-links."""
    project = tmp_path / "link-check"
    installed_wheel_env.run("okf-schema", "init", str(project), cwd=tmp_path)
    bundle = project / "bundle"
    schema_dir = bundle / "_schema"
    schema_dir.mkdir(exist_ok=True)
    (schema_dir / "linked.schema.yaml").write_text(
        "$schema: https://json-schema.org/draft/2020-12/schema\n"
        "type: object\n"
        "properties:\n"
        "  type: {const: linked}\n"
        "  title: {type: string}\n"
        "  ref:\n"
        "    type: string\n"
        "    x-okf-link:\n"
        "      resolution: document-relative\n"
        "      syntax: plain\n"
        "required: [type, title, ref]\n",
        encoding="utf-8",
    )
    (bundle / "doc.md").write_text(
        "---\ntype: linked\ntitle: Doc\nref: missing.md\n"
        'generated:\n  at: "2026-01-01T00:00:00Z"\n  by: human:tester\n---\n\nBody.\n',
        encoding="utf-8",
    )

    without_flag = installed_wheel_env.run(
        "okf-schema", "validate", "--path", str(bundle), cwd=tmp_path
    )
    assert without_flag.returncode == 0

    with_flag = installed_wheel_env.run(
        "okf-schema", "validate", "--path", str(bundle), "--check-links", cwd=tmp_path, check=False
    )
    assert with_flag.returncode != 0
    assert "E10" in (with_flag.stdout + with_flag.stderr)
