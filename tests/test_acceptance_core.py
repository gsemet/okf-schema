"""Acceptance tests: the StRS main paths of the core scope, through the installed console scripts.

Each test walks one declared main path in a fresh temporary project with the installed
``okf-schema`` wheel, with no source checkout on ``PYTHONPATH``.
"""

from __future__ import annotations

import json
from pathlib import Path


def _snapshot(root: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _new_bundle(installed_wheel, tmp_path: Path) -> Path:
    installed_wheel.run("okf-schema", "init", "project", cwd=tmp_path)
    return tmp_path / "project" / "bundle"


# @accepts_req StRS-OKFSCHEMA-CORE-001#S1
def test_validate_a_conforming_bundle(installed_wheel, tmp_path: Path) -> None:
    """A bundle created and authored with the CLI validates as conformant, strictly too."""
    bundle = _new_bundle(installed_wheel, tmp_path)
    installed_wheel.run(
        "okf-schema",
        "new",
        "--path",
        str(bundle),
        "--name",
        "guides/intro",
        "--type",
        "guide",
        "--title",
        "Intro",
        cwd=tmp_path,
    )

    result = installed_wheel.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)

    assert result.returncode == 0
    assert "Bundle is conformant" in result.stdout


# @accepts_req StRS-OKFSCHEMA-CORE-001#S2
def test_report_a_non_conforming_bundle_without_changing_it(
    installed_wheel, tmp_path: Path
) -> None:
    """Violations are reported with a failing exit status and no authored byte changes."""
    bundle = _new_bundle(installed_wheel, tmp_path)
    (bundle / "notes.md").write_text("Just body text.\n", encoding="utf-8")
    (bundle / "nested.md").write_text(
        "---\ntype: concept\ntitle: Nested\n# kept comment\ntags: [[a, b], c]\n---\n\nBody.\n",
        encoding="utf-8",
    )
    before = _snapshot(bundle)

    result = installed_wheel.run(
        "okf-schema", "validate", "--path", str(bundle), cwd=tmp_path, check=False
    )

    assert result.returncode == 1, result.stdout
    output = result.stdout + result.stderr
    assert "E1" in output
    assert "notes.md" in output
    assert "E5" in output
    assert "nested.md" in output
    assert _snapshot(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-002#S1
def test_create_a_bundle_and_author_a_concept(installed_wheel, tmp_path: Path) -> None:
    """init and new create a bundle and a typed concept that show reads back."""
    bundle = _new_bundle(installed_wheel, tmp_path)
    assert (bundle / "index.md").is_file()
    assert (bundle / "_schema").is_dir()

    installed_wheel.run(
        "okf-schema",
        "new",
        "--path",
        str(bundle),
        "--name",
        "concepts/cache",
        "--type",
        "concept",
        "--title",
        "Cache",
        cwd=tmp_path,
    )
    concept = bundle / "concepts" / "cache.md"
    concept.write_text(
        concept.read_text(encoding="utf-8") + "\nThe cache keeps hot entries.\n",
        encoding="utf-8",
    )
    shown = installed_wheel.run(
        "okf-schema", "show", "--path", str(bundle), "concepts/cache.md", cwd=tmp_path
    )

    assert "type: concept" in concept.read_text(encoding="utf-8")
    assert "Cache" in shown.stdout
    assert "The cache keeps hot entries." in shown.stdout


# @accepts_req StRS-OKFSCHEMA-CORE-002#S2
def test_normalize_and_index_a_bundle(installed_wheel, tmp_path: Path) -> None:
    """lint previews, then normalizes frontmatter; index writes indexes; authored text stays."""
    bundle = _new_bundle(installed_wheel, tmp_path)
    concept = bundle / "concepts" / "cache.md"
    concept.parent.mkdir()
    original = (
        "---\ntype: concept\ntitle: Cache\n# reviewed by the team\n"
        "tags:\n  - storage\n  - [hot, cold]\nowner_note: keep\n---\n\n# Cache\n\nAuthored body.\n"
    )
    concept.write_text(original, encoding="utf-8")

    check = installed_wheel.run(
        "okf-schema", "lint", "--path", str(bundle), "--check", cwd=tmp_path, check=False
    )
    diff = installed_wheel.run(
        "okf-schema", "lint", "--path", str(bundle), "--diff", cwd=tmp_path, check=False
    )
    assert check.returncode == 1, check.stdout
    assert "tags" in diff.stdout
    assert concept.read_text(encoding="utf-8") == original

    installed_wheel.run("okf-schema", "lint", "--path", str(bundle), cwd=tmp_path)
    installed_wheel.run("okf-schema", "index", "--path", str(bundle), cwd=tmp_path)

    text = concept.read_text(encoding="utf-8")
    assert "tags:\n- storage\n- hot\n- cold\n" in text
    assert "# reviewed by the team" in text
    assert "owner_note: keep" in text
    assert text.endswith("# Cache\n\nAuthored body.\n")
    assert "cache" in (bundle / "concepts" / "index.md").read_text(encoding="utf-8").lower()
    installed_wheel.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)


