"""Shared pytest fixtures for okf-schema tests."""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path

import pytest


@pytest.fixture
def valid_bundle(tmp_path: Path) -> Path:
    """Create a complete valid OKF bundle."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    # Root index.md with frontmatter
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n\n# Test Bundle\n',
        encoding="utf-8",
    )

    # Root log.md
    (bundle / "log.md").write_text("## 2024-01-01\n\nInitial log.\n", encoding="utf-8")

    # Subdirectory with concepts
    subdir = bundle / "subdir"
    subdir.mkdir()
    (subdir / "concept-a.md").write_text(
        "---\ntype: concept\ntitle: Concept A\n"
        "description: First concept\ntags: [a, b]\n"
        'generated:\n  at: "2024-01-15T00:00:00Z"\n  by: bot:test\n'
        "---\n\nBody of A.\n",
        encoding="utf-8",
    )
    (subdir / "concept-b.md").write_text(
        "---\ntype: concept\ntitle: Concept B\n"
        "description: Second concept\ntags: [b, c]\n"
        'generated:\n  at: "2024-01-15T00:00:00Z"\n  by: bot:test\n'
        "---\n\n"
        "Body of B linking to [A](concept-a.md).\n",
        encoding="utf-8",
    )

    # Another subdirectory
    subdir2 = bundle / "another"
    subdir2.mkdir()
    (subdir2 / "concept-c.md").write_text(
        "---\ntype: reference\ntitle: Concept C\ndescription: Third concept\n"
        'generated:\n  at: "2024-01-15T00:00:00Z"\n  by: bot:test\n'
        "---\n\nBody of C.\n",
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


@dataclass(frozen=True)
class InstalledWheel:
    """A virtual environment holding only the built okf-schema wheel."""

    environment: Path
    environment_variables: dict[str, str]
    repository_root: Path

    @property
    def interpreter(self) -> Path:
        return self.environment / "bin" / "python"

    def executable(self, name: str) -> Path:
        return self.environment / "bin" / name

    def run(
        self, name: str, *args: str, cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run an installed console script with no source checkout on ``PYTHONPATH``."""
        result = subprocess.run(
            [str(self.executable(name)), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            env=self.environment_variables,
        )
        if check:
            assert result.returncode == 0, (name, args, result.stdout, result.stderr)
        return result


def _link_runtime_dependencies(destination: Path) -> None:
    source = Path(sysconfig.get_paths()["purelib"])
    destination.mkdir()
    for entry in source.iterdir():
        if entry.suffix == ".pth" or entry.name.startswith("okf_schema"):
            continue
        (destination / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())


@pytest.fixture(scope="session")
def installed_wheel(tmp_path_factory: pytest.TempPathFactory) -> InstalledWheel:
    """Build the wheel once per pytest worker and install it into an isolated environment."""
    if sys.platform == "win32":
        pytest.skip("installed console scripts are exercised on POSIX layouts only")
    repository_root = Path(__file__).parents[1]
    workspace = tmp_path_factory.mktemp("installed-wheel")
    wheel_directory = workspace / "wheel"
    subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(wheel_directory)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel_path = next(wheel_directory.glob("*.whl"))
    environment = workspace / "venv"
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(environment / "bin" / "python"),
            "--no-deps",
            str(wheel_path),
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    runtime_dependencies = workspace / "runtime-dependencies"
    _link_runtime_dependencies(runtime_dependencies)
    environment_variables = os.environ.copy()
    environment_variables["PYTHONPATH"] = str(runtime_dependencies)
    environment_variables["PYTHONNOUSERSITE"] = "1"
    return InstalledWheel(environment, environment_variables, repository_root)
