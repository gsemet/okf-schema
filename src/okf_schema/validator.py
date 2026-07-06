"""OKF bundle validation engine.

Implements all conformance error (E1-E7) and best-practice warning (W1-W7)
rules for validating OKF (Open Knowledge Format) bundles.
"""

from __future__ import annotations

import json
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

    Args:
        fm_text: Raw YAML frontmatter text (without ``---`` delimiters).

    Returns:
        ``True`` when at least one list uses block style.
    """
    y = make_yaml()
    try:
        data = y.load(fm_text)
    except Exception:  # noqa: BLE001
        return False
    if not isinstance(data, dict):
        return False

    for value in data.values():
        if (
            hasattr(value, "fa")
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

    Checks E1, E2, E4, E5, W1, W2, W3, W6, W7.

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

    # W3 — missing timestamp
    if "timestamp" not in frontmatter:
        report.add_warning("W3", f"No 'timestamp (ISO 8601)' field in '{path}'", path)

    # W2 — broken cross-links
    broken = find_broken_links(body, path, bundle_root)
    for target in broken:
        report.add_warning("W2", f"Broken cross-link '{target}' in '{path}'", path)


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

        # W3 — missing timestamp
        if "timestamp" not in frontmatter:
            report.add_warning("W3", f"No 'timestamp (ISO 8601)' field in '{path}'", path)

    return report
