"""Verify that canonical agent skills are complete package resources."""

from __future__ import annotations

import re
import subprocess
from importlib import resources
from pathlib import Path
from zipfile import ZipFile

import pytest
from parametrization import Parametrization

_SKILL_ROOTS = (
    "okf-schema",
    "okfkb",
    "okfkb-distill",
    "okfkb-gardening",
    "okfkb-record-findings",
    "okfreq",
    "okfreq-gardening",
    "okfreq-setup",
)


def _canonical_root() -> Path:
    return Path(__file__).parents[1] / "skills"


def _relative_files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _resource_root():
    return resources.files("skills")


def test_canonical_skills_are_importable_resources() -> None:
    """The canonical top-level skills directory is an importlib resource namespace."""
    actual_roots = sorted(entry.name for entry in _resource_root().iterdir() if entry.is_dir())

    assert actual_roots == sorted(_SKILL_ROOTS)


def test_each_skill_routes_all_local_references() -> None:
    """Every packaged reference is discoverable from its owning SKILL.md."""
    for skill_root in _SKILL_ROOTS:
        skill_directory = _canonical_root() / skill_root
        references_directory = skill_directory / "references"
        if not references_directory.is_dir():
            continue

        skill_text = (skill_directory / "SKILL.md").read_text(encoding="utf-8")
        for reference in sorted(references_directory.rglob("*")):
            if not reference.is_file():
                continue
            relative_reference = reference.relative_to(skill_directory).as_posix()
            link_pattern = re.compile(
                rf"\]\((?:\./)?{re.escape(relative_reference)}(?:[#?][^)]*)?\)"
            )
            assert link_pattern.search(skill_text), (
                f"{skill_root}/SKILL.md does not route {relative_reference}"
            )


def test_installable_skills_do_not_use_cross_skill_relative_links() -> None:
    """Installed skills resolve companion resources by skill name, not siblings."""
    skill_names = set(_SKILL_ROOTS)
    for skill_root in _SKILL_ROOTS:
        skill_text = (_canonical_root() / skill_root / "SKILL.md").read_text(encoding="utf-8")
        for other_skill in skill_names - {skill_root}:
            pattern = re.compile(rf"\]\((?:\.\./)+{re.escape(other_skill)}/")
            assert not pattern.search(skill_text), (
                f"{skill_root}/SKILL.md assumes {other_skill} is an installed sibling"
            )


def _build_wheel(repository_root: Path, wheel_directory: Path) -> Path:
    wheel_directory.mkdir()
    subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(wheel_directory)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return next(wheel_directory.glob("*.whl"))


def test_distill_skill_keeps_evidence_and_asks_before_promoting_or_marking() -> None:
    """The packaged distill workflow proposes, links evidence and waits for confirmation."""
    text = " ".join(
        (_resource_root() / "okfkb-distill" / "SKILL.md").read_text(encoding="utf-8").split()
    )

    assert "It proposes changes; a human confirms each mutation." in text
    assert "Never edit or delete a Finding body." in text
    assert "Never promote a Finding to a Principle without explicit human confirmation." in text
    assert "For convergent Findings, propose a promotion:" in text
    for destination in ("`Structure`", "`Concept`", "`Principle`"):
        assert destination in text
    assert "Link promoted documents to their sources with authored `derived_from`" in text
    assert "Present every candidate contradiction to the human." in text
    assert "On confirmation, add `contradicts: [<old-id>]` to the newer Finding" in text
    assert "Keep both bodies unchanged." in text
    assert "For unresolved or low-confidence contradictions, propose an `Experiment`" in text


def test_built_wheel_contains_canonical_skill_trees_unchanged(tmp_path: Path) -> None:
    """A wheel contains exactly the canonical skill files under package resources."""
    repository_root = Path(__file__).parents[1]
    wheel_path = _build_wheel(repository_root, tmp_path / "wheel")
    resource_prefix = "okf_schema/skills/"
    canonical_files = {
        Path(skill_root) / relative_file
        for skill_root in _SKILL_ROOTS
        for relative_file in _relative_files(_canonical_root() / skill_root)
    }

    with ZipFile(wheel_path) as wheel:
        packaged_files = {
            Path(member.removeprefix(resource_prefix))
            for member in wheel.namelist()
            if member.startswith(resource_prefix)
            and not member.endswith("/")
            and member != f"{resource_prefix}__init__.py"
            and Path(member.removeprefix(resource_prefix)).parts[0] in _SKILL_ROOTS
        }
        assert {path.parts[0] for path in packaged_files} == set(_SKILL_ROOTS)
        assert packaged_files == canonical_files

        for relative_file in canonical_files:
            member = f"{resource_prefix}{relative_file.as_posix()}"
            assert wheel.read(member) == (_canonical_root() / relative_file).read_bytes()


