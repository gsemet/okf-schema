"""Domain operations for standalone Open Knowledge Format requirements.

The module initializes requirement bundles, creates EARS (Easy Approach to
Requirements Syntax) scaffolds, validates requirement graphs and schemas,
scans implementation and test markers, and generates traceability reports.
Callers normally start with :func:`init_requirements`, then use
:func:`create_requirement`, :func:`validate_requirements`, and :func:`report`.

Examples:
    >>> from pathlib import Path
    >>> from tempfile import TemporaryDirectory
    >>> with TemporaryDirectory() as directory:
    ...     bundle = init_requirements(Path(directory) / "requirements")
    ...     bundle.is_dir()
    True
"""

from __future__ import annotations

import datetime
import difflib
import json
import os
import re
import tempfile
import uuid
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml, parse_yaml
from okf_schema.validator import load_schema_database

DEFAULT_CONFIG = """version: 1
levels:
  StRS: {folder: strs, prefix: StRS, derives_from: []}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS]}
id_policy: scope-prefix-sequence
lifecycle:
  values: [draft, proposed, approved, deprecated, superseded]
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, implemented_in_files, tested_in_files]
scopes:
  default: {source_dirs: [src], test_dirs: [tests]}
"""

GENERATED_BASE_SCHEMA = """$schema: https://json-schema.org/draft/2020-12/schema
$id: base.schema.yaml
title: okfreq requirement base profile
description: Shared frontmatter contract for every okfreq requirement.
type: object
properties:
    type:
    type: string
    description: Configured level and schema discriminator.
    id:
        type: string
        pattern: '^[A-Za-z][A-Za-z0-9_-]*$'
        description: Stable requirement identifier.
    uuid:
        type: string
        format: uuid
        description: Stable UUID retained when the document moves or is renamed.
    title:
        type: string
        minLength: 1
        description: Concise human-readable subject.
    description:
        type: string
        minLength: 1
        description: Normative requirement statement supplied by the author.
    project:
        type: string
        minLength: 1
        description: Project or product that owns the requirement.
    scope:
        type: string
        minLength: 1
        description: Domain used for organization and evidence scanning.
    lifecycle:
        type: string
        enum: [draft, proposed, approved, deprecated, superseded]
        description: Explicit human-controlled lifecycle state.
    origin:
        type: string
        minLength: 1
        description: Producer or source, such as native or imported.
    tier:
        type: string
        description: Configured level label; constrained by the tier schema.
    derives_from:
        type: array
        items:
            type: string
        description: Authored IDs of higher-level requirements.
    derived_by:
        type: array
        items:
            type: string
        description: Generated reverse links computed from derives_from.
    depends_on:
        type: array
        items:
            type: string
        description: Authored prerequisite or peer requirement IDs.
required: [type, id, uuid, title, description, project, scope, lifecycle, origin, tier]
additionalProperties: true
examples:
    - type: StRS
        id: StRS-example-001
        uuid: 00000000-0000-4000-8000-000000000001
        title: Example requirement
        description: The system SHALL support the stakeholder outcome.
        project: example
        scope: default
        lifecycle: draft
        origin: native
        tier: StRS
"""

GENERATED_STRS_SCHEMA = """$schema: https://json-schema.org/draft/2020-12/schema
$id: strs.schema.yaml
title: okfreq stakeholder requirement profile
description: StRS records a stakeholder-observable outcome and its need.
allOf:
  - $ref: base.schema.yaml
  - type: object
    properties:
      type: {const: StRS}
      tier: {const: StRS}
      user_need: {type: string, minLength: 1}
    required: [type, tier, user_need]
additionalProperties: true
examples:
    - type: StRS
        id: StRS-example-001
        uuid: 00000000-0000-4000-8000-000000000001
        title: Example requirement
        description: The system SHALL support the stakeholder outcome.
        project: example
        scope: default
        lifecycle: draft
        origin: native
        tier: StRS
        user_need: Users need the stakeholder outcome.
"""

GENERATED_SWRS_SCHEMA = """$schema: https://json-schema.org/draft/2020-12/schema
$id: swrs.schema.yaml
title: okfreq software requirement profile
description: SwRS defines observable software behavior derived from an StRS.
allOf:
  - $ref: base.schema.yaml
  - type: object
    properties:
      type: {const: SwRS}
      tier: {const: SwRS}
      annotation_exemption: {type: boolean}
    exemption_reason: {type: [string, 'null'], minLength: 1}
      implemented_in_files: {type: array, items: {type: string}}
      tested_in_files: {type: array, items: {type: string}}
      verification_method: {type: string}
      verification_criteria: {type: string}
    required: [type, tier, annotation_exemption]
        allOf:
            - if:
                    properties:
                        annotation_exemption: {const: true}
                then:
                    required: [exemption_reason]
                    properties:
                        exemption_reason: {type: string, minLength: 1}
additionalProperties: true
examples:
    - type: SwRS
        id: SwRS-example-001
        uuid: 00000000-0000-4000-8000-000000000002
        title: Example software behavior
        description: The service SHALL return the requested result.
        project: example
        scope: default
        lifecycle: draft
        origin: native
        tier: SwRS
        derives_from: [StRS-example-001]
        annotation_exemption: false
        exemption_reason: null
        implemented_in_files: []
        tested_in_files: []
"""

LIFECYCLES = ("draft", "proposed", "approved", "deprecated", "superseded")
GUIDELINE_NAME = "requirements.guidelines.md"
DEFAULT_ID_PATTERN = r"[A-Za-z][A-Za-z0-9_-]*"
SUPPORTED_GENERATED_FIELDS = frozenset({"derived_by", "implemented_in_files", "tested_in_files"})

_EARS_PLACEHOLDER = "<"
_USER_NEED_PLACEHOLDER = "<stakeholder need in the stakeholder's language>"

