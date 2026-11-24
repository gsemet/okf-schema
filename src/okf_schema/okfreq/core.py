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
import io
import json
import os
import re
import tempfile
import time
import uuid
from collections.abc import Iterable, Mapping
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import LiteralScalarString

from okf_schema._internal.yaml import dump_yaml, extract_frontmatter, make_yaml, parse_yaml
from okf_schema.api import check_file_links
from okf_schema.file_links import _FileLinkContext
from okf_schema.projection import (
    BundleProjector,
    Derive,
    ProjectionError,
    projected_status,
    projection_problems,
    schema_projection,
)
from okf_schema.validator import _parse_stale_after, load_schema_database_with_diagnostics
from okf_schema.validator import load_schema_database as load_schema_database
from okf_schema.validator import validate_bundle as validate_okf_bundle

DEFAULT_CONFIG = """version: 1
tiers:
  StRS: {folder: strs, prefix: StRS, derives_from: [], approval_lock: true}
  SwRS: {folder: swrs, prefix: SwRS, derives_from: [StRS], approval_lock: false}
id_policy: scope-prefix-sequence
strs_test_coverage_mode: linked-swrs
lifecycle:
  field: req_lifecycle
markers:
  implements: '@implements_req'
  tests: '@tests_req'
  accepts: '@accepts_req'
  id_pattern: '[A-Za-z][A-Za-z0-9_-]*'
generated_fields: [derived_by, supersedes, implemented_in_files, tested_in_files,
  accepted_in_files, default_owner_email, status, verified]
retired_ids: []
scopes:
  default: {source_dirs: [src], test_dirs: [tests]}
"""

LIFECYCLES = ("draft", "proposed", "approved", "deprecated", "superseded")
DEFAULT_LIFECYCLE_FIELD = "req_lifecycle"
# OKF section 5.4 status read by plain OKF consumers for each okfreq lifecycle.
STATUS_PROJECTION = {
    "draft": "draft",
    "proposed": "stable",
    "approved": "stable",
    "deprecated": "deprecated",
    "superseded": "deprecated",
}
LINK_PROJECTION_LABELS = {
    "derives_from": "Derives from",
    "derived_by": "Derived by",
    "depends_on": "Depends on",
    "superseded_by": "Superseded by",
    "supersedes": "Supersedes",
    "relates_to": "Relates to",
}
LIFECYCLE_DESCRIPTION = """Explicit, human-controlled lifecycle state.
- draft: a requirement proposal that is not implemented yet. A project whose
  requirements are delivered with the code they describe should not keep drafts
  on its default branch.
- proposed: implemented and in force, but not frozen. It may change through the
  usual plan and review, without an explicit owner agreement.
- approved: frozen by its owner. Any significant change (normative statement,
  scenarios, criteria, deprecation or supersession) needs the owner's explicit,
  justified agreement, recorded in approved_by and approved_at. Allowed only where
  approval_lock is true for the requirement's tier and scope. An edit that only
  adds the scenarios: frontmatter field keeps the body as it is and is logged in
  tiers/log.md naming the owner's agreement; approved_by and approved_at stay
  unchanged unless the owner gives a new approval.
- deprecated: no longer in force and not replaced; kept for history.
- superseded: replaced by the requirements listed in superseded_by; kept for history.
OKF consumers read the generated status mapped by x-okf-status-projection.
"""
GUIDELINE_NAME = "requirements.guidelines.md"
DEFAULT_ID_PATTERN = r"[A-Za-z][A-Za-z0-9_-]*"
SUPPORTED_GENERATED_FIELDS = frozenset(
    {
        "derived_by",
        "supersedes",
        "implemented_in_files",
        "tested_in_files",
        "accepted_in_files",
        "default_owner_email",
        "status",
        "verified",
    }
)
_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
ACCEPTANCE_PATHS_MODE = "linked-swrs-and-acceptance-paths"
STRS_TEST_COVERAGE_MODES = (
    "linked-swrs",
    "linked-swrs-and-validation-test",
    ACCEPTANCE_PATHS_MODE,
)
MARKER_KINDS = ("implements", "tests", "accepts")
DEFAULT_MARKERS = {
    "implements": "@implements_req",
    "tests": "@tests_req",
    "accepts": "@accepts_req",
}
DECLARED_SCENARIOS_URL = (
    "https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html"
    "#okfreq-declared-scenarios"
)
EXECUTION_COST_URL = (
    "https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html"
    "#okfreq-execution-cost"
)
_SCENARIO_ID = re.compile(r"S[1-9][0-9]*")
_LIVE_EXCLUDED_LIFECYCLES = frozenset({"deprecated", "superseded"})
STRS_TEST_COVERAGE_DESCRIPTIONS = {
    "linked-swrs": (
        "An StRS is considered as covered when it is linked to at least one SwRS and "
        "every linked SwRS has at least one test marker."
    ),
    "linked-swrs-and-validation-test": (
        "An StRS is considered as covered when it is linked to at least one SwRS, every "
        "linked SwRS has at least one test marker, and at least one validation test "
        "is defined directly for the StRS."
    ),
    ACCEPTANCE_PATHS_MODE: (
        "An StRS is considered as covered when it is linked to at least one SwRS, every "
        "linked SwRS is test-covered (one test per declared transition), and every "
        "declared main path has an acceptance test (@accepts_req) (when it declares no "
        "paths, at least one @accepts_req names the StRS). Paths with a test marker are "
        "reported as tested."
    ),
}

_EARS_PLACEHOLDER = "<"
_USER_NEED_PLACEHOLDER = "<stakeholder need in the stakeholder's language>"

_STRS_BODY = """## {title}

### Normative behavior

{description}
{main_paths}
### Preserved stakeholder intent

## User Need

{user_need}

### Rationale and constraints

<!-- Record stakeholder constraints, exclusions, or decisions that shape the
     outcome. Remove this section when there are none. -->

- <known constraint, exclusion, or rationale>
"""

_SWRS_BODY = """## {title}

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

_STRS_MAIN_PATHS = """
### Main paths

#### Path 1: <main path title>

1. <first step the stakeholder observes>
2. <next step, up to the observable outcome>
"""


def ears_body(
    level: str,
    description: str,
    *,
    user_need: str | None = None,
    title: str | None = None,
    main_paths: bool = False,
) -> str:
    """Return the EARS scaffold for a configured tier.

    .. versionchanged:: 0.13.0
        Use the requirement title as the first Markdown heading.

    .. versionchanged:: 0.18.0
        Accept ``main_paths`` to add a ``### Main paths`` section to a StRS.

    The scaffold is deliberately full of bracketed placeholders so an agent or
    author can see exactly which parts must be filled in.

    Args:
        level:
            The configured tier name, such as ``StRS`` or ``SwRS``.
        description:
            Normative EARS behavior supplied by the author.
        user_need:
            Stakeholder need for a top-tier requirement.
        title:
            Human-readable requirement title. Defaults to the description
            when called directly without a title.
        main_paths:
            Add a ``### Main paths`` section with one placeholder path after the
            normative behavior of a StRS, as mode
            ``linked-swrs-and-acceptance-paths`` does. Ignored for a SwRS.

    Returns:
        A Markdown body template for the tier.

    Examples:
        >>> body = ears_body("SwRS", "The tool SHALL validate the bundle.")
        >>> "### Scenario:" in body
        True
        >>> "#### Path 1:" in ears_body("StRS", "Users SHALL export.", main_paths=True)
        True
    """
    if level.lower().startswith("sw"):
        return _SWRS_BODY.format(
            title=title if title is not None else description, description=description
        )
    return _STRS_BODY.format(
        title=title if title is not None else description,
        description=description,
        user_need=user_need or _USER_NEED_PLACEHOLDER,
        main_paths=_STRS_MAIN_PATHS if main_paths else "",
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


def _scenarios_schema() -> dict[str, Any]:
    """Return the base-schema declaration of the authored ``scenarios:`` field."""
    return {
        "type": "array",
        "minItems": 1,
        "description": (
            "Authored main paths (StRS) or transition scenarios (SwRS). Each id S<n> "
            "is stable and never reused, even after its scenario is removed. Test "
            "markers name one with a #S<n> fragment."
        ),
        "items": {
            "type": "object",
            "required": ["id", "title"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string", "pattern": "^S[1-9][0-9]*$"},
                "title": {"type": "string", "minLength": 1},
            },
        },
    }


def _marker_files_schema(description: str, marker: str) -> dict[str, Any]:
    """Return the declaration of a generated, marker-derived file list."""
    return {
        "type": "array",
        "description": description,
        "items": {
            "type": "string",
            "x-okf-link": {
                "resolution": "project-relative",
                "syntax": "plain",
                "basename_marker": marker,
                "id_marker": "id",
                "show_line_number": True,
            },
        },
    }


def _swrs_accepted_in_files_schema() -> dict[str, Any]:
    """Return the SwRS declaration that refuses ``accepted_in_files``."""
    return {
        "type": "array",
        "maxItems": 0,
        "description": (
            "Never present. @accepts_req names a StRS main path; mark a SwRS test "
            "with @tests_req <SwRS-ID>#S<n>."
        ),
    }


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
        for attempt in range(5):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                # Windows refuses a replace while a scanner briefly holds the target open.
                if attempt == 4:
                    raise
                time.sleep(0.05 * (attempt + 1))
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def init_requirements(path: Path, force: bool = False) -> Path:
    """Create a complete standalone requirements bundle.

    See :func:`initialize_bundle` for the guideline outcome.

    Args:
        path:
            A project directory or an explicit bundle directory.
        force:
            When ``True``, merge into a non-empty directory and replace the
            installed guideline with the packaged one.

    Returns:
        The created bundle root.
    """
    return initialize_bundle(path, force)[0]


def initialize_bundle(path: Path, force: bool = False) -> tuple[Path, str]:
    """Create a complete standalone requirements bundle and report the guideline outcome.

    The bundle is split: ``config.yml``, ``guidelines/``, and generated reports
    live at the bundle root, while ``_schema/`` and the configured tier folders
    live under ``tiers/``.

    Args:
        path:
            A project directory or an explicit bundle directory.
        force:
            When ``True``, merge into a non-empty directory without replacing
            existing files, except the installed guideline, which is replaced
            by the packaged text. Project rules belong in a separate file of
            ``guidelines/`` (for example ``project.guidelines.md``), which
            initialization never touches.

    Returns:
        The bundle root and the guideline outcome: ``"installed"``, ``"replaced"``,
        ``"up to date"`` or ``"kept"`` (an existing guideline without ``force``).

    Raises:
        RequirementError:
            If the target exists, is not empty, and ``force`` is
            not set.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root, outcome = initialize_bundle(Path(directory) / "requirements")
        ...     (root / "config.yml").is_file(), outcome
        (True, 'installed')
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
        base: dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "base.schema.yaml",
            "title": "okfreq requirement base profile",
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Document type; selects which tier profile applies.",
                },
                "id": {
                    "type": "string",
                    "description": "Human-readable requirement identifier, e.g. SwRS-CORE-002.",
                },
                "uuid": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Stable UUIDv4 identifying this requirement across renames.",
                },
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Short, imperative summary of the requirement.",
                },
                "description": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Full requirement statement in EARS or plain prose.",
                },
                "project": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Project code this requirement belongs to.",
                },
                "scope": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Functional scope, e.g. Core, Safety, Connectivity.",
                },
                DEFAULT_LIFECYCLE_FIELD: {
                    "type": "string",
                    "enum": list(LIFECYCLES),
                    "description": LiteralScalarString(LIFECYCLE_DESCRIPTION),
                    "x-okf-status-projection": dict(STATUS_PROJECTION),
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "stable", "deprecated"],
                    "description": (
                        "Generated OKF lifecycle (OKF section 5.4), mapped from "
                        f"{DEFAULT_LIFECYCLE_FIELD} by x-okf-status-projection, so a plain "
                        "OKF consumer reads it. Never edit it by hand."
                    ),
                },
                "owner_email": {
                    "type": "string",
                    "format": "email",
                    "description": (
                        "Authored owner of this requirement. Overrides default_owner_email; "
                        "the owner approves the requirement and any change to it once "
                        "approved."
                    ),
                },
                "default_owner_email": {
                    "type": "string",
                    "format": "email",
                    "description": (
                        "Generated owner from config.yml: scopes.<scope>.tiers.<tier>."
                        "owner_email, else scopes.<scope>.owner_email, else "
                        "tiers.<tier>.owner_email. Absent when none is configured. "
                        "owner_email, when set, replaces it."
                    ),
                },
                "approved_by": {
                    "type": "string",
                    "format": "email",
                    "description": (
                        "Email of the owner who approved the current content. Required "
                        "when the lifecycle is approved; set only on the owner's explicit "
                        "agreement, never by an agent's own decision."
                    ),
                },
                "approved_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": (
                        "ISO 8601 datetime with an explicit UTC offset (for example "
                        "2026-10-28T09:00:00+01:00) of the owner's approval of the current "
                        "content. Required when the lifecycle is approved; updated with "
                        "every agreed change."
                    ),
                },
                "verified": {
                    "type": "object",
                    "properties": {
                        "by": {"type": "string"},
                        "at": {"type": "string", "format": "date-time"},
                    },
                    "description": (
                        "Generated OKF trust event (OKF section 5.2): by human:<approved_by> "
                        "at approved_at, so an approved requirement reads as human-reviewed. "
                        "Never edit it by hand."
                    ),
                },
                "origin": {
                    "type": "string",
                    "minLength": 1,
                    "description": (
                        "Where the requirement came from, e.g. native, imported, elicited."
                    ),
                },
                "tier": {
                    "type": "string",
                    "description": "Requirement tier; must match the document's directory profile.",
                },
                "derives_from": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                            "tooltip_shows_fields": ["description"],
                            "preview_shows_fields": ["description"],
                        },
                    },
                    "description": "Upstream requirement IDs this one is derived from.",
                },
                "derived_by": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                            "tooltip_shows_fields": ["description"],
                            "preview_shows_fields": ["description"],
                        },
                    },
                    "description": "Downstream requirement IDs deriving this one.",
                },
                "depends_on": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                        },
                    },
                    "description": "Other requirement IDs this one depends on.",
                },
                "superseded_by": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                            "tooltip_shows_fields": ["description"],
                            "preview_shows_fields": ["description"],
                        },
                    },
                    "description": (
                        "Requirement IDs that replace this one; required when the lifecycle "
                        "is superseded and forbidden otherwise."
                    ),
                },
                "supersedes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                            "tooltip_shows_fields": ["description"],
                            "preview_shows_fields": ["description"],
                        },
                    },
                    "description": "Generated IDs of the requirements this one replaces.",
                },
                "relates_to": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "x-okf-link": {
                            "resolution": "filename-stem",
                            "syntax": "plain",
                            "id_marker": "id",
                            "tooltip_shows_fields": ["description"],
                            "preview_shows_fields": ["description"],
                        },
                    },
                    "description": (
                        "Requirement IDs this one is laterally related to; carries no "
                        "derivation, supersession or coverage meaning."
                    ),
                },
                "scenarios": _scenarios_schema(),
            },
            "required": [
                "type",
                "id",
                "uuid",
                "title",
                "description",
                "project",
                "scope",
                DEFAULT_LIFECYCLE_FIELD,
                "origin",
                "tier",
            ],
            "additionalProperties": True,
        }
        base_properties = cast("dict[str, dict[str, Any]]", base["properties"])
        for name, label in LINK_PROJECTION_LABELS.items():
            base_properties[name]["items"]["x-okf-link"]["link-projection"] = label
        if level == "base":
            return dump_yaml(base) + "\n"
        tier = "StRS" if level == "strs" else "SwRS"
        properties: dict[str, Any] = {
            "type": {
                "const": tier,
                "description": (
                    "Fixed document type for stakeholder requirements."
                    if tier == "StRS"
                    else "Fixed document type for software requirements."
                ),
            },
            "tier": {
                "const": tier,
                "description": (
                    "Fixed tier for stakeholder requirements."
                    if tier == "StRS"
                    else "Fixed tier for software requirements."
                ),
            },
        }
        required = ["type", "tier"]
        if tier == "StRS":
            properties["user_need"] = {
                "type": "string",
                "minLength": 1,
                "description": "The stakeholder need this requirement formalizes.",
            }
            required.append("user_need")
            properties["tested_in_files"] = _marker_files_schema(
                "Generated test paths.", "@tests_req"
            )
            properties["accepted_in_files"] = _marker_files_schema(
                "Generated acceptance-test paths: files of @accepts_req markers that count, "
                f"in mode {ACCEPTANCE_PATHS_MODE}.",
                "@accepts_req",
            )
        else:
            properties["annotation_exemption"] = {
                "type": "boolean",
                "description": "True when this requirement is exempt from coverage annotations.",
            }
            required.append("annotation_exemption")
            properties["implemented_in_files"] = _marker_files_schema(
                "Generated source paths.", "@implements_req"
            )
            properties["tested_in_files"] = _marker_files_schema(
                "Generated test paths.", "@tests_req"
            )
            properties["accepted_in_files"] = _swrs_accepted_in_files_schema()
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{level}.schema.yaml",
            "title": f"okfreq {level} requirement profile",
            "description": (
                "StRS records stakeholder intent and carries no implementation fields. "
                f"In mode {ACCEPTANCE_PATHS_MODE} it carries the generated "
                "tested_in_files and accepted_in_files. Stakeholder test coverage is "
                "computed from linked SwRS according to configuration."
                if tier == "StRS"
                else "SwRS defines observable software behavior and its traceability."
            ),
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
    return root, _install_guideline(root, replace=force)


