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
  justified agreement, recorded in approved_by and approved_at. An edit that
  only adds declared scenarios: in frontmatter (body intact) leaves approved_by
  and approved_at unchanged unless the owner gives a new approval, and is logged
  in tiers/log.md naming the owner's agreement. Allowed only where approval_lock
  is true for the requirement's tier and scope.
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
STRS_TEST_COVERAGE_MODES = (
    "linked-swrs",
    "linked-swrs-and-validation-test",
    "linked-swrs-and-acceptance-paths",
)
ACCEPTANCE_PATHS_MODE = "linked-swrs-and-acceptance-paths"
_SCENARIO_ID_PATTERN = re.compile(r"^S[1-9][0-9]*$")
_W003_DOC_URL = (
    "https://okf-schema.readthedocs.io/en/stable/reference/okfreq-frontmatter.html"
    "#okfreq-declared-scenarios"
)
_W004_DOC_URL = (
    "https://okf-schema.readthedocs.io/en/stable/explanation/okfreq-acceptance-paths.html"
    "#okfreq-execution-cost"
)
_SWRS_ACCEPTED_IN_FILES_DESCRIPTION = (
    "Never present. @accepts_req names a StRS main path; mark a SwRS test "
    "with @tests_req <SwRS-ID>#S<n>."
)
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
    "linked-swrs-and-acceptance-paths": (
        "An StRS is considered as covered when it is linked to at least one SwRS, every "
        "linked SwRS is test-covered or individually exempted with a non-blank "
        "exemption_reason, and either every declared main path has an acceptance test "
        "marker (or at least one fragmentless acceptance test marker when no paths are "
        "declared) or the whole StRS carries a justified acceptance_exemption; tested "
        "paths are reported separately."
    ),
}

_EARS_PLACEHOLDER = "<"
_USER_NEED_PLACEHOLDER = "<stakeholder need in the stakeholder's language>"

_STRS_BODY = """## {title}

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

_STRS_BODY_WITH_PATHS = """## {title}

### Normative behavior

{description}

### Main paths

#### Path S1: <main path title>

1. <first step the stakeholder observes>
2. <next step, up to the observable outcome>

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

