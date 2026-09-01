"""Tests for src/okf_schema/okfkb/scaffold.py — scaffold_kb()."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import yaml
from parametrization import Parametrization

from okf_schema.okfkb.scaffold import scaffold_kb

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_DIRS = {
    "concepts",
    "experiments",
    "findings",
    "playbooks",
    "hypotheses",
    "outcomes",
    "principles",
    "reference",
    "structures",
}

SCHEMA_FILES = {
    "Base.schema.yaml",
    "Concept.schema.yaml",
    "Experiment.schema.yaml",
    "Finding.schema.yaml",
    "Hypothesis.schema.yaml",
    "Outcome.schema.yaml",
    "Playbook.schema.yaml",
    "Principle.schema.yaml",
    "Reference.schema.yaml",
    "Structure.schema.yaml",
}


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


# @tests_req SwRS-OKFSCHEMA-OKFKB-002


def test_scaffold_kb_creates_layout_creates_all_content_dirs(tmp_path: Path) -> None:
    """Creates the 8 canonical content directories."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    for name in CONTENT_DIRS:
        assert (target / name).is_dir(), f"Missing directory: {name}"


def test_scaffold_kb_creates_layout_creates_schema_dir(tmp_path: Path) -> None:
    """Creates the _schema/ directory."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    assert (target / "_schema").is_dir()


def test_scaffold_kb_creates_layout_creates_all_schema_files(tmp_path: Path) -> None:
    """Copies all 8 schema YAML files into _schema/."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    for name in SCHEMA_FILES:
        assert (target / "_schema" / name).is_file(), f"Missing schema file: {name}"


def test_scaffold_kb_creates_layout_creates_index_md(tmp_path: Path) -> None:
    """Creates index.md at the KB root."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    assert (target / "index.md").is_file()


def test_scaffold_kb_creates_layout_creates_log_md(tmp_path: Path) -> None:
    """Creates log.md at the KB root."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    assert (target / "log.md").is_file()


def test_scaffold_kb_creates_layout_creates_target_dir_if_missing(tmp_path: Path) -> None:
    """Creates the target directory if it does not exist."""
    target = tmp_path / "new" / "kb"
    scaffold_kb(target)
    assert target.is_dir()


# ---------------------------------------------------------------------------
# index.md content
# ---------------------------------------------------------------------------


def test_index_md_content_index_has_okf_version(tmp_path: Path) -> None:
    """index.md frontmatter contains okf_version."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "index.md").read_text(encoding="utf-8")
    assert "okf_version" in content


def test_index_md_content_index_frontmatter_is_valid_yaml(tmp_path: Path) -> None:
    """index.md frontmatter parses as valid YAML."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "index.md").read_text(encoding="utf-8")
    # Extract YAML between --- delimiters
    parts = content.split("---")
    assert len(parts) >= 3, "Expected --- frontmatter delimiters in index.md"
    fm = yaml.safe_load(parts[1])
    assert fm is not None
    assert "okf_version" in fm


def test_index_md_content_index_okf_version_value(tmp_path: Path) -> None:
    """index.md okf_version is '0.2'."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "index.md").read_text(encoding="utf-8")
    parts = content.split("---")
    fm = yaml.safe_load(parts[1])
    assert fm["okf_version"] == "0.2"


# ---------------------------------------------------------------------------
# log.md content
# ---------------------------------------------------------------------------


def test_log_md_content_log_has_date_heading(tmp_path: Path) -> None:
    """log.md contains today's date as a heading."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "log.md").read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()
    assert today in content


def test_log_md_content_log_has_heading_marker(tmp_path: Path) -> None:
    """log.md has a markdown heading (##)."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "log.md").read_text(encoding="utf-8")
    assert "##" in content


# ---------------------------------------------------------------------------
# Schema file validity
# ---------------------------------------------------------------------------


@Parametrization.autodetect_parameters()
@Parametrization.case(name="base", schema_name="Base.schema.yaml")
@Parametrization.case(name="concept", schema_name="Concept.schema.yaml")
@Parametrization.case(name="experiment", schema_name="Experiment.schema.yaml")
@Parametrization.case(name="finding", schema_name="Finding.schema.yaml")
@Parametrization.case(name="hypothesis", schema_name="Hypothesis.schema.yaml")
@Parametrization.case(name="outcome", schema_name="Outcome.schema.yaml")
@Parametrization.case(name="playbook", schema_name="Playbook.schema.yaml")
@Parametrization.case(name="principle", schema_name="Principle.schema.yaml")
@Parametrization.case(name="reference", schema_name="Reference.schema.yaml")
@Parametrization.case(name="structure", schema_name="Structure.schema.yaml")
def test_schema_files_are_valid_yaml_schema_file_is_valid_yaml(
    tmp_path: Path, schema_name: str
) -> None:
    """Each schema file parses without errors."""
    target = tmp_path / "kb"
    scaffold_kb(target)
    content = (target / "_schema" / schema_name).read_bytes()
    result = yaml.safe_load(content)
    assert result is not None, f"{schema_name} parsed to None (empty file?)"


# ---------------------------------------------------------------------------
# Error handling: non-empty dir without --force
# ---------------------------------------------------------------------------


def test_scaffold_kb_error_on_non_empty_errors_on_nonempty_dir(tmp_path: Path) -> None:
    """Raises RuntimeError when PATH is non-empty and force=False."""
    target = tmp_path / "kb"
    target.mkdir()
    (target / "existing.txt").write_text("existing", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not empty"):
        scaffold_kb(target, force=False)


def test_scaffold_kb_error_on_non_empty_error_message_mentions_force(tmp_path: Path) -> None:
    """Error message mentions --force as the remedy."""
    target = tmp_path / "kb"
    target.mkdir()
    (target / "existing.txt").write_text("existing", encoding="utf-8")
    with pytest.raises(RuntimeError, match="[Ff]orce"):
        scaffold_kb(target, force=False)


def test_scaffold_kb_error_on_non_empty_no_error_on_empty_dir(tmp_path: Path) -> None:
    """Does not raise when PATH exists but is empty."""
    target = tmp_path / "kb"
    target.mkdir()
    scaffold_kb(target)  # should not raise
    assert (target / "index.md").is_file()


# ---------------------------------------------------------------------------
# --force flag
# ---------------------------------------------------------------------------


def test_scaffold_kb_force_force_overwrites_existing(tmp_path: Path) -> None:
    """force=True does not raise on non-empty directory."""
    target = tmp_path / "kb"
    target.mkdir()
    (target / "existing.txt").write_text("existing", encoding="utf-8")
    scaffold_kb(target, force=True)  # should not raise
    assert (target / "index.md").is_file()


def test_scaffold_kb_force_force_creates_all_dirs(tmp_path: Path) -> None:
    """force=True creates all content dirs even on non-empty target."""
    target = tmp_path / "kb"
    target.mkdir()
    (target / "junk.md").write_text("junk", encoding="utf-8")
    scaffold_kb(target, force=True)
    for name in CONTENT_DIRS:
        assert (target / name).is_dir()


def test_scaffold_kb_force_force_overwrites_index(tmp_path: Path) -> None:
    """force=True overwrites an existing index.md."""
    target = tmp_path / "kb"
    target.mkdir()
    (target / "index.md").write_text("old content", encoding="utf-8")
    scaffold_kb(target, force=True)
    content = (target / "index.md").read_text(encoding="utf-8")
    assert "okf_version" in content
