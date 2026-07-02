"""Tests for CLI core commands: init, new, validate, format."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from okf_schema.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
BUNDLE_FIXTURES = FIXTURES / "bundle"
VALID_BUNDLE = BUNDLE_FIXTURES / "valid"


# ---------------------------------------------------------------------------
# Global options
# ---------------------------------------------------------------------------


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_version(self) -> None:
        """--version prints version and exits 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "okf-schema" in result.output
        assert "." in result.output

    def test_no_subcommand_shows_help(self) -> None:
        """Running with no subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_verbose_quiet_are_accepted(self) -> None:
        """--verbose and --quiet are accepted without error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--version"])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["--quiet", "--version"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


class TestInit:
    """Tests for the init subcommand."""

    def test_creates_bundle_structure(self, tmp_path: Path) -> None:
        """init creates bundle/, _schema/, index.md, and log.md."""
        runner = CliRunner()
        name = tmp_path / "mybundle"
        result = runner.invoke(cli, ["init", str(name)])
        assert result.exit_code == 0
        assert (name / "bundle").is_dir()
        assert (name / "bundle" / "_schema").is_dir()
        assert (name / "bundle" / "index.md").exists()
        assert (name / "bundle" / "log.md").exists()

    def test_index_md_has_frontmatter(self, tmp_path: Path) -> None:
        """index.md contains okf_version frontmatter."""
        runner = CliRunner()
        name = tmp_path / "mybundle"
        runner.invoke(cli, ["init", str(name)])
        text = (name / "bundle" / "index.md").read_text(encoding="utf-8")
        assert "okf_version" in text

    def test_log_md_has_date_heading(self, tmp_path: Path) -> None:
        """log.md contains a date heading."""
        runner = CliRunner()
        name = tmp_path / "mybundle"
        runner.invoke(cli, ["init", str(name)])
        text = (name / "bundle" / "log.md").read_text(encoding="utf-8")
        assert text.startswith("## ")
        # Should contain today's date-ish format YYYY-MM-DD
        import datetime

        today = datetime.date.today().isoformat()
        assert today in text

    def test_exits_1_when_directory_exists(self, tmp_path: Path) -> None:
        """init exits 1 if target already exists."""
        runner = CliRunner()
        name = tmp_path / "mybundle"
        name.mkdir()
        result = runner.invoke(cli, ["init", str(name)])
        assert result.exit_code == 1
        assert "already exists" in result.output.lower() or "exists" in result.output.lower()

    def test_creates_base_schema(self, tmp_path: Path) -> None:
        """init creates _base.schema.yaml with OKF fields."""
        runner = CliRunner()
        name = tmp_path / "mybundle"
        result = runner.invoke(cli, ["init", str(name)])
        assert result.exit_code == 0
        base_schema = name / "bundle" / "_schema" / "_base.schema.yaml"
        assert base_schema.exists()
        text = base_schema.read_text(encoding="utf-8")
        assert "type:" in text
        assert "title:" in text
        assert "description:" in text
        assert "resource:" in text
        assert "tags:" in text
        assert "timestamp:" in text
        assert "required:" in text
        assert "- type" in text
        assert "additionalProperties: true" in text


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