_OWN_MARKER_LINE = re.compile(
    r"^[ \t]*(?:(?:#|//|/\*|\*|<!--)[ \t]*)?@(?:implements|tests|accepts)_req[ \t]+"
    r"[A-Za-z][A-Za-z0-9_-]*(?:#S[0-9]+)?"
    r"[ \t]*(?:-->|\*/)?[ \t]*\r?\n(?:[ \t]*\r?\n)?",
    re.MULTILINE,
)


def _strip_own_markers(text: str) -> str:
    """Remove the line-level requirement markers of okf-schema's own bundle.

    The packaged guideline is evidence for okf-schema's requirements, so it
    carries markers that must not leak into the project it is installed in.

    Args:
        text:
            The packaged guideline text.

    Returns:
        The text without marker lines (and one blank line that followed each).

    Examples:
        >>> _strip_own_markers("# T\\n\\n<!-- @implements_req SwRS-A-001 -->\\n\\nBody\\n")
        '# T\\n\\nBody\\n'
    """
    return _OWN_MARKER_LINE.sub("", text)


def _install_guideline(root: Path, replace: bool = False) -> str:
    """Copy the packaged requirements guideline into the bundle.

    Args:
        root:
            The bundle root.
        replace:
            Replace an existing guideline with the packaged text.

    Returns:
        ``"installed"`` when it was missing, ``"replaced"`` or ``"up to date"``
        when ``replace`` is set, and ``"kept"`` when it exists and ``replace`` is not.
    """
    destination = root / "guidelines" / GUIDELINE_NAME
    existed = destination.exists()
    if existed and not replace:
        return "kept"
    source = files("okf_schema.data.requirements").joinpath("guidelines").joinpath(GUIDELINE_NAME)
    with as_file(source) as resolved:
        text = _strip_own_markers(Path(resolved).read_text(encoding="utf-8"))
    if existed and destination.read_text(encoding="utf-8") == text:
        return "up to date"
    _atomic_write(destination, text)
    return "replaced" if existed else "installed"


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
    if "tiers" in data and "levels" in data:
        raise RequirementError(
            "config.yml declares both tiers and the legacy levels key; keep tiers only"
        )
    if "tiers" not in data and "levels" not in data:
        data["tiers"] = {}
    data.setdefault("scopes", {"default": {"source_dirs": ["src"], "test_dirs": ["tests"]}})
    markers = data.setdefault("markers", {})
    if not isinstance(markers, dict):
        raise RequirementError("markers must be a mapping")
    for kind, keyword in DEFAULT_MARKERS.items():
        markers.setdefault(kind, keyword)
    markers.setdefault("id_pattern", DEFAULT_ID_PATTERN)
    seen: dict[str, str] = {}
    for kind in MARKER_KINDS:
        keyword = str(markers[kind])
        if keyword in seen:
            raise RequirementError(
                f"markers.{seen[keyword]} and markers.{kind} use the same keyword {keyword}"
            )
        seen[keyword] = kind
    lifecycle = data.setdefault("lifecycle", {})
    if "values" not in lifecycle:
        lifecycle.setdefault("field", DEFAULT_LIFECYCLE_FIELD)
    data.setdefault("id_policy", "scope-prefix-sequence")
    data.setdefault("generated_fields", sorted(SUPPORTED_GENERATED_FIELDS))
    data.setdefault("strs_test_coverage_mode", "linked-swrs")
    _strs_test_coverage_mode(data)
    data["retired_ids"] = _retired_ids(data)
    return data


def _retired_ids(config: dict[str, Any]) -> list[str]:
    """Return the validated ``retired_ids`` list, empty when it is not configured."""
    value = config.get("retired_ids")
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RequirementError("invalid retired_ids: expected a list of requirement ID strings")
    return [str(item) for item in value]


def _strs_test_coverage_mode(config: dict[str, Any]) -> str:
    """Return the configured StRS test-coverage rule."""
    mode = str(config.get("strs_test_coverage_mode", "linked-swrs"))
    if mode not in STRS_TEST_COVERAGE_MODES:
        allowed = ", ".join(STRS_TEST_COVERAGE_MODES)
        raise RequirementError(
            f"unsupported strs_test_coverage_mode: {mode}; expected one of: {allowed}"
        )
    return mode


def _id_pattern(config: dict[str, Any]) -> re.Pattern[str]:
    """Compile the configured requirement-ID pattern."""
    value = str(config.get("markers", {}).get("id_pattern", DEFAULT_ID_PATTERN))
    try:
        return re.compile(value)
    except re.error as exc:
        raise RequirementError(f"invalid markers.id_pattern: {exc}") from exc


def config_tiers(config: dict[str, Any]) -> dict[str, Any]:
    """Return the configured tiers, read from ``tiers`` or the legacy ``levels`` key.

    .. versionadded:: 0.16.0

    Args:
        config:
            A configuration returned by :func:`load_config`.

    Returns:
        Tier names mapped to their settings; empty when none is configured.

    Examples:
        >>> config_tiers({"levels": {"StRS": {"folder": "strs"}}})
        {'StRS': {'folder': 'strs'}}
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    tiers = config.get("tiers", config.get("levels", {}))
    return tiers if isinstance(tiers, dict) else {}


def lifecycle_field(config: dict[str, Any]) -> str:
    """Return the frontmatter field that holds the lifecycle state.

    .. versionadded:: 0.16.0

    Args:
        config:
            A configuration returned by :func:`load_config`.

    Returns:
        ``lifecycle.field`` from the configuration, ``"req_lifecycle"`` by default.

    .. versionchanged:: 0.17.0
        The default field is ``req_lifecycle``, distinct from the OKF ``status``.

    Examples:
        >>> lifecycle_field({"lifecycle": {"field": "state"}})
        'state'
    """
    lifecycle = config.get("lifecycle", {})
    if isinstance(lifecycle, dict):
        return str(lifecycle.get("field", DEFAULT_LIFECYCLE_FIELD))
    return DEFAULT_LIFECYCLE_FIELD


def lifecycle_values(root: Path, config: dict[str, Any]) -> list[str]:
    """Return the accepted lifecycle values.

    The values come from the ``enum`` of the lifecycle field in
    ``tiers/_schema/base.schema.yaml``. A legacy ``lifecycle.values`` list in
    ``config.yml`` still takes precedence. Without either, the built-in values apply.

    .. versionadded:: 0.16.0

    Args:
        root:
            The bundle root.
        config:
            A configuration returned by :func:`load_config`.

    Returns:
        The accepted lifecycle values.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     lifecycle_values(root, load_config(root))
        ['draft', 'proposed', 'approved', 'deprecated', 'superseded']
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    lifecycle = config.get("lifecycle", {})
    if isinstance(lifecycle, dict) and isinstance(lifecycle.get("values"), list):
        return [str(value) for value in lifecycle["values"]]
    schema_file = tiers_path(root) / "_schema" / "base.schema.yaml"
    if schema_file.is_file():
        schema = parse_yaml(schema_file.read_text(encoding="utf-8"))
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        field = properties.get(lifecycle_field(config)) if isinstance(properties, dict) else None
        if isinstance(field, dict) and isinstance(field.get("enum"), list):
            return [str(value) for value in field["enum"]]
    return list(LIFECYCLES)


