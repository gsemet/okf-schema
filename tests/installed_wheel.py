"""Build the wheel once per pytest worker and install it in an isolated environment.

The acceptance tests of the stakeholder requirements exercise the product the way a
user receives it: an installed wheel, its console scripts, and no source checkout on
``PYTHONPATH``. Building a wheel and a virtual environment costs several seconds, so
the distribution is created once and shared by every test of the worker.
"""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class InstalledDistribution:
    """An installed wheel, its isolated environment and its console scripts."""

    wheel: Path
    interpreter: Path
    bin_directory: Path
    environment: dict[str, str]

    def run(
        self, executable: str, *arguments: str, cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run one installed console script in the isolated environment."""
        return subprocess.run(
            [str(self.bin_directory / executable), *arguments],
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            env=self.environment,
        )

    def python(self, code: str, *arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        """Run a snippet with the installed wheel's own interpreter."""
        return subprocess.run(
            [str(self.interpreter), "-c", code, *arguments],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            env=self.environment,
        )


def build_wheel(repository_root: Path, wheel_directory: Path) -> Path:
    """Build the project wheel offline into *wheel_directory*."""
    wheel_directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(wheel_directory)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return next(wheel_directory.glob("*.whl"))


def link_runtime_dependencies(destination: Path) -> None:
    """Expose the test environment's third-party packages to the isolated install."""
    source = Path(sysconfig.get_paths()["purelib"])
    destination.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        if entry.suffix == ".pth" or entry.name.startswith("okf_schema"):
            continue
        (destination / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())


def isolate(environment: dict[str, str], runtime_dependencies: Path) -> dict[str, str]:
    """Remove any source checkout from the interpreter's import path."""
    environment.pop("PYTHONPATH", None)
    environment["PYTHONPATH"] = str(runtime_dependencies)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


_cached: InstalledDistribution | None = None


def installed_distribution() -> InstalledDistribution:
    """Return this worker's single installed wheel, building it on first use."""
    global _cached
    if _cached is not None:
        return _cached
    workspace = Path(tempfile.mkdtemp(prefix="okf-schema-acceptance-"))
    wheel_path = build_wheel(REPOSITORY_ROOT, workspace / "wheel")
    environment_path = workspace / "venv"
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment_path)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    executable = "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    interpreter = environment_path / executable
    subprocess.run(
        ["uv", "pip", "install", "--python", str(interpreter), "--no-deps", str(wheel_path)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    runtime_dependencies = workspace / "runtime-dependencies"
    link_runtime_dependencies(runtime_dependencies)
    _cached = InstalledDistribution(
        wheel=wheel_path,
        interpreter=interpreter,
        bin_directory=environment_path / ("Scripts" if sys.platform == "win32" else "bin"),
        environment=isolate(os.environ.copy(), runtime_dependencies),
    )
    return _cached