_STRS_BODY = """## EARS Expression

### Normative behavior

{description}

### Preserved stakeholder intent

## User Need

{user_need}

### Rationale and constraints

<!-- Record stakeholder constraints, exclusions, or decisions that shape the
     outcome. Remove this section when there are none. -->

- <known constraint, exclusion, or rationale>
"""

_SWRS_BODY = """## EARS Expression

### Normative behavior

{description}

### Scenario: <nominal behavior>

- GIVEN <precondition and relevant inputs>
- WHEN <trigger or action>
- THEN <single observable, verifiable outcome>

### Scenario: <boundary or failure behavior>

- GIVEN <boundary precondition or failure>
- WHEN <trigger or action>
- THEN <observable recovery, rejection, or boundary outcome>

### Verification notes

<!-- Name the verification method, evidence, and boundaries. Do not claim
     coverage until implementation and test markers exist. -->

- Method: <test, inspection, analysis, or demonstration>
- Criteria: <objective pass condition>
"""


def ears_body(
    level: str,
    description: str,
    *,
    user_need: str | None = None,
) -> str:
    """Return the EARS scaffold for a configured level.

    The scaffold is deliberately full of bracketed placeholders so an agent or
    author can see exactly which parts must be filled in.

    Args:
        level:
            The configured level name, such as ``StRS`` or ``SwRS``.
        description:
            Normative EARS behavior supplied by the author.
        user_need:
            Stakeholder need for an upper-level requirement.

    Returns:
        A Markdown body template for the level.

    Examples:
        >>> body = ears_body("SwRS", "The tool SHALL validate the bundle.")
        >>> "### Scenario:" in body
        True
    """
    if level.lower().startswith("sw"):
        return _SWRS_BODY.format(description=description)
    return _STRS_BODY.format(
        description=description,
        user_need=user_need or _USER_NEED_PLACEHOLDER,
    )


def body_is_unfilled(text: str) -> bool:
    """Report whether a requirement body still contains EARS placeholders.

    Args:
        text:
            The full Markdown document text.

    Returns:
        ``True`` when the body is missing, is only a stub, or still contains
        bracketed placeholders from the scaffold.

    Examples:
        >>> body_is_unfilled("---\\nid: example\\n---\\n\\nThe tool SHALL work.\\n")
        False
    """
    _, body = extract_frontmatter(text)
    stripped = body.strip()
    if not stripped or "SHALL" not in stripped:
        return True
    return bool(re.search(r"<[a-z][^>\n]{3,}>", stripped, flags=re.IGNORECASE))


class RequirementError(ValueError):
    """Raised when a requirements operation cannot be completed safely."""


def bundle_path(path: Path) -> Path:
    """Resolve the requirements bundle root that owns ``config.yml``.

    The bundle root holds ``config.yml``, ``guidelines/``, and generated
    reports. Requirement documents and their schema live under
    :func:`tiers_path`.

    Args:
        path:
            A project directory or an already-initialized bundle directory.

    Returns:
        The resolved bundle root, which may not exist yet.

    Examples:
        >>> bundle_path(Path("project"))
        PosixPath('project/.agents/requirements')
    """
    if (path / "config.yml").is_file():
        return path
    if (path / "tiers" / "config.yml").is_file():  # legacy config placement
        return path / "tiers"
    for candidate in (
        path / "requirements",
        path / ".agents" / "requirements",
        path / ".github" / "requirements",
    ):
        if (candidate / "config.yml").is_file():
            return candidate
    if path.name in {"requirements", "tiers"}:
        return path
    return path / ".agents" / "requirements"


def tiers_path(root: Path) -> Path:
    """Resolve the directory holding requirement documents and ``_schema/``.

    Args:
        root:
            The bundle root returned by :func:`bundle_path`.

    Returns:
        ``root / "tiers"`` for split bundles, or ``root`` for legacy flat
        bundles that keep documents beside ``config.yml``.
    """
    tiers = root / "tiers"
    if tiers.is_dir():
        return tiers
    return root


def project_path(root: Path) -> Path:
    """Resolve the project root that scope directories are relative to.

    Args:
        root:
            The bundle root returned by :func:`bundle_path`.

    Returns:
        The directory containing the project sources and tests.
    """
    if root.name == "tiers":  # legacy bundle nested under requirements/
        root = root.parent
    if root.parent.name in {".agents", ".github"}:
        return root.parent.parent
    return root.parent


