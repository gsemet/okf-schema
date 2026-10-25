"""Validate Open Knowledge Format (OKF) bundles and standalone documents.

Implements conformance error (E1-E9) and best-practice warning (W1-W17)
rules. :func:`validate_bundle` is the main entry point for a bundle;
:func:`validate_markdown_files` validates documents without bundle-level rules.

OKF 0.2 additions (E7-E9, W8-W13, W16):
  E7 – `generated` block present but `at` field missing
  E8 – `sources` entry missing required `resource` field
  E9 – `verified` entry missing required `by` or `at` field
  W8  – Deprecated `timestamp` field; use `generated.at` instead
  W9  – Deprecated body `# Citations` section; use `sources` frontmatter
  W10 – Malformed actor string in `verified[].by`
  W11 – File is stale (`stale_after` date or instant has passed)
  W12 – Footnote `[^id]` with no matching `sources[].id`
  W13 – Broken path in path-form `resource` or `sources[].resource`
  W14 – Invalid authored OKFKB derivation or stale computed `derives_to`
  W16 – `stale_after` cannot be parsed, so staleness is not checked

Schema loading diagnostics (see :func:`load_schema_database_with_diagnostics`):
  I1  – Informational: schema file is empty (type stays without schema)
  W17 – Schema file cannot be parsed or is not a mapping (type stays without schema)

Examples:
    >>> from tempfile import TemporaryDirectory
    >>> from pathlib import Path
    >>> from okf_schema.validator import validate_bundle
    >>> with TemporaryDirectory() as directory:
    ...     report = validate_bundle(Path(directory))
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, cast

import pyjson5
from jsonschema import Draft202012Validator
from ruamel.yaml.error import YAMLError

from okf_schema._internal.models import Finding, Report
from okf_schema._internal.utils import (
    ISO8601_DATE_RE,
    RESERVED_FILES,
    collect_markdown_files,
    find_broken_links,
)
from okf_schema._internal.yaml import extract_frontmatter, make_yaml, parse_yaml
from okf_schema.file_links import _FileLinkContext, check_file_links
from okf_schema.okfkb.derivations import (
    build_derivation_graph,
    content_document_paths,
    supports_derivation_graph,
)

# Matches OKF actor strings: <prefix>:<identifier>  e.g. human:alice, bot:ci
_ACTOR_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*:.+$")
# Matches Markdown footnote references [^id] in body text
_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")
# Matches Markdown footnote definitions [^id]: ...
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.MULTILINE)
# Matches body-level # Citations heading
_CITATIONS_HEADING_RE = re.compile(r"^#{1,6}\s+Citations\s*$", re.MULTILINE | re.IGNORECASE)


def _resolve_ref(
    ref_path: str,
    schema_db: Path,
    y: Any,
) -> dict | None:
    """Load a schema fragment referenced by *ref_path*.

    The *ref_path* is resolved relative to *schema_db*.  Supported
    extensions are ``.json``, ``.json5``, ``.yaml``, and ``.yml``.
    If *ref_path* has no recognised extension, each extension is tried
    in turn (``.json``, ``.json5``, ``.yaml``, ``.yml``) until a file
    is found and parsed successfully.

    Args:
        ref_path:
            Relative path to the referenced schema file.
        schema_db:
            Base directory for relative resolution.
        y:
            Configured ``ruamel.yaml`` instance.

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


