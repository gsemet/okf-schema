"""Public Python API for okf-schema.

Provides clean, typed functions for programmatic use of all okf-schema
capabilities: validation, formatting, listing, searching, graphing,
statistics, and index regeneration.
"""

from __future__ import annotations

import re
from pathlib import Path

from okf_schema._internal.models import (
    BacklinkResult,
    BundleStats,
    ConceptDetail,
    ConceptSummary,
    IndexUpdate,
    Report,
    SearchResult,
)
from okf_schema._internal.utils import (
    RESERVED_FILES,
    collect_markdown_files,
    get_concept_info,
    has_markdown_files,
    resolve_link,
)
from okf_schema._internal.yaml import extract_frontmatter, parse_yaml
from okf_schema.formatter import FormattedResult
from okf_schema.formatter import format_bundle as _format_bundle
from okf_schema.formatter import lint_bundle as _lint_bundle
from okf_schema.validator import load_schema_database
from okf_schema.validator import validate_bundle as _validate_bundle


def _resolve_bundle(bundle_path: str | Path) -> Path:
    """Resolve *bundle_path* to an absolute :class:`Path`.

    Raises:
        FileNotFoundError: When the path does not exist or is not a directory.
    """
    path = Path(bundle_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Bundle path does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Bundle path is not a directory: {path}")
    return path


def validate_bundle(
    bundle_path: str | Path,
    schema_db: str | Path | None = None,
) -> Report:
    """Validate an OKF bundle.

    Args:
        bundle_path: Path to the OKF bundle directory.
        schema_db: Optional directory containing JSON/YAML schema files.
            If not provided, the ``_schema`` subdirectory inside the bundle
            is used automatically when it exists.

    Returns:
        A :class:`Report` with all errors and warnings.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    schemas = None
    if schema_db is not None:
        schemas = load_schema_database(Path(schema_db))
    elif (bundle / "_schema").is_dir():
        schemas = load_schema_database(bundle / "_schema")
    return _validate_bundle(bundle, schemas)


def format_bundle(
    bundle_path: str | Path,
    check: bool = False,
    diff: bool = False,
) -> list[FormattedResult]:
    """Format frontmatter in all concept files of an OKF bundle.

    Args:
        bundle_path: Path to the OKF bundle directory.
        check: If ``True``, do not modify files; only report changes needed.
        diff: If ``True``, include unified diff in results without modifying.

    Returns:
        List of :class:`FormattedResult`, one per markdown file.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    return _format_bundle(bundle, check=check, diff=diff)


def lint_bundle(
    bundle_path: str | Path,
    check: bool = False,
    diff: bool = False,
    links: bool = False,
) -> list[FormattedResult]:
    """Lint frontmatter in all concept files of an OKF bundle.

    Converts block-style (multi-line) lists to inline notation so that
    frontmatter stays compact.  This is important for coding agents that
    load only the first *n* lines of a file.

    Args:
        bundle_path: Path to the OKF bundle directory.
        check: If ``True``, do not modify files; only report changes needed.
        diff: If ``True``, include unified diff in results without modifying.
        links: If ``True``, also update ``links`` and ``backlinks``
            frontmatter fields based on markdown body content.

    Returns:
        List of :class:`FormattedResult`, one per markdown file.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    return _lint_bundle(bundle, check=check, diff=diff, links=links)


def list_bundle(bundle_path: str | Path) -> list[ConceptSummary]:
    """List all concepts in an OKF bundle.

    Args:
        bundle_path: Path to the OKF bundle directory.

    Returns:
        Sorted list of :class:`ConceptSummary` objects.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    results: list[ConceptSummary] = []

    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES:
            continue
        rel = path.relative_to(bundle).as_posix()
        info = get_concept_info(path)
        results.append(ConceptSummary(path=rel, type=info.type, title=info.title))

    results.sort(key=lambda c: c.path)
    return results


def show_bundle(bundle_path: str | Path, concept_path: str) -> ConceptDetail:
    """Show a single concept's frontmatter and body.

    Args:
        bundle_path: Path to the OKF bundle directory.
        concept_path: Relative path to the concept markdown file.

    Returns:
        A :class:`ConceptDetail` with frontmatter dict and body text.

    Raises:
        FileNotFoundError: When the concept file does not exist.
    """
    bundle = _resolve_bundle(bundle_path)
    target = bundle / concept_path
    if not target.exists():
        raise FileNotFoundError(f"Concept not found: {target}")

    text = target.read_text(encoding="utf-8")
    fm_text, body = extract_frontmatter(text)
    frontmatter: dict = {}
    if fm_text is not None:
        parsed = parse_yaml(fm_text)
        if parsed is not None:
            frontmatter = parsed

    return ConceptDetail(frontmatter=frontmatter, body=body)


def index_bundle(bundle_path: str | Path) -> list[IndexUpdate]:
    """Regenerate all ``index.md`` files in an OKF bundle.

    For each directory containing markdown files, generates or updates an
    ``index.md`` listing child concepts and subdirectories. Preserves
    bundle-root frontmatter if present.

    Args:
        bundle_path: Path to the OKF bundle directory.

    Returns:
        List of :class:`IndexUpdate` records describing what changed.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    updates: list[IndexUpdate] = []

    # Load schema database if available
    schema_db_path = bundle / "_schema"
    schema_info: dict[str, dict] = {}
    if schema_db_path.is_dir():
        raw_schemas = load_schema_database(schema_db_path)
        for type_key, schema in raw_schemas.items():
            schema_info[type_key] = {
                "title": schema.get("title", ""),
                "description": schema.get("description", ""),
                "x-okf-summary": schema.get("x-okf-summary", ""),
            }

    # Collect all directories that contain markdown files
    dirs_with_md: set[Path] = set()
    for md_file in collect_markdown_files(bundle):
        dirs_with_md.add(md_file.parent)
    dirs_with_md.add(bundle)

    for dir_path in sorted(dirs_with_md):
        concepts = _get_concept_files(dir_path)
        subdirs = _get_immediate_subdirs_with_content(dir_path)

        if dir_path != bundle and not concepts and not subdirs:
            continue

        index_path = dir_path / "index.md"
        preserved_descriptions: dict[str, str] = {}
        preserved_intro: str = ""
        preserve_frontmatter: str | None = None

        if index_path.exists():
            text = index_path.read_text(encoding="utf-8")
            fm_text, _body = extract_frontmatter(text)
            if dir_path == bundle and fm_text is not None:
                preserve_frontmatter = fm_text.strip()
            parsed = _parse_existing_index(text)
            preserved_descriptions = parsed.get("descriptions", {})
            preserved_intro = parsed.get("intro", "")

        new_content = _generate_index_content(
            dir_path,
            bundle,
            preserve_frontmatter,
            preserved_descriptions,
            schema_info,
            preserved_intro,
        )

        if index_path.exists():
            old_content = index_path.read_text(encoding="utf-8")
            if old_content == new_content:
                rel = index_path.relative_to(bundle).as_posix()
                updates.append(IndexUpdate(path=rel, action="unchanged"))
                continue

        rel = index_path.relative_to(bundle).as_posix()
        action = "updated" if index_path.exists() else "created"
        index_path.write_text(new_content, encoding="utf-8")
        updates.append(IndexUpdate(path=rel, action=action))

    return updates


def search_bundle(bundle_path: str | Path, query: str) -> list[SearchResult]:
    """Search concepts in an OKF bundle.

    Performs a case-insensitive substring search across ``title``,
    ``description``, ``type``, and ``tags`` frontmatter fields.

    Args:
        bundle_path: Path to the OKF bundle directory.
        query: Search string.

    Returns:
        Sorted list of matching :class:`SearchResult` objects.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    query_lower = query.lower()
    results: list[SearchResult] = []
    seen: set[str] = set()

    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES:
            continue
        rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        fm_text, _body = extract_frontmatter(text)
        if fm_text is None:
            continue
        frontmatter = parse_yaml(fm_text)
        if frontmatter is None:
            continue

        fields: list[str] = []
        for key in ("title", "description", "type", "tags"):
            value = frontmatter.get(key)
            if value is None:
                continue
            if isinstance(value, list):
                fields.extend(str(v).lower() for v in value)
            else:
                fields.append(str(value).lower())

        if any(query_lower in field for field in fields) and rel not in seen:
            seen.add(rel)
            info = get_concept_info(path)
            results.append(SearchResult(path=rel, type=info.type, title=info.title))

    results.sort(key=lambda r: r.path)
    return results


def graph_bundle(bundle_path: str | Path) -> dict[str, list[str]]:
    """Build a concept link graph for an OKF bundle.

    Parses all internal markdown links in concept bodies and returns an
    adjacency dictionary mapping each concept's relative path to the list
    of concept paths it links to.

    Args:
        bundle_path: Path to the OKF bundle directory.

    Returns:
        Adjacency dict: ``{concept_path: [linked_path, ...]}``.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    graph: dict[str, list[str]] = {}
    link_re = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")

    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES:
            continue
        rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        _fm_text, body = extract_frontmatter(text)
        links: list[str] = []

        for _text_part, target in link_re.findall(body):
            resolved = resolve_link(target, path, bundle)
            if resolved is None:
                continue  # external link
            # Only include links to other markdown files within the bundle
            try:
                resolved_rel = resolved.relative_to(bundle).as_posix()
            except ValueError:
                continue  # link outside bundle
            if resolved_rel != rel and resolved_rel not in links:
                links.append(resolved_rel)

        if links:
            graph[rel] = sorted(links)

    return graph


def backlinks_bundle(
    bundle_path: str | Path,
    targets: list[str],
) -> list[BacklinkResult]:
    """Find all concepts that link to any of the given target concepts.

    For each target path, scans every concept in the bundle and returns
    a backlink record for each concept that contains an internal markdown
    link pointing to that target.  Reserved files (``index.md``,
    ``log.md``) are excluded as sources.  Self-links are ignored.

    Targets may be given with or without the ``.md`` extension.

    Args:
        bundle_path: Path to the OKF bundle directory.
        targets: List of relative concept paths to find backlinks for.

    Returns:
        Sorted list of :class:`BacklinkResult` records, one per backlink.
        Results are ordered by ``(target, source)``.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    link_re = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
    target_set = {t if t.endswith(".md") else f"{t}.md" for t in targets}
    results: list[BacklinkResult] = []

    for path in collect_markdown_files(bundle):
        if path.name in RESERVED_FILES:
            continue
        source_rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        _fm_text, body = extract_frontmatter(text)

        for _text_part, target in link_re.findall(body):
            resolved = resolve_link(target, path, bundle)
            if resolved is None:
                continue  # external link
            try:
                resolved_rel = resolved.relative_to(bundle).as_posix()
            except ValueError:
                continue  # link outside bundle
            if resolved_rel == source_rel:
                continue  # self-link
            if resolved_rel in target_set:
                results.append(BacklinkResult(target=resolved_rel, source=source_rel))

    results.sort(key=lambda r: (r.target, r.source))
    return results


def stats_bundle(bundle_path: str | Path) -> BundleStats:
    """Compute statistics for an OKF bundle.

    Args:
        bundle_path: Path to the OKF bundle directory.

    Returns:
        A :class:`BundleStats` object with file counts, link counts,
        type/tag distributions, and directory counts.

    Raises:
        FileNotFoundError: When *bundle_path* does not exist.
        NotADirectoryError: When *bundle_path* is not a directory.
    """
    bundle = _resolve_bundle(bundle_path)
    total_files = 0
    total_concepts = 0
    files_without_frontmatter = 0
    total_size = 0
    total_links = 0
    broken_links = 0
    types_distribution: dict[str, int] = {}
    tags_distribution: dict[str, int] = {}
    dirs_with_md: set[Path] = set()

    for path in collect_markdown_files(bundle):
        total_files += 1
        total_size += path.stat().st_size
        dirs_with_md.add(path.parent)

        if path.name in RESERVED_FILES:
            continue

        total_concepts += 1
        text = path.read_text(encoding="utf-8")
        fm_text, body = extract_frontmatter(text)
        if fm_text is None:
            files_without_frontmatter += 1
            continue

        frontmatter = parse_yaml(fm_text)
        if frontmatter is not None:
            type_val = frontmatter.get("type")
            if type_val:
                type_str = str(type_val).strip()
                types_distribution[type_str] = types_distribution.get(type_str, 0) + 1

            tags = frontmatter.get("tags")
            if isinstance(tags, list):
                for tag in tags:
                    tag_str = str(tag).strip()
                    if tag_str:
                        tags_distribution[tag_str] = tags_distribution.get(tag_str, 0) + 1

        # Count links
        for _text_part, target in re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)").findall(body):
            total_links += 1
            resolved = resolve_link(target, path, bundle)
            if resolved is not None and not resolved.exists():
                broken_links += 1

    return BundleStats(
        total_files=total_files,
        total_concepts=total_concepts,
        files_without_frontmatter=files_without_frontmatter,
        total_size=total_size,
        total_links=total_links,
        broken_links=broken_links,
        types_distribution=types_distribution,
        tags_distribution=tags_distribution,
        directories=len(dirs_with_md),
    )