def _atomic_write(path: Path, text: str) -> None:  # pragma: no cover - OS failure cleanup
    """Write text atomically in the destination directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def init_requirements(path: Path, force: bool = False) -> Path:
    """Create a complete standalone requirements bundle.

    The bundle is split: ``config.yml``, ``guidelines/``, and generated reports
    live at the bundle root, while ``_schema/`` and the configured tier folders
    live under ``tiers/``.

    Args:
        path:
            A project directory or an explicit bundle directory.
        force:
            When ``True``, merge into a non-empty directory without
            replacing existing files.

    Returns:
        The created bundle root.

    Raises:
        RequirementError:
            If the target exists, is not empty, and ``force`` is
            not set.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     (root / "config.yml").is_file()
        True
    """
    root = bundle_path(path)
    if root.exists() and any(root.iterdir()) and not force:
        raise RequirementError(f"'{root}' is not empty; use --force to merge explicitly")
    tiers = root / "tiers"
    for folder in (root / "guidelines", tiers / "_schema", tiers / "strs", tiers / "swrs"):
        folder.mkdir(parents=True, exist_ok=True)
    index = "---\nokf_version: '0.2'\nrequirements_layer: okfreq\n---\n\n# Requirements\n"

    def schema_text(level: str) -> str:
        """Return a valid generated schema for the requested level."""
        base = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "base.schema.yaml",
            "title": "okfreq requirement base profile",
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "id": {"type": "string"},
                "uuid": {"type": "string", "format": "uuid"},
                "title": {"type": "string", "minLength": 1},
                "description": {"type": "string", "minLength": 1},
                "project": {"type": "string", "minLength": 1},
                "scope": {"type": "string", "minLength": 1},
                "lifecycle": {"type": "string"},
                "origin": {"type": "string", "minLength": 1},
                "tier": {"type": "string"},
                "derives_from": {"type": "array", "items": {"type": "string"}},
                "derived_by": {"type": "array", "items": {"type": "string"}},
                "depends_on": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "type",
                "id",
                "uuid",
                "title",
                "description",
                "project",
                "scope",
                "lifecycle",
                "origin",
                "tier",
            ],
            "additionalProperties": True,
        }
        if level == "base":
            return dump_yaml(base) + "\n"
        tier = "StRS" if level == "strs" else "SwRS"
        properties: dict[str, Any] = {"type": {"const": tier}, "tier": {"const": tier}}
        required = ["type", "tier"]
        if tier == "StRS":
            properties["user_need"] = {"type": "string", "minLength": 1}
            required.append("user_need")
        else:
            properties["annotation_exemption"] = {"type": "boolean"}
            required.append("annotation_exemption")
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{level}.schema.yaml",
            "title": f"okfreq {level} requirement profile",
            "allOf": [
                {"$ref": "base.schema.yaml"},
                {"type": "object", "properties": properties, "required": required},
            ],
        }
        return dump_yaml(schema) + "\n"

    generated_files = {
        root / "config.yml": DEFAULT_CONFIG,
        tiers / "_schema" / "base.schema.yaml": schema_text("base"),
        tiers / "_schema" / "strs.schema.yaml": schema_text("strs"),
        tiers / "_schema" / "swrs.schema.yaml": schema_text("swrs"),
        tiers / "index.md": index,
        tiers / "log.md": f"# Update Log\n\n## {datetime.date.today().isoformat()}\n",
    }
    for destination, content in generated_files.items():
        if not destination.exists():
            _atomic_write(destination, content)
    _install_guideline(root)
    return root


def _install_guideline(root: Path) -> Path | None:
    """Copy the packaged requirements guideline into the bundle.

    Args:
        root:
            The bundle root.

    Returns:
        The installed guideline path, or ``None`` when it already exists.
    """
    destination = root / "guidelines" / GUIDELINE_NAME
    if destination.exists():
        return None
    source = files("okf_schema.data.requirements").joinpath("guidelines").joinpath(GUIDELINE_NAME)
    with as_file(source) as resolved:
        _atomic_write(destination, Path(resolved).read_text(encoding="utf-8"))
    return destination


def load_config(root: Path) -> dict[str, Any]:
    """Load and normalize the requirements configuration.

    Args:
        root:
            Bundle root containing ``config.yml``.

    Returns:
        The parsed configuration with defaults for optional settings.

    Raises:
        RequirementError:
            If ``config.yml`` is empty or cannot be parsed as a mapping.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     load_config(root)["id_policy"]
        'scope-prefix-sequence'
    """
    data = parse_yaml((root / "config.yml").read_text(encoding="utf-8"))
    if data is None:
        raise RequirementError(f"invalid configuration: {root / 'config.yml'}")
    data.setdefault("levels", {})
    data.setdefault("scopes", {"default": {"source_dirs": ["src"], "test_dirs": ["tests"]}})
    data.setdefault("markers", {"implements": "@implements_req", "tests": "@tests_req"})
    data["markers"].setdefault("id_pattern", DEFAULT_ID_PATTERN)
    data.setdefault("lifecycle", {}).setdefault("values", list(LIFECYCLES))
    data.setdefault("id_policy", "scope-prefix-sequence")
    data.setdefault("generated_fields", sorted(SUPPORTED_GENERATED_FIELDS))
    return data


def _id_pattern(config: dict[str, Any]) -> re.Pattern[str]:
    """Compile the configured requirement-ID pattern."""
    value = str(config.get("markers", {}).get("id_pattern", DEFAULT_ID_PATTERN))
    try:
        return re.compile(value)
    except re.error as exc:
        raise RequirementError(f"invalid markers.id_pattern: {exc}") from exc


def _leaf_levels(config: dict[str, Any]) -> set[str]:
    """Return configured levels that are not parents of another level."""
    levels = config.get("levels", {})
    if not isinstance(levels, dict):
        return set()
    parent_levels = {
        str(parent)
        for value in levels.values()
        if isinstance(value, dict)
        for parent in value.get("derives_from", [])
    }
    return {str(level) for level in levels} - parent_levels


# @implements_req SwRS-OKFSCHEMA-OKFREQ-006
def merge_config(root: Path, source: Path) -> list[str]:
    """Merge a configuration while preserving unknown keys.

    Existing values take precedence over conflicting imported values.

    Args:
        root:
            Bundle root containing the destination ``config.yml``.
        source:
            YAML configuration file to import.

    Returns:
        Dotted paths of settings whose imported values conflicted with
        existing values.

    Raises:
        RequirementError:
            If the imported configuration cannot be parsed.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     location = Path(directory)
        ...     root = init_requirements(location / "requirements")
        ...     source = location / "import.yml"
        ...     _ = source.write_text("custom: true\\n", encoding="utf-8")
        ...     merge_config(root, source)
        []
    """
    current = load_config(root)
    imported = parse_yaml(source.read_text(encoding="utf-8"))
    if imported is None:
        raise RequirementError(f"invalid configuration: {source}")
    conflicts: list[str] = []

    def merge(
        destination: dict[str, Any],
        incoming: dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Merge nested mappings and collect conflicting dotted paths.

        Args:
            destination:
                Mapping updated with non-conflicting values.
            incoming:
                Mapping whose values are imported.
            prefix:
                Dotted parent path used for conflict diagnostics.
        """
        for key, value in incoming.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            if (
                key not in destination
            ):  # pragma: no branch - both merge outcomes are covered by callers
                destination[key] = value
            elif isinstance(destination[key], dict) and isinstance(value, dict):
                merge(destination[key], value, name)
            elif destination[key] != value:
                conflicts.append(name)

    merge(current, imported)
    _atomic_write(root / "config.yml", dump_yaml(current))
    return conflicts


