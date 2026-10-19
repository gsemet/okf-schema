"""Select the reviewed release notes file for an exact Git tag."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    """Copy the notes file whose name exactly matches the release tag."""
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract-release-notes.py TAG OUTPUT")

    tag, output = sys.argv[1:]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise SystemExit(f"invalid release tag: {tag}")

    notes_path = Path("release-notes") / f"{tag}.md"
    if not notes_path.is_file():
        raise SystemExit(f"release notes file not found: {notes_path}")

    body = notes_path.read_text(encoding="utf-8").strip()
    if not body:
        raise SystemExit(f"release notes file is empty: {notes_path}")
    Path(output).write_text(body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