_SWRS_BODY_WITH_SCENARIO_IDS = """## {title}

### Normative behavior

{description}

### Scenario S1: <nominal behavior>

- GIVEN <precondition and relevant inputs>
- WHEN <trigger or action>
- THEN <single observable, verifiable outcome>

### Scenario S2: <boundary or failure behavior>

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
    title: str | None = None,
    include_scenario_ids: bool = False,
) -> str:
    """Return the EARS scaffold for a configured tier.

    .. versionchanged:: 0.13.0
        Use the requirement title as the first Markdown heading.

    .. versionchanged:: 0.18.0
        Accept ``include_scenario_ids`` to emit ``### Main paths`` with
        ``#### Path S1:`` on StRS and ``### Scenario S1:`` / ``S2:`` on SwRS
        in ``linked-swrs-and-acceptance-paths`` mode.

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
        include_scenario_ids:
            When ``True``, emit explicit ``S<n>`` scenario headings (and a
            ``### Main paths`` section for StRS).

    Returns:
        A Markdown body template for the tier.

    Examples:
        >>> body = ears_body("SwRS", "The tool SHALL validate the bundle.")
        >>> "### Scenario:" in body
        True
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    if level.lower().startswith("sw"):
        template = _SWRS_BODY_WITH_SCENARIO_IDS if include_scenario_ids else _SWRS_BODY
        return template.format(
            title=title if title is not None else description, description=description
        )
    template = _STRS_BODY_WITH_PATHS if include_scenario_ids else _STRS_BODY
    return template.format(
        title=title if title is not None else description,
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

    .. versionchanged:: 0.18.0
        Write ``markers.accepts`` and ``accepted_in_files`` in ``config.yml``,
        declare ``scenarios`` in ``base.schema.yaml``, declare
        ``tested_in_files``, ``accepted_in_files`` and authored acceptance
        waiver fields in ``strs.schema.yaml``, and refuse ``accepted_in_files``
        in ``swrs.schema.yaml``.

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
                "scenarios": {
                    "type": "array",
                    "minItems": 1,
                    "description": (
                        "Authored main paths (StRS) or transition scenarios (SwRS). "
                        "Each id S<n> is stable and never reused, even after its "
                        "scenario is removed. Test markers name one with a #S<n> fragment."
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
                },
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
        extra_clauses: list[dict[str, Any]] = []
        if tier == "StRS":
            properties["user_need"] = {
                "type": "string",
                "minLength": 1,
                "description": "The stakeholder need this requirement formalizes.",
            }
            required.append("user_need")
            properties["acceptance_exemption"] = {
                "type": "boolean",
                "description": (
                    "True when automated acceptance testing is not possible for the "
                    "whole StRS; requires a justified acceptance_exemption_reason."
                ),
            }
            properties["acceptance_exemption_reason"] = {
                "type": "string",
                "description": (
                    "Explicit rationale explaining why automated acceptance testing is "
                    "not possible for this StRS. Required and non-empty when "
                    "acceptance_exemption is true."
                ),
            }
            properties["tested_in_files"] = {
                "type": "array",
                "description": "Generated test paths.",
                "items": {
                    "type": "string",
                    "x-okf-link": {
                        "resolution": "project-relative",
                        "syntax": "plain",
                        "basename_marker": "@tests_req",
                        "id_marker": "id",
                        "show_line_number": True,
                    },
                },
            }
            properties["accepted_in_files"] = {
                "type": "array",
                "description": (
                    "Generated acceptance-test paths: files of @accepts_req markers "
                    "that count, in mode linked-swrs-and-acceptance-paths."
                ),
                "items": {
                    "type": "string",
                    "x-okf-link": {
                        "resolution": "project-relative",
                        "syntax": "plain",
                        "basename_marker": "@accepts_req",
                        "id_marker": "id",
                        "show_line_number": True,
                    },
                },
            }
            extra_clauses.append(
                {
                    "if": {
                        "properties": {"acceptance_exemption": {"const": True}},
                        "required": ["acceptance_exemption"],
                    },
                    "then": {
                        "required": ["acceptance_exemption_reason"],
                        "properties": {
                            "acceptance_exemption_reason": {
                                "type": "string",
                                "minLength": 1,
                            }
                        },
                    },
                }
            )
        else:
            properties["annotation_exemption"] = {
                "type": "boolean",
                "description": "True when this requirement is exempt from coverage annotations.",
            }
            required.append("annotation_exemption")
            properties["implemented_in_files"] = {
                "type": "array",
                "description": "Generated source paths.",
                "items": {
                    "type": "string",
                    "x-okf-link": {
                        "resolution": "project-relative",
                        "syntax": "plain",
                        "basename_marker": "@implements_req",
                        "id_marker": "id",
                        "show_line_number": True,
                    },
                },
            }
            properties["tested_in_files"] = {
                "type": "array",
                "description": "Generated test paths.",
                "items": {
                    "type": "string",
                    "x-okf-link": {
                        "resolution": "project-relative",
                        "syntax": "plain",
                        "basename_marker": "@tests_req",
                        "id_marker": "id",
                        "show_line_number": True,
                    },
                },
            }
            properties["accepted_in_files"] = {
                "type": "array",
                "maxItems": 0,
                "description": _SWRS_ACCEPTED_IN_FILES_DESCRIPTION,
            }
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{level}.schema.yaml",
            "title": f"okfreq {level} requirement profile",
            "description": (
                "StRS records stakeholder intent and carries no implementation fields; "
                "in mode linked-swrs-and-acceptance-paths it carries the generated "
                "tested_in_files and accepted_in_files. Stakeholder test coverage is "
                "computed from linked SwRS according to configuration."
                if tier == "StRS"
                else "SwRS defines observable software behavior and its traceability."
            ),
            "allOf": [
                {"$ref": "base.schema.yaml"},
                {"type": "object", "properties": properties, "required": required},
                *extra_clauses,
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
    r"[A-Za-z][A-Za-z0-9_-]*(?:#S[0-9]+)?[ \t]*(?:-->|\*/)?[ \t]*\r?\n(?:[ \t]*\r?\n)?",
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

    .. versionchanged:: 0.18.0
        Default ``markers.accepts`` to ``@accepts_req``, reject duplicate
        marker keywords, accept ``linked-swrs-and-acceptance-paths`` as
        ``strs_test_coverage_mode``, and include ``accepted_in_files`` in
        default ``generated_fields``.

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
    markers = data.setdefault(
        "markers",
        {
            "implements": "@implements_req",
            "tests": "@tests_req",
            "accepts": "@accepts_req",
        },
    )
    if isinstance(markers, dict):
        markers.setdefault("implements", "@implements_req")
        markers.setdefault("tests", "@tests_req")
        markers.setdefault("accepts", "@accepts_req")
        markers.setdefault("id_pattern", DEFAULT_ID_PATTERN)
        _validate_marker_keywords(markers)
    lifecycle = data.setdefault("lifecycle", {})
    if "values" not in lifecycle:
        lifecycle.setdefault("field", DEFAULT_LIFECYCLE_FIELD)
    data.setdefault("id_policy", "scope-prefix-sequence")
    data.setdefault("generated_fields", sorted(SUPPORTED_GENERATED_FIELDS))
    data.setdefault("strs_test_coverage_mode", "linked-swrs")
    _strs_test_coverage_mode(data)
    data["retired_ids"] = _retired_ids(data)
    return data


def _validate_marker_keywords(markers: dict[str, Any]) -> None:
    """Reject configurations that reuse one keyword for two marker kinds."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    pairs = (("implements", "tests"), ("implements", "accepts"), ("tests", "accepts"))
    for first, second in pairs:
        first_kw = str(markers.get(first, ""))
        second_kw = str(markers.get(second, ""))
        if first_kw and first_kw == second_kw:
            raise RequirementError(
                f"markers.{first} and markers.{second} use the same keyword {first_kw}"
            )


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
        In ``linked-swrs-and-acceptance-paths`` mode, pre-fill ``scenarios:``
        from the generated template headings and include ``### Main paths`` on
        StRS templates.

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
    use_acceptance_paths = _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE
    body = ears_body(
        level,
        description,
        user_need=user_need,
        title=title,
        include_scenario_ids=use_acceptance_paths,
    )
    if use_acceptance_paths:
        headings = _scenario_headings(f"---\nid: {identifier}\n---\n\n{body}")
        if headings:
            data["scenarios"] = [{"id": sid, "title": stitle} for sid, stitle, _ in headings]
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

    .. versionchanged:: 0.18.0
        Refuse retirement when an ``@accepts_req`` (configured ``markers.accepts``)
        marker references the ID, in every coverage mode.

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
            source, test, or acceptance marker still references it. Nothing is changed.

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
        Read ``markers.accepts`` (default ``@accepts_req``) in ``test_dirs`` and
        capture optional ``#S<n>`` scenario fragments; add ``accepted`` and
        ``scenario_markers`` to the returned mapping.

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
        ['accepted', 'duplicates', 'implemented', 'missing_ids', 'non_leaf',
         'scenario_markers', 'tested', 'validation_tests', 'warnings']
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-003
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    config = load_config(root)
    project = project_path(root)
    markers = config["markers"]
    implements = str(markers.get("implements", "@implements_req"))
    tests = str(markers.get("tests", "@tests_req"))
    accepts = str(markers.get("accepts", "@accepts_req"))
    configured_id = _id_pattern(config)
    embedded_id_pattern = configured_id.pattern.removeprefix("^").removesuffix("$")
    pattern = re.compile(
        rf"(?m)^\s*(?:(?:#|//|/\*|\*|<!--)\s*)?"
        rf"(?P<marker>{re.escape(implements)}|{re.escape(tests)}|{re.escape(accepts)})\s+"
        rf"(?P<identifier>{embedded_id_pattern})"
        rf"(?:#(?P<fragment>S[0-9]+)(?![A-Za-z0-9_-]))?"
    )
    result: dict[str, Any] = {
        "implemented": {},
        "tested": {},
        "accepted": {},
        "validation_tests": {},
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
    seen_scenario_markers: set[tuple[str, str, str | None, str]] = set()
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
                        marker = match.group("marker")
                        identifier = match.group("identifier")
                        fragment = match.group("fragment")
                        if _kind == "implemented" and marker != implements:
                            continue
                        if _kind == "tested" and marker not in (tests, accepts):
                            continue
                        relative = file.relative_to(project).as_posix()
                        if identifier not in requirements:
                            result["missing_ids"].append(identifier)
                            continue
                        if _kind == "tested":
                            marker_kind = "tests" if marker == tests else "accepts"
                            scenario_key = (marker_kind, identifier, fragment, relative)
                            if scenario_key not in seen_scenario_markers:
                                seen_scenario_markers.add(scenario_key)
                                line = text.count("\n", 0, match.start()) + 1
                                result["scenario_markers"].append(
                                    {
                                        "marker": marker_kind,
                                        "id": identifier,
                                        "fragment": fragment,
                                        "file": relative,
                                        "line": line,
                                    }
                                )
                            if marker == accepts:
                                occurrence = ("accepted", identifier, relative)
                                if occurrence not in seen_markers:
                                    seen_markers.add(occurrence)
                                    result["accepted"].setdefault(identifier, []).append(relative)
                                continue
                        target = "implemented" if marker == implements else "tested"
                        # Requirement reports use portable project-relative paths
                        # regardless of the host platform.
                        occurrence = (target, identifier, relative)
                        if occurrence in seen_markers:
                            # Several tests or code points in one file may carry
                            # the same ID; the file is listed once.
                            continue
                        seen_markers.add(occurrence)
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


def _declared_scenarios(data: dict[str, Any]) -> tuple[list[tuple[str, str]], list[str]]:
    """Parse and validate the authored ``scenarios:`` frontmatter field.

    Returns:
        A tuple ``(valid_entries, problems)`` where ``valid_entries`` is a list
        of ``(id, title)`` pairs and ``problems`` lists structural errors.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    if "scenarios" not in data:
        return [], []
    raw = data["scenarios"]
    if not isinstance(raw, list) or not raw:
        return [], ["must be a non-empty list"]
    valid: list[tuple[str, str]] = []
    problems: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            problems.append(f"entry {index} must be a mapping")
            continue
        extra = sorted(set(entry.keys()) - {"id", "title"})
        if extra:
            problems.append(f"entry {index} has unexpected keys: {', '.join(extra)}")
        sid = entry.get("id")
        title = entry.get("title")
        sid_str: str | None = None
        if not isinstance(sid, str) or _SCENARIO_ID_PATTERN.fullmatch(sid) is None:
            problems.append(f"entry {index} has invalid id {sid!r}")
        elif sid in seen_ids:
            problems.append(f"duplicate id {sid}")
        else:
            seen_ids.add(sid)
            sid_str = sid
        title_str: str | None = None
        if not isinstance(title, str) or not title.strip():
            problems.append(f"entry {index} must have a non-empty title")
        else:
            title_str = title
        if sid_str is not None and title_str is not None and not extra:
            valid.append((sid_str, title_str))
    return valid, problems


_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_PATH_EXPLICIT_RE = re.compile(r"^Path\s+(S[1-9][0-9]*)\s*:\s*(.+)$", flags=re.IGNORECASE)
_PATH_LEGACY_RE = re.compile(r"^Path\s+\d+\s*:\s*(.+)$", flags=re.IGNORECASE)
_SCENARIO_EXPLICIT_RE = re.compile(r"^Scenario\s+(S[1-9][0-9]*)\s*:\s*(.+)$", flags=re.IGNORECASE)
_SCENARIO_LEGACY_RE = re.compile(r"^Scenario\s*:\s*(.+)$", flags=re.IGNORECASE)


def _scenario_headings(text: str) -> list[tuple[str, str, str]]:
    """Extract scenario IDs, titles, and raw headings from a requirement body.

    Reads every heading under ``### Main paths`` (until the next heading of
    level 1 to 3 or ``<!-- okf:links:start -->``) plus every ``### Scenario``
    heading. Preserves explicit ``S<n>`` IDs and assigns unique ``S<n>`` IDs
    without collisions for legacy or untagged headings.

    Returns:
        Tuples of ``(id, title, raw_heading)`` in document order.
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    _, body = extract_frontmatter(text)
    parsed: list[tuple[str | None, str, str]] = []
    in_main_paths = False
    in_fence = False

    def parse_heading(heading_text: str, raw_heading: str) -> None:
        if match := _PATH_EXPLICIT_RE.match(heading_text):
            parsed.append((match.group(1).upper(), match.group(2).strip(), raw_heading))
        elif match := _PATH_LEGACY_RE.match(heading_text):
            parsed.append((None, match.group(1).strip(), raw_heading))
        elif match := _SCENARIO_EXPLICIT_RE.match(heading_text):
            parsed.append((match.group(1).upper(), match.group(2).strip(), raw_heading))
        elif match := _SCENARIO_LEGACY_RE.match(heading_text):
            parsed.append((None, match.group(1).strip(), raw_heading))
        else:
            parsed.append((None, heading_text.strip(), raw_heading))

    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped == "<!-- okf:links:start -->":
            in_main_paths = False
            continue
        heading_match = _HEADING_PATTERN.match(stripped)
        if not heading_match:
            continue
        level = len(heading_match.group(1))
        heading_text = heading_match.group(2).strip()
        if level == 3 and heading_text.casefold() == "main paths":
            in_main_paths = True
            continue
        if in_main_paths:
            if level <= 3:
                in_main_paths = False
            else:
                parse_heading(heading_text, stripped)
                continue
        if level == 3 and heading_text.casefold().startswith("scenario"):
            parse_heading(heading_text, stripped)

    used_ids = {explicit for explicit, _, _ in parsed if explicit is not None}
    emitted: set[str] = set()
    result: list[tuple[str, str, str]] = []
    next_number = 1
    for explicit, title, raw_heading in parsed:
        if explicit is not None and explicit not in emitted:
            assigned = explicit
            emitted.add(assigned)
        else:
            while f"S{next_number}" in used_ids:
                next_number += 1
            assigned = f"S{next_number}"
            used_ids.add(assigned)
            emitted.add(assigned)
            next_number += 1
        result.append((assigned, title, raw_heading))
    return result


def _has_valid_acceptance_exemption(data: dict[str, Any]) -> bool:
    """Return whether a StRS carries a justified whole-StRS acceptance waiver."""
    reason = data.get("acceptance_exemption_reason")
    return (
        data.get("acceptance_exemption") is True
        and isinstance(reason, str)
        and bool(reason.strip())
    )


def _has_valid_annotation_exemption(data: dict[str, Any]) -> bool:
    """Return whether a SwRS carries an explicit annotation exemption with a reason."""
    reason = data.get("exemption_reason")
    return (
        data.get("annotation_exemption") is True
        and isinstance(reason, str)
        and bool(reason.strip())
    )


def _scenario_coverage(
    requirements: dict[str, tuple[Path, dict[str, Any], str]],
    scan: dict[str, Any],
) -> dict[str, Any]:
    """Compute counting markers and per-scenario coverage for StRS and SwRS."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    declared_ids: dict[str, list[str]] = {}
    for identifier, (_, data, _) in requirements.items():
        entries, _ = _declared_scenarios(data)
        declared_ids[identifier] = [sid for sid, _ in entries]

    counting_tests_files: dict[str, set[str]] = {identifier: set() for identifier in requirements}
    counting_accepts_files: dict[str, set[str]] = {identifier: set() for identifier in requirements}
    tested_scenarios: dict[str, set[str]] = {identifier: set() for identifier in requirements}
    accepted_scenarios: dict[str, set[str]] = {identifier: set() for identifier in requirements}
    has_fragmentless_test: dict[str, bool] = dict.fromkeys(requirements, False)
    has_fragmentless_accept: dict[str, bool] = dict.fromkeys(requirements, False)

    for entry in scan.get("scenario_markers", []):
        identifier = entry["id"]
        if identifier not in requirements:
            continue
        req_type = requirements[identifier][1].get("type")
        if req_type not in ("StRS", "SwRS"):
            continue
        marker_kind = entry["marker"]
        if req_type == "SwRS" and marker_kind == "accepts":
            continue
        fragment = entry["fragment"]
        file_path = entry["file"]
        declared = declared_ids[identifier]
        if declared:
            if fragment is None or fragment not in declared:
                continue
            if marker_kind == "tests":
                tested_scenarios[identifier].add(fragment)
                counting_tests_files[identifier].add(file_path)
            else:
                accepted_scenarios[identifier].add(fragment)
                counting_accepts_files[identifier].add(file_path)
        else:
            if fragment is not None:
                continue
            if marker_kind == "tests":
                has_fragmentless_test[identifier] = True
                counting_tests_files[identifier].add(file_path)
            else:
                has_fragmentless_accept[identifier] = True
                counting_accepts_files[identifier].add(file_path)

    return {
        "declared_ids": declared_ids,
        "counting_tests_files": {k: sorted(v) for k, v in counting_tests_files.items()},
        "counting_accepts_files": {k: sorted(v) for k, v in counting_accepts_files.items()},
        "tested_scenarios": tested_scenarios,
        "accepted_scenarios": accepted_scenarios,
        "has_fragmentless_test": has_fragmentless_test,
        "has_fragmentless_accept": has_fragmentless_accept,
    }


def _swrs_schema_refuses_accepted_in_files(swrs_schema: dict[str, Any]) -> bool:
    """Return whether the composed SwRS schema refuses a non-empty ``accepted_in_files``."""
    validator = Draft202012Validator(swrs_schema, format_checker=FormatChecker())
    probe = {"accepted_in_files": ["tests/test_probe.py"]}
    return any(
        list(error.absolute_path)[:1] == ["accepted_in_files"]
        for error in validator.iter_errors(probe)
    )


def _format_w003(file: Path, identifier: str, text: str) -> str:
    """Build the agent-directed W003 finding for a live StRS with no ``scenarios:``."""
    headings = _scenario_headings(text)
    if headings:
        quoted = "\n".join(f"  - {raw}" for _, _, raw in headings)
        headings_block = f"Headings found in body:\n{quoted}\n"
        yaml_entries = "\n".join(f"  - id: {sid}\n    title: {title}" for sid, title, _ in headings)
    else:
        headings_block = "No ### Main paths or ### Scenario headings were found in the body.\n"
        yaml_entries = "  - id: S1\n    title: <main path title>"
    return (
        f"W003 {file}: {identifier} declares no scenarios:.\n"
        f"{headings_block}"
        f"Paste into frontmatter:\n"
        f"scenarios:\n{yaml_entries}\n"
        f"Edit frontmatter only (keep the body intact). On an approved StRS, log the "
        f"change in tiers/log.md naming the owner's agreement.\n"
        f"See {_W003_DOC_URL}"
    )


def _format_w004(file: Path, identifier: str, *, tests_kw: str, accepts_kw: str) -> str:
    """Build the W004 warning for a live, non-waived StRS with no acceptance test."""
    return (
        f"W004 {file}: {identifier} has no acceptance test: no {accepts_kw} marker "
        f"that counts names it. Mark the test closest to the final product that walks "
        f"each main path with {accepts_kw} {identifier}#S<n> ({accepts_kw} {identifier} "
        f"while it declares no scenarios:). That test may be costly and run in the "
        f"main-branch pipeline, beside cheaper {tests_kw} tests run on every pull or "
        f"merge request. See {_W004_DOC_URL}"
    )


def _scenario_findings(
    requirements: dict[str, tuple[Path, dict[str, Any], str]],
    scan: dict[str, Any],
    config: dict[str, Any],
    lifecycle_key: str,
) -> list[str]:
    """Return fragment errors and W003/W004 warnings in acceptance-paths mode."""
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    findings: list[str] = []
    markers_cfg = config.get("markers", {})
    tests_kw = str(markers_cfg.get("tests", "@tests_req"))
    accepts_kw = str(markers_cfg.get("accepts", "@accepts_req"))
    cov = _scenario_coverage(requirements, scan)
    declared_ids = cov["declared_ids"]

    for entry in scan.get("scenario_markers", []):
        identifier = entry["id"]
        if identifier not in requirements:
            continue
        req_type = requirements[identifier][1].get("type")
        if req_type not in ("StRS", "SwRS"):
            continue
        marker_kind = entry["marker"]
        if req_type == "SwRS" and marker_kind == "accepts":
            continue
        kw = tests_kw if marker_kind == "tests" else accepts_kw
        fragment = entry["fragment"]
        declared = declared_ids[identifier]
        if declared:
            if fragment is None:
                findings.append(
                    f"{entry['file']}:{entry['line']}: {kw} {identifier} has no scenario "
                    f"fragment; {identifier} declares scenarios {', '.join(declared)}: "
                    f"write {kw} {identifier}#S<n> (this marker does not count)"
                )
            elif fragment not in declared:
                findings.append(
                    f"{entry['file']}:{entry['line']}: {kw} {identifier}#{fragment} "
                    f"names no declared scenario of {identifier} "
                    f"(declared: {', '.join(declared)})"
                )
        elif fragment is not None:
            findings.append(
                f"{entry['file']}:{entry['line']}: {kw} {identifier}#{fragment} "
                f"names no declared scenario of {identifier} "
                f"({identifier} declares no scenarios:)"
            )

    for identifier, (file, data, text) in sorted(requirements.items()):
        if data.get("type") != "StRS":
            continue
        if data.get(lifecycle_key) in ("deprecated", "superseded"):
            continue
        if not declared_ids[identifier] and "scenarios" not in data:
            findings.append(_format_w003(file, identifier, text))
        if (
            not _has_valid_acceptance_exemption(data)
            and not cov["counting_accepts_files"][identifier]
        ):
            findings.append(
                _format_w004(file, identifier, tests_kw=tests_kw, accepts_kw=accepts_kw)
            )
    return findings


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


# @implements_req SwRS-OKFSCHEMA-OKFREQ-005
# @implements_req SwRS-OKFSCHEMA-OKFREQ-015
def validate_requirements(
    root: Path,
    prose: bool = False,
    *,
    check_links: bool = False,
    project_root: Path | None = None,
) -> list[str]:
    """Run deterministic structural and graph checks.

    .. versionchanged:: 0.18.0
        In ``linked-swrs-and-acceptance-paths`` mode, scan markers to enforce
        scenario fragments, verify that ``swrs.schema.yaml`` refuses
        ``accepted_in_files``, validate ``scenarios:`` and StRS
        ``acceptance_exemption`` in code, and emit ``W003``/``W004`` warnings
        with or without ``prose=True``.

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
    is_acceptance_mode = _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE
    accepts_kw = str(config.get("markers", {}).get("accepts", "@accepts_req"))
    scan = marker_scan(root) if is_acceptance_mode else None
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
    if is_acceptance_mode:
        base_for_swrs = normalized_schemas.get("base") or normalized_schemas.get("base.schema")
        if base_for_swrs is not None:
            swrs_composed = dict(normalized_schemas["swrs"])
            swrs_composed["allOf"] = [base_for_swrs, *swrs_composed.get("allOf", [])[1:]]
            if not _swrs_schema_refuses_accepted_in_files(swrs_composed):
                swrs_schema_path = schemas_dir / "swrs.schema.yaml"
                errors.append(
                    f"{swrs_schema_path}: accepted_in_files is not refused; mode "
                    f"{ACCEPTANCE_PATHS_MODE} needs the okf-schema 0.18.0 declaration: "
                    "update the bundle schema by adding under properties:\n"
                    "  accepted_in_files:\n"
                    "    type: array\n"
                    "    maxItems: 0\n"
                    f"    description: {_SWRS_ACCEPTED_IN_FILES_DESCRIPTION}"
                )
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
            accepts_files = (
                scan["accepted"].get(identifier, [])
                if scan is not None and level in ("StRS", "SwRS")
                else []
            )
            validation_data = (
                {**data, "accepted_in_files": list(accepts_files)} if accepts_files else data
            )
            reported_accepted_markers = False
            for error in validator.iter_errors(validation_data):
                if (
                    accepts_files
                    and scan is not None
                    and list(error.absolute_path)[:1] == ["accepted_in_files"]
                ):
                    if not reported_accepted_markers:
                        reported_accepted_markers = True
                        detail = (
                            error.schema.get("description")
                            if isinstance(error.schema, dict) and error.schema.get("description")
                            else error.message
                        )
                        for entry in scan["scenario_markers"]:
                            if entry["marker"] == "accepts" and entry["id"] == identifier:
                                suffix = f"#{entry['fragment']}" if entry["fragment"] else ""
                                errors.append(
                                    f"{entry['file']}:{entry['line']}: "
                                    f"{accepts_kw} {identifier}{suffix}: {detail}"
                                )
                    continue
                errors.append(f"{file}: {error.message}")
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
        if is_acceptance_mode:
            _, scenario_problems = _declared_scenarios(data)
            for problem in scenario_problems:
                errors.append(
                    f"{file}: scenarios: {problem} "
                    "(each entry is {id: S<n>, title: <text>}, ids unique)"
                )
            if level == "StRS" and data.get("acceptance_exemption") is True:
                reason = data.get("acceptance_exemption_reason")
                if not isinstance(reason, str) or not reason.strip():
                    errors.append(
                        f"{file}: acceptance_exemption requires a non-blank "
                        "acceptance_exemption_reason"
                    )
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
    if is_acceptance_mode and scan is not None:
        errors.extend(_scenario_findings(requirements, scan, config, lifecycle_key))
    errors.extend(graph(root)["errors"])
    errors.extend(_relation_findings(requirements, lifecycle_key))
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
        In ``linked-swrs-and-acceptance-paths`` mode, write counting-marker
        ``tested_in_files`` on SwRS and StRS and ``accepted_in_files`` on StRS
        when listed in ``generated_fields``; in older modes remove both
        ``tested_in_files`` and ``accepted_in_files`` from StRS.

    Examples:
        >>> from pathlib import Path
        >>> from tempfile import TemporaryDirectory
        >>> with TemporaryDirectory() as directory:
        ...     root = init_requirements(Path(directory) / "requirements")
        ...     update_coverage(root, check=True)
        []
    """
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
    requirements = load_requirements(root)
    config = load_config(root)
    scan = marker_scan(root)
    is_acceptance_mode = _strs_test_coverage_mode(config) == ACCEPTANCE_PATHS_MODE
    scenario_cov = _scenario_coverage(requirements, scan) if is_acceptance_mode else None
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
        req_type = str(authored.get("type"))
        if req_type == "SwRS":
            tested_files = (
                scenario_cov["counting_tests_files"][identifier]
                if scenario_cov is not None
                else sorted(scan["tested"].get(identifier, []))
            )
            available_updates.update(
                {
                    "implemented_in_files": sorted(scan["implemented"].get(identifier, [])),
                    "tested_in_files": tested_files,
                }
            )
        elif req_type == "StRS" and scenario_cov is not None:
            available_updates.update(
                {
                    "tested_in_files": scenario_cov["counting_tests_files"][identifier],
                    "accepted_in_files": scenario_cov["counting_accepts_files"][identifier],
                }
            )
        updates = {
            key: available_updates[key] for key in configured_fields if key in available_updates
        }
        rendered = _render_frontmatter(text, updates)
        if req_type == "StRS":
            frontmatter, body = extract_frontmatter(rendered)
            if frontmatter is not None:
                data = make_yaml().load(frontmatter)
                if isinstance(data, dict):
                    data.pop("implemented_in_files", None)
                    if not is_acceptance_mode:
                        data.pop("tested_in_files", None)
                        data.pop("accepted_in_files", None)
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

    .. versionchanged:: 0.18.0
        Emit ``format_version`` 2 in every mode; in
        ``linked-swrs-and-acceptance-paths`` mode report per-StRS path
        counters, independent ``tested``/``accepted`` booleans, ``tests``,
        ``acceptance_tests``, optional ``acceptance_exemption``, per-SwRS
        ``transitions``, and aggregate StRS path totals from counting markers.

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
    # @implements_req SwRS-OKFSCHEMA-OKFREQ-015
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
    is_acceptance_mode = strs_test_coverage_mode == ACCEPTANCE_PATHS_MODE
    scenario_cov = _scenario_coverage(requirements, trace) if is_acceptance_mode else None
    lifecycle: dict[str, int] = {}
    for _, data, _ in requirements.values():
        value = str(data.get(lifecycle_field(config), "invalid"))
        lifecycle[value] = lifecycle.get(value, 0) + 1
    leaf_levels = _leaf_levels(config)
    missing_implementation: list[str] = []
    missing_tests: list[str] = []
    exemptions: list[dict[str, str]] = []

    def _leaf_test_files(identifier: str, req_type: Any) -> list[str]:
        if scenario_cov is not None and req_type == "SwRS":
            return list(scenario_cov["counting_tests_files"][identifier])
        return list(trace["tested"].get(identifier, []))

    def _leaf_is_test_covered(identifier: str, req_type: Any) -> bool:
        if scenario_cov is not None and req_type == "SwRS":
            declared = scenario_cov["declared_ids"][identifier]
            if declared:
                return all(sid in scenario_cov["tested_scenarios"][identifier] for sid in declared)
            return bool(scenario_cov["has_fragmentless_test"][identifier])
        return identifier in trace["tested"]

    for identifier, (_, data, _) in requirements.items():
        req_type = data.get("type")
        if req_type not in leaf_levels:
            continue
        if data.get("annotation_exemption") is True:
            exemptions.append({"id": identifier, "reason": str(data.get("exemption_reason") or "")})
            continue
        if identifier not in trace["implemented"]:
            missing_implementation.append(identifier)
        if not _leaf_is_test_covered(identifier, req_type):
            missing_tests.append(identifier)
    coverage_targets = {
        identifier: (file, data, text)
        for identifier, (file, data, text) in requirements.items()
        if data.get("type") in leaf_levels and data.get("annotation_exemption") is not True
    }
    implemented = set(trace["implemented"]) & set(coverage_targets)
    tested = {
        identifier
        for identifier, (_, data, _) in coverage_targets.items()
        if _leaf_is_test_covered(identifier, data.get("type"))
    }
    fully_traceable = implemented & tested
    stakeholder_coverage: dict[str, dict[str, Any]] = {}
    total_paths = 0
    total_paths_tested = 0
    total_paths_accepted = 0
    for identifier, (_, data, _) in requirements.items():
        if data.get("type") != "StRS":
            continue
        linked_swrs = sorted(
            child
            for child in graph_result["derived_by"].get(identifier, [])
            if child in requirements and requirements[child][1].get("type") == "SwRS"
        )
        if is_acceptance_mode and scenario_cov is not None:
            linked_swrs_report = []
            for child in linked_swrs:
                child_data = requirements[child][1]
                if child_data.get("annotation_exemption") is True:
                    child_status = (
                        "exempt" if _has_valid_annotation_exemption(child_data) else "missing"
                    )
                else:
                    child_status = "covered" if child in tested else "missing"
                linked_swrs_report.append({"id": child, "status": child_status})
            linked_swrs_covered = bool(linked_swrs) and all(
                item["status"] in ("covered", "exempt") for item in linked_swrs_report
            )
            declared = scenario_cov["declared_ids"][identifier]
            if declared:
                paths_total = len(declared)
                paths_tested = len(scenario_cov["tested_scenarios"][identifier])
                paths_accepted = len(scenario_cov["accepted_scenarios"][identifier])
                is_tested = paths_tested == paths_total
                is_accepted = paths_accepted == paths_total
            else:
                paths_total = 0
                paths_tested = 0
                paths_accepted = 0
                is_tested = bool(scenario_cov["has_fragmentless_test"][identifier])
                is_accepted = bool(scenario_cov["has_fragmentless_accept"][identifier])
            total_paths += paths_total
            total_paths_tested += paths_tested
            total_paths_accepted += paths_accepted
            waived = _has_valid_acceptance_exemption(data)
            covered = linked_swrs_covered and (is_accepted or waived)
            tests_files = scenario_cov["counting_tests_files"][identifier]
            accepts_files = scenario_cov["counting_accepts_files"][identifier]
            accepts_block = {
                "status": "defined" if accepts_files else "missing",
                "files": accepts_files,
                "count": len(accepts_files),
            }
            entry: dict[str, Any] = {
                "status": "covered" if covered else "missing",
                "mode": strs_test_coverage_mode,
                "linked_swrs": linked_swrs_report,
                "paths": {
                    "total": paths_total,
                    "tested": paths_tested,
                    "accepted": paths_accepted,
                },
                "tested": is_tested,
                "accepted": is_accepted,
                "tests": {
                    "status": "defined" if tests_files else "missing",
                    "files": tests_files,
                    "count": len(tests_files),
                },
                "acceptance_tests": accepts_block,
                "validation_tests": dict(accepts_block),
            }
            if waived:
                entry["acceptance_exemption"] = {"reason": str(data["acceptance_exemption_reason"])}
            stakeholder_coverage[identifier] = entry
        else:
            linked_swrs_report = [
                {"id": child, "status": "covered" if child in tested else "missing"}
                for child in linked_swrs
            ]
            validation_files = trace["validation_tests"].get(identifier, [])
            linked_swrs_covered = bool(linked_swrs) and all(
                child in tested for child in linked_swrs
            )
            validation_defined = bool(validation_files)
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

    stakeholder_total = len(stakeholder_coverage)
    stakeholder_covered = sum(
        coverage["status"] == "covered" for coverage in stakeholder_coverage.values()
    )

    def percentage(count: int, total: int) -> float:
        """Return a percentage rounded to two decimal places."""
        return round((count / total) * 100, 2) if total else 100.0

    requirement_records: list[dict[str, Any]] = []
    for identifier, (file, data, text) in sorted(requirements.items()):
        req_type = data.get("type")
        source_links = trace["implemented"].get(identifier, [])
        test_links = _leaf_test_files(identifier, req_type)
        coverage_target = identifier in coverage_targets
        stakeholder_details = stakeholder_coverage.get(identifier)
        implementation = {
            "status": "not_applicable"
            if stakeholder_details
            else ("covered" if source_links else "missing"),
            "files": [] if stakeholder_details else source_links,
            "count": 0 if stakeholder_details else len(source_links),
        }
        leaf_covered = _leaf_is_test_covered(identifier, req_type)
        tests = {
            "status": stakeholder_details["status"]
            if stakeholder_details
            else ("covered" if leaf_covered else "missing"),
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
            "tier": data.get("tier", req_type),
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
        if is_acceptance_mode and scenario_cov is not None and req_type == "SwRS":
            declared = scenario_cov["declared_ids"][identifier]
            if declared:
                tested_set = scenario_cov["tested_scenarios"][identifier]
                record["transitions"] = {
                    "tested": [sid for sid in declared if sid in tested_set],
                    "missing": [sid for sid in declared if sid not in tested_set],
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
    if is_acceptance_mode and scenario_cov is not None:
        marker_tested_count = sum(
            bool(_leaf_test_files(identifier, data.get("type")))
            for identifier, (_, data, _) in requirements.items()
            if data.get("type") in leaf_levels
        )
        marker_validation_tests = {
            identifier: cov["acceptance_tests"]["files"]
            for identifier, cov in stakeholder_coverage.items()
            if cov["acceptance_tests"]["files"]
        }
        tests_definition = (
            "every declared transition has a test marker with its fragment, "
            "or at least one test marker when none is declared"
        )
    else:
        marker_tested_count = len(trace["tested"])
        marker_validation_tests = trace["validation_tests"]
        tests_definition = "at least one @tests_req marker for each SwRS coverage target"
    stakeholder_summary: dict[str, Any] = {
        "mode": strs_test_coverage_mode,
        "requirements": stakeholder_total,
        "covered": stakeholder_covered,
        "coverage_percent": percentage(stakeholder_covered, stakeholder_total),
    }
    if is_acceptance_mode:
        stakeholder_summary["paths"] = {
            "total": total_paths,
            "tested": total_paths_tested,
            "accepted": total_paths_accepted,
        }
    marker_coverage_block = {
        "implemented": len(trace["implemented"]),
        "tested": marker_tested_count,
        "missing_ids": trace["missing_ids"],
        "duplicates": trace["duplicates"],
        "non_leaf": trace["non_leaf"],
        "warnings": trace["warnings"],
        "missing_implementation": sorted(missing_implementation),
        "missing_tests": sorted(missing_tests),
        "validation_tests": marker_validation_tests,
        "exemptions": exemptions,
    }
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
            "tests": tests_definition,
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
        "stakeholder_test_coverage": stakeholder_summary,
        "scopes": scopes,
        "requirements": requirement_records,
        # Keep the original aggregate section stable for callers that consumed
        # the pre-v1 report while exposing the richer fields above.
        "marker_coverage": marker_coverage_block,
        "legacy": {
            "provenance": {
                "generator": "okfreq",
                "command": "okfreq generate-report",
                "config_version": config.get("version"),
                "sources": ["config.yml", "tiers/"],
            },
            "schema_health": {"requirements": len(requirements), "errors": len(errors)},
            "structural_traceability": {"graph_errors": len(graph_result["errors"])},
            "marker_coverage": dict(marker_coverage_block),
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

    .. versionchanged:: 0.18.0
        Increment ``format_version`` to 2, add ``linked-swrs-and-acceptance-paths``
        to mode enums, and declare optional ``paths``, ``tested``, ``accepted``,
        ``tests``, ``acceptance_tests``, ``acceptance_exemption``, ``exempt``
        linked-SwRS status, and ``transitions``.

    Returns:
        A JSON Schema mapping describing the detailed report format.
    """
    path_counts_schema: dict[str, Any] = {
        "type": "object",
        "required": ["total", "tested", "accepted"],
        "properties": {
            "total": {"type": "integer", "minimum": 0},
            "tested": {"type": "integer", "minimum": 0},
            "accepted": {"type": "integer", "minimum": 0},
        },
        "additionalProperties": False,
    }
    defined_files_schema: dict[str, Any] = {
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
                    "paths": path_counts_schema,
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
                        "additionalProperties": False,
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
                                "status": {"enum": ["covered", "missing", "exempt"]},
                            },
                        },
                    },
                    "paths": path_counts_schema,
                    "tested": {"type": "boolean"},
                    "accepted": {"type": "boolean"},
                    "tests": defined_files_schema,
                    "acceptance_tests": defined_files_schema,
                    "validation_tests": defined_files_schema,
                    "acceptance_exemption": {
                        "type": "object",
                        "required": ["reason"],
                        "properties": {
                            "reason": {"type": "string", "minLength": 1},
                        },
                        "additionalProperties": False,
                    },
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

    .. versionchanged:: 0.18.0
        In ``linked-swrs-and-acceptance-paths`` mode, add the StRS paths
        summary line, ``Tested`` and ``Accepted`` columns (or ``exempt`` for a
        waived StRS) to the StRS table, and ``Missing transitions`` to the SwRS
        table.

    Args:
        root:
            Bundle root to report on.
        destination:
            Output Markdown path, whose parent directory must exist.
    """

    def status_emoji(status: str) -> str:
        """Return the compact status marker used in the Markdown summary."""
        return {"covered": "✅", "missing": "❌"}.get(status, "⚪")

    def path_cell(count: int, total: int, complete: bool) -> str:
        """Format a Tested or Accepted cell in acceptance-paths mode."""
        if total == 0:
            return "✅ no paths" if complete else "❌ no paths"
        return f"{count}/{total} ✅" if complete else f"{count}/{total}"

    data = report(root)
    totals = data["totals"]
    stakeholder_totals = data["stakeholder_test_coverage"]
    mode = stakeholder_totals["mode"]
    is_acceptance_mode = mode == ACCEPTANCE_PATHS_MODE
    summary_lines = [
        f"- Requirements: {totals['requirements']} "
        f"({totals['coverage_target_requirements']} coverage targets)",
        f"- SwRS source coverage: {totals['source_coverage_percent']}% "
        f"({totals['implemented']}/{totals['coverage_target_requirements']})",
        f"- SwRS test-link coverage: {totals['test_coverage_percent']}% "
        f"({totals['tested']}/{totals['coverage_target_requirements']})",
        f"- StRS test coverage: {stakeholder_totals['coverage_percent']}% "
        f"({stakeholder_totals['covered']}/{stakeholder_totals['requirements']})",
    ]
    if is_acceptance_mode:
        agg_paths = stakeholder_totals["paths"]
        summary_lines.append(
            f"- StRS paths: tested {agg_paths['tested']}/{agg_paths['total']}, "
            f"accepted {agg_paths['accepted']}/{agg_paths['total']}"
        )
    summary_lines.append(
        f"- Combined traceability: {totals['combined_coverage_percent']}% "
        f"({totals['fully_traceable']}/{totals['coverage_target_requirements']})"
    )
    lines = [
        "# Requirements report",
        "",
        f"Generated: {data['generated_at']}",
        "",
        "## Summary",
        "",
        *summary_lines,
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
    if is_acceptance_mode:
        lines.extend(
            [
                "",
                "## By stakeholder requirement",
                "",
                "| Scope | Tier | ID | Name | Tested | Accepted | Tests |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for requirement in stakeholder_requirements:
            name = str(requirement["frontmatter"].get("title", requirement["id"]))
            cov = requirement["stakeholder_test_coverage"]
            paths = cov["paths"]
            tested_cell = path_cell(paths["tested"], paths["total"], cov["tested"])
            accepted_cell = (
                "exempt"
                if "acceptance_exemption" in cov
                else path_cell(paths["accepted"], paths["total"], cov["accepted"])
            )
            lines.append(
                f"| {requirement['scope']} | {requirement['tier']} | "
                f"{requirement['id']} | {name} | "
                f"{tested_cell} | {accepted_cell} | "
                f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
            )
    else:
        lines.extend(
            [
                "",
                "## By stakeholder requirement",
                "",
                "| Scope | Tier | ID | Name | Tests |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for requirement in stakeholder_requirements:
            name = str(requirement["frontmatter"].get("title", requirement["id"]))
            lines.append(
                f"| {requirement['scope']} | {requirement['tier']} | "
                f"{requirement['id']} | {name} | "
                f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
            )
    coverage_description = STRS_TEST_COVERAGE_DESCRIPTIONS[mode]
    coverage_sentence = coverage_description[0].lower() + coverage_description[1:]
    coverage_note = f"*Note: current configuration is that {coverage_sentence}*"
    if is_acceptance_mode:
        lines.extend(
            [
                "",
                coverage_note,
                "",
                "## By software requirement",
                "",
                "| Scope | Tier | ID | Name | Source | Tests | Missing transitions |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for requirement in (item for item in requirements if item["coverage_target"]):
            name = str(requirement["frontmatter"].get("title", requirement["id"]))
            missing = requirement.get("transitions", {}).get("missing", [])
            missing_cell = ", ".join(missing) if missing else "—"
            lines.append(
                f"| {requirement['scope']} | {requirement['tier']} | "
                f"{requirement['id']} | {name} | "
                f"{status_emoji(requirement['implementation']['status'])} "
                f"{requirement['implementation']['status']} | "
                f"{status_emoji(requirement['tests']['status'])} "
                f"{requirement['tests']['status']} | "
                f"{missing_cell} |"
            )
    else:
        lines.extend(
            [
                "",
                coverage_note,
                "",
                "## By software requirement",
                "",
                "| Scope | Tier | ID | Name | Source | Tests |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for requirement in (item for item in requirements if item["coverage_target"]):
            name = str(requirement["frontmatter"].get("title", requirement["id"]))
            lines.append(
                f"| {requirement['scope']} | {requirement['tier']} | "
                f"{requirement['id']} | {name} | "
                f"{status_emoji(requirement['implementation']['status'])} "
                f"{requirement['implementation']['status']} | "
                f"{status_emoji(requirement['tests']['status'])} {requirement['tests']['status']} |"
            )
    _atomic_write(destination, "\n".join(lines) + "\n")