def load_requirements(root: Path) -> dict[str, tuple[Path, dict[str, Any], str]]:
    """Load requirement Markdown documents keyed by stable ID.

    Args:
        root:
            The bundle root returned by :func:`bundle_path`.

    Returns:
        A mapping of requirement ID to its path, frontmatter, and raw text.

    Raises:
        RequirementError:
            If two documents declare the same ID.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     load_requirements(root)
        {}
    """
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for file in sorted(tiers_path(root).glob("**/*.md")):
        if file.name in {"index.md", "log.md"} or "_schema" in file.parts:
            continue
        if "guidelines" in file.parts:
            continue
        text = file.read_text(encoding="utf-8")
        frontmatter, _ = extract_frontmatter(text)
        data = parse_yaml(frontmatter) if frontmatter is not None else None
        if data and data.get("id"):
            identifier = str(data["id"])
            if identifier in result:
                raise RequirementError(f"duplicate requirement ID: {identifier}")
            result[identifier] = (file, data, text)
    return result


def create_requirement(
    root: Path,
    level: str,
    title: str,
    description: str,
    *,
    project: str,
    scope: str,
    origin: str,
    derives_from: list[str] | None = None,
    user_need: str | None = None,
) -> Path:
    """Create a native requirement using configured level and ID rules.

    The document body is an EARS scaffold for the level, so the author or agent
    can see which parts still need to be written.

    Args:
        root:
            The bundle root.
        level:
            A configured level name, such as ``StRS`` or ``SwRS``.
        title:
            Concise statement of the requirement's subject.
        description:
            The requirement statement recorded in frontmatter.
        project:
            Owning project code.
        scope:
            Scope used for allocation and scan mapping.
        origin:
            ``native`` for locally authored requirements.
        derives_from:
            Parent requirement IDs, required for derived levels.
        user_need:
            Optional stakeholder need, recorded for upper levels. When
            omitted, the StRS scaffold retains an explicit placeholder instead
            of inventing or duplicating stakeholder intent.

    Returns:
        The created requirement path.

    Raises:
        RequirementError:
            If the level is unconfigured, a parent is unknown or
            of the wrong level, a required parent is missing, or the allocated
            ID would collide.

    Examples:
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     created = create_requirement(
        ...         root,
        ...         "StRS",
        ...         "Readable reports",
        ...         "The tool SHALL produce readable reports.",
        ...         project="example",
        ...         scope="default",
        ...         origin="native",
        ...         user_need="Users need to review requirement coverage.",
        ...     )
        ...     created.name
        'StRS-default-001.md'
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-002
    config = load_config(root)
    if config.get("id_policy") != "scope-prefix-sequence":
        raise RequirementError(f"unsupported id_policy: {config.get('id_policy')}")
    level_config = config.get("levels", {}).get(level)
    if not isinstance(level_config, dict):
        raise RequirementError(f"level is not configured: {level}")
    configured_scopes = config.get("scopes", {})
    scope_name = scope
    scope_config: dict[str, Any] = {}
    if isinstance(configured_scopes, dict):
        for configured_name, configured_value in configured_scopes.items():
            if str(configured_name).casefold() != scope.casefold():
                continue
            scope_name = str(configured_name)
            if isinstance(configured_value, dict):
                scope_config = configured_value
            break
    parent = derives_from or []
    existing = load_requirements(root)
    configured_parents = level_config.get("derives_from", [])
    if configured_parents and not parent:
        raise RequirementError(f"native {level} requires at least one derives_from ID")
    for parent_id in parent:
        if parent_id not in existing:
            raise RequirementError(f"unknown derives_from target: {parent_id}")
        parent_type = existing[parent_id][1].get("type")
        if configured_parents and parent_type not in configured_parents:
            raise RequirementError(f"{level} cannot derive from {parent_type}")
    prefix = str(level_config.get("prefix", level))
    scope_token = str(scope_config.get("id_token", scope_name))
    number = 1
    while f"{prefix}-{scope_token}-{number:03d}" in existing:
        number += 1
    identifier = f"{prefix}-{scope_token}-{number:03d}"
    data: dict[str, Any] = {
        "type": level,
        "id": identifier,
        "uuid": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "project": project,
        "scope": scope_name,
        "lifecycle": "draft",
        "origin": origin,
        "tier": level,
        "derives_from": parent,
    }
    if configured_parents:
        if user_need is not None:
            raise RequirementError(f"{level} does not accept user_need")
        # Derived levels carry annotation coverage, so record exemption intent.
        data["annotation_exemption"] = False
        data["exemption_reason"] = None
    else:
        data["user_need"] = user_need or _USER_NEED_PLACEHOLDER
    folder = tiers_path(root) / str(level_config.get("folder", level.lower()))
    if scope_config.get("folder"):
        folder /= str(scope_config["folder"])
    target = folder / f"{identifier}.md"
    if target.exists() or identifier in existing:
        raise RequirementError(f"requirement ID collision: {identifier}")
    body = ears_body(level, description, user_need=user_need)
    _atomic_write(target, f"---\n{dump_yaml(data)}---\n\n{body}")
    return target


def _render_frontmatter(text: str, updates: dict[str, Any]) -> str:
    """Update selected generated fields while preserving the body."""
    frontmatter, body = extract_frontmatter(text)
    if frontmatter is None:
        raise RequirementError("requirement has no frontmatter")
    data = make_yaml().load(frontmatter)
    if not isinstance(data, dict):
        raise RequirementError("requirement frontmatter is not a mapping")
    for key, value in updates.items():
        data[key] = value
    return f"---\n{dump_yaml(data)}---\n{body}"


def marker_scan(root: Path) -> dict[str, Any]:
    """Scan configured source and test directories for requirement markers.

    Args:
        root:
            Bundle root whose scope mappings determine which files are scanned.

    Returns:
        Marker locations and diagnostics grouped by category.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     sorted(marker_scan(root))
        ['duplicates', 'implemented', 'missing_ids', 'non_leaf', 'tested', 'warnings']
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-003
    config = load_config(root)
    project = project_path(root)
    markers = config["markers"]
    implements = str(markers.get("implements", "@implements_req"))
    tests = str(markers.get("tests", "@tests_req"))
    configured_id = _id_pattern(config)
    embedded_id_pattern = configured_id.pattern.removeprefix("^").removesuffix("$")
    pattern = re.compile(
        rf"(?m)^\s*(?:(?:#|//|/\*|\*|<!--)\s*)?"
        rf"(?P<marker>{re.escape(implements)}|{re.escape(tests)})\s+"
        rf"(?P<identifier>{embedded_id_pattern})"
    )
    result: dict[str, Any] = {
        "implemented": {},
        "tested": {},
        "duplicates": [],
        "non_leaf": [],
        "missing_ids": [],
        "warnings": [],
    }
    requirements = load_requirements(root)
    leaf_levels = _leaf_levels(config)
    seen_markers: set[tuple[str, str, str]] = set()
    for scope, mapping in config.get("scopes", {}).items():
        if not isinstance(mapping, dict):  # pragma: no branch - malformed scope is defensive input
            continue
        for _kind, directories in (
            ("implemented", mapping.get("source_dirs", [])),
            ("tested", mapping.get("test_dirs", [])),
        ):
            if not isinstance(
                directories, list
            ):  # pragma: no branch - malformed scope is defensive input
                continue
            for directory in directories:
                location = project / str(directory)
                if not location.exists():
                    result["warnings"].append(f"scope {scope}: missing directory {directory}")
                    continue
                candidate_files = [location] if location.is_file() else location.rglob("*")
                for file in candidate_files:
                    if not file.is_file() or "__pycache__" in file.parts:
                        continue
                    text = file.read_text(encoding="utf-8", errors="ignore")
                    for match in pattern.finditer(text):
                        marker = match.group("marker")
                        identifier = match.group("identifier")
                        if _kind == "implemented" and marker != implements:
                            continue
                        if _kind == "tested" and marker != tests:
                            continue
                        target = "implemented" if marker == implements else "tested"
                        # Requirement reports use portable project-relative paths
                        # regardless of the host platform.
                        relative = file.relative_to(project).as_posix()
                        occurrence = (target, identifier, relative)
                        if occurrence in seen_markers:
                            result["duplicates"].append(identifier)
                            continue
                        seen_markers.add(occurrence)
                        if identifier not in requirements:
                            result["missing_ids"].append(identifier)
                            continue
                        if requirements[identifier][1].get("type") not in leaf_levels:
                            result["non_leaf"].append(identifier)
                            continue
                        locations = result[target].setdefault(identifier, [])
                        locations.append(relative)
    for key in ("duplicates", "non_leaf", "missing_ids"):
        result[key] = sorted(set(result[key]))
    return result


