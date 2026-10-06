"""Regression tests for generated requirement navigation and authored log ownership."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from parametrization import Parametrization

from okf_schema.okfreq.cli import okfreq
from okf_schema.okfreq.core import RequirementError, create_requirement, init_requirements
from okf_schema.okfreq.navigation import lint_indexes

# @tests_req SwRS-OKFSCHEMA-OKFREQ-009


def _bundle(tmp_path: Path) -> Path:
    root = init_requirements(tmp_path / "requirements")
    config = root / "config.yml"
    config.write_text(
        config.read_text().replace(
            "default: {source_dirs: [src], test_dirs: [tests]}",
            "default: {folder: delivery, source_dirs: [src], test_dirs: [tests]}",
        ),
        encoding="utf-8",
    )
    create_requirement(
        root,
        "StRS",
        "Dispatch orders",
        "The team SHALL receive orders.",
        project="demo",
        scope="default",
        origin="native",
    )
    create_requirement(
        root,
        "SwRS",
        "Write manifest",
        "The service SHALL write CSV.",
        project="demo",
        scope="default",
        origin="native",
        derives_from=["StRS-default-001"],
    )
    return root


def test_lint_generates_all_ancestors_and_preserves_authored_material(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    root_index = root / "index.md"
    root_index.write_text("# My authored guide\n\nKeep my table.\n", encoding="utf-8")
    tiers_index = root / "tiers/index.md"
    tiers_index.write_text(tiers_index.read_text() + "\nMy introduction.\n", encoding="utf-8")
    log = root / "tiers/log.md"
    log.write_text(log.read_text() + "\n- Authored stakeholder decision.\n", encoding="utf-8")
    original = {p: p.read_bytes() for p in (root_index, tiers_index, log)}
    runner = CliRunner()
    result = runner.invoke(okfreq, ["lint", str(root)])
    assert result.exit_code == 0, result.output
    assert len(list((root / "tiers").rglob("index.md"))) == 5
    assert "swrs/index.md" in tiers_index.read_text()
    parent = root / "tiers/swrs/index.md"
    assert "delivery/index.md" in parent.read_text()
    leaf = root / "tiers/swrs/delivery/index.md"
    assert "SwRS-default-001.md" in leaf.read_text()
    assert "Write manifest" in leaf.read_text()
    assert "The service SHALL write CSV." in leaf.read_text()
    assert tiers_index.read_bytes().startswith(original[tiers_index])
    assert root_index.read_bytes() == original[root_index]
    assert log.read_bytes() == original[log]
    assert lint_indexes(root, check=True) == []
    assert runner.invoke(okfreq, ["lint", str(root), "--check"]).exit_code == 0


def test_index_previews_are_read_only_and_preserve_text_after_block(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    runner = CliRunner()
    original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert runner.invoke(okfreq, ["lint", str(root), "--check"]).exit_code == 1
    diff = runner.invoke(okfreq, ["lint", str(root), "--diff"])
    assert diff.exit_code == 0 and "---" in diff.output and "+- [swrs]" in diff.output
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == original
    lint_indexes(root)
    index = root / "tiers/swrs/delivery/index.md"
    index.write_text(
        index.read_text() + "\n## Decision\n\nKeep CSV compatibility.\n", encoding="utf-8"
    )
    requirement = root / "tiers/swrs/delivery/SwRS-default-001.md"
    requirement.write_text(
        requirement.read_text().replace("Write manifest", "Export manifest"), encoding="utf-8"
    )
    lint_indexes(root)
    assert "Export manifest" in index.read_text()
    assert index.read_text().endswith("\n## Decision\n\nKeep CSV compatibility.\n")


@Parametrization.autodetect_parameters()
@Parametrization.case("unclosed", content="<!-- okfreq:index:start -->\n")
@Parametrization.case("reversed", content="<!-- okfreq:index:end --><!-- okfreq:index:start -->")
@Parametrization.case(
    "duplicate",
    content="<!-- okfreq:index:start --><!-- okfreq:index:start --><!-- okfreq:index:end -->",
)
def test_invalid_blocks_abort_without_partial_writes(tmp_path: Path, content: str) -> None:
    root = _bundle(tmp_path)
    index = root / "tiers/swrs/index.md"
    index.parent.mkdir(exist_ok=True)
    index.write_text(content, encoding="utf-8")
    original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(RequirementError, match="index"):
        lint_indexes(root)
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == original


def test_invalid_requirements_do_not_generate_indexes(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    (root / "tiers/swrs/broken.md").write_text("---\ntype: SwRS\n---\n", encoding="utf-8")
    before = (root / "tiers/index.md").read_bytes()
    result = CliRunner().invoke(okfreq, ["lint", str(root)])
    assert result.exit_code == 1 and "broken.md" in result.output
    assert (root / "tiers/index.md").read_bytes() == before
    assert not (root / "tiers/swrs/index.md").exists()


def test_level_folder_cannot_escape_bundle(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    config = root / "config.yml"
    config.write_text(
        config.read_text().replace("folder: swrs", "folder: ../../outside"), encoding="utf-8"
    )
    with pytest.raises(RequirementError, match="escapes"):
        lint_indexes(root)
    assert not (tmp_path / "outside").exists()


def test_removed_last_requirement_does_not_leave_stale_scope_links(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    lint_indexes(root)
    requirement = root / "tiers/swrs/delivery/SwRS-default-001.md"
    requirement.unlink()
    lint_indexes(root)
    scope = root / "tiers/swrs/delivery/index.md"
    assert "SwRS-default-001.md" not in scope.read_text()
    assert "No requirements" in scope.read_text()
    assert lint_indexes(root, check=True) == []


def test_empty_tiers_get_indexes_and_scope_paths_are_url_encoded(tmp_path: Path) -> None:
    root = init_requirements(tmp_path / "requirements")
    lint_indexes(root)
    assert "No requirements" in (root / "tiers/swrs/index.md").read_text()
    config = root / "config.yml"
    config.write_text(
        config.read_text().replace("folder: swrs", "folder: software requirements"),
        encoding="utf-8",
    )
    lint_indexes(root)
    assert "software%20requirements/index.md" in (root / "tiers/index.md").read_text()