class TestNew:
    """Tests for the new subcommand."""

    def test_creates_file_with_frontmatter(self, tmp_path: Path) -> None:
        """new creates a concept file with frontmatter."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        result = runner.invoke(
            cli,
            ["new", "--path", str(root), "--name", "concepts/idea"],
        )
        assert result.exit_code == 0
        file_path = root / "concepts" / "idea.md"
        assert file_path.exists()
        text = file_path.read_text(encoding="utf-8")
        assert "type:" in text
        assert "title:" in text
        assert "description:" in text
        assert "tags:" in text

    def test_uses_provided_type_and_title(self, tmp_path: Path) -> None:
        """new respects --type and --title."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        result = runner.invoke(
            cli,
            [
                "new",
                "--path",
                str(root),
                "--name",
                "concepts/idea",
                "--type",
                "pattern",
                "--title",
                "My Idea",
            ],
        )
        assert result.exit_code == 0
        text = (root / "concepts" / "idea.md").read_text(encoding="utf-8")
        assert "type: pattern" in text
        assert "title: My Idea" in text

    def test_defaults_type_and_title(self, tmp_path: Path) -> None:
        """new defaults type to 'concept' and title to stem."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        result = runner.invoke(
            cli,
            ["new", "--path", str(root), "--name", "concepts/idea"],
        )
        assert result.exit_code == 0
        text = (root / "concepts" / "idea.md").read_text(encoding="utf-8")
        assert "type: concept" in text
        assert "title: idea" in text

    def test_exits_2_when_path_missing(self, tmp_path: Path) -> None:
        """new exits 2 when --path is missing."""
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "--name", "concepts/idea"])
        assert result.exit_code == 2
        assert "--path" in result.output or "Missing option" in result.output

    def test_exits_2_when_name_missing(self, tmp_path: Path) -> None:
        """new exits 2 when --name is missing."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        result = runner.invoke(cli, ["new", "--path", str(root)])
        assert result.exit_code == 2
        assert "--name" in result.output or "Missing option" in result.output

    def test_exits_1_when_file_exists(self, tmp_path: Path) -> None:
        """new exits 1 when file already exists."""
        runner = CliRunner()
        root = tmp_path / "root"
        root.mkdir()
        (root / "concepts").mkdir()
        (root / "concepts" / "idea.md").write_text("# Existing\n", encoding="utf-8")
        result = runner.invoke(
            cli,
            ["new", "--path", str(root), "--name", "concepts/idea"],
        )
        assert result.exit_code == 1
        assert "already exists" in result.output.lower() or "exists" in result.output.lower()


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidate:
    """Tests for the validate subcommand."""

    def test_valid_bundle_exits_0(self) -> None:
        """validate exits 0 for a conformant bundle."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--path", str(VALID_BUNDLE)])
        assert result.exit_code == 0
        assert "conformant" in result.output.lower() or "0 error" in result.output.lower()

    def test_invalid_bundle_exits_1(self) -> None:
        """validate exits 1 for a non-conformant bundle."""
        runner = CliRunner()
        invalid = BUNDLE_FIXTURES / "invalid" / "e1-no-frontmatter"
        result = runner.invoke(cli, ["validate", "--path", str(invalid)])
        assert result.exit_code == 1
        assert "E1" in result.output

    def test_with_schema_db(self) -> None:
        """validate accepts --schema-db option and applies it."""
        runner = CliRunner()
        schema_db = FIXTURES / "schema"
        result = runner.invoke(
            cli,
            ["validate", "--path", str(VALID_BUNDLE), "--schema-db", str(schema_db)],
        )
        # The fixture schema requires a "timestamp" field.  The bundle
        # includes ``timestamp: 2024-01-15`` which is now transparently
        # normalised to a string, so validation passes.
        assert result.exit_code == 0
        assert "conformant" in result.output.lower()

    def test_nonexistent_bundle(self) -> None:
        """validate exits 2 for nonexistent bundle (Click usage error)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--path", str(VALID_BUNDLE / "does-not-exist")])
        assert result.exit_code == 2
        assert "does not exist" in result.output.lower() or "not found" in result.output.lower()

    def test_strict_exits_1_on_warnings(self) -> None:
        """validate --strict exits 1 when only warnings are present."""
        runner = CliRunner()
        bundle = BUNDLE_FIXTURES / "invalid" / "w7-block-list"
        result = runner.invoke(cli, ["validate", "--path", str(bundle), "--strict"])
        assert result.exit_code == 1
        assert "strict mode" in result.output.lower()

    def test_strict_exits_0_when_clean(self) -> None:
        """validate --strict exits 0 for a fully clean bundle."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--path", str(VALID_BUNDLE), "--strict"])
        assert result.exit_code == 0

    def test_validate_warnings_only_no_strict_exits_0(self) -> None:
        """validate without --strict exits 0 even with warnings."""
        runner = CliRunner()
        bundle = BUNDLE_FIXTURES / "invalid" / "w7-block-list"
        result = runner.invoke(cli, ["validate", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "warning" in result.output.lower()

    def test_validate_not_a_directory(self) -> None:
        """validate exits 2 when path is a file (Click usage error)."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["validate", "--path", str(VALID_BUNDLE / "subdir" / "concept-a.md")]
        )
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------


class TestLint:
    """Tests for the lint subcommand."""

    def test_modifies_files_in_place(self, tmp_path: Path) -> None:
        """lint converts block lists to inline in-place."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["lint", "--path", str(bundle), "--no-links"])
        assert result.exit_code == 0
        text = concept.read_text(encoding="utf-8")
        assert "tags: [a, b]" in text

    def test_modifies_files_with_links_default(self, tmp_path: Path) -> None:
        """lint with default --links adds links/backlinks fields."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["lint", "--path", str(bundle)])
        assert result.exit_code == 0
        text = concept.read_text(encoding="utf-8")
        assert "tags: [a, b]" in text
        assert "links: []" in text
        assert "backlinks: []" in text

    def test_check_exits_1_when_changes_needed(self, tmp_path: Path) -> None:
        """lint --check exits 1 when block lists are found."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["lint", "--path", str(bundle), "--check", "--no-links"])
        assert result.exit_code == 1
        assert "would lint" in result.output.lower()

    def test_check_exits_0_when_no_changes(self, tmp_path: Path) -> None:
        """lint --check exits 0 when all lists are already inline."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: concept\ntitle: Test\ntags: [a, b]\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["lint", "--path", str(bundle), "--check", "--no-links"])
        assert result.exit_code == 0

    def test_check_exits_0_with_links_when_already_linted(self, tmp_path: Path) -> None:
        """lint --check exits 0 when links are already present and inline."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        concept.write_text(
            "---\ntype: concept\ntitle: Test\ntags: [a, b]\n"
            "links: []\nbacklinks: []\n---\n\n# Test\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["lint", "--path", str(bundle), "--check"])
        assert result.exit_code == 0

    def test_diff_prints_diff(self, tmp_path: Path) -> None:
        """lint --diff prints unified diff without modifying files."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        concept = bundle / "concept.md"
        original = "---\ntype: concept\ntitle: Test\ntags:\n  - a\n  - b\n---\n\n# Test\n"
        concept.write_text(original, encoding="utf-8")
        result = runner.invoke(cli, ["lint", "--path", str(bundle), "--diff", "--no-links"])
        assert result.exit_code == 0
        assert "---" in result.output
        assert concept.read_text(encoding="utf-8") == original

    def test_nonexistent_bundle(self) -> None:
        """lint exits 2 for nonexistent bundle (Click usage error)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["lint", "--path", str(VALID_BUNDLE / "does-not-exist")])
        assert result.exit_code == 2
        assert "does not exist" in result.output.lower() or "not found" in result.output.lower()
