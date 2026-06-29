"""Shared utilities for OKF bundle processing."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterable
from pathlib import Path

from okf_schema._internal.models import ConceptInfo
from okf_schema._internal.yaml import extract_frontmatter, parse_yaml

RESERVED_FILES = {"index.md", "log.md"}
ISO8601_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")


def collect_markdown_files(bundle: Path) -> Iterable[Path]:
    """Yield every ``.md`` file under *bundle*, sorted alphabetically."""
    for path in sorted(bundle.rglob("*.md")):
        if path.is_file():
            yield path


def resolve_link(target: str, source: Path, bundle_root: Path) -> Path | None:
    """Resolve a markdown link target to an absolute path.

    Returns ``None`` for external URLs (``https://``, ``mailto:``, etc.).
    Absolute paths starting with ``/`` are resolved relative to
    *bundle_root*. Relative paths are resolved relative to *source*'s
    parent directory.
    """
    if "://" in target or target.startswith("mailto:"):
        return None

    if target.startswith("/"):
        resolved = bundle_root / target.lstrip("/")
    else:
        resolved = source.parent / target

    with contextlib.suppress(OSError):
        resolved = resolved.resolve()

    return resolved


def find_broken_links(body: str, source: Path, bundle_root: Path) -> list[str]:
    """Find broken internal links in markdown body text.

    Returns a list of link targets that do not exist on disk.
    External links are skipped. Directories are accepted as valid targets.
    """
    broken: list[str] = []
    for _text, target in MARKDOWN_LINK_RE.findall(body):
        resolved = resolve_link(target, source, bundle_root)
        if resolved is None:
            continue  # external link — can't check
        if not resolved.exists():
            broken.append(target)
    return broken


def has_markdown_files(dir_path: Path) -> bool:
    """Return True if *dir_path* or any descendant contains ``.md`` files."""
    if not dir_path.is_dir():
        return False
    return any(item.is_file() for item in dir_path.rglob("*.md"))


def get_concept_info(path: Path) -> ConceptInfo:
    """Extract title, description, and type from a concept file.

    Falls back to a title derived from the file stem (replacing ``-`` and
    ``_`` with spaces, title-cased) when frontmatter is missing or
    incomplete.
    """
    text = path.read_text(encoding="utf-8")
    fm_text, _body = extract_frontmatter(text)

    fallback_title = path.stem.replace("-", " ").replace("_", " ").title()
    info = ConceptInfo(title=fallback_title, description="", type="")

    if fm_text is not None:
        frontmatter = parse_yaml(fm_text)
        if frontmatter is not None:
            if frontmatter.get("title"):
                info.title = str(frontmatter["title"]).strip()
            if frontmatter.get("description"):
                info.description = str(frontmatter["description"]).strip()
            if frontmatter.get("type"):
                info.type = str(frontmatter["type"]).strip()

    return info