def _resolve_refs_in_schema(
    schema: dict,
    schema_db: Path,
    y: Any,
) -> dict:
    """Recursively inline all ``$ref`` references inside *schema*.

    When a ``$ref`` appears alongside other keys, the referenced dict is
    merged with the remaining keys (siblings override the referenced
    content).

    Args:
        schema:
            Schema dictionary potentially containing ``$ref`` keys.
        schema_db:
            Base directory for relative path resolution.
        y:
            Configured ``ruamel.yaml`` instance.

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


def _load_schema_file(path: Path, y: Any) -> tuple[str, dict | None, Finding | None] | None:
    """Parse one schema file.

    Returns:
        ``None`` when *path* is not a schema file; otherwise ``(type, schema,
        diagnostic)`` where *schema* is ``None`` if the file produced no schema.
    """
    name = path.name
    for suffix in (".schema.json", ".schema.json5", ".schema.yaml", ".schema.yml"):
        if name.endswith(suffix):
            type_key = name[: -len(suffix)]
            break
    else:
        return None

    def unparsable(reason: str) -> tuple[str, None, Finding]:
        message = f"schema file '{name}' cannot be parsed: {reason}"
        return type_key, None, Finding("W17", message, path)

    try:
        text = path.read_text(encoding="utf-8-sig")
        if suffix == ".schema.json":
            data = json.loads(text) if text.strip() else None
        elif suffix == ".schema.json5":
            data = pyjson5.loads(text) if text.strip() else None
        else:
            data = y.load(text)
    except pyjson5.Json5DecoderException as exc:
        reason = str(exc.args[0]) if exc.args else str(exc)
        if reason.startswith("No JSON data found"):  # JSON5 holding only comments
            return type_key, None, Finding("I1", f"schema file '{name}' is empty", path)
        return unparsable(" ".join(reason.split()))
    except (json.JSONDecodeError, YAMLError, OSError) as exc:
        return unparsable(" ".join(str(exc).split()))
    if data is None:
        return type_key, None, Finding("I1", f"schema file '{name}' is empty", path)
    if not isinstance(data, dict):
        return unparsable(f"top-level value must be a mapping, got {type(data).__name__}")
    return type_key, dict(data), None


# @implements_req SwRS-OKFSCHEMA-CORE-008
def load_schema_database_with_diagnostics(
    schema_db: Path,
) -> tuple[dict[str, dict], list[Finding]]:
    """Load schema files and report every file that produced no schema.

    Behaves like :func:`load_schema_database` but also returns diagnostics, so
    that a type left without schema is never silent. The contract is the same
    for ``.schema.json``, ``.schema.json5``, ``.schema.yaml`` and
    ``.schema.yml``:

    * An empty file, a whitespace-only file, or a JSON5 or YAML file holding only
      comments yields ``I1`` (informational): ``schema file '<name>' is empty``.
      It never fails validation, not even with ``--strict``.
    * A file that cannot be parsed (JSON, JSON5 or YAML syntax error, or an
      unreadable file) or whose top-level value is not a mapping yields warning
      ``W17``: ``schema file '<name>' cannot be parsed: <parser error>``.

    In both cases the type stays without schema. Each diagnostic carries the
    schema file path. Diagnostics are sorted by file name.

    Args:
        schema_db:
            Directory containing schema files.

    Returns:
        A pair of the type-to-schema mapping and the list of diagnostics, as
        :class:`~okf_schema._internal.models.Finding` records with code
        ``I1`` or ``W17``.

    Examples:
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> from okf_schema.validator import load_schema_database_with_diagnostics
        >>> with TemporaryDirectory() as directory:
        ...     schema_dir = Path(directory)
        ...     _ = (schema_dir / "task.schema.yaml").write_text("# todo")
        ...     schemas, diagnostics = load_schema_database_with_diagnostics(schema_dir)
        ...     schemas, [(d.code, d.message) for d in diagnostics]
        ({}, [('I1', "schema file 'task.schema.yaml' is empty")])
    """
    schemas: dict[str, dict] = {}
    diagnostics: list[Finding] = []
    if not schema_db.is_dir():
        return schemas, diagnostics

    y = make_yaml()
    for path in sorted(schema_db.iterdir()):
        if not path.is_file():
            continue
        loaded = _load_schema_file(path, y)
        if loaded is None:
            continue
        type_key, raw_schema, diagnostic = loaded
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        if raw_schema is not None:
            schemas[type_key] = _resolve_refs_in_schema(raw_schema, schema_db, y)

    return schemas, diagnostics


def load_schema_database(schema_db: Path) -> dict[str, dict]:
    """Load all JSON/YAML schema files from *schema_db* into a type→schema map.

    Files are expected to be named ``<type>.schema.json``,
    ``<type>.schema.json5``, ``<type>.schema.yaml`` or ``<type>.schema.yml``.
    The *type* key is the stem before ``.schema``.

    ``$ref`` references to external files are resolved relative to
    *schema_db* and inlined into the loaded schema.

    Empty, unparsable and non-mapping files are skipped silently. Use
    :func:`load_schema_database_with_diagnostics` to learn why a type has no
    schema.

    Args:
        schema_db:
            Directory containing schema files.

    Returns:
        Mapping from type name to schema dict.

    Examples:
        >>> import json
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> from okf_schema.validator import load_schema_database
        >>> with TemporaryDirectory() as directory:
        ...     schema_dir = Path(directory)
        ...     schema_file = schema_dir / "concept.schema.json"
        ...     _ = schema_file.write_text(json.dumps({"type": "object"}))
        ...     sorted(load_schema_database(schema_dir))
        ['concept']
    """
    return load_schema_database_with_diagnostics(schema_db)[0]


def validate_against_schema(
    frontmatter: dict,
    schema: dict,
    type_name: str,
) -> list[str]:
    """Validate *frontmatter* against *schema*.

    Args:
        frontmatter:
            Parsed YAML frontmatter dictionary.
        schema:
            JSON Schema dictionary.
        type_name:
            Type name for error messages.

    Returns:
        List of human-readable validation error strings.

    Examples:
        >>> schema = {"type": "object", "required": ["type"]}
        >>> validate_against_schema({"type": "concept"}, schema, "concept")
        []
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


