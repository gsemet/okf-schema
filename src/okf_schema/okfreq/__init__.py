"""Create and manage requirement documents in Open Knowledge Format bundles.

The package exposes the safe initialization and requirement-creation entry
points from :mod:`okf_schema.okfreq.core`. Requirement operations raise
:class:`RequirementError` when an input or bundle state is invalid.

Examples:
    >>> from pathlib import Path
    >>> from tempfile import TemporaryDirectory
    >>> from okf_schema.okfreq import init_requirements
    >>> with TemporaryDirectory() as directory:
    ...     bundle = init_requirements(Path(directory) / "requirements")
    ...     bundle.name
    'requirements'
"""

from .core import RequirementError, create_requirement, init_requirements

__all__ = ["RequirementError", "create_requirement", "init_requirements"]
