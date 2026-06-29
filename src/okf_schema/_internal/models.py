"""Data models for okf-schema validation and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    """A single validation finding (error or warning)."""

    code: str
    message: str
    path: Path | None = None


@dataclass
class Report:
    """Aggregated validation report for an OKF bundle."""

    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    @property
    def is_conformant(self) -> bool:
        """Return True if the report contains no errors."""
        return len(self.errors) == 0

    def add_error(self, code: str, message: str, path: Path | None = None) -> None:
        """Append an error finding to the report."""
        self.errors.append(Finding(code, message, path))

    def add_warning(self, code: str, message: str, path: Path | None = None) -> None:
        """Append a warning finding to the report."""
        self.warnings.append(Finding(code, message, path))


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


@dataclass
class ConceptDetail:
    """Detailed view of a single concept file."""

    frontmatter: dict
    body: str


@dataclass
class IndexUpdate:
    """Record of an index.md update operation."""

    path: str
    action: str
