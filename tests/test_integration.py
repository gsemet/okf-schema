"""Integration tests for okf-schema end-to-end workflows."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from okf_schema.api import (
    format_bundle,
    graph_bundle,
    index_bundle,
    search_bundle,
    stats_bundle,
    validate_bundle,
)
from okf_schema.cli import cli


class TestEndToEndWorkflow:
    """Full workflow: init → new → validate → format → index → search → graph → stats."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Run a complete workflow from empty to indexed bundle."""
        runner = CliRunner()
        project = tmp_path / "project"

        # 1. init
        result = runner.invoke(cli, ["init", str(project)])
        assert result.exit_code == 0
        bundle = project / "bundle"
        assert bundle.is_dir()

        # 2. new concept in a subdirectory
        result = runner.invoke(
            cli,
            [
                "new",
                "--path",
                str(bundle),
                "--name",
                "guides/getting-started",
                "--type",
                "guide",
                "--title",
                "Getting Started",
            ],
        )
        assert result.exit_code == 0
        concept = bundle / "guides" / "getting-started.md"
        assert concept.exists()

        # 3. validate (should pass)
        report = validate_bundle(bundle)
        assert report.is_conformant

        # 4. format (should be no-op for newly created concept)
        results = format_bundle(bundle)
        assert all(not r.changed for r in results)

        # 5. index
        updates = index_bundle(bundle)
        assert any(u.action in ("created", "updated") for u in updates)

        # 6. search
        results = search_bundle(bundle, "started")
        assert len(results) == 1
        assert results[0].title == "Getting Started"

        # 7. graph (no links yet)
        graph = graph_bundle(bundle)
        assert graph == {}

        # 8. stats
        stats = stats_bundle(bundle)
        assert stats.total_concepts >= 1
        assert stats.total_files >= 1

    def test_cli_sequence_on_same_bundle(self, tmp_path: Path) -> None:
        """Multiple CLI commands on the same bundle produce consistent state."""
        runner = CliRunner()
        project = tmp_path / "project"

        # init
        result = runner.invoke(cli, ["init", str(project)])
        assert result.exit_code == 0
        bundle = project / "bundle"

        # Add concepts via CLI new (in subdirectories to comply with E7)
        runner.invoke(
            cli,
            ["new", "--path", str(bundle), "--name", "concepts/alpha", "--type", "concept"],
        )
        runner.invoke(
            cli,
            ["new", "--path", str(bundle), "--name", "concepts/beta", "--type", "concept"],
        )

        # validate via CLI
        result = runner.invoke(cli, ["validate", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "conformant" in result.output

        # list via CLI
        result = runner.invoke(cli, ["list", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output

        # stats via CLI
        result = runner.invoke(cli, ["stats", "--path", str(bundle)])
        assert result.exit_code == 0
        assert "concepts" in result.output
        assert "Health:" in result.output

    def test_format_then_validate_consistency(self, tmp_path: Path) -> None:
        """Formatting should not introduce validation errors."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\n---\n\n# Bundle\n',
            encoding="utf-8",
        )
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\ntags: [[a, b], c]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        # Validate before format — should have E5
        report_before = validate_bundle(bundle)
        assert any(f.code == "E5" for f in report_before.errors)

        # Format
        format_bundle(bundle)

        # Validate after format — E5 should be gone
        report_after = validate_bundle(bundle)
        assert not any(f.code == "E5" for f in report_after.errors)

    def test_index_regenerates_all_indices(self, tmp_path: Path) -> None:
        """index_bundle creates index.md in every directory with markdown."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        sub = bundle / "sub"
        sub.mkdir()
        (sub / "concept.md").write_text(
            "---\ntype: concept\ntitle: Sub Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        updates = index_bundle(bundle)
        actions = {u.action for u in updates}
        assert "created" in actions
        # Both root and sub should have index.md
        assert (bundle / "index.md").exists()
        assert (sub / "index.md").exists()

    def test_graph_with_cross_references(self, tmp_path: Path) -> None:
        """graph_bundle correctly maps cross-references between concepts."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntype: concept\ntitle: A\n---\n\nLink to [B](b.md).\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: concept\ntitle: B\n---\n\nLink to [A](a.md).\n",
            encoding="utf-8",
        )

        graph = graph_bundle(bundle)
        assert "a.md" in graph
        assert "b.md" in graph
        assert "b.md" in graph["a.md"]
        assert "a.md" in graph["b.md"]

    def test_search_across_multiple_fields(self, tmp_path: Path) -> None:
        """search_bundle finds matches in title, description, type, and tags."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "c1.md").write_text(
            "---\ntype: guide\ntitle: Alpha Guide\n"
            "description: Learn alpha\ntags: [tutorial]\n---\n\nBody.\n",
            encoding="utf-8",
        )
        (bundle / "c2.md").write_text(
            "---\ntype: reference\ntitle: Beta Ref\n"
            "description: Beta details\ntags: [alpha]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        # Search by title
        assert len(search_bundle(bundle, "alpha")) == 2
        # Search by type
        assert len(search_bundle(bundle, "guide")) == 1
        # Search by tag
        assert len(search_bundle(bundle, "tutorial")) == 1
        # Search by description
        assert len(search_bundle(bundle, "details")) == 1

    def test_stats_computes_all_metrics(self, tmp_path: Path) -> None:
        """stats_bundle returns accurate counts for a known bundle."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text("# Index\n", encoding="utf-8")
        (bundle / "a.md").write_text(
            "---\ntype: concept\ntitle: A\ntags: [x]\n---\n\n[broken](missing.md)\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: concept\ntitle: B\ntags: [x, y]\n---\n\nBody.\n",
            encoding="utf-8",
        )

        stats = stats_bundle(bundle)
        assert stats.total_files == 3
        assert stats.total_concepts == 2
        # index.md is reserved and skipped for frontmatter counting
        assert stats.files_without_frontmatter == 0
        assert stats.total_links == 1

    def test_validate_with_ref_schema(self, tmp_path: Path) -> None:
        """Validation works when schemas use $ref to external files."""
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        schema_dir = bundle / "_schema"
        schema_dir.mkdir()

        base = schema_dir / "_base.schema.yaml"
        base.write_text(
            "type: object\nproperties:\n  type:\n    type: string\n"
            "  title:\n    type: string\nrequired:\n  - type\n",
            encoding="utf-8",
        )
        concept = schema_dir / "concept.schema.yaml"
        concept.write_text(
            "$ref: _base.schema.yaml\n",
            encoding="utf-8",
        )

        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\n---\n\n# Index\n',
            encoding="utf-8",
        )
        (bundle / "guides").mkdir()
        (bundle / "guides" / "idea.md").write_text(
            "---\ntype: concept\ntitle: Idea\n---\n\nBody.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert report.is_conformant
        assert not any(f.code == "W6" for f in report.warnings)

    def test_init_creates_base_schema_and_validates(self, tmp_path: Path) -> None:
        """A bundle created with init validates cleanly including _base.schema.yaml."""
        runner = CliRunner()
        project = tmp_path / "project"
        result = runner.invoke(cli, ["init", str(project)])
        assert result.exit_code == 0
        bundle = project / "bundle"

        # Add a concept that matches _base.schema.yaml
        (bundle / "guides").mkdir()
        (bundle / "guides" / "intro.md").write_text(
            "---\ntype: guide\ntitle: Intro\n"
            "description: Getting started\ntags: [intro]\n"
            "timestamp: 2024-01-01T00:00:00Z\n---\n\nBody.\n",
            encoding="utf-8",
        )

        report = validate_bundle(bundle)
        assert report.is_conformant


class TestCliIntegration:
    """CLI-level integration tests."""

    def test_validate_cli_with_schema_db(self, tmp_path: Path, schema_db: Path) -> None:
        """CLI validate with --schema-db option works end-to-end."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.1"\n---\n\n# Bundle\n',
            encoding="utf-8",
        )
        subdir = bundle / "concepts"
        subdir.mkdir()
        (subdir / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test Concept\n---\n\nBody.\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli, ["validate", "--path", str(bundle), "--schema-db", str(schema_db)]
        )
        assert result.exit_code == 0
        assert "conformant" in result.output

    def test_show_cli_output(self, tmp_path: Path) -> None:
        """CLI show displays frontmatter and body."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "concept.md").write_text(
            "---\ntype: concept\ntitle: Shown\n---\n\nBody text here.\n",
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["show", "--path", str(bundle), "concept.md"])
        assert result.exit_code == 0
        assert "type:" in result.output
        assert "Body text here" in result.output

    def test_backlinks_cli_output(self, tmp_path: Path) -> None:
        """CLI backlinks prints one line per backlink."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "react-pattern.md").write_text(
            "---\ntype: concept\ntitle: React Pattern\n---\n\n# React Pattern\n",
            encoding="utf-8",
        )
        (bundle / "chain-of-thought.md").write_text(
            "---\ntype: paper\ntitle: Chain of Thought\n---\n\n"
            "See [React Pattern](react-pattern.md).\n",
            encoding="utf-8",
        )
        (bundle / "toolformer.md").write_text(
            "---\ntype: paper\ntitle: Toolformer\n---\n\nUses [React Pattern](react-pattern.md).\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            ["backlinks", "--path", str(bundle), "react-pattern.md"],
        )
        assert result.exit_code == 0
        lines = [line for line in result.output.strip().split("\n") if line]
        assert len(lines) == 2
        assert "react-pattern.md ← chain-of-thought.md" in lines
        assert "react-pattern.md ← toolformer.md" in lines

    def test_backlinks_cli_multiple_targets(self, tmp_path: Path) -> None:
        """CLI backlinks accepts multiple target arguments."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "a.md").write_text(
            "---\ntype: concept\ntitle: A\n---\n\nLink to [B](b.md)\n",
            encoding="utf-8",
        )
        (bundle / "b.md").write_text(
            "---\ntype: concept\ntitle: B\n---\n\nLink to [A](a.md)\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            ["backlinks", "--path", str(bundle), "a.md", "b.md"],
        )
        assert result.exit_code == 0
        lines = [line for line in result.output.strip().split("\n") if line]
        assert len(lines) == 2
        assert "a.md ← b.md" in lines
        assert "b.md ← a.md" in lines

    def test_backlinks_cli_no_backlinks(self, tmp_path: Path) -> None:
        """CLI backlinks prints a placeholder when no backlinks exist."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "orphan.md").write_text(
            "---\ntype: concept\ntitle: Orphan\n---\n\n# Orphan\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            ["backlinks", "--path", str(bundle), "orphan.md"],
        )
        assert result.exit_code == 0
        assert "orphan.md ← ❌" in result.output

    def test_backlinks_cli_extensionless_target(self, tmp_path: Path) -> None:
        """CLI backlinks accepts targets without the .md extension."""
        runner = CliRunner()
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "react-pattern.md").write_text(
            "---\ntype: concept\ntitle: React Pattern\n---\n\n# React Pattern\n",
            encoding="utf-8",
        )
        (bundle / "chain-of-thought.md").write_text(
            "---\ntype: paper\ntitle: Chain of Thought\n---\n\n"
            "See [React Pattern](react-pattern.md).\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            ["backlinks", "--path", str(bundle), "react-pattern"],
        )
        assert result.exit_code == 0
        assert "react-pattern.md ← chain-of-thought.md" in result.output

    def test_backlinks_cli_nonexistent_bundle(self, tmp_path: Path) -> None:
        """CLI backlinks exits with error for nonexistent bundle."""
        runner = CliRunner()
        missing = tmp_path / "missing"

        result = runner.invoke(
            cli,
            ["backlinks", "--path", str(missing), "a.md"],
        )
        assert result.exit_code == 2
        assert "Error:" in result.output


# ---------------------------------------------------------------------------
# KB subcommand end-to-end workflow
# ---------------------------------------------------------------------------


class TestKbEndToEndWorkflow:
    """End-to-end: okfkb init then okfkb install on a project directory."""

    def test_kb_init_then_install(self, tmp_path: Path) -> None:
        """Full KB workflow: init a KB bundle, then install skills into a project."""
        runner = CliRunner()
        kb_path = tmp_path / "mykb"
        project_path = tmp_path / "project"
        project_path.mkdir()

        # Step 1 — init a KB at kb_path
        result = runner.invoke(cli, ["kb", "init", str(kb_path)])
        assert result.exit_code == 0, f"kb init failed: {result.output}"
        assert (kb_path / "concepts").is_dir()
        assert (kb_path / "index.md").is_file()
        assert (kb_path / "log.md").is_file()

        # Step 2 — install KB skills into project_path
        result = runner.invoke(cli, ["kb", "install", str(project_path)])
        assert result.exit_code == 0, f"kb install failed: {result.output}"

        # Verify skills were deployed
        agents_dir = project_path / ".agents"
        assert agents_dir.is_dir()
        assert (agents_dir / "skills" / "record-finding" / "SKILL.md").is_file()
        assert (agents_dir / "skills" / "consolidate-knowledge-base" / "SKILL.md").is_file()

        # Verify guideline was deployed
        assert (agents_dir / "guidelines" / "knowledge-base.guidelines.md").is_file()

        # Verify AGENTS.md was created and references the guideline
        agents_md = project_path / "AGENTS.md"
        assert agents_md.is_file()
        assert "knowledge-base.guidelines.md" in agents_md.read_text(encoding="utf-8")
