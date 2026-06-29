"""Sphinx configuration for okf-schema documentation."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src/ to the path so autodoc can import okf_schema
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from okf_schema import __version__

# -- Project information -----------------------------------------------------
project = "okf-schema"
copyright = "2026, Gaetan Semet"  # noqa: A001
author = "Gaetan Semet"
release = __version__
version = __version__

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]

# -- Autodoc configuration ---------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- Napoleon configuration --------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