def owner_policy(config: dict[str, Any], tier: str, scope: str) -> tuple[bool, str | None]:
    """Resolve the approval lock and the default owner of a tier in a scope.

    ``scopes.<scope>.tiers.<tier>`` wins over ``scopes.<scope>`` (owner only),
    which wins over ``tiers.<tier>``. A ``null`` ``approval_lock`` counts as
    unset. Without ``approval_lock`` anywhere, a top tier (no ``derives_from``)
    is lockable and a derived tier is not. An unknown scope uses the tier settings.

    .. versionadded:: 0.16.0

    Args:
        config:
            A configuration returned by :func:`load_config`.
        tier:
            Requirement tier, such as ``StRS``.
        scope:
            Requirement scope, matched case-insensitively.

    Returns:
        Whether ``approved`` is allowed, and the default owner email or ``None``.

    Examples:
        >>> config = {
        ...     "tiers": {"SwRS": {"derives_from": ["StRS"], "owner_email": "a@x.org"}},
        ...     "scopes": {"ui": {"tiers": {"SwRS": {"approval_lock": True}}}},
        ... }
        >>> owner_policy(config, "SwRS", "UI")
        (True, 'a@x.org')
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    tier_config = config_tiers(config).get(tier)
    tier_config = tier_config if isinstance(tier_config, dict) else {}
    scope_config: dict[str, Any] = {}
    scopes = config.get("scopes", {})
    if isinstance(scopes, dict):
        for name, value in scopes.items():
            if str(name).casefold() == scope.casefold() and isinstance(value, dict):
                scope_config = value
                break
    scope_tiers = scope_config.get("tiers", {})
    scope_tier = scope_tiers.get(tier) if isinstance(scope_tiers, dict) else None
    scope_tier = scope_tier if isinstance(scope_tier, dict) else {}
    # An absent or null approval_lock is unset: fall back to the broader setting.
    lock = scope_tier.get("approval_lock")
    if lock is None:
        lock = tier_config.get("approval_lock")
    if lock is None:
        lock = not tier_config.get("derives_from")
    owner = (
        scope_tier.get("owner_email")
        or scope_config.get("owner_email")
        or tier_config.get("owner_email")
    )
    return lock is True, str(owner) if owner else None


def _ownership_config_findings(config: dict[str, Any]) -> list[str]:
    """Return configuration errors in ``approval_lock`` and ``owner_email`` settings."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    findings: list[str] = []
    places: list[tuple[str, Any]] = [
        (f"tiers.{name}", value) for name, value in config_tiers(config).items()
    ]
    scopes = config.get("scopes", {})
    for name, value in scopes.items() if isinstance(scopes, dict) else []:
        if not isinstance(value, dict):
            continue
        places.append((f"scopes.{name}", {"owner_email": value.get("owner_email")}))
        scope_tiers = value.get("tiers", {})
        for tier, tier_value in scope_tiers.items() if isinstance(scope_tiers, dict) else []:
            places.append((f"scopes.{name}.tiers.{tier}", tier_value))
    for path, value in places:
        if not isinstance(value, dict):
            continue
        lock = value.get("approval_lock")
        if lock is not None and not isinstance(lock, bool):
            findings.append(f"config.yml: {path}.approval_lock must be true or false")
        owner = value.get("owner_email")
        if owner is not None and not _EMAIL_PATTERN.fullmatch(str(owner)):
            findings.append(f"config.yml: {path}.owner_email is not an email address")
    return findings


def _approval_findings(
    file: Path, data: dict[str, Any], config: dict[str, Any], field: str
) -> list[str]:
    """Check that an approved requirement is lockable and records its approval."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    if data.get(field) != "approved":
        return []
    tier = str(data.get("tier") or data.get("type") or "")
    scope = str(data.get("scope") or "")
    lock, default_owner = owner_policy(config, tier, scope)
    owner = data.get("owner_email") or default_owner
    findings: list[str] = []
    if not lock:
        findings.append(
            f"{file}: lifecycle approved is not allowed for tier {tier} in scope {scope} "
            "(approval_lock is false). Keep it proposed, or ask the owner to set "
            "approval_lock: true for this tier or scope in config.yml."
        )
    missing = [name for name in ("approved_by", "approved_at") if not data.get(name)]
    if missing:
        findings.append(
            f"{file}: lifecycle approved requires {' and '.join(missing)}. Only the "
            f"requirement owner ({owner or 'owner_email or default_owner_email'}) approves "
            "a requirement or a change to an approved one; a coding agent never decides it "
            "alone. If the owner agreed, for example during planning, set approved_by to "
            "the owner's email and approved_at to the current date and time with its UTC "
            "offset (for example 2026-10-28T09:00:00+01:00), then request the owner's "
            "review of this file on the pull or merge request (for example through "
            "CODEOWNERS). Otherwise restore the previous lifecycle and content."
        )
    elif _approval_instant(data.get("approved_at")) is None:
        findings.append(
            f"{file}: approved_at must be an ISO 8601 datetime with an explicit UTC offset, "
            "for example 2026-10-28T09:00:00+01:00"
        )
    return findings


def _approval_instant(value: Any) -> datetime.datetime | None:
    """Return the approval instant, or ``None`` unless it is a datetime with an offset."""
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return None
    if isinstance(value, str) and "T" not in value.upper():
        return None
    parsed = _parse_stale_after(value)
    return parsed if isinstance(parsed, datetime.datetime) else None


def _verified_update(data: CommentedMap) -> dict[str, tuple[Any, str | None]]:
    """Return the generated OKF ``verified`` event of the owner approval, if any."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-014
    by, at = data.get("approved_by"), data.get("approved_at")
    if not by or _approval_instant(at) is None:
        return {"verified": (None, None)}
    event = CommentedMap()
    event["by"] = f"human:{by}"
    # A copy keeps the authored form of the instant without a YAML alias;
    # ruamel's replace() keeps the offset that deepcopy drops.
    event["at"] = at.replace() if isinstance(at, datetime.datetime) else str(at)
    return {"verified": (event, "approved_at")}


def _tier_schemas(root: Path) -> dict[str, dict[str, Any]]:
    """Return the tier schemas keyed by case-folded type, each composed with the base."""
    schemas = {
        name.casefold(): schema
        for name, schema in load_schema_database(tiers_path(root) / "_schema").items()
    }
    base = schemas.pop("base", None) or schemas.pop("base.schema", None)
    composed: dict[str, dict[str, Any]] = {}
    for name, schema in schemas.items():
        data = dict(schema)
        if base is not None:
            data["allOf"] = [base, *data.get("allOf", [])[1:]]
        composed[name] = data
    return composed


class _RequirementProjector(BundleProjector):
    """Project requirements onto OKF ``status``, ``verified`` and Links sections."""

    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        generated = {str(name) for name in config.get("generated_fields", [])}
        super().__init__(tiers_path(root), _tier_schemas(root), status="status" in generated)
        self.verified = "verified" in generated

    def project(
        self,
        path: Path,
        text: str,
        *,
        updates: Mapping[str, tuple[Any, str | None]] | None = None,
        derive: Derive | None = None,
    ) -> str:
        """Project one requirement; ``verified`` follows the owner approval."""
        if derive is None and self.verified:
            derive = _verified_update
        return super().project(path, text, updates=updates, derive=derive)


def requirement_projector(root: Path, config: dict[str, Any] | None = None) -> BundleProjector:
    """Return the OKF projector of a requirements bundle.

    The projections come from the annotations of ``tiers/_schema/``: a Links
    section per ``link-projection``, ``status`` per ``x-okf-status-projection``
    when ``status`` is a generated field, and ``verified`` from ``approved_by``
    and ``approved_at`` when ``verified`` is a generated field.

    .. versionadded:: 0.17.0

    Args:
        root:
            The bundle root.
        config:
            A configuration returned by :func:`load_config`; loaded when omitted.

    Returns:
        A projector whose ``project(path, text)`` returns the projected text.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-014
    return _RequirementProjector(root, config if config is not None else load_config(root))


def _projected(root: Path, file: Path, text: str) -> str:
    """Return *text* projected for OKF consumers, as a domain error on malformed sections."""
    try:
        return requirement_projector(root).project(file, text)
    except ProjectionError as exc:
        raise RequirementError(f"{file}: {exc}") from exc


def project_requirements(
    root: Path,
    *,
    check: bool = False,
    show_diff: bool = False,
) -> list[Path]:
    """Refresh the OKF projection of every requirement.

    .. versionadded:: 0.17.0

    Args:
        root:
            The bundle root.
        check:
            Report stale requirements without writing.
        show_diff:
            Print unified diffs without writing.

    Returns:
        Requirement paths that changed or would change.

    Raises:
        RequirementError:
            If a requirement holds an incomplete or repeated generated Links section.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     project_requirements(init_requirements(Path(directory) / "requirements"))
        []
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-014
    projector = requirement_projector(root)
    changed: list[Path] = []
    for file, _, text in sorted(load_requirements(root).values(), key=lambda item: item[0]):
        try:
            rendered = projector.project(file, text)
        except ProjectionError as exc:
            raise RequirementError(f"{file}: {exc}") from exc
        if rendered == text:
            continue
        changed.append(file)
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


def _leaf_levels(config: dict[str, Any]) -> set[str]:
    """Return configured tiers that are not parents of another tier."""
    levels = config_tiers(config)
    if not isinstance(levels, dict):
        return set()
    parent_levels = {
        str(parent)
        for value in levels.values()
        if isinstance(value, dict)
        for parent in value.get("derives_from", [])
    }
    return {str(level) for level in levels} - parent_levels


def _rename_legacy_levels(config: dict[str, Any]) -> None:
    """Rename a legacy top-level ``levels`` key to ``tiers`` in place, keeping its position."""
    if "levels" not in config or "tiers" in config:
        return
    position = list(config).index("levels")
    value = config.pop("levels")
    if isinstance(config, CommentedMap):  # keeps the key position and its comments
        config.insert(position, "tiers", value)
    else:
        config["tiers"] = value


# @implements_req SwRS-OKFSCHEMA-OKFREQ-006
def merge_config(root: Path, source: Path) -> list[str]:
    """Merge a configuration while preserving unknown keys.

    Existing values take precedence over conflicting imported values. A legacy
    ``levels`` key is renamed ``tiers`` on both sides before merging. When the
    destination names its ``lifecycle.field``, an imported legacy
    ``lifecycle.values`` list is not imported and is reported as a conflict.

    .. versionchanged:: 0.16.0
        Normalize ``levels`` to ``tiers`` and refuse a legacy lifecycle values list.

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
            If the imported configuration cannot be parsed or declares both
            ``tiers`` and ``levels``.

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
    if "tiers" in imported and "levels" in imported:
        raise RequirementError(
            f"{source} declares both tiers and the legacy levels key; keep tiers only"
        )
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-013
    _rename_legacy_levels(current)
    _rename_legacy_levels(imported)
    conflicts: list[str] = []
    current_lifecycle = current.get("lifecycle")
    imported_lifecycle = imported.get("lifecycle")
    if (
        isinstance(current_lifecycle, dict)
        and "field" in current_lifecycle
        and "values" not in current_lifecycle
        and isinstance(imported_lifecycle, dict)
        and "values" in imported_lifecycle
    ):
        # The destination takes its values from the schema enum: a legacy list
        # would silently override it, so it is reported instead of imported.
        imported_lifecycle.pop("values")
        conflicts.append("lifecycle.values")

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
            if not prefix and key == "retired_ids" and isinstance(value, list):
                # A retired number is retired for good: union, never a conflict.
                incoming_ids = _retired_ids({"retired_ids": value})
                kept = _retired_ids(destination)
                destination[key] = kept + [item for item in incoming_ids if item not in kept]
            elif (
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

    .. versionchanged:: 0.13.0
        Reject every discovered requirement with absent or malformed mapping
        frontmatter or a missing string ID instead of omitting it from reports.

    Args:
        root:
            The bundle root returned by :func:`bundle_path`.

    Returns:
        A mapping of requirement ID to its path, frontmatter, and raw text.

    Raises:
        RequirementError:
            If a document cannot be indexed safely or two documents declare
            the same ID. Reserved index/log and schema/guideline files are excluded.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     load_requirements(root)
        {}
    """
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for file in sorted(tiers_path(root).glob("**/*.md")):
        if (
            file.name in {"index.md", "log.md"}
            or "_schema" in file.relative_to(tiers_path(root)).parts
        ):
            continue
        if "guidelines" in file.relative_to(tiers_path(root)).parts:
            continue
        text = file.read_text(encoding="utf-8")
        frontmatter, _ = extract_frontmatter(text)
        data = parse_yaml(frontmatter) if frontmatter is not None else None
        if not isinstance(data, dict):
            raise RequirementError(f"{file}: missing or invalid mapping frontmatter")
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise RequirementError(f"{file}: missing or invalid requirement ID")
        if identifier in result:
            raise RequirementError(f"duplicate requirement ID: {identifier}")
        result[identifier] = (file, data, text)
    return result


