"""Verify that canonical agent skills are complete package resources."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import sysconfig
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
)


def _canonical_root() -> Path:
    return Path(__file__).parents[1] / "skills"


def _relative_files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _resource_root():
    return resources.files("skills")


def _link_runtime_dependencies(destination: Path) -> None:
    source = Path(sysconfig.get_paths()["purelib"])
    destination.mkdir()
    for entry in source.iterdir():
        if entry.suffix == ".pth" or entry.name.startswith("okf_schema"):
            continue
        (destination / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())


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


# @tests_req SwRS-OKFSCHEMA-OKFKB-005
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
) -> None:
    """Installed console scripts deploy packaged families and nested resources in isolation."""
    if sys.platform == "win32":
        return

    repository_root = Path(__file__).parents[1]
    wheel_directory = tmp_path / "wheel"
    subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(wheel_directory)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel_path = next(wheel_directory.glob("*.whl"))
    environment = tmp_path / "venv"
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    interpreter = environment / "bin" / "python"
    subprocess.run(
        ["uv", "pip", "install", "--python", str(interpreter), "--no-deps", str(wheel_path)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    runtime_dependencies = tmp_path / "runtime-dependencies"
    _link_runtime_dependencies(runtime_dependencies)
    isolated_environment = os.environ.copy()
    isolated_environment.pop("PYTHONPATH", None)
    isolated_environment["PYTHONPATH"] = str(runtime_dependencies)
    isolated_environment["PYTHONNOUSERSITE"] = "1"
    destinations = {
        "okf-schema": ("okf-schema",),
        "okfkb": ("okfkb", "okfkb-distill", "okfkb-gardening", "okfkb-record-findings"),
        "okfreq": ("okfreq", "okfreq-gardening"),
    }
    nested_files = {
        "okf-schema": "references/okf-v0.2.md",
        "okfkb": "references/lifecycle-and-taxonomy.md",
        "okfreq": "references/requirements.guidelines.md",
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


# @tests_req SwRS-OKFSCHEMA-OKFREQ-008
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