# ---------------------------------------------------------------------------
# Internal helpers for index generation (adapted from index_okf.py)
# ---------------------------------------------------------------------------


def _get_concept_files(dir_path: Path) -> list[Path]:
    """Return concept ``.md`` files directly in *dir_path* (non-reserved)."""
    concepts: list[Path] = []
    for item in sorted(dir_path.iterdir()):
        if item.is_file() and item.suffix == ".md" and item.name not in RESERVED_FILES:
            concepts.append(item)
    return concepts


def _get_immediate_subdirs_with_content(dir_path: Path) -> list[Path]:
    """Return immediate subdirectories that contain markdown files."""
    subdirs: list[Path] = []
    for item in sorted(dir_path.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and has_markdown_files(item):
            subdirs.append(item)
    return subdirs


def _get_subdir_description(
    subdir: Path,
    schema_info: dict[str, dict] | None = None,
) -> str:
    """Extract a description for a subdirectory.

    Prefers schema ``x-okf-summary`` (or ``description`` as fallback) when
    all concepts in the subdirectory share the same type and a matching
    schema is available. Otherwise falls back to the subdirectory's
    existing ``index.md`` body or a generic placeholder.
    """
    schema_info = schema_info or {}

    # Determine the dominant type in the subdirectory
    concept_files = _get_concept_files(subdir)
    types_found: set[str] = set()
    for concept in concept_files:
        info = get_concept_info(concept)
        if info.type:
            types_found.add(info.type)

    # If all concepts share a single type and we have schema info, use it
    if len(types_found) == 1:
        type_key = next(iter(types_found))
        if type_key in schema_info:
            info_map: dict[str, str] = schema_info[type_key]
            summary = info_map.get("x-okf-summary", "")
            if summary:
                return summary
            desc = info_map.get("description", "")
            if desc:
                # Truncate long descriptions
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                return desc

    # Fallback: extract from existing index.md body
    index_path = subdir / "index.md"
    if not index_path.exists():
        return f"Auto-generated index for concepts in `{subdir.name}`."

    try:
        text = index_path.read_text(encoding="utf-8")
        _fm_text, body = extract_frontmatter(text)
    except (OSError, UnicodeDecodeError):
        return f"Auto-generated index for concepts in `{subdir.name}`."

    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            if stripped.startswith("- ") or stripped.startswith("* "):
                stripped = stripped[2:].strip()
            if len(stripped) > 120:
                stripped = stripped[:117] + "..."
            return stripped

    return f"Auto-generated index for concepts in `{subdir.name}`."


def _parse_existing_index(text: str) -> dict:
    """Parse an existing index.md to extract preserved descriptions.

    Returns a dict with keys ``title``, ``intro``, and ``descriptions``
    (mapping link target -> description string).
    """
    result: dict = {"title": "", "intro": "", "descriptions": {}}
    lines = text.splitlines()
    in_intro = False
    current_intro_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not result["title"]:
            result["title"] = stripped[2:].strip()
            in_intro = True
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            in_intro = False
            if current_intro_lines:
                result["intro"] = "\n".join(current_intro_lines).strip()
                current_intro_lines = []

            item_text = stripped[2:].strip()
            match = re.match(r"\[([^\]]+)\]\(([^)]+)\)\s*[—\-]\s*(.+)", item_text)
            if match:
                target = match.group(2)
                desc = match.group(3).strip()
                desc = re.sub(r"\s+\[[^\]]+\]\s*$", "", desc)
                result["descriptions"][target] = desc
            continue

        if in_intro and stripped:
            current_intro_lines.append(stripped)

    if current_intro_lines and not result["intro"]:
        result["intro"] = "\n".join(current_intro_lines).strip()

    return result


def _generate_index_content(
    dir_path: Path,
    bundle_root: Path,
    preserve_frontmatter: str | None = None,
    preserved_descriptions: dict[str, str] | None = None,
    schema_info: dict[str, dict] | None = None,
    preserved_intro: str = "",
) -> str:
    """Generate the full content for an index.md file."""
    lines: list[str] = []
    preserved = preserved_descriptions or {}
    schema_info = schema_info or {}

    if preserve_frontmatter is not None:
        lines.append("---")
        lines.append(preserve_frontmatter)
        lines.append("---")
        lines.append("")

    # Determine heading and intro for non-root directories
    heading = bundle_root.name if dir_path == bundle_root else dir_path.name
    intro = ""
    has_schema_info = False

    if dir_path != bundle_root:
        # Determine the dominant type in this directory
        concept_files = _get_concept_files(dir_path)
        types_found: set[str] = set()
        for concept in concept_files:
            info = get_concept_info(concept)
            if info.type:
                types_found.add(info.type)

        # If all concepts share a single type and we have schema info, use it
        if len(types_found) == 1:
            type_key = next(iter(types_found))
            if type_key in schema_info:
                has_schema_info = True
                schema_title = schema_info[type_key].get("title", "")
                schema_desc = schema_info[type_key].get("description", "")
                if schema_title:
                    heading = schema_title
                if schema_desc:
                    intro = schema_desc

        # If no schema info available, preserve existing intro text
        if not has_schema_info and preserved_intro:
            intro = preserved_intro

    lines.append(f"# {heading}")
    lines.append("")

    if intro:
        lines.append(intro)
        lines.append("")

    concepts = _get_concept_files(dir_path)
    subdirs = _get_immediate_subdirs_with_content(dir_path)

    if not concepts and not subdirs:
        lines.append("No concepts or subdirectories found.")
        lines.append("")
        return "\n".join(lines)

    entries: list[tuple[str, str]] = []

    for concept in concepts:
        info = get_concept_info(concept)
        rel_path = concept.name
        desc = preserved.get(rel_path, info.description)
        parts = [f"- [{info.title}]({rel_path})"]
        if desc:
            parts.append(f" — {desc}")
        if info.type:
            parts.append(f"  [{info.type}]")
        entries.append((info.title.lower(), "".join(parts)))

    for subdir in subdirs:
        subdir_rel = f"./{subdir.name}/"
        # Determine if schema info applies to this subdir
        subdir_concepts = _get_concept_files(subdir)
        subdir_types: set[str] = set()
        for sc in subdir_concepts:
            s_info = get_concept_info(sc)
            if s_info.type:
                subdir_types.add(s_info.type)

        if len(subdir_types) == 1:
            type_key = next(iter(subdir_types))
            if type_key in schema_info:
                # Schema info available: use it directly (replaces existing text)
                summary = schema_info[type_key].get("x-okf-summary", "")
                if summary:
                    desc = summary
                else:
                    desc = schema_info[type_key].get("description", "")
                    if len(desc) > 120:
                        desc = desc[:117] + "..."
            else:
                desc = preserved.get(subdir_rel, _get_subdir_description(subdir, schema_info))
        else:
            desc = preserved.get(subdir_rel, _get_subdir_description(subdir, schema_info))
        entries.append((subdir.name.lower(), f"- [{subdir.name}]({subdir_rel}) — {desc}"))

    entries.sort(key=lambda x: x[0])

    for _sort_key, line in entries:
        lines.append(line)

    lines.append("")
    return "\n".join(lines)