def _next_number(prefix: str, scope_token: str, identifiers: Iterable[str]) -> int:
    """Return one more than the highest number used for ``prefix`` and ``scope_token``.

    Args:
        prefix:
            Level prefix of the IDs, such as ``SwRS-PROJECT``.
        scope_token:
            Scope token of the IDs, such as ``CORE``.
        identifiers:
            Existing and retired requirement IDs; unrelated IDs are ignored.

    Returns:
        ``1`` when no ID matches, otherwise the highest matching number plus one.

    Examples:
        >>> _next_number("SwRS", "CORE", ["SwRS-CORE-001", "SwRS-CORE-140", "SwRS-API-900"])
        141
    """
    pattern = re.compile(rf"{re.escape(prefix)}-{re.escape(scope_token)}-(\d+)")
    numbers = [int(m.group(1)) for item in identifiers if (m := pattern.fullmatch(item))]
    return max(numbers, default=0) + 1


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
    lifecycle: str = "draft",
) -> Path:
    """Create a native requirement using configured tier and ID rules.

    .. versionchanged:: 0.14.0
        The number is one more than the highest number ever used in the tier
        prefix and scope, counting existing requirements and ``retired_ids``.
        A deleted requirement's number is never handed out again.

    .. versionchanged:: 0.16.0
        Accept ``lifecycle`` to create a ``proposed`` requirement delivered with
        its implementation.

    .. versionchanged:: 0.18.0
        In mode ``linked-swrs-and-acceptance-paths``, a StRS body gains a
        ``### Main paths`` section and ``scenarios:`` is pre-filled from the
        main-path or scenario headings of the body.

    The document body is an EARS scaffold for the tier, so the author or agent
    can see which parts still need to be written.

    Args:
        root:
            The bundle root.
        level:
            A configured tier name, such as ``StRS`` or ``SwRS``.
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
            Parent requirement IDs, required for derived tiers.
        user_need:
            Optional stakeholder need, recorded for top tiers. When
            omitted, the StRS scaffold retains an explicit placeholder instead
            of inventing or duplicating stakeholder intent.
        lifecycle:
            Initial lifecycle, ``draft`` (default) or ``proposed``.

    Returns:
        The created requirement path.

    Raises:
        RequirementError:
            If the tier is unconfigured, a parent is unknown or
            of the wrong tier, a required parent is missing, or the allocated
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
    if lifecycle not in ("draft", "proposed"):
        raise RequirementError(f"a new requirement starts as draft or proposed, not {lifecycle}")
    if config.get("id_policy") != "scope-prefix-sequence":
        raise RequirementError(f"unsupported id_policy: {config.get('id_policy')}")
    level_config = config_tiers(config).get(level)
    if not isinstance(level_config, dict):
        raise RequirementError(f"tier is not configured: {level}")
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
    number = _next_number(prefix, scope_token, [*existing, *config["retired_ids"]])
    identifier = f"{prefix}-{scope_token}-{number:03d}"
    data: dict[str, Any] = {
        "type": level,
        "id": identifier,
        "uuid": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "project": project,
        "scope": scope_name,
        lifecycle_field(config): lifecycle,
        "origin": origin,
        "tier": level,
        "derives_from": parent,
    }
    if configured_parents:
        if user_need is not None:
            raise RequirementError(f"{level} does not accept user_need")
        # Derived tiers carry annotation coverage, so record exemption intent.
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
    acceptance_paths = _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE
    body = ears_body(
        level,
        description,
        user_need=user_need,
        title=title,
        main_paths=acceptance_paths and level == "StRS",
    )
    if acceptance_paths and level in ("StRS", "SwRS"):
        # The frontmatter starts in step with the body's main paths or scenarios.
        data["scenarios"] = _proposed_scenarios(body)
    text = f"---\n{dump_yaml(data)}---\n\n{body}"
    _atomic_write(target, _projected(root, target, text))
    return target


def _log_retirement(root: Path, identifier: str, title: str, reason: str | None) -> None:
    """Append a retirement entry to the tier ``log.md`` under today's date."""
    log = tiers_path(root) / "log.md"
    today = datetime.date.today().isoformat()
    entry = f"- Retired {identifier} ({title}); the number is never reused."
    if reason:
        entry += f" Reason: {reason}"
    lines = log.read_text(encoding="utf-8").splitlines() if log.is_file() else ["# Update Log"]
    heading = f"## {today}"
    if heading in lines:
        start = lines.index(heading) + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
        while end > start and not lines[end - 1].strip():
            end -= 1
        lines[end:end] = ["", entry] if end == start else [entry]
    else:
        first = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
        block = [heading, "", entry, ""]
        lines[first:first] = block if first < len(lines) else ["", *block[:-1]]
    _atomic_write(log, "\n".join(lines).rstrip("\n") + "\n")


def retire_requirement(root: Path, identifier: str, *, reason: str | None = None) -> Path:
    """Delete a never-published draft requirement and retire its ID for good.

    The ID is added to ``retired_ids`` in ``config.yml`` before the file is
    removed, so a failure never leaves a number free for reuse. An entry is
    appended to ``tiers/log.md``. Published requirements are retired with
    ``archive`` or ``supersede`` instead, which keep the document.

    .. versionadded:: 0.14.0

    Args:
        root:
            The bundle root.
        identifier:
            ID of the requirement to delete.
        reason:
            Optional explanation recorded in the change log.

    Returns:
        The path of the deleted requirement document.

    Raises:
        RequirementError:
            If the ID is unknown, the requirement is not a ``draft``, another
            requirement derives from, depends on, relates to or is superseded by it, or a
            source or test marker (``@implements_req``, ``@tests_req`` or
            ``@accepts_req``) still references it. Nothing is changed.

    .. versionchanged:: 0.18.0
        Also refused when an ``@accepts_req`` marker names the ID.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     stakeholder = create_requirement(
        ...         root, "StRS", "Draft", "The tool SHALL work.", project="p",
        ...         scope="default", origin="native",
        ...     )
        ...     retire_requirement(root, "StRS-default-001") == stakeholder
        ...     load_config(root)["retired_ids"]
        True
        ['StRS-default-001']
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-011
    requirements = load_requirements(root)
    if identifier not in requirements:
        raise RequirementError(f"unknown requirement: {identifier}")
    file, data, _ = requirements[identifier]
    field = lifecycle_field(load_config(root))
    if data.get(field) != "draft":
        raise RequirementError(
            f"{identifier} is {data.get(field)}, not draft; "
            "use archive or supersede to retire a published requirement"
        )
    references = sorted(
        other
        for other, (_, other_data, _) in requirements.items()
        if other != identifier
        and (
            identifier in (other_data.get("derives_from") or [])
            or identifier in (other_data.get("depends_on") or [])
            or identifier in _listed_ids(other_data.get("relates_to"))
            or identifier in _superseded_by_ids(other_data)
        )
    )
    if references:
        raise RequirementError(f"cannot retire {identifier}: referenced by {', '.join(references)}")
    markers = marker_scan(root)
    marked = sorted(
        {
            location
            for kind in ("implemented", "tested", "validation_tests", "accepted")
            for location in markers[kind].get(identifier, [])
        }
    )
    if marked:
        raise RequirementError(
            f"cannot retire {identifier}: referenced by markers in {', '.join(marked)}"
        )
    config_file = root / "config.yml"
    # Round-trip edit: comments, quoting and flow style of the project config survive.
    yaml = make_yaml()
    config = yaml.load(config_file.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise RequirementError(f"invalid configuration: {config_file}")
    retired = _retired_ids(config)
    if identifier not in retired:
        if "retired_ids" in config and config["retired_ids"] is not None:
            config["retired_ids"].append(identifier)
        else:
            config["retired_ids"] = [identifier]
        buffer = io.StringIO()
        yaml.dump(config, buffer)
        _atomic_write(config_file, buffer.getvalue())
    file.unlink()
    _log_retirement(root, identifier, str(data.get("title", "")), reason)
    return file


def supersede_requirement(root: Path, target: str, replacements: list[str]) -> Path:
    """Mark ``target`` superseded by one or more replacement requirements.

    Sets ``lifecycle: superseded`` and writes ``superseded_by`` as a list,
    replacing any previous value (including the legacy scalar form). The body,
    UUID and other metadata are preserved. Nothing is written when a check fails.

    .. versionadded:: 0.15.0

    Args:
        root:
            The bundle root.
        target:
            ID of the requirement to supersede.
        replacements:
            IDs of the requirements that replace it, in the order to record.

    Returns:
        The path of the updated requirement document.

    Raises:
        RequirementError:
            If the target or a replacement is unknown, a replacement is the
            target itself or is listed twice, no replacement is given, or the
            replacements would make ``superseded_by`` cyclic.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     supersede_requirement(root, "StRS-default-001", [])
        Traceback (most recent call last):
        ...
        okf_schema.okfreq.core.RequirementError: unknown requirement: StRS-default-001
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-007
    requirements = load_requirements(root)
    if target not in requirements:
        raise RequirementError(f"unknown requirement: {target}")
    if not replacements:
        raise RequirementError("supersede needs at least one replacement requirement")
    for replacement in replacements:
        if replacement not in requirements:
            raise RequirementError(f"unknown replacement requirement: {replacement}")
        if replacement == target:
            raise RequirementError("a requirement cannot supersede itself")
    if len(set(replacements)) != len(replacements):
        raise RequirementError("duplicate replacement requirement")
    edges = {
        identifier: [item for item in _superseded_by_ids(data) if item in requirements]
        for identifier, (_, data, _) in requirements.items()
    }
    edges[target] = list(replacements)
    for cycle in _supersession_cycles(edges):
        if target in cycle:
            raise RequirementError(f"superseded_by would form a cycle: {' -> '.join(cycle)}")
    file, _, text = requirements[target]
    field = lifecycle_field(load_config(root))
    rendered = _render_frontmatter(text, {field: "superseded", "superseded_by": replacements})
    _atomic_write(file, _projected(root, file, rendered))
    return file


def _render_frontmatter(text: str, updates: dict[str, Any]) -> str:
    """Update selected generated fields while preserving the body."""
    frontmatter, body = extract_frontmatter(text)
    if frontmatter is None:
        raise RequirementError("requirement has no frontmatter")
    data = make_yaml().load(frontmatter)
    if not isinstance(data, dict):
        raise RequirementError("requirement frontmatter is not a mapping")
    for key, value in updates.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    return f"---\n{dump_yaml(data)}---\n{body}"


