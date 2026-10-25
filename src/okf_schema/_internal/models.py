"""Typed records shared by okf-schema validation and reporting code.

The models contain data only; validation and bundle mutations live in the
public :mod:`okf_schema.api` module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    """A single validation finding (error, warning or informational note)."""

    code: str
    message: str
    path: Path | None = None


@dataclass
class Report:
    """Aggregated validation report for an OKF bundle."""

    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)
    infos: list[Finding] = field(default_factory=list)

    @property
    def is_conformant(self) -> bool:
        """Return True if the report contains no errors."""
        return len(self.errors) == 0

    def add_error(
        self,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> None:
        """Append an error finding to the report.

        Args:
            code:
                Stable machine-readable finding code.
            message:
                Human-readable explanation.
            path:
                Optional path associated with the finding.

        Examples:
            >>> from okf_schema._internal.models import Report
            >>> report = Report()
            >>> report.add_error("missing-title", "Title is required")
            >>> report.is_conformant
            False
        """
        self.errors.append(Finding(code, message, path))

    def add_warning(
        self,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> None:
        """Append a warning finding to the report.

        Args:
            code:
                Stable machine-readable finding code.
            message:
                Human-readable explanation.
            path:
                Optional path associated with the finding.

        Examples:
            >>> from okf_schema._internal.models import Report
            >>> report = Report()
            >>> report.add_warning("missing-description", "Description is recommended")
            >>> len(report.warnings)
            1
        """
        self.warnings.append(Finding(code, message, path))

    def add_info(
        self,
        code: str,
        message: str,
        path: Path | None = None,
    ) -> None:
        """Append an informational finding to the report.

        Informational findings never make a report non-conformant and are
        never counted by ``--strict``.

        Args:
            code:
                Stable machine-readable finding code.
            message:
                Human-readable explanation.
            path:
                Optional path associated with the finding.

        Examples:
            >>> from okf_schema._internal.models import Report
            >>> report = Report()
            >>> report.add_info("I1", "schema file is empty")
            >>> report.is_conformant, len(report.infos)
            (True, 1)
        """
        self.infos.append(Finding(code, message, path))

    def add_schema_diagnostics(self, diagnostics: list[Finding]) -> None:
        """Route schema-loading diagnostics to warnings or informational notes.

        Args:
            diagnostics:
                Findings returned by
                :func:`okf_schema.validator.load_schema_database_with_diagnostics`.
                Codes starting with ``W`` become warnings; the others become
                informational notes.

        Examples:
            >>> from okf_schema._internal.models import Finding, Report
            >>> report = Report()
            >>> report.add_schema_diagnostics([Finding("I1", "empty"), Finding("W17", "bad")])
            >>> len(report.infos), len(report.warnings)
            (1, 1)
        """
        for finding in diagnostics:
            target = self.warnings if finding.code.startswith("W") else self.infos
            target.append(finding)


@dataclass
class ConceptInfo:
    """Extracted metadata from an OKF concept file."""

    title: str
    description: str
    type: str


@dataclass
class SearchResult:
    """Result from searching an OKF bundle."""

    path: str
    type: str
    title: str


@dataclass
class BundleStats:
    """Statistics for an OKF bundle."""

    total_files: int
    total_concepts: int
    files_without_frontmatter: int
    total_size: int
    total_links: int
    broken_links: int
    types_distribution: dict[str, int]
    tags_distribution: dict[str, int]
    directories: int


@dataclass
class ConceptSummary:
    """Summary of a single concept in an OKF bundle."""

    path: str
    type: str
    title: str
    stale: bool = False


@dataclass
class ConceptDetail:
    """Detailed view of a single concept file."""

    frontmatter: dict[str, object]
    body: str
    trust_tier: str = "unverified"
    stale: bool = False


@dataclass
class IndexUpdate:
    """Record of an index.md update operation."""

    path: str
    action: str


@dataclass
class BacklinkResult:
    """A single backlink: a source concept that links to a target concept."""

    target: str
    source: str