@Parametrization.autodetect_parameters()
@Parametrization.case(name="okf_schema", skill_root="okf-schema")
@Parametrization.case(name="okfkb", skill_root="okfkb")
@Parametrization.case(name="okfreq", skill_root="okfreq")
def test_base_skills_document_cli_and_agent_skill_installation(skill_root: str) -> None:
    """Base skills explain Python tool installation separately from skill deployment."""
    required_commands = ("uv tool install okf-schema", "uv tool upgrade okf-schema")
    expected_executables = ("okf-schema", "okfkb", "okfreq")

    text = (_canonical_root() / skill_root / "SKILL.md").read_text(encoding="utf-8")
    for command in required_commands:
        assert command in text
    assert all(executable in text for executable in expected_executables)
    assert "install-skills" in text


def test_installed_wheel_commands_install_complete_families_without_source_checkout(
    tmp_path: Path,
    installed_wheel,
) -> None:
    """Installed console scripts deploy packaged families and nested resources in isolation."""
    repository_root = installed_wheel.repository_root
    environment = installed_wheel.environment
    interpreter = installed_wheel.interpreter
    isolated_environment = installed_wheel.environment_variables
    destinations = {
        "okf-schema": ("okf-schema",),
        "okfkb": ("okfkb", "okfkb-distill", "okfkb-gardening", "okfkb-record-findings"),
        "okfreq": ("okfreq", "okfreq-gardening", "okfreq-setup"),
    }
    nested_files = {
        "okf-schema": "references/okf-v0.2.md",
        "okfkb": "references/lifecycle-and-taxonomy.md",
        "okfreq": "references/operations.md",
    }

    imported_module = subprocess.run(
        [str(interpreter), "-c", "import okf_schema; print(okf_schema.__file__)"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=isolated_environment,
    )
    assert str(repository_root) not in imported_module.stdout

    for executable, skill_roots in destinations.items():
        destination = tmp_path / f"installed-{executable}"
        result = subprocess.run(
            [str(environment / "bin" / executable), "install-skills", str(destination)],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            env=isolated_environment,
        )
        assert f"Destination: {destination}" in result.stdout
        for skill_root in skill_roots:
            skill_file = destination / skill_root / "SKILL.md"
            assert skill_file.is_file()
            assert skill_file.read_text(encoding="utf-8")
        nested_file = destination / skill_roots[0] / nested_files[executable]
        assert nested_file.is_file()
        assert nested_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("executable", "skill_roots"),
    (
        ("okf-schema", ("okf-schema",)),
        ("okfkb", ("okfkb", "okfkb-distill", "okfkb-gardening", "okfkb-record-findings")),
        ("okfreq", ("okfreq", "okfreq-gardening")),
    ),
)
def test_source_checkout_commands_install_families(
    tmp_path: Path,
    executable: str,
    skill_roots: tuple[str, ...],
) -> None:
    """Each source-checkout console command installs its family into a temporary directory."""
    repository_root = Path(__file__).parents[1]
    destination = tmp_path / executable

    result = subprocess.run(
        ["uv", "run", "--no-sync", executable, "install-skills", str(destination)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"Destination: {destination}" in result.stdout
    for skill_root in skill_roots:
        assert (destination / skill_root / "SKILL.md").is_file()


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S1
def test_installed_okfreq_skill_references_are_self_contained(tmp_path: Path) -> None:
    """Operational links remain usable when the installation has no docs/source tree."""
    from okf_schema.skill_installer import install_skill_family

    destination = tmp_path / "agent-skills"
    install_skill_family("okfreq", destination)
    for document in destination.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            resource = (document.parent / target.split("#")[0]).resolve()
            assert resource.is_relative_to(destination.resolve())
            assert resource.is_file(), (document, target)


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008#S2
def test_installed_okfreq_reference_separates_errors_skips_and_coverage_gaps(
    tmp_path: Path,
) -> None:
    """The installed operations reference tells errors, skipped checks and gaps apart."""
    from okf_schema.skill_installer import install_skill_family

    destination = tmp_path / "agent-skills"
    install_skill_family("okfreq", destination)
    text = " ".join(
        (destination / "okfreq" / "references" / "operations.md")
        .read_text(encoding="utf-8")
        .split()
    )

    assert "`missing_ids` needs a real requirement or a corrected marker" in text
    assert "For structural errors repair the indicated file" in text
    assert "For `E10` fix the target, filename ambiguity, or annotation" in text
    assert "`W15` provide the correct root or restore access" in text
    assert "Missing scan directories make coverage incomplete." in text
    assert "Execute the project's actual tests separately and report their results" in text


def test_okfreq_skills_read_the_installed_guideline_instead_of_embedding_it(
    tmp_path: Path,
) -> None:
    """The guideline has one source; the skills point to the copy `okfreq init` installs."""
    from okf_schema.skill_installer import install_skill_family

    destination = tmp_path / "agent-skills"
    install_skill_family("okfreq", destination)

    assert not list(destination.rglob("requirements.guidelines.md"))
    for name in ("okfreq", "okfreq-gardening"):
        text = (destination / name / "SKILL.md").read_text(encoding="utf-8")
        assert "guidelines/requirements.guidelines.md" in text
        assert "okfreq init" in text
        assert "project.guidelines.md" in text
        assert "references/requirements.guidelines.md" not in text


# @tests_req SwRS-OKFSCHEMA-OKFREQ-010#S1
# @tests_req SwRS-OKFSCHEMA-OKFREQ-010#S2
# @tests_req SwRS-OKFSCHEMA-OKFREQ-010#S3
def test_installed_okfreq_setup_skill_is_complete_and_self_contained(tmp_path: Path) -> None:
    """The setup skill ships with the okfreq family and states its stop rules and delivery."""
    from okf_schema.skill_installer import install_skill_family

    destination = tmp_path / "agent-skills"
    install_skill_family("okfreq", destination)
    skill = destination / "okfreq-setup" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")

    assert text.startswith("---\nname: okfreq-setup\n")
    for required in (
        "## Stop rules",
        "okfreq init requirements",
        "okfreq-gardening",
        "Never merge",
        "requirements/guidelines/requirements.guidelines.md",
        "requirements/guidelines/project.guidelines.md",
        "--lifecycle proposed",
        "owner_email",
        "approval_lock",
        "Nothing is approved during setup",
        "`okfreq-gardening` applies.",
        "The directory is not a git repository, or the default branch cannot be determined",
        "Never modify, stage or revert changes that were in the worktree before you started.",
    ):
        assert required in text
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        assert (skill.parent / target.split("#")[0]).resolve().is_file(), target


@Parametrization.autodetect_parameters()
@Parametrization.case(name="okfreq", document="okfreq/SKILL.md")
@Parametrization.case(name="operations", document="okfreq/references/operations.md")
@Parametrization.case(name="gardening", document="okfreq-gardening/SKILL.md")
@Parametrization.case(name="setup", document="okfreq-setup/SKILL.md")
def test_okfreq_skills_teach_acceptance_paths(document: str) -> None:
    """Each shipped okfreq skill teaches the acceptance-paths mode on its own."""
    text = (_resource_root() / document).read_text(encoding="utf-8")

    for expected in ("linked-swrs-and-acceptance-paths", "@accepts_req", "scenarios:", "#S<n>"):
        assert expected in text, (document, expected)


def test_shipped_guideline_teaches_acceptance_paths() -> None:
    """The shipped guideline states both verbs, the cost rule, the fragment rule and Rule 7."""
    guideline = resources.files("okf_schema").joinpath(
        "data", "requirements", "guidelines", "requirements.guidelines.md"
    )
    text = " ".join(guideline.read_text(encoding="utf-8").split())

    assert "`@tests_req <ID>#S<n>` tests an SwRS transition or an StRS main path" in text
    assert "`@accepts_req <StRS-ID>#S<n>` is the acceptance test of an StRS main path" in text
    assert "Choose the verb by execution cost." in text
    assert "When the tests are cheap, put `@accepts_req` directly" in text
    assert (
        "when the target declares `scenarios:`, a test marker must carry the `#S<n>` of a "
        "declared scenario, otherwise it is an error and counts for nothing" in text
    )
    assert "a marker without fragment counts for the whole requirement" in text
    assert "An edit that only adds `scenarios:` to an approved requirement" in text
    assert "leave `approved_by` and `approved_at` unchanged unless the owner gives a new" in text
    assert "### Main paths" in text and "#### Path S<n>: <title>" in text
