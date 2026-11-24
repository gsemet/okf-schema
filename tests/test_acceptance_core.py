"""Acceptance tests for the OKF bundle stakeholder requirements.

Each test walks one declared main path of a stakeholder requirement using the
installed wheel only: console scripts, or the installed Python API, in a
subprocess that cannot import this checkout.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the isolated install harness is POSIX-only",
)


def _digest(directory: Path) -> dict[str, str]:
    """Return a content digest of every file below *directory*."""
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
def test_validate_reports_a_conforming_bundle(installed_distribution, tmp_path: Path) -> None:
    """A freshly created bundle validated from the installed CLI reports no violation."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)

    result = distribution.run(
        "okf-schema", "validate", "--path", "project/bundle", cwd=tmp_path, check=False
    )

    assert result.returncode == 0
    assert "Bundle is conformant" in result.stdout
    assert "0 errors" in result.stdout
    assert "ERROR" not in result.stderr


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
def test_validate_reports_a_non_conforming_bundle_without_changing_it(
    installed_distribution, tmp_path: Path
) -> None:
    """A broken bundle fails with a located violation and keeps every byte on disk."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)
    bundle = tmp_path / "project" / "bundle"
    (bundle / "_schema" / "guide.schema.yaml").write_text(
        "type: object\nrequired:\n  - title\nproperties:\n  title:\n    type: string\n",
        encoding="utf-8",
    )
    (bundle / "broken.md").write_text("---\ntype: guide\n---\n\nBody.\n", encoding="utf-8")
    before = _digest(bundle)

    result = distribution.run(
        "okf-schema", "validate", "--path", "project/bundle", cwd=tmp_path, check=False
    )

    assert result.returncode == 1
    assert "[E4]" in result.stderr
    assert "broken.md" in result.stderr
    assert "'title' is a required property" in result.stderr
    assert _digest(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
def test_create_a_bundle_and_author_a_concept(installed_distribution, tmp_path: Path) -> None:
    """A created concept carries its authored identity and validates in the bundle."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)
    bundle = tmp_path / "project" / "bundle"

    created = distribution.run(
        "okf-schema",
        "new",
        "--path",
        "project/bundle",
        "--name",
        "guides/getting-started",
        "--type",
        "guide",
        "--title",
        "Getting Started",
        cwd=tmp_path,
    )

    concept = bundle / "guides" / "getting-started.md"
    assert created.returncode == 0
    assert concept.is_file()
    text = concept.read_text(encoding="utf-8")
    assert "type: guide" in text
    assert "title: Getting Started" in text

    concept.write_text(
        text.replace("description: ''", "description: First steps").rstrip() + "\n\nBody text.\n",
        encoding="utf-8",
    )
    validation = distribution.run(
        "okf-schema", "validate", "--path", "project/bundle", cwd=tmp_path, check=False
    )
    assert validation.returncode == 0
    assert "ERROR" not in validation.stderr


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_normalize_and_index_a_bundle(installed_distribution, tmp_path: Path) -> None:
    """Lint and index rewrite generated parts and keep authored comments and metadata."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)
    bundle = tmp_path / "project" / "bundle"
    concept = bundle / "concepts" / "idea.md"
    concept.parent.mkdir()
    concept.write_text(
        "---\n"
        "# an authored comment\n"
        "type: idea\n"
        "title: An Idea\n"
        "description: Something to remember\n"
        "tags:\n"
        "  - notes\n"
        "authored_field: keep me\n"
        "---\n\n"
        "Authored body.\n",
        encoding="utf-8",
    )

    distribution.run("okf-schema", "lint", "--path", "project/bundle", cwd=tmp_path)
    distribution.run("okf-schema", "index", "--path", "project/bundle", cwd=tmp_path)

    normalized = concept.read_text(encoding="utf-8")
    assert "# an authored comment" in normalized
    assert "authored_field: keep me" in normalized
    assert "tags: [notes]" in normalized
    assert "Authored body." in normalized
    assert "links: []" in normalized

    root_index = (bundle / "index.md").read_text(encoding="utf-8")
    assert "concepts/" in root_index
    assert "An Idea" in (bundle / "concepts" / "index.md").read_text(encoding="utf-8")


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_inspect_bundle_knowledge_read_only(installed_distribution, tmp_path: Path) -> None:
    """Listing and reading answer from disk and leave every file untouched."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)
    bundle = tmp_path / "project" / "bundle"
    (bundle / "notes").mkdir()
    (bundle / "notes" / "kept.md").write_text(
        "---\ntype: note\ntitle: Kept\ndescription: d\n---\n\nRemembered detail.\n",
        encoding="utf-8",
    )
    distribution.run("okf-schema", "index", "--path", "project/bundle", cwd=tmp_path)
    before = _digest(bundle)

    listed = distribution.run(
        "okf-schema", "list", "--path", "project/bundle", cwd=tmp_path, check=False
    )
    shown = distribution.run(
        "okf-schema", "show", "--path", "project/bundle", "notes/kept.md", cwd=tmp_path, check=False
    )

    assert listed.returncode == 0
    assert "notes/kept.md" in listed.stdout
    assert shown.returncode == 0
    assert "Remembered detail." in shown.stdout
    assert _digest(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
def test_navigate_declared_file_links(installed_distribution, tmp_path: Path) -> None:
    """The installed API resolves each annotated target without changing the value."""
    distribution = installed_distribution
    bundle = tmp_path / "project" / "bundle"
    (bundle / "_schema").mkdir(parents=True)
    (bundle / "_schema" / "guide.schema.yaml").write_text(
        "type: object\n"
        "properties:\n"
        "  evidence:\n"
        "    type: array\n"
        "    items:\n"
        "      type: string\n"
        "      x-okf-link: {resolution: project-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    (bundle / "guides").mkdir()
    (tmp_path / "project" / "evidence").mkdir()
    target = tmp_path / "project" / "evidence" / "measured.txt"
    target.write_text("measured\n", encoding="utf-8")
    (bundle / "guides" / "report.md").write_text(
        "---\ntype: guide\ntitle: Report\nevidence: [evidence/measured.txt]\n---\n\nBody.\n",
        encoding="utf-8",
    )
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from okf_schema._internal.yaml import extract_frontmatter, parse_yaml\n"
        "from okf_schema.file_links import inspect_file_links\n"
        "from okf_schema.validator import load_schema_database\n"
        "bundle = Path(sys.argv[1])\n"
        "project = Path(sys.argv[2])\n"
        "schemas = load_schema_database(bundle / '_schema')\n"
        "text = (bundle / 'guides' / 'report.md').read_text(encoding='utf-8')\n"
        "frontmatter_text, _body = extract_frontmatter(text)\n"
        "frontmatter = parse_yaml(frontmatter_text)\n"
        "results = inspect_file_links(\n"
        "    frontmatter,\n"
        "    schemas['guide'],\n"
        "    bundle / 'guides' / 'report.md',\n"
        "    bundle_root=bundle,\n"
        "    project_root=project,\n"
        ")\n"
        "print(json.dumps([\n"
        "    {\n"
        "        'value': result.value,\n"
        "        'field_path': result.field_path,\n"
        "        'resolution': result.resolution,\n"
        "        'status': result.status,\n"
        "        'resolved_path': str(result.resolved_path),\n"
        "    }\n"
        "    for result in results\n"
        "]))\n"
    )

    completed = distribution.python(script, str(bundle), str(tmp_path / "project"), cwd=tmp_path)

    payload = json.loads(completed.stdout)
    assert len(payload) == 1
    result = payload[0]
    assert result["status"] == "valid"
    assert result["field_path"] == "evidence[0]"
    assert result["resolution"] == "project-relative"
    assert result["value"] == "evidence/measured.txt"
    assert Path(result["resolved_path"]) == target.resolve()


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
def test_check_declared_file_links_on_request(installed_distribution, tmp_path: Path) -> None:
    """Link checking reports existing and missing targets, and only on request."""
    distribution = installed_distribution
    distribution.run("okf-schema", "init", "project", cwd=tmp_path)
    bundle = tmp_path / "project" / "bundle"
    (bundle / "_schema" / "guide.schema.yaml").write_text(
        "type: object\n"
        "properties:\n"
        "  evidence:\n"
        "    type: array\n"
        "    items:\n"
        "      type: string\n"
        "      x-okf-link: {resolution: project-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    (tmp_path / "project" / "evidence").mkdir()
    (tmp_path / "project" / "evidence" / "present.txt").write_text("x\n", encoding="utf-8")
    (bundle / "guide.md").write_text(
        "---\n"
        "type: guide\n"
        "title: Guide\n"
        "description: d\n"
        'generated: {at: "2024-01-01T00:00:00Z"}\n'
        "evidence: [evidence/present.txt, evidence/missing.txt]\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )

    unchecked = distribution.run(
        "okf-schema", "validate", "--path", "project/bundle", cwd=tmp_path, check=False
    )
    checked = distribution.run(
        "okf-schema",
        "validate",
        "--path",
        "project/bundle",
        "--check-links",
        "--project-root",
        "project",
        cwd=tmp_path,
        check=False,
    )

    assert unchecked.returncode == 0
    assert "missing.txt" not in unchecked.stderr

    assert checked.returncode == 1
    assert "[E10]" in checked.stderr
    assert "evidence/missing.txt" in checked.stderr
    assert "evidence/present.txt" not in checked.stderr