def graph(root: Path) -> dict[str, Any]:
    """Return authored and computed reverse derivation edges.

    Args:
        root:
            Bundle root containing the requirement documents.

    Returns:
        Authored parent edges, computed child edges, and graph errors.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     graph(root)["errors"]
        []
    """
    requirements = load_requirements(root)
    reverse: dict[str, list[str]] = {identifier: [] for identifier in requirements}
    errors: list[str] = []
    for identifier, (file, data, _) in requirements.items():
        for parent in data.get("derives_from", []) or []:
            if parent not in requirements:
                errors.append(f"{file}: unknown derives_from target {parent}")
            else:
                reverse[parent].append(identifier)
    return {
        "derives_from": {
            identifier: data[1].get("derives_from", []) or []
            for identifier, data in requirements.items()
        },
        "derived_by": {identifier: sorted(values) for identifier, values in reverse.items()},
        "errors": errors,
    }


# @implements_req SwRS-OKFSCHEMA-OKFREQ-005
def validate_requirements(root: Path, prose: bool = False) -> list[str]:
    """Run deterministic structural and graph checks.

    Args:
        root:
            The bundle root.
        prose:
            When ``True``, also emit advisory ``W`` prose warnings. Advisory
            findings never make structural validation fail on their own.

    Returns:
        A list of findings. Structural errors have no ``W`` prefix.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     validate_requirements(root)
        []
    """
    config = load_config(root)
    requirements = load_requirements(root)
    errors: list[str] = []
    fields = (
        "type",
        "id",
        "uuid",
        "title",
        "description",
        "project",
        "scope",
        "lifecycle",
        "origin",
        "tier",
    )
    schemas_dir = tiers_path(root) / "_schema"
    base_schema = schemas_dir / "base.schema.yaml"
    if not base_schema.is_file():
        raise RequirementError(f"missing requirement schema: {base_schema}")
    schemas = load_schema_database(schemas_dir)
    normalized_schemas = {name.casefold(): schema for name, schema in schemas.items()}
    for level in ("StRS", "SwRS"):
        if level.casefold() not in normalized_schemas:
            raise RequirementError(f"missing requirement schema for type {level}: {schemas_dir}")
    for identifier, (file, data, text) in requirements.items():
        if prose and body_is_unfilled(text):
            errors.append(f"W002 {file}: body has no filled EARS expression")
        level = str(data.get("type", ""))
        if level.casefold() not in normalized_schemas:
            errors.append(f"{file}: no schema configured for type {level}")
        else:
            schema_data = dict(normalized_schemas[level.casefold()])
            base = normalized_schemas.get("base") or normalized_schemas.get("base.schema")
            if base is None:
                raise RequirementError(f"missing requirement schema: {base_schema}")
            schema_data["allOf"] = [base, *schema_data.get("allOf", [])[1:]]
            validator = Draft202012Validator(schema_data, format_checker=FormatChecker())
            errors.extend(f"{file}: {error.message}" for error in validator.iter_errors(data))
        errors.extend(f"{file}: missing {field}" for field in fields if not data.get(field))
        if data.get("id") != identifier or _id_pattern(config).fullmatch(identifier) is None:
            errors.append(f"{file}: invalid ID")
        try:
            uuid.UUID(str(data.get("uuid")))
        except (ValueError, AttributeError, TypeError):
            errors.append(f"{file}: invalid UUID")
        if data.get("lifecycle") not in config["lifecycle"]["values"]:
            errors.append(f"{file}: invalid lifecycle")
        if data.get("type") not in config["levels"]:
            errors.append(f"{file}: unconfigured level {data.get('type')}")
        if data.get("annotation_exemption") is True and not data.get("exemption_reason"):
            errors.append(f"{file}: annotation exemption requires exemption_reason")
        level_config = config["levels"].get(data.get("type"), {})
        if level_config.get("derives_from") and not data.get("derives_from"):
            errors.append(f"{file}: {data.get('type')} requires derives_from")
        for parent in data.get("derives_from", []) or []:
            if (
                parent in requirements
                and level_config.get("derives_from")
                and requirements[parent][1].get("type") not in level_config["derives_from"]
            ):
                errors.append(f"{file}: invalid parent level")
        if prose and len(str(data.get("description", "")).split()) < 3:
            errors.append(f"W001 {file}: description is unusually short")
    errors.extend(graph(root)["errors"])
    return errors


