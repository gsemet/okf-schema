---
name: okf-schema
description: CLI and Python library for OKF bundle management
---

# okf-schema

**okf-schema** is a CLI tool and Python library for working with **OKF (Open Knowledge Format)** bundles — validating frontmatter metadata against JSONSchema, formatting while preserving comments, and managing bundle structure.

## Overview

[OKF (Open Knowledge Format)](./references/okf-v0.1.md) is a markdown-based knowledge format where each concept is a markdown file with YAML frontmatter. An OKF bundle is valid if it follows the structural rules defined in the OKF specification: reserved files (`index.md`, `log.md`), YAML frontmatter delimiters, relative markdown links, and so on.

`okf-schema` is a **validator and toolkit layered on top of OKF**. It does not change the OKF format; it adds:

- **JSONSchema validation** of frontmatter via auto-discovered `_schema/` definitions
- **Bundle integrity checks** (broken links, missing `index.md`, malformed `log.md`, reserved-file violations)
- **Linting** of frontmatter: flattens nested lists and converts block-style to inline while preserving YAML comments
- **Bundle management** via CLI and Python API: init, list, show, stats, index

In other words: **all `okf-schema` bundles are OKF bundles, but not all OKF bundles need `okf-schema`.** You can author plain OKF without schemas, then opt into validation later by adding a `_schema/` directory.

## Installation

```bash
uv tool install okf-schema
```

## Quickstart

```bash
# Initialize a new OKF bundle
okf-schema init my-bundle

# Create a new concept
okf-schema new --path my-bundle --name concepts/architecture --type concept --title "Architecture"

# Validate the bundle
okf-schema validate --path my-bundle
# Or with a strict mode that treats warnings as errors
okf-schema validate --path my-bundle --strict

# Lint frontmatter
okf-schema lint --path my-bundle
```

## CLI Reference

| Subcommand | Description |
|-----------|-------------|
| `init <name>` | Create a new OKF bundle directory structure |
| `new --path <dir> --name <name>` | Create a new concept file with frontmatter template |
| `validate --path <bundle>` | Validate bundle structure and frontmatter |
| `validate --path <bundle> --strict` | Validate and treat warnings as errors |
| `lint --path <bundle>` | Lint frontmatter: flatten nested lists and convert block-style to inline |
| `list --path <bundle>` | List all concepts in a bundle |
| `show --path <bundle> <concept>` | Show a single concept's frontmatter and body |
| `index --path <bundle>` | Regenerate all `index.md` files |
| `stats --path <bundle>` | Show bundle statistics |

Global options: `--version`, `--verbose` (`-v`), `--quiet` (`-q`).

## Python API

```python
from okf_schema.api import validate_bundle, lint_bundle, list_bundle

# Validate
report = validate_bundle("path/to/bundle")
print(f"Conformant: {report.is_conformant}")
for err in report.errors:
    print(f"ERROR [{err.code}] {err.message}")

# Lint (flatten nested lists and convert block lists to inline)
results = lint_bundle("path/to/bundle", check=True)
for r in results:
    if r.changed:
        print(f"Would lint: {r.path}")

# List concepts
concepts = list_bundle("path/to/bundle")
for c in concepts:
    print(f"{c.path} ({c.type}): {c.title}")
```

## Validation Rules

### Errors (E1–E6)

| Code | Rule | Description |
|------|------|-------------|
| E1 | Parseable frontmatter | Every concept file must have valid YAML frontmatter |
| E2 | Non-empty `type` field | Frontmatter must contain a non-empty `type` field |
| E3 | Reserved file frontmatter | Only bundle-root `index.md` may have frontmatter; `log.md` must not |
| E4 | Schema validation | Frontmatter must validate against its type's JSONSchema |
| E5 | Flat lists | Frontmatter lists must not be nested (e.g. `tags: [[a], b]`) |
| E6 | Reserved file location | `log.md` must exist only at bundle root |

### Warnings (W1–W7)

| Code | Rule | Description |
|------|------|-------------|
| W1 | Missing recommended fields | `title` or `description` is missing or empty |
| W2 | Broken cross-links | Internal markdown link points to a non-existent file |
| W3 | Missing timestamp | No `timestamp` field in frontmatter |
| W4 | Missing `index.md` | Directory with markdown files has no `index.md` |
| W5 | Non-ISO date heading | `log.md` date heading not in `YYYY-MM-DD` format |
| W6 | Missing schema | No schema found for the concept's `type` |
| W7 | Block-style lists | Frontmatter lists should use inline notation (e.g. `tags: [a, b]`) to keep frontmatter compact |

## Tips for Agents

- **Recommended workflow before shipping a bundle**: Run the three commands in this order — `index` → `lint` → `validate` — and fix all warnings before packaging:
  ```bash
  okf-schema index --path <bundle>    # regenerate all index.md files
  okf-schema lint --path <bundle>     # convert block lists to inline for compact frontmatter
  okf-schema validate --path <bundle> --strict # check structure, schema, and links; fail on warnings
  ```
  Only zip or distribute the bundle once `validate --strict` reports zero errors **and** zero warnings. Warnings such as missing `index.md` (W4), block-style lists (W7), or broken cross-links (W2) signal issues that will degrade the experience for downstream consumers.
- **Always validate after creating or modifying bundles**: Run `okf-schema validate --path <bundle>` to catch structural issues early.
- **Use `check` mode before linting**: `okf-schema lint --path <bundle> --check` shows what would change without modifying files.
- **Preserve comments**: The formatter and linter both use `ruamel.yaml` round-trip mode, so YAML comments and quotes are preserved.
- **Custom schemas**: Place `.schema.json`, `.schema.json5`, or `.schema.yaml` files in a schema directory and pass `--schema-db` to `validate`. JSON5 allows comments and trailing commas.
- **Bundle structure**: A standard OKF bundle contains a `bundle/` directory with markdown concept files. Custom JSONSchema definitions go in a `_schema/` directory inside the bundle root; they are auto-discovered by `validate`.
- **Reserved files**: `index.md` and `log.md` are reserved. `index.md` can exist at any directory level; `log.md` must be at bundle root only.
- **Link resolution**: Internal links are resolved relative to the source file. Absolute paths (`/path`) are resolved relative to bundle root. External URLs (`https://`, `mailto:`) are ignored during validation.

## References

- **[OKF v0.1 Specification](./references/okf-v0.1.md)** — The base format that `okf-schema` validates and extends. All OKF structural rules (bundle layout, frontmatter syntax, reserved files, linking conventions) are defined here.
- **[Conversions Guide](./references/conversions.md)** — Quick reference for converting existing content into OKF format (Obsidian vaults, CSV/spreadsheets, wikilinks, inline tags).
