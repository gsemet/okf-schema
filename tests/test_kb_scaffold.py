"""Tests for src/okf_schema/kb/scaffold.py — scaffold_kb()."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import yaml

from okf_schema.kb.scaffold import scaffold_kb

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_DIRS = {
    "concepts",
    "experiments",
    "findings",
    "guides",
    "ideas",
    "principles",
    "reference",
    "structures",
}

SCHEMA_FILES = {
    "Base.schema.yaml",
    "Concept.schema.yaml",
    "Experiment.schema.yaml",
    "Finding.schema.yaml",
    "Playbook.schema.yaml",
    "Principle.schema.yaml",
    "Reference.schema.yaml",
    "Structure.schema.yaml",
}


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestScaffoldKbCreatesLayout:
    """scaffold_kb creates the canonical KB layout."""

    def test_creates_all_content_dirs(self, tmp_path: Path) -> None:
        """Creates the 8 canonical content directories."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        for name in CONTENT_DIRS:
            assert (target / name).is_dir(), f"Missing directory: {name}"

    def test_creates_schema_dir(self, tmp_path: Path) -> None:
        """Creates the _schema/ directory."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        assert (target / "_schema").is_dir()

    def test_creates_all_schema_files(self, tmp_path: Path) -> None:
        """Copies all 8 schema YAML files into _schema/."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        for name in SCHEMA_FILES:
            assert (target / "_schema" / name).is_file(), f"Missing schema file: {name}"

    def test_creates_index_md(self, tmp_path: Path) -> None:
        """Creates index.md at the KB root."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        assert (target / "index.md").is_file()

    def test_creates_log_md(self, tmp_path: Path) -> None:
        """Creates log.md at the KB root."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        assert (target / "log.md").is_file()

    def test_creates_target_dir_if_missing(self, tmp_path: Path) -> None:
        """Creates the target directory if it does not exist."""
        target = tmp_path / "new" / "kb"
        scaffold_kb(target)
        assert target.is_dir()


# ---------------------------------------------------------------------------
# index.md content
# ---------------------------------------------------------------------------


class TestIndexMdContent:
    """index.md has valid OKF frontmatter."""

    def test_index_has_okf_version(self, tmp_path: Path) -> None:
        """index.md frontmatter contains okf_version."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        content = (target / "index.md").read_text(encoding="utf-8")
        assert "okf_version" in content

    def test_index_frontmatter_is_valid_yaml(self, tmp_path: Path) -> None:
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

    def test_index_okf_version_value(self, tmp_path: Path) -> None:
        """index.md okf_version is '0.1'."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        content = (target / "index.md").read_text(encoding="utf-8")
        parts = content.split("---")
        fm = yaml.safe_load(parts[1])
        assert fm["okf_version"] == "0.1"


# ---------------------------------------------------------------------------
# log.md content
# ---------------------------------------------------------------------------


class TestLogMdContent:
    """log.md has a date heading."""

    def test_log_has_date_heading(self, tmp_path: Path) -> None:
        """log.md contains today's date as a heading."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        content = (target / "log.md").read_text(encoding="utf-8")
        today = datetime.date.today().isoformat()
        assert today in content

    def test_log_has_heading_marker(self, tmp_path: Path) -> None:
        """log.md has a markdown heading (##)."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        content = (target / "log.md").read_text(encoding="utf-8")
        assert "##" in content


# ---------------------------------------------------------------------------
# Schema file validity
# ---------------------------------------------------------------------------


class TestSchemaFilesAreValidYaml:
    """Schema files copied from bundled data are valid YAML."""

    @pytest.mark.parametrize("schema_name", sorted(SCHEMA_FILES))
    def test_schema_file_is_valid_yaml(self, tmp_path: Path, schema_name: str) -> None:
        """Each schema file parses without errors."""
        target = tmp_path / "kb"
        scaffold_kb(target)
        content = (target / "_schema" / schema_name).read_bytes()
        result = yaml.safe_load(content)
        assert result is not None, f"{schema_name} parsed to None (empty file?)"


# ---------------------------------------------------------------------------
# Error handling: non-empty dir without --force
# ---------------------------------------------------------------------------


class TestScaffoldKbErrorOnNonEmpty:
    """scaffold_kb raises an error when target is non-empty and force=False."""

    def test_errors_on_nonempty_dir(self, tmp_path: Path) -> None:
        """Raises RuntimeError when PATH is non-empty and force=False."""
        target = tmp_path / "kb"
        target.mkdir()
        (target / "existing.txt").write_text("existing", encoding="utf-8")
        with pytest.raises(RuntimeError, match="not empty"):
            scaffold_kb(target, force=False)

    def test_error_message_mentions_force(self, tmp_path: Path) -> None:
        """Error message mentions --force as the remedy."""
        target = tmp_path / "kb"
        target.mkdir()
        (target / "existing.txt").write_text("existing", encoding="utf-8")
        with pytest.raises(RuntimeError, match="[Ff]orce"):
            scaffold_kb(target, force=False)

    def test_no_error_on_empty_dir(self, tmp_path: Path) -> None:
        """Does not raise when PATH exists but is empty."""
        target = tmp_path / "kb"
        target.mkdir()
        scaffold_kb(target)  # should not raise
        assert (target / "index.md").is_file()


# ---------------------------------------------------------------------------
# --force flag
# ---------------------------------------------------------------------------


class TestScaffoldKbForce:
    """scaffold_kb with force=True overwrites existing files."""

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """force=True does not raise on non-empty directory."""
        target = tmp_path / "kb"
        target.mkdir()
        (target / "existing.txt").write_text("existing", encoding="utf-8")
        scaffold_kb(target, force=True)  # should not raise
        assert (target / "index.md").is_file()

    def test_force_creates_all_dirs(self, tmp_path: Path) -> None:
        """force=True creates all content dirs even on non-empty target."""
        target = tmp_path / "kb"
        target.mkdir()
        (target / "junk.md").write_text("junk", encoding="utf-8")
        scaffold_kb(target, force=True)
        for name in CONTENT_DIRS:
            assert (target / name).is_dir()

    def test_force_overwrites_index(self, tmp_path: Path) -> None:
        """force=True overwrites an existing index.md."""
        target = tmp_path / "kb"
        target.mkdir()
        (target / "index.md").write_text("old content", encoding="utf-8")
        scaffold_kb(target, force=True)
        content = (target / "index.md").read_text(encoding="utf-8")
        assert "okf_version" in content
