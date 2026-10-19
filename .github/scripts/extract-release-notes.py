"""Extract the release notes section for a tag from CHANGELOG.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    """Write the matching changelog section without its version heading."""
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract-release-notes.py TAG OUTPUT")

    tag, output = sys.argv[1:]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise SystemExit(f"invalid release tag: {tag}")

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## ", changelog)
    section = next((item for item in sections if item.startswith(f"{tag} ")), None)
    if section is None:
        raise SystemExit(f"CHANGELOG.md has no section for {tag}")

    _, _, body = section.partition("\n")
    body = body.strip()
    if not body:
        raise SystemExit(f"CHANGELOG.md has empty release notes for {tag}")
    Path(output).write_text(body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
