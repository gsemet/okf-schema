"""Discover concepts and resolve links within Open Knowledge Format bundles.

The module provides Markdown traversal, frontmatter metadata extraction, and
link-graph construction for the package's validation and reporting layers.
"""

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
    """Yield every ``.md`` file under *bundle*, sorted alphabetically.

    Args:
        bundle:
            Directory to search recursively.

    Yields:
        Paths to regular Markdown files.
    """
    for path in sorted(bundle.rglob("*.md")):
        if path.is_file():
            yield path


def resolve_link(
    target: str,
    source: Path,
    bundle_root: Path,
) -> Path | None:
    """Resolve a markdown link target to an absolute path.

    Returns ``None`` for external URLs (``https://``, ``mailto:``, etc.).
    Absolute paths starting with ``/`` are resolved relative to
    *bundle_root*. Relative paths are resolved relative to *source*'s
    parent directory.

    Args:
        target:
            Link destination as written in Markdown.
        source:
            Path of the document containing the link.
        bundle_root:
            Root used to resolve slash-prefixed bundle paths.

    Returns:
        Resolved path, or ``None`` for an external destination.

    Examples:
        >>> resolve_link("concepts/clock.md", Path("/bundle/index.md"), Path("/bundle"))
        PosixPath('/bundle/concepts/clock.md')
        >>> resolve_link("https://example.com", Path("index.md"), Path(".")) is None
        True
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


def find_broken_links(
    body: str,
    source: Path,
    bundle_root: Path,
) -> list[str]:
    """Find broken internal links in markdown body text.

    Returns a list of link targets that do not exist on disk.
    External links are skipped. Directories are accepted as valid targets.

    Args:
        body:
            Markdown body to inspect.
        source:
            Path of the document containing the body.
        bundle_root:
            Root directory of the bundle.

    Returns:
        Internal link targets whose resolved paths do not exist.

    Examples:
        >>> find_broken_links("[web](https://example.com)", Path("index.md"), Path("."))
        []
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
    """Return whether *dir_path* or any descendant contains Markdown files.

    Args:
        dir_path:
            Directory to search recursively.

    Returns:
        ``True`` when a regular ``.md`` file is present.
    """
    if not dir_path.is_dir():
        return False
    return any(item.is_file() for item in dir_path.rglob("*.md"))


def get_concept_info(path: Path) -> ConceptInfo:
    """Extract title, description, and type from a concept file.

    Falls back to a title derived from the file stem (replacing ``-`` and
    ``_`` with spaces, title-cased) when frontmatter is missing or
    incomplete.

    Args:
        path:
            Markdown concept file to inspect.

    Returns:
        Extracted concept metadata with fallback values applied.
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


def extract_outgoing_links(
    body: str,
    source: Path,
    bundle_root: Path,
) -> list[str]:
    """Extract internal markdown links from *body* as bundle-relative paths.

    Skips external URLs, self-links, and links that resolve outside the
    bundle. Returns sorted, deduplicated relative paths.

    Args:
        body:
            Markdown body to inspect.
        source:
            Path of the document containing the body.
        bundle_root:
            Root directory of the bundle.

    Returns:
        Sorted, deduplicated bundle-relative link paths.

    Examples:
        >>> root = Path("/bundle")
        >>> extract_outgoing_links("[Clock](clock.md)", root / "index.md", root)
        ['clock.md']
    """
    links: list[str] = []
    source_rel = source.relative_to(bundle_root).as_posix()

    for _text_part, target in MARKDOWN_LINK_RE.findall(body):
        resolved = resolve_link(target, source, bundle_root)
        if resolved is None:
            continue  # external link
        try:
            resolved_rel = resolved.relative_to(bundle_root).as_posix()
        except ValueError:
            continue  # link outside bundle
        if resolved_rel == source_rel:
            continue  # self-link
        if resolved_rel not in links:
            links.append(resolved_rel)

    links.sort()
    return links


# @implements_req SwRS-OKFSCHEMA-CORE-005
def build_link_graph(bundle: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    r"""Build outgoing and incoming link graphs for an OKF bundle.

    Returns a tuple ``(outgoing, incoming)`` where:

    - *outgoing* maps each concept's relative path to the list of
      concept paths it links to.
    - *incoming* maps each concept's relative path to the list of
      concept paths that link to it.

    Reserved files (``index.md``, ``log.md``) are excluded.

    Args:
        bundle:
            Root directory of the OKF bundle.

    Returns:
        Pair of outgoing and incoming adjacency mappings.

    Examples:
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> from okf_schema._internal.utils import build_link_graph
        >>> with TemporaryDirectory() as directory:
        ...     bundle = Path(directory).resolve()
        ...     _ = (bundle / "a.md").write_text(
        ...         "---\ntype: concept\n---\n\n# A\n\n[B](b.md)\n"
        ...     )
        ...     _ = (bundle / "b.md").write_text(
        ...         "---\ntype: concept\n---\n\n# B\n\n[A](a.md)\n"
        ...     )
        ...     outgoing, incoming = build_link_graph(bundle)
        ...     outgoing == {"a.md": ["b.md"], "b.md": ["a.md"]}
        True
        >>> incoming == {"a.md": ["b.md"], "b.md": ["a.md"]}
        True
    """
    outgoing: dict[str, list[str]] = {}

    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES:
            continue
        rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        _fm_text, body = extract_frontmatter(text)
        links = extract_outgoing_links(body, path, bundle)
        if links:
            outgoing[rel] = links

    # Build reverse mapping (backlinks)
    incoming: dict[str, list[str]] = {}
    for source_rel, targets in outgoing.items():
        for target_rel in targets:
            if target_rel not in incoming:
                incoming[target_rel] = []
            if source_rel not in incoming[target_rel]:
                incoming[target_rel].append(source_rel)

    for target_rel in incoming:
        incoming[target_rel].sort()

    return outgoing, incoming
