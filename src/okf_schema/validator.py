"""OKF bundle validation engine.

Implements conformance error (E1-E10) and best-practice warning (W1-W13)
rules for validating OKF (Open Knowledge Format) bundles.

OKF 0.2 additions (E8-E10, W8-W13):
  E8  – `generated` block present but `at` field missing
  E9  – `sources` entry missing required `resource` field
  E10 – `verified` entry missing required `by` or `at` field
  W8  – Deprecated `timestamp` field; use `generated.at` instead
  W9  – Deprecated body `# Citations` section; use `sources` frontmatter
  W10 – Malformed actor string in `verified[].by`
  W11 – File is stale (`stale_after` date has passed)
  W12 – Footnote `[^id]` with no matching `sources[].id`
  W13 – Broken path in path-form `resource` or `sources[].resource`
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, cast

import pyjson5
from jsonschema import Draft202012Validator
from ruamel.yaml.error import YAMLError

from okf_schema._internal.models import Report
from okf_schema._internal.utils import (
    ISO8601_DATE_RE,
    RESERVED_FILES,
    collect_markdown_files,
    find_broken_links,
)
from okf_schema._internal.yaml import extract_frontmatter, make_yaml, parse_yaml

# Matches OKF actor strings: <prefix>:<identifier>  e.g. human:alice, bot:ci
_ACTOR_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*:.+$")
# Matches Markdown footnote references [^id] in body text
_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")
# Matches Markdown footnote definitions [^id]: ...
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.MULTILINE)
# Matches body-level # Citations heading
_CITATIONS_HEADING_RE = re.compile(r"^#{1,6}\s+Citations\s*$", re.MULTILINE | re.IGNORECASE)


def _resolve_ref(ref_path: str, schema_db: Path, y: Any) -> dict | None:
    """Load a schema fragment referenced by *ref_path*.

    The *ref_path* is resolved relative to *schema_db*.  Supported
    extensions are ``.json``, ``.json5``, ``.yaml``, and ``.yml``.
    If *ref_path* has no recognised extension, each extension is tried
    in turn (``.json``, ``.json5``, ``.yaml``, ``.yml``) until a file
    is found and parsed successfully.

    Args:
        ref_path: Relative path to the referenced schema file.
        schema_db: Base directory for relative resolution.
        y: Configured ruamel.yaml instance.

    Returns:
        The loaded schema dict, or ``None`` if the file cannot be read
        or parsed.
    """
    target = schema_db / ref_path
    candidates = [target]
    if not any(ref_path.endswith(ext) for ext in (".json", ".json5", ".yaml", ".yml")):
        candidates.extend(target.with_suffix(ext) for ext in (".json", ".json5", ".yaml", ".yml"))

    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError:
            continue

        name = candidate.name
        try:
            if name.endswith(".json"):
                return cast(dict, json.loads(text))
            if name.endswith(".json5"):
                return cast(dict, pyjson5.loads(text))
            if name.endswith(".yaml") or name.endswith(".yml"):
                data = y.load(text)
                if isinstance(data, dict):
                    return dict(data)
        except (json.JSONDecodeError, pyjson5.Json5DecoderException, YAMLError):
            continue
    return None


def _resolve_refs_in_schema(schema: dict, schema_db: Path, y: Any) -> dict:
    """Recursively inline all ``$ref`` references inside *schema*.

    When a ``$ref`` appears alongside other keys, the referenced dict is
    merged with the remaining keys (siblings override the referenced
    content).

    Args:
        schema: Schema dict potentially containing ``$ref`` keys.
        schema_db: Base directory for relative path resolution.
        y: Configured ruamel.yaml instance.

    Returns:
        A new dict with all ``$ref`` nodes replaced by the loaded
        referenced content.
    """
    ref_value = schema.get("$ref")
    if isinstance(ref_value, str):
        resolved = _resolve_ref(ref_value, schema_db, y)
        if resolved is not None:
            base = _resolve_refs_in_schema(resolved, schema_db, y)
            # Merge remaining keys on top of the referenced content
            merged = dict(base)
            for key, value in schema.items():
                if key == "$ref":
                    continue
                if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                    merged[key] = {**merged[key], **_resolve_refs_in_schema(value, schema_db, y)}
                else:
                    merged[key] = (
                        _resolve_refs_in_schema(value, schema_db, y)
                        if isinstance(value, dict)
                        else value
                    )
            return merged

    result: dict = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            result[key] = _resolve_refs_in_schema(value, schema_db, y)
        elif isinstance(value, list):
            result[key] = [
                _resolve_refs_in_schema(item, schema_db, y) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def load_schema_database(schema_db: Path) -> dict[str, dict]:
    """Load all JSON/YAML schema files from *schema_db* into a type→schema map.

    Files are expected to be named ``<type>.schema.json``,
    ``<type>.schema.json5``, or ``<type>.schema.yaml``.  The *type* key
    is the stem before ``.schema``.

    ``$ref`` references to external files are resolved relative to
    *schema_db* and inlined into the loaded schema.

    Args:
        schema_db: Directory containing schema files.

    Returns:
        Mapping from type name to schema dict.
    """
    schemas: dict[str, dict] = {}
    if not schema_db.is_dir():
        return schemas

    y = make_yaml()
    for path in schema_db.iterdir():
        if not path.is_file():
            continue
        name = path.name
        raw_schema: dict | None = None
        if name.endswith(".schema.json"):
            type_key = name[: -len(".schema.json")]
            try:
                raw_schema = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
        elif name.endswith(".schema.json5"):
            type_key = name[: -len(".schema.json5")]
            try:
                raw_schema = pyjson5.loads(path.read_text(encoding="utf-8"))
            except (pyjson5.Json5DecoderException, OSError):
                continue
        elif name.endswith(".schema.yaml") or name.endswith(".schema.yml"):
            type_key = (
                name[: -len(".schema.yaml")]
                if name.endswith(".schema.yaml")
                else name[: -len(".schema.yml")]
            )
            try:
                data = y.load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    raw_schema = dict(data)
            except YAMLError:
                continue

        if raw_schema is not None:
            schemas[type_key] = _resolve_refs_in_schema(raw_schema, schema_db, y)

    return schemas


def validate_against_schema(
    frontmatter: dict,
    schema: dict,
    type_name: str,
) -> list[str]:
    """Validate *frontmatter* against *schema*.

    Args:
        frontmatter: Parsed YAML frontmatter dict.
        schema: JSON Schema dict.
        type_name: Type name for error messages.

    Returns:
        List of human-readable validation error strings.
    """
    errors: list[str] = []
    try:
        validator = Draft202012Validator(schema)
        for err in validator.iter_errors(frontmatter):
            path = "/".join(str(p) for p in err.path) if err.path else "<root>"
            errors.append(f"[{path}] {err.message}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Schema validator error for type '{type_name}': {exc}")
    return errors


def _derive_trust_tier(frontmatter: dict) -> str:
    """Derive the OKF 0.2 trust tier from `verified` entries.

    Returns one of: ``"unverified"``, ``"machine-confirmed"``, or
    ``"human-reviewed"``.  Only well-formed actor strings contribute to
    tier promotion; malformed entries are ignored (W10).
    """
    verified = frontmatter.get("verified")
    if not verified:
        return "unverified"

    # Normalize bare mapping to one-element list
    if isinstance(verified, dict):
        verified = [verified]

    if not isinstance(verified, list):
        return "unverified"

    has_machine = False
    for entry in verified:
        if not isinstance(entry, dict):
            continue
        by = entry.get("by")
        if not isinstance(by, str) or not _ACTOR_RE.match(by):
            continue  # malformed actor — skip for tier derivation
        if by.startswith("human:"):
            return "human-reviewed"
        has_machine = True

    return "machine-confirmed" if has_machine else "unverified"


def _is_stale(frontmatter: dict) -> bool:
    """Return ``True`` when today ≥ the ``stale_after`` date in *frontmatter*."""
    stale_after = frontmatter.get("stale_after")
    if not stale_after:
        return False
    stale_str = str(stale_after).strip()
    if not ISO8601_DATE_RE.match(stale_str):
        return False
    try:
        return date.today() >= date.fromisoformat(stale_str)
    except ValueError:
        return False


def _validate_okf2_generated(
    path: Path,
    frontmatter: dict,
    report: Report,
) -> None:
    """Validate the OKF 0.2 `generated` block (E8, W8).

    E8 — `generated` block present but `at` field missing.
    W8 — Deprecated `timestamp` field present instead of `generated.at`.
    """
    generated = frontmatter.get("generated")
    timestamp = frontmatter.get("timestamp")

    if generated is not None:
        if isinstance(generated, dict) and not generated.get("at"):
            report.add_error(
                "E8",
                f"File '{path}' has 'generated' block but 'at' field is missing. "
                "Fix: add 'generated.at: <ISO-8601-datetime>' to the frontmatter.",
                path,
            )
        # `generated` present but not a dict — handled by schema validation (E4)
    elif timestamp is not None:
        report.add_warning(
            "W8",
            f"File '{path}' uses deprecated 'timestamp' field. "
            "Migrate to 'generated.at'. "
            "Fix: okf-schema lint --path <bundle> --fix-timestamp",
            path,
        )


def _validate_okf2_sources(
    path: Path,
    frontmatter: dict,
    body: str,
    bundle_root: Path,
    report: Report,
) -> None:
    """Validate the OKF 0.2 `sources` block and footnote integrity (E9, W9, W12, W13)."""
    sources = frontmatter.get("sources")

    # W9 — deprecated body # Citations section
    if _CITATIONS_HEADING_RE.search(body):
        report.add_warning(
            "W9",
            f"File '{path}' has a deprecated '# Citations' body section. "
            "Migrate to 'sources' frontmatter with markdown footnotes. "
            "Fix: move citations to 'sources:' frontmatter entries and use [^id] footnotes.",
            path,
        )

    if sources is None:
        return

    # Normalize to list if it's a bare mapping
    if isinstance(sources, dict):
        sources_list = [sources]
    elif isinstance(sources, list):
        sources_list = sources
    else:
        return

    # E9 — each entry must have `resource`
    valid_ids: set[str] = set()
    for i, entry in enumerate(sources_list):
        if not isinstance(entry, dict):
            continue
        if not entry.get("resource"):
            report.add_error(
                "E9",
                f"File '{path}': sources entry [{i}] is missing required 'resource' field. "
                "Fix: add 'resource: <URI-or-path>' to the sources entry.",
                path,
            )

        # Collect valid IDs for W12 footnote checking
        entry_id = entry.get("id")
        if entry_id:
            valid_ids.add(str(entry_id))

        # W13 — broken path-form resource (skip URLs and scope descriptors)
        resource = entry.get("resource")
        if resource and isinstance(resource, str):
            _check_resource_path(path, resource, bundle_root, report)

    # W12 — footnote reference [^id] with no matching sources[].id
    footnote_refs = set(_FOOTNOTE_REF_RE.findall(body))
    for ref_id in footnote_refs:
        if ref_id not in valid_ids:
            report.add_warning(
                "W12",
                f"File '{path}': footnote reference '[^{ref_id}]' has no matching "
                "sources entry with id '{ref_id}'. "
                f"Fix: add a sources entry with 'id: {ref_id}' or remove the footnote.",
                path,
            )


def _check_resource_path(
    doc_path: Path,
    resource: str,
    bundle_root: Path,
    report: Report,
) -> None:
    """Emit W13 if *resource* is a path-form string that does not resolve."""
    # Skip URLs (contain "://") and scope descriptors (no file separators and no extension)
    if "://" in resource or resource.startswith("mailto:"):
        return
    # Skip apparent scope descriptors: no "/" or "\" and no "." extension
    if "/" not in resource and "\\" not in resource and "." not in resource:
        return

    # Attempt to resolve relative to bundle root and doc parent
    for base in (bundle_root, doc_path.parent):
        candidate = (base / resource).resolve()
        if candidate.exists():
            return

    report.add_warning(
        "W13",
        f"File '{doc_path}': resource path '{resource}' does not resolve to an existing file. "
        "Fix: correct the path or use a full URL.",
        doc_path,
    )


def _validate_okf2_verified(
    path: Path,
    frontmatter: dict,
    report: Report,
) -> None:
    """Validate the OKF 0.2 `verified` block (E10, W10)."""
    verified = frontmatter.get("verified")
    if verified is None:
        return

    # Normalize bare mapping to one-element list per OKF 0.2 §11 MUST
    if isinstance(verified, dict):
        entries = [verified]
    elif isinstance(verified, list):
        entries = verified
    else:
        return

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue

        by = entry.get("by")
        at = entry.get("at")

        if not by:
            report.add_error(
                "E10",
                f"File '{path}': verified entry [{i}] is missing required 'by' field. "
                "Fix: add 'by: <actor-string>' to the verified entry.",
                path,
            )
        elif not isinstance(by, str) or not _ACTOR_RE.match(by):
            report.add_warning(
                "W10",
                f"File '{path}': verified entry [{i}] has malformed 'by' value '{by}'. "
                "Actor strings must follow the format '<prefix>:<identifier>' "
                "(e.g. 'human:alice', 'bot:ci'). "
                "Fix: correct the 'by' value in verified entry [{i}].",
                path,
            )

        if not at:
            report.add_error(
                "E10",
                f"File '{path}': verified entry [{i}] is missing required 'at' field. "
                "Fix: add 'at: <ISO-8601-date>' to the verified entry.",
                path,
            )


def _validate_okf2_lifecycle(
    path: Path,
    frontmatter: dict,
    report: Report,
) -> None:
    """Validate OKF 0.2 lifecycle fields `status` and `stale_after` (W11)."""
    if _is_stale(frontmatter):
        stale_after = frontmatter.get("stale_after")
        report.add_warning(
            "W11",
            f"File '{path}' is stale: stale_after date '{stale_after}' has passed. "
            "Fix: update content and set a new 'stale_after' date, or remove the field.",
            path,
        )


def _has_nested_lists(value: object) -> bool:
    """Recursively check if *value* contains any nested list structures.

    A list is "unflatten" if it contains nested lists (e.g.
    ``tags: [[a, b], c]``).
    """
    if isinstance(value, list):
        for item in value:
            if isinstance(item, list):
                return True
            if _has_nested_lists(item):
                return True
    elif isinstance(value, dict):
        for v in value.values():
            if _has_nested_lists(v):
                return True
    return False


def _has_block_lists(fm_text: str) -> bool:
    """Check if frontmatter contains block-style (multi-line) lists.

    Uses ruamel.yaml to detect ``flow_style()`` on CommentedSeq objects.
    Block-style lists expand the frontmatter vertically, which reduces
    the amount of content visible to coding agents that load only the
    first *n* lines of a file.

    Block-style *mappings* (dicts) are exempt — OKF 0.2 fields like
    ``generated``, ``sources``, ``verified`` are naturally block-mapped.

    Args:
        fm_text: Raw YAML frontmatter text (without ``---`` delimiters).

    Returns:
        ``True`` when at least one *list* uses block style.
    """
    from ruamel.yaml.comments import CommentedSeq

    y = make_yaml()
    try:
        data = y.load(fm_text)
    except Exception:  # noqa: BLE001
        return False
    if not isinstance(data, dict):
        return False

    for value in data.values():
        if (
            isinstance(value, CommentedSeq)
            and hasattr(value, "fa")
            and hasattr(value.fa, "flow_style")
            and value.fa.flow_style() is False
        ):
            return True
    return False


def validate_concept(
    path: Path,
    report: Report,
    bundle_root: Path,
    schemas: dict[str, dict] | None,
) -> None:
    """Validate a single concept (non-reserved) ``.md`` file.

    Checks E1, E2, E4, E5, E8-E10, W1, W2, W3, W6-W13.

    Args:
        path: Path to the concept markdown file.
        report: Report to append findings to.
        bundle_root: Root directory of the OKF bundle.
        schemas: Optional schema database mapping type→schema.
    """
    text = path.read_text(encoding="utf-8")
    fm_text, body = extract_frontmatter(text)

    # E1 — parseable frontmatter
    if fm_text is None:
        report.add_error("E1", f"File '{path}' has no YAML frontmatter", path)
        return

    frontmatter = parse_yaml(fm_text)
    if frontmatter is None:
        report.add_error("E1", f"File '{path}' has unparseable YAML frontmatter", path)
        return

    # E2 — non-empty type field
    type_val = frontmatter.get("type")
    if not type_val or not str(type_val).strip():
        report.add_error("E2", f"File '{path}' has frontmatter but no 'type' field", path)
    else:
        type_str = str(type_val).strip()
        # Schema validation (E4 / W6)
        if schemas is not None:
            if type_str in schemas:
                schema_errors = validate_against_schema(frontmatter, schemas[type_str], type_str)
                for err_msg in schema_errors:
                    report.add_error(
                        "E4",
                        f"Schema validation failed for '{path}': {err_msg}",
                        path,
                    )
            else:
                report.add_warning(
                    "W6",
                    f"No schema found for type '{type_str}' in '{path}'",
                    path,
                )

    # E5 — unflatten lists in frontmatter
    if _has_nested_lists(frontmatter):
        report.add_error(
            "E5",
            f"File '{path}' has nested list structures in frontmatter",
            path,
        )

    # W7 — block-style (multi-line) lists in frontmatter
    if _has_block_lists(fm_text):
        report.add_warning(
            "W7",
            f"File '{path}' has block-style lists in frontmatter. "
            "Use inline notation (e.g. 'tags: [a, b]') to keep frontmatter compact. "
            "Run 'okf-schema lint --path <bundle>' to auto-fix.",
            path,
        )

    # W1 — missing recommended fields
    for field_name in ("title", "description"):
        if field_name not in frontmatter or not frontmatter[field_name]:
            report.add_warning(
                "W1",
                f"Missing recommended field '{field_name}' in '{path}'",
                path,
            )

    # W3 — missing provenance timestamp (accepts either generated.at or legacy timestamp)
    generated = frontmatter.get("generated")
    has_generated_at = isinstance(generated, dict) and bool(generated.get("at"))
    has_timestamp = bool(frontmatter.get("timestamp"))
    if not has_generated_at and not has_timestamp:
        report.add_warning(
            "W3",
            f"No provenance timestamp in '{path}'. "
            "Add 'generated.at: <ISO-8601-datetime>' to the frontmatter.",
            path,
        )

    # W2 — broken cross-links
    broken = find_broken_links(body, path, bundle_root)
    for target in broken:
        report.add_warning("W2", f"Broken cross-link '{target}' in '{path}'", path)

    # OKF 0.2: validate generated, sources, verified, and lifecycle fields
    _validate_okf2_generated(path, frontmatter, report)
    _validate_okf2_sources(path, frontmatter, body, bundle_root, report)
    _validate_okf2_verified(path, frontmatter, report)
    _validate_okf2_lifecycle(path, frontmatter, report)


def validate_index(
    path: Path,
    report: Report,
    bundle_root: Path,
) -> None:
    """Validate an ``index.md`` file.

    Checks E3 (non-root index.md must NOT have frontmatter).

    Args:
        path: Path to the index.md file.
        report: Report to append findings to.
        bundle_root: Root directory of the OKF bundle.
    """
    text = path.read_text(encoding="utf-8")
    fm_text, _body = extract_frontmatter(text)

    # Bundle-root index.md MAY have frontmatter with okf_version
    is_root = path.parent.resolve() == bundle_root.resolve()
    if fm_text is not None and not is_root:
        report.add_error(
            "E3",
            f"Reserved file '{path}' has unexpected frontmatter "
            "(only bundle-root index.md may have frontmatter)",
            path,
        )


def validate_log(
    path: Path,
    report: Report,
) -> None:
    """Validate a ``log.md`` file.

    Checks E3 (no frontmatter) and W5 (ISO 8601 date headings).

    Args:
        path: Path to the log.md file.
        report: Report to append findings to.
    """
    text = path.read_text(encoding="utf-8")
    fm_text, _body = extract_frontmatter(text)

    if fm_text is not None:
        report.add_error(
            "E3",
            f"Reserved file '{path}' has unexpected frontmatter",
            path,
        )

    # Check date headings
    for line in text.splitlines():
        if line.startswith("## "):
            date_candidate = line[3:].strip()
            if not ISO8601_DATE_RE.match(date_candidate):
                report.add_warning(
                    "W5",
                    f"log.md '{path}' date heading '{date_candidate}' not in ISO 8601 format",
                    path,
                )


def _check_reserved_file_naming(
    path: Path,
    report: Report,
    bundle_root: Path,
) -> None:
    """Check for E6: reserved file naming conflicts.

    Flags when a reserved file (``index.md`` or ``log.md``) exists in
    an unexpected location. ``log.md`` must only exist at bundle root.
    ``index.md`` is allowed at any directory level.

    Args:
        path: Path to the reserved file.
        report: Report to append findings to.
        bundle_root: Root directory of the OKF bundle.
    """
    filename = path.name
    if filename == "log.md":
        is_root = path.parent.resolve() == bundle_root.resolve()
        if not is_root:
            report.add_error(
                "E6",
                f"Reserved file '{path}' is not at bundle root (log.md must be at bundle root)",
                path,
            )


def validate_bundle(
    bundle: Path,
    schemas: dict[str, dict] | None = None,
) -> Report:
    """Run the full validation suite over *bundle*.

    Orchestrates all validators and emits W4 (missing index.md) for
    directories that contain markdown files but no ``index.md``,
    and E7 (loose root file) for non-reserved ``.md`` files at bundle
    root.

    Args:
        bundle: Path to the OKF bundle directory.
        schemas: Optional schema database mapping type→schema.

    Returns:
        A :class:`Report` containing all errors and warnings.
    """
    report = Report()

    if not bundle.is_dir():
        report.add_error("E0", f"Bundle path '{bundle}' is not a directory")
        return report

    # Track directories that contain markdown files
    dirs_with_md: set[Path] = set()

    for path in collect_markdown_files(bundle):
        dirs_with_md.add(path.parent)

        filename = path.name

        if filename in RESERVED_FILES:
            if filename == "index.md":
                validate_index(path, report, bundle)
            elif filename == "log.md":
                validate_log(path, report)
            _check_reserved_file_naming(path, report, bundle)
        else:
            validate_concept(path, report, bundle, schemas)
            # E7 — non-reserved .md files at bundle root
            if path.parent.resolve() == bundle.resolve():
                report.add_error(
                    "E7",
                    f"File '{path.name}' is at bundle root but is not a reserved file "
                    "(index.md or log.md). Move it into a subdirectory.",
                    path,
                )

    # W4 — directories missing index.md
    for directory in dirs_with_md:
        if directory == bundle:
            continue  # root may or may not have index.md
        index_file = directory / "index.md"
        if not index_file.exists():
            report.add_warning(
                "W4",
                f"No 'index.md' in directory '{directory.relative_to(bundle)}'",
                directory,
            )

    return report


def validate_markdown_files(
    file_paths: list[Path],
    schemas: dict[str, dict] | None = None,
) -> Report:
    """Validate standalone markdown files (not part of an OKF bundle).

    Validates each file using E1-E5 and W1-W3, W6-W7 rules.
    Bundle-specific constraints (E7, W4, E6, W5) are not applied.
    Links are not validated since there is no common root.

    Args:
        file_paths: List of markdown file paths to validate.
        schemas: Optional schema database mapping type→schema.

    Returns:
        A :class:`Report` containing all errors and warnings.
    """
    report = Report()

    for path in sorted(file_paths):
        if not path.is_file():
            report.add_warning("W0", f"Path is not a file: {path}", path)
            continue

        text = path.read_text(encoding="utf-8")
        fm_text, body = extract_frontmatter(text)

        # E1 — parseable frontmatter
        if fm_text is None:
            report.add_error("E1", f"File '{path}' has no YAML frontmatter", path)
            continue

        frontmatter = parse_yaml(fm_text)
        if frontmatter is None:
            report.add_error("E1", f"File '{path}' has unparseable YAML frontmatter", path)
            continue

        # E2 — non-empty type field
        type_val = frontmatter.get("type")
        if not type_val or not str(type_val).strip():
            report.add_error("E2", f"File '{path}' has frontmatter but no 'type' field", path)
        else:
            type_str = str(type_val).strip()
            # Schema validation (E4 / W6)
            if schemas is not None:
                if type_str in schemas:
                    schema_errors = validate_against_schema(
                        frontmatter, schemas[type_str], type_str
                    )
                    for err_msg in schema_errors:
                        report.add_error(
                            "E4",
                            f"Schema validation failed for '{path}': {err_msg}",
                            path,
                        )
                else:
                    report.add_warning(
                        "W6",
                        f"No schema found for type '{type_str}' in '{path}'",
                        path,
                    )

        # E5 — unflatten lists in frontmatter
        if _has_nested_lists(frontmatter):
            report.add_error(
                "E5",
                f"File '{path}' has nested list structures in frontmatter",
                path,
            )

        # W7 — block-style (multi-line) lists in frontmatter
        if _has_block_lists(fm_text):
            report.add_warning(
                "W7",
                f"File '{path}' has block-style lists in frontmatter. "
                "Use inline notation (e.g. 'tags: [a, b]') to keep frontmatter compact. "
                "Run 'okf-schema lint --path <bundle>' to auto-fix.",
                path,
            )

        # W1 — missing recommended fields
        for field_name in ("title", "description"):
            if field_name not in frontmatter or not frontmatter[field_name]:
                report.add_warning(
                    "W1",
                    f"Missing recommended field '{field_name}' in '{path}'",
                    path,
                )

        # W3 — missing provenance timestamp (accepts either generated.at or legacy timestamp)
        generated = frontmatter.get("generated")
        has_generated_at = isinstance(generated, dict) and bool(generated.get("at"))
        has_timestamp = bool(frontmatter.get("timestamp"))
        if not has_generated_at and not has_timestamp:
            report.add_warning(
                "W3",
                f"No provenance timestamp in '{path}'. "
                "Add 'generated.at: <ISO-8601-datetime>' to the frontmatter.",
                path,
            )

        # OKF 0.2: validate generated, sources, verified, and lifecycle fields
        _validate_okf2_generated(path, frontmatter, report)
        # For standalone files (no bundle_root), use path.parent as root for resource checks
        _validate_okf2_sources(path, frontmatter, body, path.parent, report)
        _validate_okf2_verified(path, frontmatter, report)
        _validate_okf2_lifecycle(path, frontmatter, report)

    return report