# @accepts_req StRS-OKFSCHEMA-CORE-002#S3
def test_inspect_bundle_knowledge_read_only(installed_wheel, tmp_path: Path) -> None:
    """list, show, stats and backlinks answer questions without writing to the bundle."""
    bundle = _new_bundle(installed_wheel, tmp_path)
    (bundle / "concepts").mkdir()
    (bundle / "concepts" / "alpha.md").write_text(
        "---\ntype: concept\ntitle: Alpha\ndescription: First\n---\n\nSee [Beta](beta.md).\n",
        encoding="utf-8",
    )
    (bundle / "concepts" / "beta.md").write_text(
        "---\ntype: concept\ntitle: Beta\ndescription: Second\n---\n\nBeta body.\n",
        encoding="utf-8",
    )
    before = _snapshot(bundle)

    listed = installed_wheel.run("okf-schema", "list", "--path", str(bundle), cwd=tmp_path)
    shown = installed_wheel.run(
        "okf-schema", "show", "--path", str(bundle), "concepts/beta.md", cwd=tmp_path
    )
    stats = installed_wheel.run("okf-schema", "stats", "--path", str(bundle), cwd=tmp_path)
    backlinks = installed_wheel.run(
        "okf-schema", "backlinks", "--path", str(bundle), "concepts/beta.md", cwd=tmp_path
    )

    assert "Alpha" in listed.stdout
    assert "Beta" in listed.stdout
    assert "Beta body." in shown.stdout
    assert "Health:" in stats.stdout
    assert "alpha" in backlinks.stdout
    assert _snapshot(bundle) == before


def _linked_bundle(installed_wheel, tmp_path: Path) -> Path:
    bundle = _new_bundle(installed_wheel, tmp_path)
    (bundle / "_schema" / "guide.schema.yaml").write_text(
        "type: object\nproperties:\n  see_also:\n    type: array\n    items:\n"
        "      type: string\n      x-okf-link: {resolution: bundle-relative, syntax: plain}\n",
        encoding="utf-8",
    )
    (bundle / "guides").mkdir()
    (bundle / "guides" / "setup.md").write_text(
        "---\ntype: guide\ntitle: Setup\ndescription: Setup guide\n"
        "see_also: [guides/install.md]\n---\n\nSetup body.\n",
        encoding="utf-8",
    )
    return bundle


# @accepts_req StRS-OKFSCHEMA-CORE-003#S1
def test_navigate_declared_file_links(installed_wheel, tmp_path: Path) -> None:
    """A consumer finds each declared file link, its root and its target; values stay strings."""
    bundle = _linked_bundle(installed_wheel, tmp_path)
    (bundle / "guides" / "install.md").write_text(
        "---\ntype: guide\ntitle: Install\ndescription: Install guide\n---\n\nInstall body.\n",
        encoding="utf-8",
    )
    before = _snapshot(bundle)
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from okf_schema.api import inspect_file_links, show_bundle\n"
        "from okf_schema.validator import load_schema_database\n"
        "bundle = Path(sys.argv[1])\n"
        "concept = show_bundle(bundle, 'guides/setup.md')\n"
        "schema = load_schema_database(bundle / '_schema')['guide']\n"
        "results = inspect_file_links(concept.frontmatter, schema,"
        " bundle / 'guides/setup.md', bundle_root=bundle)\n"
        "print(json.dumps({'see_also': concept.frontmatter['see_also'], 'results': ["
        "{'field': r.field_path, 'resolution': r.resolution, 'status': r.status,"
        " 'resolved': str(r.resolved_path)} for r in results]}))\n"
    )

    inspected = installed_wheel.run("python", "-c", script, str(bundle), cwd=tmp_path)
    navigation = json.loads(inspected.stdout)
    target = Path(navigation["results"][0]["resolved"])
    shown = installed_wheel.run(
        "okf-schema",
        "show",
        "--path",
        str(bundle),
        target.relative_to(bundle.resolve()).as_posix(),
        cwd=tmp_path,
    )

    assert navigation["see_also"] == ["guides/install.md"]
    assert navigation["results"] == [
        {
            "field": "see_also[0]",
            "resolution": "bundle-relative",
            "status": "valid",
            "resolved": str((bundle / "guides" / "install.md").resolve()),
        }
    ]
    assert "Install body." in shown.stdout
    assert _snapshot(bundle) == before


# @accepts_req StRS-OKFSCHEMA-CORE-003#S2
def test_check_declared_file_links_on_request(installed_wheel, tmp_path: Path) -> None:
    """Default validation ignores link targets; --check-links reports a missing one, read-only."""
    bundle = _linked_bundle(installed_wheel, tmp_path)
    before = _snapshot(bundle)

    default = installed_wheel.run("okf-schema", "validate", "--path", str(bundle), cwd=tmp_path)
    checked = installed_wheel.run(
        "okf-schema",
        "validate",
        "--path",
        str(bundle),
        "--check-links",
        cwd=tmp_path,
        check=False,
    )

    assert "E10" not in default.stdout + default.stderr
    assert checked.returncode == 1
    assert "E10" in checked.stdout + checked.stderr
    assert "see_also[0]" in checked.stdout + checked.stderr
    assert _snapshot(bundle) == before

    (bundle / "guides" / "install.md").write_text(
        "---\ntype: guide\ntitle: Install\ndescription: Install guide\n---\n\nInstall body.\n",
        encoding="utf-8",
    )
    installed_wheel.run(
        "okf-schema", "validate", "--path", str(bundle), "--check-links", cwd=tmp_path
    )