_FRACTION_RE = re.compile(r"\.(\d+)")


def _parse_stale_after(value: object) -> date | datetime | None:
    """Parse a ``stale_after`` value into a comparable date or aware instant.

    Accepts a bare ISO date (kept for backward compatibility), an ISO 8601
    datetime string with an explicit UTC offset (``Z`` or ``±HH:MM``), and
    ``date``/``datetime`` objects. A datetime without an offset names a
    different instant in every timezone, so it is rejected rather than guessed.

    Args:
        value:
            Raw ``stale_after`` frontmatter value.

    Returns:
        A :class:`~datetime.date` for a bare date, a timezone-aware
        :class:`~datetime.datetime` for an instant, or ``None`` when the value
        cannot be interpreted.
    """
    if isinstance(value, datetime):
        return value if value.tzinfo is not None and value.utcoffset() is not None else None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if ISO8601_DATE_RE.match(text):
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    # Python 3.10 ``fromisoformat`` only accepts 3 or 6 fractional digits.
    text = _FRACTION_RE.sub(lambda m: "." + m.group(1)[:6].ljust(6, "0"), text, count=1)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _is_stale(frontmatter: dict) -> bool:
    """Return ``True`` when the ``stale_after`` date or instant has been reached.

    A bare date is stale from the start of that day (local calendar day, as
    before). A datetime with a UTC offset is compared as an instant against the
    current UTC time. Absent or unparseable values are never stale; use
    :func:`_has_unparseable_stale_after` to detect the latter.
    """
    stale_after = frontmatter.get("stale_after")
    parsed = _parse_stale_after(stale_after)
    if parsed is None:
        return False
    if isinstance(parsed, datetime):
        return datetime.now(timezone.utc) >= parsed
    return date.today() >= parsed


def _has_unparseable_stale_after(frontmatter: dict) -> bool:
    """Return ``True`` when ``stale_after`` is set but cannot be interpreted."""
    stale_after = frontmatter.get("stale_after")
    if stale_after is None or stale_after == "":
        return False
    return _parse_stale_after(stale_after) is None


def _validate_okf2_generated(
    path: Path,
    frontmatter: dict,
    report: Report,
) -> None:
    """Validate the OKF 0.2 `generated` block (E7, W8).

    E7 — `generated` block present but `at` field missing.
    W8 — Deprecated `timestamp` field present instead of `generated.at`.
    """
    generated = frontmatter.get("generated")
    timestamp = frontmatter.get("timestamp")

    if generated is not None:
        if isinstance(generated, dict) and not generated.get("at"):
            report.add_error(
                "E7",
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
            "Fix: okf-schema lint --path <bundle>",
            path,
        )