def update_coverage(
    root: Path,
    *,
    check: bool = False,
    show_diff: bool = False,
) -> list[str]:
    """Update generated coverage fields atomically or preview their changes.

    Args:
        root:
            Bundle root containing requirements and scan configuration.
        check:
            When ``True``, report changed paths without writing them.
        show_diff:
            When ``True``, print unified diffs without writing them.

    Returns:
        Paths of requirement documents that changed or would change.

    Raises:
        RequirementError:
            If ``generated_fields`` is malformed or contains unsupported
            field names.

    Examples:
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     update_coverage(root, check=True)
        []
    """
    requirements = load_requirements(root)
    config = load_config(root)
    scan = marker_scan(root)
    configured_fields = config.get("generated_fields", [])
    if not isinstance(configured_fields, list):
        raise RequirementError("generated_fields must be a list")
    unsupported = set(map(str, configured_fields)) - SUPPORTED_GENERATED_FIELDS
    if unsupported:
        raise RequirementError(f"unsupported generated_fields: {', '.join(sorted(unsupported))}")
    reverse: dict[str, list[str]] = {identifier: [] for identifier in requirements}
    for _, (_, data, _) in requirements.items():
        for parent in data.get("derives_from", []) or []:
            if parent in reverse:
                reverse[parent].append(str(data.get("id")))
    changed: list[str] = []
    for identifier, (file, _, text) in requirements.items():
        available_updates = {"derived_by": sorted(reverse[identifier])}
        if str(requirements[identifier][1].get("type")) == "SwRS":
            available_updates.update(
                {
                    "implemented_in_files": scan["implemented"].get(identifier, []),
                    "tested_in_files": scan["tested"].get(identifier, []),
                }
            )
        updates = {
            key: available_updates[key] for key in configured_fields if key in available_updates
        }
        rendered = _render_frontmatter(text, updates)
        if str(requirements[identifier][1].get("type")) == "StRS":
            frontmatter, body = extract_frontmatter(rendered)
            if frontmatter is not None:
                data = make_yaml().load(frontmatter)
                if isinstance(data, dict):
                    data.pop("implemented_in_files", None)
                    data.pop("tested_in_files", None)
                    rendered = f"---\n{dump_yaml(data)}---\n{body}"
        if rendered == text:
            continue
        changed.append(str(file))
        if show_diff:
            print(
                "".join(
                    difflib.unified_diff(
                        text.splitlines(True),
                        rendered.splitlines(True),
                        fromfile=str(file),
                        tofile=str(file),
                    )
                )
            )
        elif not check:
            _atomic_write(file, rendered)
    return changed


