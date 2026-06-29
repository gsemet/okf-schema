"""Shared pytest fixtures for okf-schema tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def valid_bundle(tmp_path: Path) -> Path:
    """Create a complete valid OKF bundle."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    # Root index.md with frontmatter
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.1"\n---\n\n# Test Bundle\n',
        encoding="utf-8",
    )

    # Root log.md
    (bundle / "log.md").write_text("## 2024-01-01\n\nInitial log.\n", encoding="utf-8")

    # Subdirectory with concepts
    subdir = bundle / "subdir"
    subdir.mkdir()
    (subdir / "concept-a.md").write_text(
        "---\ntype: concept\ntitle: Concept A\n"
        "description: First concept\ntags: [a, b]\n---\n\nBody of A.\n",
        encoding="utf-8",
    )
    (subdir / "concept-b.md").write_text(
        "---\ntype: concept\ntitle: Concept B\n"
        "description: Second concept\ntags: [b, c]\n---\n\n"
        "Body of B linking to [A](concept-a.md).\n",
        encoding="utf-8",
    )

    # Another subdirectory
    subdir2 = bundle / "another"
    subdir2.mkdir()
    (subdir2 / "concept-c.md").write_text(
        "---\ntype: reference\ntitle: Concept C\ndescription: Third concept\n---\n\nBody of C.\n",
        encoding="utf-8",
    )

    return bundle


@pytest.fixture
def invalid_bundle(tmp_path: Path) -> Path:
    """Create a bundle with multiple validation errors."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    # E1: no frontmatter
    (bundle / "no-frontmatter.md").write_text("Just body text.\n", encoding="utf-8")

    # E2: missing type
    (bundle / "missing-type.md").write_text(
        "---\ntitle: Missing Type\n---\n\nBody.\n",
        encoding="utf-8",
    )

    # E3: non-root index with frontmatter
    subdir = bundle / "subdir"
    subdir.mkdir()
    (subdir / "index.md").write_text(
        "---\ntype: index\n---\n\n# Subdir Index\n",
        encoding="utf-8",
    )

    # E5: unflatten list
    (bundle / "unflatten.md").write_text(
        "---\ntype: concept\ntitle: Unflatten\ntags: [[a, b], c]\n---\n\nBody.\n",
        encoding="utf-8",
    )

    # W2: broken link
    (bundle / "broken-link.md").write_text(
        "---\ntype: concept\ntitle: Broken Link\n---\n\nSee [missing](nonexistent.md).\n",
        encoding="utf-8",
    )

    return bundle


@pytest.fixture
def empty_bundle(tmp_path: Path) -> Path:
    """Create an empty bundle directory."""
    bundle = tmp_path / "empty-bundle"
    bundle.mkdir()
    return bundle


@pytest.fixture
def schema_db(tmp_path: Path) -> Path:
    """Create a directory with test schema files."""
    db = tmp_path / "schemas"
    db.mkdir()

    (db / "concept.schema.json").write_text(
        '{"type": "object", "properties": {"type": {"type": "string"}, '
        '"title": {"type": "string"}}, "required": ["type", "title"]}',
        encoding="utf-8",
    )

    (db / "reference.schema.yaml").write_text(
        "type: object\nproperties:\n  type:\n    type: string\n  url:\n    type: string\n",
        encoding="utf-8",
    )

    return db


@pytest.fixture
def nested_list_bundle(tmp_path: Path) -> Path:
    """Create a bundle with deeply nested lists in frontmatter."""
    bundle = tmp_path / "nested-bundle"
    bundle.mkdir()

    (bundle / "index.md").write_text(
        '---\nokf_version: "0.1"\n---\n\n# Nested\n',
        encoding="utf-8",
    )

    (bundle / "deep.md").write_text(
        "---\ntype: concept\ntitle: Deep\n"
        "tags: [[[[a]]], [[[b, c]]]]\n"
        "items: [[1, 2], [3, [4, 5]]]\n---\n\nBody.\n",
        encoding="utf-8",
    )

    return bundle