def marker_scan(root: Path) -> dict[str, Any]:
    """Scan configured source and test directories for requirement markers.

    .. versionchanged:: 0.18.0
        Read ``@accepts_req`` (``markers.accepts``) in test directories and the
        ``#S<n>`` scenario fragment of test markers; return ``accepted`` and
        ``scenario_markers``.

    Implementation markers are read in ``source_dirs`` only and test markers
    (``tests`` and ``accepts``) in ``test_dirs`` only. A test marker's ID may be
    followed by a fragment, ``#`` glued to the ID then ``S`` and digits; any
    other suffix is ignored and the marker is read without fragment.

    Args:
        root:
            Bundle root whose scope mappings determine which files are scanned.

    Returns:
        Marker locations and diagnostics grouped by category: ``implemented``
        and ``tested`` (leaf ID to files), ``validation_tests`` (StRS ID to the
        files of its ``@tests_req`` markers), ``accepted`` (ID to the files of its
        ``@accepts_req`` markers), ``scenario_markers`` (one entry per test
        marker kind, ID, fragment and file, with its first line),
        ``missing_ids``, ``non_leaf``, ``duplicates`` and ``warnings``.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     sorted(marker_scan(root))
        ['accepted', 'duplicates', 'implemented', 'missing_ids', 'non_leaf',
         'scenario_markers', 'tested', 'validation_tests', 'warnings']
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-003
    config = load_config(root)
    project = project_path(root)
    markers = config["markers"]
    keywords = {kind: str(markers[kind]) for kind in MARKER_KINDS}
    kind_of = {keyword: kind for kind, keyword in keywords.items()}
    configured_id = _id_pattern(config)
    embedded_id_pattern = configured_id.pattern.removeprefix("^").removesuffix("$")
    alternatives = "|".join(
        re.escape(keyword) for keyword in sorted(kind_of, key=len, reverse=True)
    )
    pattern = re.compile(
        rf"(?m)^\s*(?:(?:#|//|/\*|\*|<!--)\s*)?"
        rf"(?P<marker>{alternatives})\s+"
        rf"(?P<identifier>{embedded_id_pattern})"
        r"(?:#(?P<fragment>S[0-9]+)(?![A-Za-z0-9_-]))?"
    )
    result: dict[str, Any] = {
        "implemented": {},
        "tested": {},
        "validation_tests": {},
        "accepted": {},
        "scenario_markers": [],
        # Kept for report compatibility; repeated markers are accepted, so it stays empty.
        "duplicates": [],
        "non_leaf": [],
        "missing_ids": [],
        "warnings": [],
    }
    requirements = load_requirements(root)
    leaf_levels = _leaf_levels(config)
    seen_markers: set[tuple[str, str, str]] = set()
    seen_scenarios: set[tuple[str, str, str | None, str]] = set()
    scanned_files: set[tuple[str, Path]] = set()
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
                    scan_key = (_kind, file.resolve())
                    if scan_key in scanned_files:
                        continue
                    scanned_files.add(scan_key)
                    text = file.read_text(encoding="utf-8", errors="ignore")
                    for match in pattern.finditer(text):
                        kind = kind_of[match.group("marker")]
                        identifier = match.group("identifier")
                        if (_kind == "implemented") != (kind == "implements"):
                            continue
                        # Requirement reports use portable project-relative paths
                        # regardless of the host platform.
                        relative = file.relative_to(project).as_posix()
                        if kind != "implements" and identifier in requirements:
                            fragment = match.group("fragment")
                            scenario_key = (kind, identifier, fragment, relative)
                            if scenario_key not in seen_scenarios:
                                seen_scenarios.add(scenario_key)
                                result["scenario_markers"].append(
                                    {
                                        "marker": kind,
                                        "id": identifier,
                                        "fragment": fragment,
                                        "file": relative,
                                        "line": text.count("\n", 0, match.start("marker")) + 1,
                                    }
                                )
                        target = {
                            "implements": "implemented",
                            "tests": "tested",
                            "accepts": "accepted",
                        }[kind]
                        occurrence = (target, identifier, relative)
                        if occurrence in seen_markers:
                            # Several tests or code points in one file may carry
                            # the same ID; the file is listed once.
                            continue
                        seen_markers.add(occurrence)
                        if identifier not in requirements:
                            result["missing_ids"].append(identifier)
                            continue
                        if target == "accepted":
                            result["accepted"].setdefault(identifier, []).append(relative)
                            continue
                        requirement_type = requirements[identifier][1].get("type")
                        if requirement_type not in leaf_levels:
                            if target == "tested" and requirement_type == "StRS":
                                validation_locations = result["validation_tests"].setdefault(
                                    identifier, []
                                )
                                validation_locations.append(relative)
                                continue
                            result["non_leaf"].append(identifier)
                            continue
                        locations = result[target].setdefault(identifier, [])
                        locations.append(relative)
    for key in ("duplicates", "non_leaf", "missing_ids"):
        result[key] = sorted(set(result[key]))
    return result


def _listed_ids(value: Any) -> list[str]:
    """Return the requirement IDs held by a relation field, tolerating legacy scalars.

    Args:
        value:
            A frontmatter value: a list of IDs, a single ID string, or anything else.

    Returns:
        The string IDs in order; a single string counts as one ID and any other
        non-list value as none. Malformed fields are reported by validation.

    Examples:
        >>> _listed_ids(["A", "B"]), _listed_ids("A"), _listed_ids(None)
        (['A', 'B'], ['A'], [])
    """
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _superseded_by_ids(data: dict[str, Any]) -> list[str]:
    """Return the IDs in ``superseded_by``, reading the legacy scalar form as one ID."""
    return _listed_ids(data.get("superseded_by"))


def _supersession_reverse(
    requirements: dict[str, tuple[Path, dict[str, Any], str]],
) -> dict[str, list[str]]:
    """Return, for each requirement, the sorted IDs of those it replaces (``supersedes``)."""
    reverse: dict[str, list[str]] = {identifier: [] for identifier in requirements}
    for identifier, (_, data, _) in requirements.items():
        for replacement in dict.fromkeys(_superseded_by_ids(data)):
            if replacement in reverse and replacement != identifier:
                reverse[replacement].append(identifier)
    return {identifier: sorted(values) for identifier, values in reverse.items()}


def _supersession_cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    """Return each cycle of the ``superseded_by`` graph once, as a closed ID path.

    Args:
        edges:
            Mapping of requirement ID to the IDs replacing it.

    Returns:
        Cycles such as ``["A", "B", "A"]``, rotated to start at their smallest ID.

    Examples:
        >>> _supersession_cycles({"A": ["B"], "B": ["A"], "C": ["A"]})
        [['A', 'B', 'A']]
    """
    cycles: dict[tuple[str, ...], list[str]] = {}
    done: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        """Depth-first walk recording back edges as cycles."""
        if node in stack:
            loop = stack[stack.index(node) :]
            pivot = loop.index(min(loop))
            ring = loop[pivot:] + loop[:pivot]
            cycles.setdefault(tuple(ring), [*ring, ring[0]])
            return
        if node in done:
            return
        stack.append(node)
        for following in edges.get(node, []):
            if following in edges:
                visit(following, stack)
        stack.pop()
        done.add(node)

    for start in sorted(edges):
        visit(start, [])
    return [cycles[key] for key in sorted(cycles)]


def _relation_findings(
    requirements: dict[str, tuple[Path, dict[str, Any], str]],
    lifecycle_key: str = "lifecycle",
) -> list[str]:
    """Check ``superseded_by`` and ``relates_to`` authoring rules.

    Returns:
        Error findings (no code prefix) plus ``I2`` informational findings for the
        legacy scalar ``superseded_by`` form, which is still accepted.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-012
    findings: list[str] = []
    edges: dict[str, list[str]] = {}
    for identifier, (file, data, _) in requirements.items():
        for field in ("superseded_by", "relates_to"):
            value = data.get(field)
            if value is None or isinstance(value, list):
                shaped = value is None or all(isinstance(item, str) for item in value)
            else:
                shaped = field == "superseded_by" and isinstance(value, str)
            if not shaped:
                findings.append(f"{file}: {field} must be a list of requirement IDs")
                continue
            if isinstance(value, str) and value.strip():
                findings.append(
                    f"I2 {file}: superseded_by is a single ID; write a list "
                    f"([{value}]) - the scalar form is still accepted"
                )
            ids = _listed_ids(value)
            for target in ids:
                if target == identifier:
                    findings.append(f"{file}: {field} must not reference the requirement itself")
            for target in sorted({item for item in ids if ids.count(item) > 1}):
                findings.append(f"{file}: duplicate {field} target {target}")
            if field == "superseded_by":
                edges[identifier] = [
                    target
                    for target in dict.fromkeys(ids)
                    if target in requirements and target != identifier
                ]
        replaced_by = _superseded_by_ids(data)
        lifecycle = data.get(lifecycle_key)
        if lifecycle == "superseded" and not replaced_by:
            findings.append(f"{file}: lifecycle superseded requires a non-empty superseded_by")
        if lifecycle != "superseded" and replaced_by:
            findings.append(f"{file}: superseded_by is only valid when lifecycle is superseded")
    for cycle in _supersession_cycles(edges):
        findings.append(f"{requirements[cycle[0]][0]}: superseded_by cycle {' -> '.join(cycle)}")
    return findings


def graph(root: Path) -> dict[str, Any]:
    """Return authored and computed reverse derivation and supersession edges.

    .. versionchanged:: 0.15.0
        Also return ``superseded_by``, the computed ``supersedes`` and ``relates_to``.

    Args:
        root:
            Bundle root containing the requirement documents.

    Returns:
        Authored parent edges (``derives_from``), computed child edges
        (``derived_by``), authored replacements (``superseded_by``), their computed
        inverse (``supersedes``), authored lateral links (``relates_to``) and graph
        errors, including unknown ``derives_from``, ``superseded_by`` or
        ``relates_to`` targets.

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
    for file, data, _ in requirements.values():
        for field in ("superseded_by", "relates_to"):
            for target in _listed_ids(data.get(field)):
                if target not in requirements:
                    errors.append(f"{file}: unknown {field} target {target}")
    return {
        "derives_from": {
            identifier: data[1].get("derives_from", []) or []
            for identifier, data in requirements.items()
        },
        "derived_by": {identifier: sorted(values) for identifier, values in reverse.items()},
        "superseded_by": {
            identifier: _superseded_by_ids(data[1]) for identifier, data in requirements.items()
        },
        "supersedes": _supersession_reverse(requirements),
        "relates_to": {
            identifier: _listed_ids(data[1].get("relates_to"))
            for identifier, data in requirements.items()
        },
        "errors": errors,
    }


def is_info_finding(finding: str) -> bool:
    """Return whether a :func:`validate_requirements` finding is informational.

    Args:
        finding:
            One finding string returned by :func:`validate_requirements`.

    Returns:
        ``True`` for ``I<number>`` findings, which never fail validation.

    Examples:
        >>> is_info_finding("I1 a.schema.yaml: schema file 'a.schema.yaml' is empty")
        True
        >>> is_info_finding("W17 a.schema.yaml: cannot be parsed")
        False
    """
    return re.match(r"I\d+ ", finding) is not None


def _declared_scenarios(data: Mapping[str, Any]) -> list[str] | None:
    """Return the valid declared scenario ids, or ``None`` when none are declared.

    A malformed ``scenarios:`` still counts as declared: only its entries with a
    valid ``S<n>`` id are kept, and :func:`_scenario_problems` reports the rest.

    Examples:
        >>> _declared_scenarios({"scenarios": [{"id": "S1", "title": "a"}, {"id": "x"}]})
        ['S1']
        >>> _declared_scenarios({}) is None
        True
    """
    if "scenarios" not in data:
        return None
    declared: list[str] = []
    value = data.get("scenarios")
    for entry in value if isinstance(value, list) else []:
        identifier = entry.get("id") if isinstance(entry, Mapping) else None
        if (
            isinstance(identifier, str)
            and _SCENARIO_ID.fullmatch(identifier)
            and identifier not in declared
        ):
            declared.append(identifier)
    return declared


def _scenario_problems(value: Any) -> list[str]:
    """Return the problems of an authored ``scenarios:`` value.

    Examples:
        >>> _scenario_problems([{"id": "S1", "title": "a"}, {"id": "S1", "title": "b"}])
        ['duplicate id S1']
        >>> _scenario_problems("S1")
        ['not a list']
    """
    if not isinstance(value, list):
        return ["not a list"]
    if not value:
        return ["empty list"]
    problems: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, Mapping):
            problems.append(f"entry {index} is not a mapping")
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str) or _SCENARIO_ID.fullmatch(identifier) is None:
            problems.append(f"entry {index} has id {identifier!r}, not S<n>")
        elif identifier in seen:
            problems.append(f"duplicate id {identifier}")
        else:
            seen.add(identifier)
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            problems.append(f"entry {index} has no title")
        extra = sorted(str(key) for key in entry if key not in ("id", "title"))
        if extra:
            problems.append(f"entry {index} has unexpected keys {', '.join(extra)}")
    return problems


_HEADING = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<text>.+?)[ \t]*$")
_SCENARIO_TITLE = re.compile(r"^(?:Path[ \t]+[0-9]+|Scenario)[ \t]*:[ \t]*(?P<title>.+)$")


def _scenario_headings(text: str) -> list[str]:
    """Return the main-path and scenario headings of a requirement body.

    Every heading under ``### Main paths`` up to the next heading of level 1 to 3
    or the generated links block, plus every ``### Scenario…`` heading, in
    order. Fenced code is skipped.

    Examples:
        >>> _scenario_headings(
        ...     "## T\\n### Main paths\\n#### Path 1: Render\\n## User Need\\n### Scenario: Gone\\n"
        ... )
        ['Path 1: Render', 'Scenario: Gone']
    """
    _, body = extract_frontmatter(text)
    headings: list[str] = []
    in_paths = False
    fence: str | None = None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            if fence is None:
                fence = stripped[:3]
            elif stripped.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        if stripped.startswith("<!-- okf:links:start"):
            in_paths = False
            continue
        match = _HEADING.match(line)
        if match is None:
            continue
        level = len(match.group("hashes"))
        heading = match.group("text")
        if level == 3 and heading == "Main paths":
            in_paths = True
            continue
        if level <= 3:
            in_paths = False
        if in_paths or (level == 3 and heading.startswith("Scenario")):
            headings.append(heading)
    return headings


def _scenario_title(heading: str) -> str:
    """Return the scenario title a heading proposes.

    Examples:
        >>> _scenario_title("Path 2: The source is gone")
        'The source is gone'
        >>> _scenario_title("Export")
        'Export'
    """
    match = _SCENARIO_TITLE.match(heading)
    return match.group("title").strip() if match else heading


def _proposed_scenarios(text: str) -> list[dict[str, str]]:
    """Return the ``scenarios:`` entries a body's headings propose, ``S1`` first."""
    return [
        {"id": f"S{index}", "title": _scenario_title(heading)}
        for index, heading in enumerate(_scenario_headings(text), start=1)
    ]


