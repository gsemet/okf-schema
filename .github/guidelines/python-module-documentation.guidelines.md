---
name: Python Module Documentation Guideline 1.1
description: Guidelines for writing clear, actionable documentation for Python modules using reStructuredText docstrings and Sphinx/MyST
metadata:
  owner: Gaetan Semet <gaetan.semet@ampere.cars>
  keywords: [python, documentation, sphinx, myst, docstrings, restructuredtext]
  guideline-id: 76734b5f-595f-4886-90a4-16097dc4f1eb
---
# Python Module Documentation Guideline

Document maintained Python modules consistently for users and developers. Use
Google-style docstrings parsed by Sphinx Napoleon and Sphinx/MyST for external
docs.

## Rules

1. Every maintained public module needs a module docstring describing its
  purpose, key constraints, and useful public API, including key APIs when
  useful. Follow project policy for test modules, scripts, generated files,
  vendored code, and `__init__.py`. Add a quick-start example when there is a
  meaningful user-facing entry point.
2. Public function docstrings use, when applicable, this Google-style order:
   summary, description, `Args`, `Returns`, `Raises`, `Examples`; parse them
   with `sphinx.ext.napoleon`. In `Args`, put each parameter name on its own
   line with a colon and put its description on the next indented line, never
   inline, including for short descriptions.
3. Add type hints to every function signature and explain complex types or
   constraints. Omit `Args` without meaningful arguments, `Returns` for
   `None`, and `Raises` or `Examples` when they add no useful information. For
   functions with at least three parameters, put every parameter on its own
   signature line; put the closing parenthesis and return annotation on their
   own lines when needed for readability.
4. Functions with more than two parameters or non-obvious behavior must have
   an `Examples` section with runnable examples using the actual API.
5. For every added or changed user-facing public API, model, exception, or CLI
   command/option, put `.. versionadded::` or `.. versionchanged::` immediately
   after the one-line summary and before the description. Use the release that
   will contain the change, normally the next minor release (for example,
   `0.70.2` → `0.71.0`), and append new entries without removing history.

6. Give every public function and class an accurate docstring, using only the
  sections that apply.

## Requirements

- Use Python 3.10+ typing, such as `list[dict]` and `str | None`.
- Use Google-style `Args`, `Returns`, `Raises`, and `Examples` sections with
  Sphinx Napoleon.
- Wrap prose at sentence and clause boundaries where practical; keep separate
  clauses on separate lines to reduce merge and rebase conflicts.
- For three or more parameters, use one parameter per signature line,
  regardless of type or default complexity.
- Define acronyms and specialized terms once at module level and use them
  consistently.
- Keep lines under 120 characters where practical, preferring sentence and
  clause boundaries.
- Use Sphinx + MyST with `sphinx.ext.autodoc`, `sphinx.ext.napoleon`, and
  `myst_parser`; set `myst_enable_extensions = ['colon_fence']`.
- Use MyST admonitions in Sphinx docs and GitHub Admonitions in non-Sphinx docs.
- Recommend enabling doctest so executable docstring examples are checked.

## Validation

- Public functions and classes have accurate docstrings with only applicable
  sections.
- Three-or-more-parameter signatures use one parameter per line.
- Every `Args` parameter is isolated on its own line with an indented
  description.
- Prose follows clause wrapping; all signatures have type hints.
- Module docstrings describe purpose and key APIs.
- Examples use actual APIs and are runnable.
- Version directives follow the summary line.
- Terminology, line length, Google-style parsing, MyST extensions, and
  admonition formats follow the requirements above.

## Positive example

```python
def fetch_data(
    endpoint: str,
    timeout: int = 30,
    retries: int = 3,
) -> dict:
    """Fetch JSON data from an HTTPS endpoint.

    Args:
        endpoint:
            HTTPS endpoint URL.
        timeout:
            Request timeout in seconds.
        retries:
            Number of retry attempts.

    Returns:
        Parsed JSON response.

    Examples:
        >>> data = fetch_data("https://api.example.com/users")
        >>> data["status"]
        "ok"
    """
    return {"status": "ok"}
```
