"""Update Python project versions and create a signed-off version commit without tagging."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from commitizen.config import read_cfg
from commitizen.providers.uv_provider import UvProvider

VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def version_tuple(value: str) -> tuple[int, ...]:
    """Validate a stable version and return its numeric components."""
    if not VERSION.fullmatch(value):
        raise ValueError(
            f"Expected X.Y.Z without a prefix or leading zeroes: {value!r}"
        )
    return tuple(map(int, value.split(".")))


def git(*arguments: str) -> str:
    """Run Git in the current checkout."""
    return subprocess.check_output(["git", *arguments], text=True).strip()


def tag_release(before: str) -> str | None:
    """Push a missing release tag only when the pushed project version increased."""
    if not re.fullmatch(r"[0-9a-f]{40,64}", before):
        raise ValueError("Expected the previous push SHA")
    manifest = tomllib.loads(Path("pyproject.toml").read_text())
    version = manifest["project"]["version"]
    version_tuple(version)
    previous = (
        None
        if set(before) == {"0"}
        else tomllib.loads(git("show", f"{before}:pyproject.toml"))
        .get("project", {})
        .get("version")
    )
    if previous == version:
        print("Project version unchanged; no release tag needed.")
        return None
    if previous and version_tuple(version) <= version_tuple(previous):
        raise ValueError(f"Release version must increase: {previous} -> {version}")
    lock = tomllib.loads(Path("uv.lock").read_text())
    if next(p for p in lock["package"] if p["name"] == "okf-schema")["version"] != version:
        raise ValueError("pyproject.toml and uv.lock versions disagree")
    tag = f"v{version}"
    if git("ls-remote", "--refs", "origin", f"refs/tags/{tag}"):
        print(f"Tag {tag} already exists; leaving it unchanged.")
        return None
    released = [
        entry[1:]
        for entry in git("tag", "--merged", "HEAD").splitlines()
        if entry.startswith("v") and VERSION.fullmatch(entry[1:])
    ]
    if released and version_tuple(version) <= max(map(version_tuple, released)):
        raise ValueError(
            "Release version must be newer than existing ancestor release tags"
        )
    git("push", "origin", f"HEAD:refs/tags/{tag}")
    return tag


def main() -> int:
    """Calculate or set the next release version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?")
    parser.add_argument(
        "--tag-before", help="CI only: tag a version change since this push SHA"
    )
    arguments = parser.parse_args()
    try:
        if arguments.tag_before:
            tag = tag_release(arguments.tag_before)
            if tag and os.environ.get("GITHUB_OUTPUT"):
                with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
                    output.write(f"tag={tag}\n")
            return 0
        current = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
        tags = git("tag", "--merged", "HEAD").splitlines()
        released = [
            tag[1:]
            for tag in tags
            if tag.startswith("v") and VERSION.fullmatch(tag[1:])
        ]
        baseline = max([current, *released], key=version_tuple)
        if arguments.version:
            next_version = arguments.version
        else:
            settings = dict(read_cfg().settings)
            settings.update(version=baseline, version_provider="commitizen")
            with tempfile.TemporaryDirectory(prefix="okf-schema-version-") as directory:
                config = Path(directory) / ".cz.json"
                config.write_text(json.dumps({"commitizen": settings}))
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "commitizen",
                        "--config",
                        str(config),
                        "bump",
                        "--get-next",
                        "--yes",
                        "--allow-no-commit",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                next_version = result.stdout.strip().splitlines()[-1]
        if version_tuple(next_version) <= version_tuple(baseline):
            raise ValueError(f"Version must be newer than {baseline}: {next_version}")
        if git("tag", "--list", f"v{next_version}"):
            raise ValueError(f"Tag v{next_version} already exists")
        if git("status", "--porcelain", "--", "pyproject.toml", "uv.lock"):
            raise ValueError(
                "Commit or stash existing pyproject.toml and uv.lock edits before changing the version"
            )
        git("var", "GIT_AUTHOR_IDENT")
        git("var", "GIT_COMMITTER_IDENT")
        UvProvider(read_cfg()).set_version(next_version)
        print(f"Updated project versions: {current} -> {next_version}")
        git(
            "commit",
            "--only",
            "-s",
            "-m",
            f"chore: version {next_version}",
            "--",
            "pyproject.toml",
            "uv.lock",
        )
        print(f"Created signed-off commit: chore: version {next_version}")
        print("CI creates the tag after merge.")
        return 0
    except (ValueError, subprocess.CalledProcessError) as error:
        print(getattr(error, "stderr", None) or str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