def report(root: Path) -> dict[str, Any]:
    """Build a detailed requirements-linkage report.

    Linkage coverage is deliberately separate from test execution coverage:
    a requirement is test-covered when at least one test marker references it.
    No conclusion about whether that test ran or passed is made here.

    Args:
        root:
            Bundle root to validate and scan.

    Returns:
        A serializable report containing traceability totals, requirement
        records, diagnostics, and provenance.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     report(root)["totals"]["requirements"]
        0
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-004
    requirements = load_requirements(root)
    trace = marker_scan(root)
    graph_result = graph(root)
    errors = validate_requirements(root)
    lifecycle: dict[str, int] = {}
    for _, data, _ in requirements.values():
        value = str(data.get("lifecycle", "invalid"))
        lifecycle[value] = lifecycle.get(value, 0) + 1
    config = load_config(root)
    leaf_levels = _leaf_levels(config)
    missing_implementation: list[str] = []
    missing_tests: list[str] = []
    exemptions: list[dict[str, str]] = []
    for identifier, (_, data, _) in requirements.items():
        if data.get("type") not in leaf_levels:
            continue
        if data.get("annotation_exemption") is True:
            exemptions.append({"id": identifier, "reason": str(data.get("exemption_reason") or "")})
            continue
        if identifier not in trace["implemented"]:
            missing_implementation.append(identifier)
        if identifier not in trace["tested"]:
            missing_tests.append(identifier)
    coverage_targets = {
        identifier: (file, data, text)
        for identifier, (file, data, text) in requirements.items()
        if data.get("type") in leaf_levels and data.get("annotation_exemption") is not True
    }
    implemented = set(trace["implemented"]) & set(coverage_targets)
    tested = set(trace["tested"]) & set(coverage_targets)
    fully_traceable = implemented & tested

    def percentage(count: int, total: int) -> float:
        """Return a percentage rounded to two decimal places."""
        return round((count / total) * 100, 2) if total else 100.0

    requirement_records: list[dict[str, Any]] = []
    for identifier, (file, data, text) in sorted(requirements.items()):
        source_links = trace["implemented"].get(identifier, [])
        test_links = trace["tested"].get(identifier, [])
        coverage_target = identifier in coverage_targets
        requirement_records.append(
            {
                "id": identifier,
                "path": file.relative_to(project_path(root)).as_posix(),
                "text": text,
                "frontmatter": data,
                "scope": data.get("scope"),
                "tier": data.get("tier", data.get("type")),
                "derives_from": data.get("derives_from", []) or [],
                "coverage_target": coverage_target,
                "implementation": {
                    "status": "covered" if source_links else "missing",
                    "files": source_links,
                    "count": len(source_links),
                },
                "tests": {
                    "status": "covered" if test_links else "missing",
                    "files": test_links,
                    "count": len(test_links),
                },
                "execution": {"status": "not_collected", "results": []},
                "diagnostics": {
                    "exempted": data.get("annotation_exemption") is True,
                    "errors": [error for error in errors if identifier in error],
                },
            }
        )

    scopes: dict[str, dict[str, Any]] = {}
    configured_scopes = config.get("scopes", {})
    for identifier, (_, data, _) in coverage_targets.items():
        scope_name = str(data.get("scope", ""))
        scope_report = scopes.setdefault(
            scope_name,
            {"requirements": 0, "implemented": 0, "tested": 0, "fully_traceable": 0},
        )
        scope_report["requirements"] += 1
        scope_report["implemented"] += identifier in implemented
        scope_report["tested"] += identifier in tested
        scope_report["fully_traceable"] += identifier in fully_traceable
        scope_report["configured"] = (
            isinstance(configured_scopes, dict) and scope_name in configured_scopes
        )
    for values in scopes.values():
        total = values["requirements"]
        values["source_coverage_percent"] = percentage(values["implemented"], total)
        values["test_coverage_percent"] = percentage(values["tested"], total)
        values["combined_coverage_percent"] = percentage(values["fully_traceable"], total)

    total = len(coverage_targets)
    try:
        package_version = version("okf-schema")
    except PackageNotFoundError:
        package_version = "unknown"
    detailed = {
        "report_format": "okfreq-requirements-report",
        "format_version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generated_by": {
            "tool": "okfreq",
            "version": package_version,
            "command": "okfreq generate-report",
        },
        "bundle_path": root.as_posix(),
        "scan": {
            "project_root": project_path(root).as_posix(),
            "source_and_test_directories": config.get("scopes", {}),
        },
        "execution_evidence": {
            "status": "not_collected",
            "result_files": [],
            "description": "Only linked test markers were scanned.",
        },
        "coverage_definition": {
            "population": "configured leaf requirements without annotation exemptions",
            "source": "at least one @implements_req marker",
            "tests": "at least one @tests_req marker",
            "combined": "at least one source marker and one test marker",
        },
        "totals": {
            "requirements": len(requirements),
            "coverage_target_requirements": total,
            "implemented": len(implemented),
            "tested": len(tested),
            "fully_traceable": len(fully_traceable),
            "source_coverage_percent": percentage(len(implemented), total),
            "test_coverage_percent": percentage(len(tested), total),
            "combined_coverage_percent": percentage(len(fully_traceable), total),
        },
        "scopes": scopes,
        "requirements": requirement_records,
        # Keep the original aggregate section stable for callers that consumed
        # the pre-v1 report while exposing the richer v1 fields above.
        "marker_coverage": {
            "implemented": len(trace["implemented"]),
            "tested": len(trace["tested"]),
            "missing_ids": trace["missing_ids"],
            "duplicates": trace["duplicates"],
            "non_leaf": trace["non_leaf"],
            "warnings": trace["warnings"],
            "missing_implementation": sorted(missing_implementation),
            "missing_tests": sorted(missing_tests),
            "exemptions": exemptions,
        },
        "legacy": {
            "provenance": {
                "generator": "okfreq",
                "command": "okfreq generate-report",
                "config_version": config.get("version"),
                "sources": ["config.yml", "tiers/"],
            },
            "schema_health": {"requirements": len(requirements), "errors": len(errors)},
            "structural_traceability": {"graph_errors": len(graph_result["errors"])},
            "marker_coverage": {
                "implemented": len(trace["implemented"]),
                "tested": len(trace["tested"]),
                "missing_ids": trace["missing_ids"],
                "duplicates": trace["duplicates"],
                "non_leaf": trace["non_leaf"],
                "warnings": trace["warnings"],
                "missing_implementation": sorted(missing_implementation),
                "missing_tests": sorted(missing_tests),
                "exemptions": exemptions,
            },
            "lifecycle": lifecycle,
            "errors": errors,
        },
    }
    return detailed


def write_json_report(root: Path, destination: Path) -> None:
    """Write a generated requirements report as JSON.

    Args:
        root:
            Bundle root to report on.
        destination:
            Output JSON path, whose parent directory must exist.
    """
    _atomic_write(destination, json.dumps(report(root), indent=2) + "\n")


def report_schema() -> dict[str, Any]:
    """Return the JSON Schema for generated requirements reports.

    Returns:
        A JSON Schema mapping describing the detailed report format.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://okf-schema.dev/schemas/okfreq-requirements-report.schema.json",
        "title": "okfreq Requirements Report",
        "description": "Detailed linkage report generated by okfreq generate-report.",
        "type": "object",
        "required": [
            "report_format",
            "format_version",
            "generated_at",
            "generated_by",
            "bundle_path",
            "scan",
            "execution_evidence",
            "coverage_definition",
            "totals",
            "scopes",
            "requirements",
        ],
        "properties": {
            "report_format": {"const": "okfreq-requirements-report"},
            "format_version": {"type": "integer", "const": 1},
            "generated_at": {"type": "string", "format": "date-time"},
            "generated_by": {
                "type": "object",
                "required": ["tool", "version", "command"],
                "properties": {
                    "tool": {"type": "string"},
                    "version": {"type": "string"},
                    "command": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "bundle_path": {"type": "string"},
            "scan": {"type": "object"},
            "execution_evidence": {
                "type": "object",
                "required": ["status", "result_files", "description"],
                "properties": {
                    "status": {"const": "not_collected"},
                    "result_files": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
            },
            "coverage_definition": {"type": "object"},
            "totals": {
                "type": "object",
                "required": [
                    "requirements",
                    "coverage_target_requirements",
                    "implemented",
                    "tested",
                    "fully_traceable",
                    "source_coverage_percent",
                    "test_coverage_percent",
                    "combined_coverage_percent",
                ],
                "properties": {
                    "requirements": {"type": "integer", "minimum": 0},
                    "coverage_target_requirements": {"type": "integer", "minimum": 0},
                    "implemented": {"type": "integer", "minimum": 0},
                    "tested": {"type": "integer", "minimum": 0},
                    "fully_traceable": {"type": "integer", "minimum": 0},
                    "source_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    "test_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    "combined_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                },
            },
            "scopes": {"type": "object", "additionalProperties": {"$ref": "#/$defs/scope"}},
            "requirements": {"type": "array", "items": {"$ref": "#/$defs/requirement"}},
        },
        "additionalProperties": True,
        "$defs": {
            "scope": {
                "type": "object",
                "required": [
                    "requirements",
                    "implemented",
                    "tested",
                    "fully_traceable",
                    "source_coverage_percent",
                    "test_coverage_percent",
                    "combined_coverage_percent",
                ],
                "properties": {
                    "requirements": {"type": "integer", "minimum": 0},
                    "implemented": {"type": "integer", "minimum": 0},
                    "tested": {"type": "integer", "minimum": 0},
                    "fully_traceable": {"type": "integer", "minimum": 0},
                    "configured": {"type": "boolean"},
                    "source_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    "test_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    "combined_coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                },
            },
            "requirement": {
                "type": "object",
                "required": [
                    "id",
                    "path",
                    "text",
                    "frontmatter",
                    "scope",
                    "tier",
                    "coverage_target",
                    "implementation",
                    "tests",
                    "execution",
                    "diagnostics",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "path": {"type": "string"},
                    "text": {"type": "string"},
                    "frontmatter": {"type": "object"},
                    "scope": {"type": ["string", "null"]},
                    "tier": {"type": ["string", "null"]},
                    "derives_from": {"type": "array", "items": {"type": "string"}},
                    "coverage_target": {"type": "boolean"},
                    "implementation": {"$ref": "#/$defs/linkage"},
                    "tests": {"$ref": "#/$defs/linkage"},
                    "execution": {
                        "type": "object",
                        "required": ["status", "results"],
                        "properties": {
                            "status": {"const": "not_collected"},
                            "results": {"type": "array"},
                        },
                    },
                    "diagnostics": {"type": "object"},
                },
            },
            "linkage": {
                "type": "object",
                "required": ["status", "files", "count"],
                "properties": {
                    "status": {"enum": ["covered", "missing"]},
                    "files": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer", "minimum": 0},
                },
            },
        },
    }


def write_report_schema(destination: Path) -> None:
    """Write the JSON Schema describing a generated requirements report.

    Args:
        destination:
            Output JSON path, whose parent directory must exist.
    """
    _atomic_write(destination, json.dumps(report_schema(), indent=2) + "\n")


def write_markdown_report(root: Path, destination: Path) -> None:
    """Write the concise human summary corresponding to :func:`report`.

    Args:
        root:
            Bundle root to report on.
        destination:
            Output Markdown path, whose parent directory must exist.
    """

    def status_emoji(status: str) -> str:
        """Return the compact status marker used in the Markdown summary."""
        return {"covered": "✅", "missing": "❌"}.get(status, "⚪")

    data = report(root)
    totals = data["totals"]
    lines = [
        "# Requirements report",
        "",
        f"Generated: {data['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Requirements: {totals['requirements']} "
        f"({totals['coverage_target_requirements']} coverage targets)",
        f"- Source coverage: {totals['source_coverage_percent']}% "
        f"({totals['implemented']}/{totals['coverage_target_requirements']})",
        f"- Test-link coverage: {totals['test_coverage_percent']}% "
        f"({totals['tested']}/{totals['coverage_target_requirements']})",
        f"- Combined traceability: {totals['combined_coverage_percent']}% "
        f"({totals['fully_traceable']}/{totals['coverage_target_requirements']})",
        "",
        "## By scope",
        "",
        "| Scope | Requirements | Source | Tests | Combined |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for scope, values in sorted(data["scopes"].items()):
        lines.append(
            f"| {scope} | {values['requirements']} | {values['source_coverage_percent']}% | "
            f"{values['test_coverage_percent']}% | {values['combined_coverage_percent']}% |"
        )
    lines.extend(
        [
            "",
            "## By requirement",
            "",
            "| Scope | Tier | ID | Name | Source | Tests |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    requirements = sorted(
        data["requirements"],
        key=lambda requirement: (
            str(requirement["scope"]).casefold(),
            str(requirement["tier"]).casefold(),
            requirement["id"].casefold(),
        ),
    )
    for requirement in requirements:
        name = str(requirement["frontmatter"].get("title", requirement["id"]))
        lines.append(
            f"| {requirement['scope']} | {requirement['tier']} | "
            f"{requirement['id']} | {name} | "
            f"{status_emoji(requirement['implementation']['status'])} "
            f"{requirement['implementation']['status']} | "
            f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
        )
    _atomic_write(destination, "\n".join(lines) + "\n")
