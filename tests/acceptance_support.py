"""Run the installed wheel of this project in isolation for acceptance tests."""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path


def link_runtime_dependencies(destination: Path) -> None:
    """Expose the third-party runtime dependencies of the test interpreter, never the sources.

    Args:
        destination: New directory that receives one symlink per installed distribution,
            skipping ``.pth`` files (editable installs) and ``okf_schema`` itself.
    """
    source = Path(sysconfig.get_paths()["purelib"])
    destination.mkdir()
    for entry in source.iterdir():
        if entry.suffix == ".pth" or entry.name.startswith("okf_schema"):
            continue
        (destination / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    """Return what a command printed, on both standard streams.

    Args:
        result: Completed process of an installed console script.

    Returns:
        Standard output followed by standard error.
    """
    return result.stdout + result.stderr


@dataclass(frozen=True)
class InstalledProduct:
    """The wheel of this project installed in an isolated virtual environment.

    Attributes:
        environment: Root of the virtual environment holding the installed wheel.
        env: Process environment whose only ``PYTHONPATH`` entry is the runtime dependencies.
    """

    environment: Path
    env: dict[str, str]

    @property
    def interpreter(self) -> Path:
        """Return the Python interpreter of the isolated environment."""
        return self.environment / "bin" / "python"

    def run(
        self, executable: str, *args: str, cwd: Path, check: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Run an installed console script in a subprocess.

        Args:
            executable: Console script name, such as ``okf-schema``.
            *args: Arguments passed to the console script.
            cwd: Working directory of the subprocess, normally the test's own project.
            check: Whether a non-zero exit status raises ``CalledProcessError``.

        Returns:
            The completed process with captured text output.
        """
        return subprocess.run(
            [str(self.environment / "bin" / executable), *args],
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def run_python(
        self, script: str, *args: str, cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run a short script with the isolated interpreter.

        Args:
            script: Python source passed to ``python -c``.
            *args: Arguments exposed to the script as ``sys.argv[1:]``.
            cwd: Working directory of the subprocess.
            check: Whether a non-zero exit status raises ``CalledProcessError``.

        Returns:
            The completed process with captured text output.
        """
        return subprocess.run(
            [str(self.interpreter), "-c", script, *args],
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            env=self.env,
        )


def install_product(workspace: Path) -> InstalledProduct:
    """Build the wheel of this repository and install it in a fresh virtual environment.

    Args:
        workspace: Empty directory that receives the wheel, the environment and the
            linked runtime dependencies.

    Returns:
        The installed product, isolated from the source checkout.
    """
    repository_root = Path(__file__).parents[1]
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
    link_runtime_dependencies(runtime_dependencies)
    isolated_environment = os.environ.copy()
    isolated_environment["PYTHONPATH"] = str(runtime_dependencies)
    isolated_environment["PYTHONNOUSERSITE"] = "1"
    product = InstalledProduct(environment=environment, env=isolated_environment)
    imported = product.run_python(
        "import okf_schema; print(okf_schema.__file__)", cwd=workspace
    ).stdout
    assert str(repository_root / "src") not in imported
    return product
