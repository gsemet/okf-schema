"""Scaffold a KB (knowledge-base) bundle directory layout.

The canonical KB layout contains 8 content directories, a ``_schema/``
directory with 8 bundled YAML schema files, ``index.md``, and ``log.md``.
"""

from __future__ import annotations

import datetime
from importlib.resources import files
from pathlib import Path

import click

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Content directories created at the KB root.
CONTENT_DIRS: tuple[str, ...] = (
    "concepts",
    "experiments",
    "findings",
    "guides",
    "ideas",
    "principles",
    "reference",
    "structures",
)

#: Bundled schema file names to copy into ``_schema/``.
SCHEMA_FILES: tuple[str, ...] = (
    "Base.schema.yaml",
    "Concept.schema.yaml",
    "Experiment.schema.yaml",
    "Finding.schema.yaml",
    "Playbook.schema.yaml",
    "Principle.schema.yaml",
    "Reference.schema.yaml",
    "Structure.schema.yaml",
)

_INDEX_TEMPLATE = """\
---
okf_version: "0.1"
links: []
backlinks: []
---

# knowledge
"""

_LOG_TEMPLATE = """\
# Update Log

## {today}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scaffold_kb(path: Path, force: bool = False) -> None:
    """Scaffold a knowledge-base bundle at *path*.

    Creates the canonical KB folder layout with 8 content directories,
    8 schema YAML files (copied from bundled package data), ``index.md``,
    and ``log.md``.

    Args:
        path: Target directory for the KB bundle.  Created if it does not
            exist; must be empty (or non-existent) unless *force* is ``True``.
        force: When ``True``, overwrite existing files without raising an
            error even if *path* is non-empty.

    Raises:
        RuntimeError: If *path* exists and is non-empty and *force* is
            ``False``.
    """
    if path.exists() and any(path.iterdir()) and not force:
        raise RuntimeError(
            f"Directory '{path}' already exists and is not empty. Use --force to overwrite."
        )

    path.mkdir(parents=True, exist_ok=True)

    created_dirs: list[str] = []
    created_files: list[str] = []

    # --- content directories -----------------------------------------------
    for name in CONTENT_DIRS:
        dir_path = path / name
        dir_path.mkdir(exist_ok=True)
        created_dirs.append(name + "/")

    # --- _schema directory and YAML files -----------------------------------
    schema_dir = path / "_schema"
    schema_dir.mkdir(exist_ok=True)

    schema_pkg = files("okf_schema.data.kb").joinpath("_schema")
    for schema_name in SCHEMA_FILES:
        src = schema_pkg.joinpath(schema_name)
        dst = schema_dir / schema_name
        dst.write_bytes(src.read_bytes())
        created_files.append(f"_schema/{schema_name}")

    # --- index.md -----------------------------------------------------------
    index_path = path / "index.md"
    index_path.write_text(_INDEX_TEMPLATE, encoding="utf-8")
    created_files.append("index.md")

    # --- log.md -------------------------------------------------------------
    log_path = path / "log.md"
    today = datetime.date.today().isoformat()
    log_path.write_text(_LOG_TEMPLATE.format(today=today), encoding="utf-8")
    created_files.append("log.md")

    # --- summary ------------------------------------------------------------
    click.echo(f"Scaffolded KB bundle at '{path}':")
    for name in created_dirs:
        click.echo(f"  created  {name}")
    for name in created_files:
        click.echo(f"  created  {name}")