def _validate_okf2_sources(
    path: Path,
    frontmatter: dict,
    body: str,
    bundle_root: Path,
    report: Report,
) -> None:
    """Validate the OKF 0.2 `sources` block and footnote integrity (E8, W9, W12, W13)."""
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

    # E8 — each entry must have `resource`
    valid_ids: set[str] = set()
    for i, entry in enumerate(sources_list):
        if not isinstance(entry, dict):
            continue
        if not entry.get("resource"):
            report.add_error(
                "E8",
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
    """Validate the OKF 0.2 `verified` block (E9, W10)."""
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
                "E9",
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
                "E9",
                f"File '{path}': verified entry [{i}] is missing required 'at' field. "
                "Fix: add 'at: <ISO-8601-date>' to the verified entry.",
                path,
            )


def _validate_okf2_lifecycle(
    path: Path,
    frontmatter: dict,
    report: Report,
) -> None:
    """Validate OKF 0.2 lifecycle fields `status` and `stale_after` (W11, W16).

    W11 — ``stale_after`` (bare date or ISO 8601 datetime with UTC offset) has passed.
    W16 — ``stale_after`` cannot be parsed, so the staleness check is disabled.
    """
    stale_after = frontmatter.get("stale_after")
    if _has_unparseable_stale_after(frontmatter):
        report.add_warning(
            "W16",
            f"File '{path}' has an unparseable stale_after value '{stale_after}'; "
            "staleness is not checked. "
            "Fix: use an ISO 8601 datetime with a UTC offset such as "
            "'2026-12-31T00:00:00Z' (a bare date 'YYYY-MM-DD' is also accepted).",
            path,
        )
    elif _is_stale(frontmatter):
        report.add_warning(
            "W11",
            f"File '{path}' is stale: stale_after '{stale_after}' has passed. "
            "Fix: update content and set a new 'stale_after' value, or remove the field.",
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
        fm_text:
            Raw YAML frontmatter text without ``---`` delimiters.

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


# @implements_req SwRS-OKFSCHEMA-CORE-006
def validate_concept(
    path: Path,
    report: Report,
    bundle_root: Path,
    schemas: dict[str, dict] | None,
    *,
    check_links: bool = False,
    project_root: Path | None = None,
    _link_context: _FileLinkContext | None = None,
) -> None:
    r"""Validate a single concept (non-reserved) ``.md`` file.

    Checks E1, E2, E4, E5, E7-E9, W1, W2, W3, W6-W13, W16.

    Args:
        path:
            Path to the concept markdown file.
        report:
            Report to append findings to.
        bundle_root:
            Root directory of the OKF bundle.
        schemas:
            Optional schema database mapping type to schema.
        check_links:
            Enable opt-in ``x-okf-link`` target checking.
        project_root:
            Explicit project root for project-relative links.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> from pathlib import Path
        >>> from okf_schema._internal.models import Finding, Report
        >>> with TemporaryDirectory() as directory:
        ...     path = Path(directory) / "concept.md"
        ...     _ = path.write_text("---\ntype: concept\n---\n")
        ...     report = Report()
        ...     validate_concept(path, report, Path(directory), schemas=None)
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
                if check_links:
                    for diagnostic in check_file_links(
                        frontmatter,
                        schemas[type_str],
                        path,
                        bundle_root=bundle_root,
                        project_root=project_root,
                        _context=_link_context,
                    ):
                        add_finding = (
                            report.add_error
                            if diagnostic.severity == "error"
                            else report.add_warning
                        )
                        add_finding(diagnostic.code, diagnostic.message, path)
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
    r"""Validate an ``index.md`` file.

    Checks E3 (non-root index.md must NOT have frontmatter).

    Args:
        path:
            Path to the ``index.md`` file.
        report:
            Report to append findings to.
        bundle_root:
            Root directory of the OKF bundle.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> from pathlib import Path
        >>> from okf_schema._internal.models import Finding, Report
        >>> with TemporaryDirectory() as directory:
        ...     path = Path(directory) / "index.md"
        ...     _ = path.write_text("# Index\n")
        ...     report = Report()
        ...     validate_index(path, report, Path(directory))
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
        path:
            Path to the ``log.md`` file.
        report:
            Report to append findings to.
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
        path:
            Path to the reserved file.
        report:
            Report to append findings to.
        bundle_root:
            Root directory of the OKF bundle.
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


# @implements_req SwRS-OKFSCHEMA-CORE-001
def validate_bundle(
    bundle: Path,
    schemas: dict[str, dict] | None = None,
    *,
    check_links: bool = False,
    project_root: Path | None = None,
) -> Report:
    """Run the full validation suite over *bundle*.

    Orchestrates all validators and emits W4 (missing index.md) for
    directories that contain markdown files but no ``index.md``. Concept
    documents may appear at the bundle root or in subdirectories, as allowed
    by OKF 0.2. Non-markdown files are ignored by document validation and may
    be kept in the bundle as attachments or other referenced resources.

    Args:
        bundle:
            Path to the OKF bundle directory.
        schemas:
            Optional schema database mapping type to schema.
        check_links:
            Enable opt-in ``x-okf-link`` target checking.
        project_root:
            Explicit project root for project-relative links. If unavailable,
            the containing Git root of each document is used.

    Returns:
        A :class:`Report` containing all errors and warnings.
    """
    report = Report()

    if not bundle.is_dir():
        report.add_error("E0", f"Bundle path '{bundle}' is not a directory")
        return report

    # Track directories that contain markdown files
    dirs_with_md: set[Path] = set()
    link_context = _FileLinkContext()

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
            validate_concept(
                path,
                report,
                bundle,
                schemas,
                check_links=check_links,
                project_root=project_root,
                _link_context=link_context,
            )

    # W14 — OKFKB computed reverse derivations are missing, stale, or based
    # on invalid authored canonical paths. Validation is deliberately read-only.
    # @implements_req SwRS-OKFSCHEMA-OKFKB-006
    if supports_derivation_graph(bundle):
        graph = build_derivation_graph(bundle)
        documents = content_document_paths(bundle)
        for invalid in graph.invalid:
            path = documents[invalid.document_id]
            report.add_warning(
                "W14",
                f"Authored derived_from value '{invalid.source_id}' in '{path}' is not "
                "an existing canonical bundle-relative extensionless document path",
                path,
            )
        for identifier, path in documents.items():
            text = path.read_text(encoding="utf-8")
            fm_text, _body = extract_frontmatter(text)
            frontmatter = parse_yaml(fm_text) if fm_text is not None else None
            actual = frontmatter.get("derives_to") if isinstance(frontmatter, dict) else None
            expected = graph.derives_to[identifier]
            if actual != expected:
                report.add_warning(
                    "W14",
                    f"Computed derives_to in '{path}' is stale or missing; expected "
                    f"{expected!r}. Run 'okfkb update <bundle>'.",
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
    *,
    check_links: bool = False,
    bundle_root: Path | None = None,
    project_root: Path | None = None,
) -> Report:
    """Validate standalone markdown files (not part of an OKF bundle).

    Validates each file using E1, E2, E4, E5, E7-E9 and W1, W3,
    W6-W13 and W16 rules.
    Bundle-specific constraints (W4, E6, W5) are not applied. File-link
    annotations are checked only when explicitly enabled and roots are supplied
    or can be derived from the document's containing Git repository.

    Args:
        file_paths:
            List of markdown file paths to validate.
        schemas:
            Optional schema database mapping type to schema.
        check_links:
            Enable opt-in ``x-okf-link`` target checking.
        bundle_root:
            Optional bundle root for bundle-relative and filename-stem links.
        project_root:
            Explicit project root for project-relative links. If unavailable,
            the containing Git root of each document is used.

    Returns:
        A :class:`Report` containing all errors and warnings.
    """
    report = Report()
    link_context = _FileLinkContext()

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
                    if check_links:
                        for diagnostic in check_file_links(
                            frontmatter,
                            schemas[type_str],
                            path,
                            bundle_root=bundle_root,
                            project_root=project_root,
                            _context=link_context,
                        ):
                            add_finding = (
                                report.add_error
                                if diagnostic.severity == "error"
                                else report.add_warning
                            )
                            add_finding(diagnostic.code, diagnostic.message, path)
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
