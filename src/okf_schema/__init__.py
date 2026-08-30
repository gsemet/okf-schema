"""Top-level package for Open Knowledge Format (OKF) bundle tooling.

Use :mod:`okf_schema.api` for the supported programmatic interface. The
package root exposes :data:`__version__` for diagnostics and integrations.
"""

from importlib.metadata import version

__version__ = version("okf_schema")