def _scenario_coverage(
    requirements: Mapping[str, tuple[Path, dict[str, Any], str]],
    scan: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Evaluate test markers against declared scenarios (mode acceptance paths).

    Returns:
        Per StRS and SwRS ID: ``declared`` (ids or ``None``), ``tested`` and
        ``accepted`` (declared ids or ``"*"`` for a counting fragmentless
        marker), ``tested_files`` and ``accepted_files`` (files of counting
        markers); and the marker errors of Rule 4.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    keywords = config["markers"]
    coverage: dict[str, dict[str, Any]] = {}
    for identifier, (_, data, _) in requirements.items():
        if str(data.get("type")) in ("StRS", "SwRS"):
            coverage[identifier] = {
                "type": str(data.get("type")),
                "declared": _declared_scenarios(data),
                "tested": set(),
                "accepted": set(),
                "tested_files": set(),
                "accepted_files": set(),
            }
    errors: list[str] = []
    for marker in scan.get("scenario_markers", []):
        entry = coverage.get(marker["id"])
        if entry is None or (marker["marker"] == "accepts" and entry["type"] == "SwRS"):
            # Other tiers keep today's handling; @accepts_req on a SwRS is refused
            # by the SwRS schema (accepted_in_files).
            continue
        identifier = marker["id"]
        keyword = str(keywords[marker["marker"]])
        fragment = marker["fragment"]
        declared = entry["declared"]
        location = f"{marker['file']}:{marker['line']}"
        if fragment is not None and fragment not in (declared or []):
            known = (
                f"(declared: {', '.join(declared)})"
                if declared
                else f"({identifier} declares no scenarios:)"
            )
            errors.append(
                f"{location}: {keyword} {identifier}#{fragment} names no declared "
                f"scenario of {identifier} {known}"
            )
            continue
        if fragment is None and declared is not None:
            errors.append(
                f"{location}: {keyword} {identifier} has no scenario fragment; {identifier} "
                f"declares scenarios {', '.join(declared)}: write {keyword} "
                f"{identifier}#S<n> (this marker does not count)"
            )
            continue
        counter = "tested" if marker["marker"] == "tests" else "accepted"
        entry[counter].add(fragment or "*")
        entry[f"{counter}_files"].add(marker["file"])
    for entry in coverage.values():
        declared = entry["declared"]
        total = len(declared) if declared is not None else 0
        entry["paths"] = {
            "total": total,
            "tested": len(entry["tested"] - {"*"}),
            "accepted": len(entry["accepted"] - {"*"}),
        }
        for counter in ("tested", "accepted"):
            entry[f"is_{counter}"] = (
                bool(entry[counter]) if declared is None else 0 < total == len(entry[counter])
            )
            entry[f"{counter}_files"] = sorted(entry[f"{counter}_files"])
    return coverage, errors


def _schema_file(schemas_dir: Path, level: str) -> Path:
    """Return the schema file of a tier, or the schema folder when it is not found."""
    for path in sorted(schemas_dir.iterdir()):
        if path.is_file() and path.name.split(".schema.")[0].casefold() == level.casefold():
            return path
    return schemas_dir  # pragma: no cover - validation refuses a missing tier schema first


def _w003(file: Path, identifier: str, text: str) -> str:
    """Return the W003 finding of a live StRS that declares no ``scenarios:``."""
    headings = _scenario_headings(text)
    proposed = _proposed_scenarios(text) or [{"id": "S1", "title": "<main path title>"}]
    found = (
        "Headings found in its body: " + "; ".join(f'"{heading}"' for heading in headings)
        if headings
        else "No main-path or scenario heading was found in its body."
    )
    block = dump_yaml({"scenarios": proposed}).rstrip("\n")
    return (
        f"W003 {file}: {identifier} declares no scenarios: (its main paths). {found}\n"
        f"Add to its frontmatter, one entry per main path:\n{block}\n"
        "Edit the frontmatter only and leave the body as it is; on an approved StRS, "
        "log the change in the bundle's tiers/log.md naming the owner's agreement. "
        f"See {DECLARED_SCENARIOS_URL}"
    )


def _w004(file: Path, identifier: str, keyword: str, tests_keyword: str) -> str:
    """Return the W004 finding of a live StRS with no counting acceptance test."""
    return (
        f"W004 {file}: {identifier} has no acceptance test: no {keyword} marker that "
        f"counts names it. Mark the test closest to the final product that walks each "
        f"main path with {keyword} {identifier}#S<n> ({keyword} {identifier} while it "
        "declares no scenarios:). That test may be costly and run in the main-branch "
        "pipeline, beside cheaper "
        f"{tests_keyword} tests run on every pull or merge request. See {EXECUTION_COST_URL}"
    )


def _acceptance_paths_findings(
    root: Path,
    config: dict[str, Any],
    requirements: Mapping[str, tuple[Path, dict[str, Any], str]],
    composed: Mapping[str, dict[str, Any]],
    schemas_dir: Path,
) -> list[str]:
    """Return the findings of mode ``linked-swrs-and-acceptance-paths``."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    scan = marker_scan(root)
    coverage, findings = _scenario_coverage(requirements, scan, config)
    keywords = config["markers"]
    swrs_schema = composed.get("swrs")
    if swrs_schema is not None:
        probe = Draft202012Validator(swrs_schema).iter_errors({"accepted_in_files": ["probe"]})
        if not any(list(error.absolute_path)[:1] == ["accepted_in_files"] for error in probe):
            declaration = dump_yaml({"accepted_in_files": _swrs_accepted_in_files_schema()})
            findings.append(
                f"{_schema_file(schemas_dir, 'swrs')}: accepted_in_files is not refused; "
                "mode linked-swrs-and-acceptance-paths needs the okf-schema 0.18.0 "
                "declaration: update the bundle schema by adding under properties:\n"
                + declaration.rstrip("\n")
            )
    for identifier, (file, data, text) in requirements.items():
        entry = coverage.get(identifier)
        if entry is None:
            continue
        if "scenarios" in data:
            findings.extend(
                f"{file}: scenarios: {problem} (each entry is {{id: S<n>, title: <text>}}, "
                "ids unique)"
                for problem in _scenario_problems(data["scenarios"])
            )
        accepted_files = sorted(set(scan["accepted"].get(identifier, [])))
        schema = composed.get(entry["type"].casefold())
        if accepted_files and schema is not None:
            merged = {**data, "accepted_in_files": accepted_files}
            refusals = [
                str(error.schema.get("description") or error.message)
                for error in Draft202012Validator(schema).iter_errors(merged)
                if list(error.absolute_path)[:1] == ["accepted_in_files"]
            ]
            for refusal in dict.fromkeys(refusals):
                findings.extend(
                    f"{marker['file']}:{marker['line']}: {keywords['accepts']} "
                    f"{identifier}: {refusal}"
                    for marker in scan["scenario_markers"]
                    if marker["marker"] == "accepts" and marker["id"] == identifier
                )
        live = data.get(lifecycle_field(config)) not in _LIVE_EXCLUDED_LIFECYCLES
        if entry["type"] == "StRS" and live:
            if entry["declared"] is None:
                findings.append(_w003(file, identifier, text))
            if not entry["accepted"]:
                findings.append(
                    _w004(file, identifier, str(keywords["accepts"]), str(keywords["tests"]))
                )
    return findings


# @implements_req SwRS-OKFSCHEMA-OKFREQ-005
def validate_requirements(
    root: Path,
    prose: bool = False,
    *,
    check_links: bool = False,
    project_root: Path | None = None,
) -> list[str]:
    """Run deterministic structural and graph checks.

    Args:
        root:
            The bundle root.
        prose:
            When ``True``, also emit advisory ``W`` prose warnings. Advisory
            findings never make structural validation fail on their own.
        check_links:
            Enable opt-in ``x-okf-link`` target checking.
        project_root:
            Explicit project root for project-relative links. If unavailable,
            the containing Git root of each requirement document is used.

    Returns:
        A list of findings. Structural errors have no ``W`` or ``I`` code
        prefix. Schema files that yield no schema are reported as ``W17``
        (unparsable or not a mapping) or ``I1`` (empty, informational).

    .. versionchanged:: 0.18.0
        In mode ``linked-swrs-and-acceptance-paths``, also scan the markers and
        report malformed ``scenarios:``, test markers with a missing or unknown
        ``#S<n>`` fragment, ``@accepts_req`` markers the tier schema refuses
        (``accepted_in_files``), a SwRS schema that does not refuse
        ``accepted_in_files``, and the warnings ``W003`` (live StRS with no
        ``scenarios:``) and ``W004`` (live StRS with no counting acceptance
        test), with or without ``prose``.

    Examples:
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     validate_requirements(root)
        []
    """
    config = load_config(root)
    requirements = load_requirements(root)
    errors: list[str] = _ownership_config_findings(config)
    lifecycle_key = lifecycle_field(config)
    accepted_lifecycles = lifecycle_values(root, config)
    fields = (
        "type",
        "id",
        "uuid",
        "title",
        "description",
        "project",
        "scope",
        lifecycle_field(config),
        "origin",
        "tier",
    )
    schemas_dir = tiers_path(root) / "_schema"
    base_schema = schemas_dir / "base.schema.yaml"
    if not base_schema.is_file():
        raise RequirementError(f"missing requirement schema: {base_schema}")
    schemas, schema_diagnostics = load_schema_database_with_diagnostics(schemas_dir)
    schema_findings = [f"{item.code} {item.path}: {item.message}" for item in schema_diagnostics]
    normalized_schemas = {name.casefold(): schema for name, schema in schemas.items()}
    for level in ("StRS", "SwRS"):
        if level.casefold() not in normalized_schemas:
            problems = "; ".join(schema_findings)
            raise RequirementError(
                f"missing requirement schema for type {level}: {schemas_dir}"
                + (f" ({problems})" if problems else "")
            )
    errors.extend(schema_findings)
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-014
    reported: set[str] = set()
    for name, schema in sorted(schemas.items()):
        for problem in projection_problems(schema):
            if problem not in reported:
                reported.add(problem)
                errors.append(f"{schemas_dir / name}: {problem}")
    projections: dict[str, Any] = {}
    link_context = _FileLinkContext()
    retired = set(config["retired_ids"])
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
            projection = projections.setdefault(level, schema_projection(schema_data))
            if projection.status_field not in (None, "status"):
                expected = projected_status(data, projection)
                if "status" in data and data["status"] != expected:
                    errors.append(
                        f"{file}: status {data.get('status')} does not match "
                        f"{projection.status_field} {data.get(projection.status_field)} "
                        f"(expected {expected}); run okfreq update-coverage"
                    )
            if check_links:
                for diagnostic in check_file_links(
                    data,
                    schema_data,
                    file,
                    bundle_root=root,
                    project_root=project_root,
                    _context=link_context,
                ):
                    errors.append(f"{diagnostic.code} {file}: {diagnostic.message}")
        errors.extend(f"{file}: missing {field}" for field in fields if not data.get(field))
        if data.get("id") != identifier or _id_pattern(config).fullmatch(identifier) is None:
            errors.append(f"{file}: invalid ID")
        try:
            uuid.UUID(str(data.get("uuid")))
        except (ValueError, AttributeError, TypeError):
            errors.append(f"{file}: invalid UUID")
        if identifier in retired:
            errors.append(
                f"{file}: ID {identifier} is listed in retired_ids and must not be reused"
            )
        if data.get(lifecycle_key) not in accepted_lifecycles:
            errors.append(f"{file}: invalid {lifecycle_key}")
        errors.extend(_approval_findings(file, data, config, lifecycle_key))
        if data.get("type") not in config_tiers(config):
            errors.append(f"{file}: unconfigured tier {data.get('type')}")
        if data.get("annotation_exemption") is True and not data.get("exemption_reason"):
            errors.append(f"{file}: annotation exemption requires exemption_reason")
        level_config = config_tiers(config).get(str(data.get("type")), {})
        if level_config.get("derives_from") and not data.get("derives_from"):
            errors.append(f"{file}: {data.get('type')} requires derives_from")
        for parent in data.get("derives_from", []) or []:
            if (
                parent in requirements
                and level_config.get("derives_from")
                and requirements[parent][1].get("type") not in level_config["derives_from"]
            ):
                errors.append(f"{file}: invalid parent tier")
        if prose and len(str(data.get("description", "")).split()) < 3:
            errors.append(f"W001 {file}: description is unusually short")
    errors.extend(graph(root)["errors"])
    errors.extend(_relation_findings(requirements, lifecycle_key))
    if _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE:
        base = normalized_schemas.get("base") or normalized_schemas.get("base.schema")
        composed = {
            level: {
                **normalized_schemas[level],
                "allOf": [base, *normalized_schemas[level].get("allOf", [])[1:]],
            }
            for level in ("strs", "swrs")
        }
        errors.extend(_acceptance_paths_findings(root, config, requirements, composed, schemas_dir))
    errors.extend(_okf_findings(root))
    return errors


# okf-schema checks that requirement bundles cover otherwise: provenance is recorded
# by verified, relation lists stay in block style, and okfreq lint owns the indexes
# (lint --check reports a missing or stale one).
_OKF_IGNORED_CODES = frozenset({"W3", "W4", "W7"})


def _okf_findings(root: Path) -> list[str]:
    """Run the base OKF checks of ``okf-schema validate`` on the tiers folder."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-014
    report = validate_okf_bundle(tiers_path(root))
    return [
        f"{finding.code} {finding.path}: {finding.message}"
        for finding in [*report.errors, *report.warnings, *report.infos]
        if finding.code not in _OKF_IGNORED_CODES
    ]


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

    .. versionchanged:: 0.15.0
        Also maintains ``supersedes``, the inverse of ``superseded_by``, when it
        is listed in ``generated_fields``.

    .. versionchanged:: 0.17.0
        Also maintains the OKF projection: ``status`` and ``verified`` when they
        are listed in ``generated_fields``, and the generated Links section of
        every field whose schema carries a ``link-projection``.

    .. versionchanged:: 0.18.0
        Maintains ``accepted_in_files``. In mode
        ``linked-swrs-and-acceptance-paths``, writes on a StRS the files of its
        counting ``@tests_req`` (``tested_in_files``) and ``@accepts_req``
        (``accepted_in_files``) markers, and lists on a SwRS only the files of
        its counting ``@tests_req`` markers. In the other modes, removes
        ``tested_in_files`` and ``accepted_in_files`` from a StRS.

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
    supersedes = _supersession_reverse(requirements)
    projector = requirement_projector(root, config)
    acceptance_paths = _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE
    scenario_coverage = (
        _scenario_coverage(requirements, scan, config)[0] if acceptance_paths else {}
    )
    changed: list[str] = []
    for identifier, (file, _, text) in requirements.items():
        available_updates: dict[str, Any] = {"derived_by": sorted(reverse[identifier])}
        if supersedes[identifier] or "supersedes" in requirements[identifier][1]:
            # Written only where it has a value (or is already present), so a bundle
            # that never supersedes anything gains no empty ``supersedes: []`` lines.
            available_updates["supersedes"] = supersedes[identifier]
        authored = requirements[identifier][1]
        _, owner = owner_policy(
            config,
            str(authored.get("tier") or authored.get("type") or ""),
            str(authored.get("scope") or ""),
        )
        # None removes a stale value once no owner is configured any more.
        available_updates["default_owner_email"] = owner
        level = str(requirements[identifier][1].get("type"))
        if level == "SwRS":
            available_updates.update(
                {
                    "implemented_in_files": sorted(scan["implemented"].get(identifier, [])),
                    "tested_in_files": sorted(scan["tested"].get(identifier, [])),
                }
            )
            if acceptance_paths:
                available_updates["tested_in_files"] = scenario_coverage[identifier]["tested_files"]
        elif level == "StRS" and acceptance_paths:
            available_updates["tested_in_files"] = scenario_coverage[identifier]["tested_files"]
            available_updates["accepted_in_files"] = scenario_coverage[identifier]["accepted_files"]
        updates = {
            key: available_updates[key] for key in configured_fields if key in available_updates
        }
        rendered = _render_frontmatter(text, updates)
        if level == "StRS":
            removed = (
                ("implemented_in_files",)
                if acceptance_paths
                else ("implemented_in_files", "tested_in_files", "accepted_in_files")
            )
            frontmatter, body = extract_frontmatter(rendered)
            if frontmatter is not None:
                data = make_yaml().load(frontmatter)
                if isinstance(data, dict):
                    for key in removed:
                        data.pop(key, None)
                    rendered = f"---\n{dump_yaml(data)}---\n{body}"
        try:
            rendered = projector.project(file, rendered)
        except ProjectionError as exc:
            raise RequirementError(f"{file}: {exc}") from exc
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

    .. versionchanged:: 0.18.0
        ``format_version`` is 2. In mode ``linked-swrs-and-acceptance-paths``,
        only counting markers feed the coverage; each StRS gains ``paths``,
        ``tested``, ``accepted``, ``tests`` and ``acceptance_tests``, each SwRS
        that declares transitions gains ``transitions``, and the aggregate
        ``stakeholder_test_coverage`` gains ``paths``.

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
    errors = [
        item
        for item in validate_requirements(root)
        if not item.startswith("W") and not is_info_finding(item)
    ]
    config = load_config(root)
    strs_test_coverage_mode = _strs_test_coverage_mode(config)
    acceptance_paths = strs_test_coverage_mode == ACCEPTANCE_PATHS_MODE
    scenario_coverage: dict[str, dict[str, Any]] = {}
    if acceptance_paths:
        # Only counting markers feed the report: a SwRS lists the files of its
        # counting @tests_req markers, a StRS the files of its counting @accepts_req.
        scenario_coverage = _scenario_coverage(requirements, trace, config)[0]
        trace = dict(trace)
        trace["tested"] = {
            identifier: (
                scenario_coverage[identifier]["tested_files"]
                if identifier in scenario_coverage
                else files
            )
            for identifier, files in trace["tested"].items()
        }
        trace["tested"] = {key: value for key, value in trace["tested"].items() if value}
        trace["validation_tests"] = {
            identifier: entry["accepted_files"]
            for identifier, entry in scenario_coverage.items()
            if entry["type"] == "StRS" and entry["accepted_files"]
        }

    def is_tested(identifier: str) -> bool:
        """Return whether a leaf requirement is test-covered (Rule 5 in the new mode)."""
        entry = scenario_coverage.get(identifier)
        if entry is not None and entry["type"] == "SwRS":
            return bool(entry["is_tested"])
        return identifier in trace["tested"]

    lifecycle: dict[str, int] = {}
    for _, data, _ in requirements.values():
        value = str(data.get(lifecycle_field(config), "invalid"))
        lifecycle[value] = lifecycle.get(value, 0) + 1
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
        if not is_tested(identifier):
            missing_tests.append(identifier)
    coverage_targets = {
        identifier: (file, data, text)
        for identifier, (file, data, text) in requirements.items()
        if data.get("type") in leaf_levels and data.get("annotation_exemption") is not True
    }
    implemented = set(trace["implemented"]) & set(coverage_targets)
    tested = {identifier for identifier in coverage_targets if is_tested(identifier)}
    fully_traceable = implemented & tested
    stakeholder_coverage: dict[str, dict[str, Any]] = {}
    for identifier, (_, data, _) in requirements.items():
        if data.get("type") != "StRS":
            continue
        linked_swrs = sorted(
            child
            for child in graph_result["derived_by"].get(identifier, [])
            if child in requirements and requirements[child][1].get("type") == "SwRS"
        )
        linked_swrs_report = [
            {"id": child, "status": "covered" if child in tested else "missing"}
            for child in linked_swrs
        ]
        validation_files = trace["validation_tests"].get(identifier, [])
        linked_swrs_covered = bool(linked_swrs) and all(child in tested for child in linked_swrs)
        validation_defined = bool(validation_files)
        if acceptance_paths:
            covered = linked_swrs_covered and scenario_coverage[identifier]["is_accepted"]
        else:
            covered = linked_swrs_covered and (
                strs_test_coverage_mode == "linked-swrs" or validation_defined
            )
        stakeholder_coverage[identifier] = {
            "status": "covered" if covered else "missing",
            "mode": strs_test_coverage_mode,
            "linked_swrs": linked_swrs_report,
            "validation_tests": {
                "status": "defined" if validation_defined else "missing",
                "files": validation_files,
                "count": len(validation_files),
            },
        }
        if acceptance_paths:
            entry = scenario_coverage[identifier]
            stakeholder_coverage[identifier].update(
                {
                    "paths": entry["paths"],
                    "tested": entry["is_tested"],
                    "accepted": entry["is_accepted"],
                    "tests": {
                        "status": "defined" if entry["tested_files"] else "missing",
                        "files": entry["tested_files"],
                        "count": len(entry["tested_files"]),
                    },
                    "acceptance_tests": dict(stakeholder_coverage[identifier]["validation_tests"]),
                }
            )

    stakeholder_total = len(stakeholder_coverage)
    stakeholder_covered = sum(
        coverage["status"] == "covered" for coverage in stakeholder_coverage.values()
    )

    def percentage(count: int, total: int) -> float:
        """Return a percentage rounded to two decimal places."""
        return round((count / total) * 100, 2) if total else 100.0

    requirement_records: list[dict[str, Any]] = []
    for identifier, (file, data, text) in sorted(requirements.items()):
        source_links = trace["implemented"].get(identifier, [])
        test_links = trace["tested"].get(identifier, [])
        coverage_target = identifier in coverage_targets
        stakeholder_details = stakeholder_coverage.get(identifier)
        implementation = {
            "status": "not_applicable"
            if stakeholder_details
            else ("covered" if source_links else "missing"),
            "files": [] if stakeholder_details else source_links,
            "count": 0 if stakeholder_details else len(source_links),
        }
        tests = {
            "status": stakeholder_details["status"]
            if stakeholder_details
            else ("covered" if is_tested(identifier) else "missing"),
            "files": (
                stakeholder_details["validation_tests"]["files"]
                if stakeholder_details
                else test_links
            ),
            "count": (
                stakeholder_details["validation_tests"]["count"]
                if stakeholder_details
                else len(test_links)
            ),
        }
        record: dict[str, Any] = {
            "id": identifier,
            "path": file.relative_to(project_path(root)).as_posix(),
            "text": text,
            "frontmatter": data,
            "scope": data.get("scope"),
            "tier": data.get("tier", data.get("type")),
            "derives_from": data.get("derives_from", []) or [],
            "superseded_by": graph_result["superseded_by"][identifier],
            "supersedes": graph_result["supersedes"][identifier],
            "relates_to": graph_result["relates_to"][identifier],
            "coverage_target": coverage_target,
            "implementation": implementation,
            "tests": tests,
            "execution": {"status": "not_collected", "results": []},
            "diagnostics": {
                "exempted": data.get("annotation_exemption") is True,
                "errors": [error for error in errors if identifier in error],
            },
        }
        if stakeholder_details:
            record["stakeholder_test_coverage"] = stakeholder_details
        swrs_entry = scenario_coverage.get(identifier)
        if swrs_entry and swrs_entry["type"] == "SwRS" and swrs_entry["declared"] is not None:
            record["transitions"] = {
                "tested": [item for item in swrs_entry["declared"] if item in swrs_entry["tested"]],
                "missing": [
                    item for item in swrs_entry["declared"] if item not in swrs_entry["tested"]
                ],
            }
        requirement_records.append(record)

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
    stakeholder_paths = {
        counter: sum(
            coverage["paths"][counter]
            for coverage in stakeholder_coverage.values()
            if "paths" in coverage
        )
        for counter in ("total", "tested", "accepted")
    }
    stakeholder_aggregate: dict[str, Any] = {
        "mode": strs_test_coverage_mode,
        "requirements": stakeholder_total,
        "covered": stakeholder_covered,
        "coverage_percent": percentage(stakeholder_covered, stakeholder_total),
    }
    if acceptance_paths:
        stakeholder_aggregate["paths"] = stakeholder_paths
    detailed = {
        "report_format": "okfreq-requirements-report",
        "format_version": 2,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generated_by": {
            "tool": "okfreq",
            "version": package_version,
            "command": "okfreq generate-report",
        },
        "scan": {
            "source_and_test_directories": config.get("scopes", {}),
        },
        "execution_evidence": {
            "status": "not_collected",
            "result_files": [],
            "description": "Only linked test markers were scanned.",
        },
        "coverage_definition": {
            "population": "configured leaf requirements without annotation exemptions",
            "source": "at least one @implements_req marker for each SwRS coverage target",
            "tests": (
                "every declared transition has a test marker with its fragment, or at "
                "least one test marker when none is declared"
                if acceptance_paths
                else "at least one @tests_req marker for each SwRS coverage target"
            ),
            "combined": "at least one source marker and one test marker",
            "stakeholder_tests": STRS_TEST_COVERAGE_DESCRIPTIONS[strs_test_coverage_mode],
            "stakeholder_test_coverage_mode": strs_test_coverage_mode,
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
        "stakeholder_test_coverage": stakeholder_aggregate,
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
            "validation_tests": trace["validation_tests"],
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
                "validation_tests": trace["validation_tests"],
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

    .. versionchanged:: 0.18.0
        ``format_version`` is 2; declares the optional fields of mode
        ``linked-swrs-and-acceptance-paths`` (``paths``, ``tested``,
        ``accepted``, ``tests``, ``acceptance_tests`` and ``transitions``).
    """
    files_linkage = {
        "type": "object",
        "required": ["status", "files", "count"],
        "properties": {
            "status": {"enum": ["defined", "missing"]},
            "files": {"type": "array", "items": {"type": "string"}},
            "count": {"type": "integer", "minimum": 0},
        },
    }
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
            "scan",
            "execution_evidence",
            "coverage_definition",
            "totals",
            "stakeholder_test_coverage",
            "scopes",
            "requirements",
        ],
        "properties": {
            "report_format": {"const": "okfreq-requirements-report"},
            "format_version": {"type": "integer", "const": 2},
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
            "coverage_definition": {
                "type": "object",
                "properties": {
                    "stakeholder_test_coverage_mode": {"enum": list(STRS_TEST_COVERAGE_MODES)},
                    "stakeholder_tests": {"type": "string"},
                },
            },
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
            "stakeholder_test_coverage": {
                "type": "object",
                "required": ["mode", "requirements", "covered", "coverage_percent"],
                "properties": {
                    "mode": {"enum": list(STRS_TEST_COVERAGE_MODES)},
                    "requirements": {"type": "integer", "minimum": 0},
                    "covered": {"type": "integer", "minimum": 0},
                    "coverage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    "paths": {"$ref": "#/$defs/paths"},
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
                    "superseded_by": {"type": "array", "items": {"type": "string"}},
                    "supersedes": {"type": "array", "items": {"type": "string"}},
                    "relates_to": {"type": "array", "items": {"type": "string"}},
                    "coverage_target": {"type": "boolean"},
                    "implementation": {"$ref": "#/$defs/linkage"},
                    "tests": {"$ref": "#/$defs/linkage"},
                    "stakeholder_test_coverage": {
                        "$ref": "#/$defs/stakeholder_requirement_coverage"
                    },
                    "transitions": {
                        "type": "object",
                        "required": ["tested", "missing"],
                        "properties": {
                            "tested": {"type": "array", "items": {"type": "string"}},
                            "missing": {"type": "array", "items": {"type": "string"}},
                        },
                    },
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
                    "status": {"enum": ["covered", "missing", "not_applicable"]},
                    "files": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer", "minimum": 0},
                },
            },
            "stakeholder_requirement_coverage": {
                "type": "object",
                "required": ["status", "mode", "linked_swrs", "validation_tests"],
                "properties": {
                    "status": {"enum": ["covered", "missing"]},
                    "mode": {"enum": list(STRS_TEST_COVERAGE_MODES)},
                    "linked_swrs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "status"],
                            "properties": {
                                "id": {"type": "string"},
                                "status": {"enum": ["covered", "missing"]},
                            },
                        },
                    },
                    "validation_tests": files_linkage,
                    "paths": {"$ref": "#/$defs/paths"},
                    "tested": {"type": "boolean"},
                    "accepted": {"type": "boolean"},
                    "tests": files_linkage,
                    "acceptance_tests": files_linkage,
                },
            },
            "paths": {
                "type": "object",
                "required": ["total", "tested", "accepted"],
                "properties": {
                    "total": {"type": "integer", "minimum": 0},
                    "tested": {"type": "integer", "minimum": 0},
                    "accepted": {"type": "integer", "minimum": 0},
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

    .. versionchanged:: 0.18.0
        In mode ``linked-swrs-and-acceptance-paths``, adds the StRS paths line,
        the ``Tested`` and ``Accepted`` StRS columns and the ``Missing
        transitions`` SwRS column.
    """

    def status_emoji(status: str) -> str:
        """Return the compact status marker used in the Markdown summary."""
        return {"covered": "✅", "missing": "❌"}.get(status, "⚪")

    data = report(root)
    totals = data["totals"]
    stakeholder_totals = data["stakeholder_test_coverage"]
    lines = [
        "# Requirements report",
        "",
        f"Generated: {data['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Requirements: {totals['requirements']} "
        f"({totals['coverage_target_requirements']} coverage targets)",
        f"- SwRS source coverage: {totals['source_coverage_percent']}% "
        f"({totals['implemented']}/{totals['coverage_target_requirements']})",
        f"- SwRS test-link coverage: {totals['test_coverage_percent']}% "
        f"({totals['tested']}/{totals['coverage_target_requirements']})",
        f"- StRS test coverage: {stakeholder_totals['coverage_percent']}% "
        f"({stakeholder_totals['covered']}/{stakeholder_totals['requirements']})",
        f"- Combined traceability: {totals['combined_coverage_percent']}% "
        f"({totals['fully_traceable']}/{totals['coverage_target_requirements']})",
        "",
        "## By scope",
        "",
        "| Scope | Requirements | Source | Tests | Combined |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    acceptance_paths = stakeholder_totals["mode"] == ACCEPTANCE_PATHS_MODE
    if acceptance_paths:
        paths = stakeholder_totals["paths"]
        lines.insert(
            lines.index("## By scope") - 2,
            f"- StRS paths: tested {paths['tested']}/{paths['total']}, "
            f"accepted {paths['accepted']}/{paths['total']}",
        )

    def path_cell(coverage: Mapping[str, Any], counter: str) -> str:
        """Return the Tested or Accepted cell of a StRS row."""
        paths = coverage["paths"]
        done = "✅ " if coverage[counter] else ""
        if not paths["total"]:
            return f"{'✅' if coverage[counter] else '❌'} no paths"
        return f"{done}{paths[counter]}/{paths['total']}"

    for scope, values in sorted(data["scopes"].items()):
        lines.append(
            f"| {scope} | {values['requirements']} | {values['source_coverage_percent']}% | "
            f"{values['test_coverage_percent']}% | {values['combined_coverage_percent']}% |"
        )
    requirements = sorted(
        data["requirements"],
        key=lambda requirement: (
            str(requirement["scope"]).casefold(),
            str(requirement["tier"]).casefold(),
            requirement["id"].casefold(),
        ),
    )
    stakeholder_requirements = [
        requirement for requirement in requirements if requirement["tier"] == "StRS"
    ]
    lines.extend(
        [
            "",
            "## By stakeholder requirement",
            "",
            "| Scope | Tier | ID | Name | Tests |"
            + (" Tested | Accepted |" if acceptance_paths else ""),
            "| --- | --- | --- | --- | --- |" + (" --- | --- |" if acceptance_paths else ""),
        ]
    )
    for requirement in stakeholder_requirements:
        name = str(requirement["frontmatter"].get("title", requirement["id"]))
        row = (
            f"| {requirement['scope']} | {requirement['tier']} | "
            f"{requirement['id']} | {name} | "
            f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
        )
        if acceptance_paths:
            coverage = requirement["stakeholder_test_coverage"]
            row += f" {path_cell(coverage, 'tested')} | {path_cell(coverage, 'accepted')} |"
        lines.append(row)
    mode = stakeholder_totals["mode"]
    coverage_description = STRS_TEST_COVERAGE_DESCRIPTIONS[mode]
    coverage_sentence = coverage_description[0].lower() + coverage_description[1:]
    coverage_note = f"*Note: current configuration is that {coverage_sentence}*"
    lines.extend(
        [
            "",
            coverage_note,
            "",
            "## By software requirement",
            "",
            "| Scope | Tier | ID | Name | Source | Tests |"
            + (" Missing transitions |" if acceptance_paths else ""),
            "| --- | --- | --- | --- | --- | --- |" + (" --- |" if acceptance_paths else ""),
        ]
    )
    for requirement in (item for item in requirements if item["coverage_target"]):
        name = str(requirement["frontmatter"].get("title", requirement["id"]))
        row = (
            f"| {requirement['scope']} | {requirement['tier']} | "
            f"{requirement['id']} | {name} | "
            f"{status_emoji(requirement['implementation']['status'])} "
            f"{requirement['implementation']['status']} | "
            f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
        )
        if acceptance_paths:
            missing = requirement.get("transitions", {}).get("missing", [])
            row += f" {', '.join(missing) or '—'} |"
        lines.append(row)
    _atomic_write(destination, "\n".join(lines) + "\n")
