---
name: okf-schema
description: 'Validate, lint, and manage OKF (Open Knowledge Format) bundles using the okf-schema CLI and Python API. Use when the user mentions OKF validation, validate a knowledge bundle, check OKF conformance, lint frontmatter, OKF schema validation, bundle integrity, broken links in OKF, or wants to initialize or manage an OKF bundle structure. Also use for okf-schema CLI commands, JSONSchema validation of OKF concepts, or formatting OKF frontmatter.'
metadata:
  keywords: [okf, open-knowledge-format, okf-schema, validator, lint, frontmatter, markdown, jsonschema, knowledge, knowledge-base, knowledge-bundle, bundle-validation]
  url: https://github.com/gsemet/okf-schema
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

## OKF at a Glance

If you are new to OKF, here are the essentials:

- **Bundle** — A directory tree of `.md` files. The unit of distribution.
- **Concept** — One markdown file = one unit of knowledge. Must have YAML frontmatter with a non-empty `type` field.
- **Reserved files** — `index.md` (directory listing, no frontmatter except at bundle root) and `log.md` (change history, bundle root only).
- **Links** — Standard markdown links between concepts. Broken links are permitted by the spec.

The three conformance rules every OKF bundle must satisfy:
1. Every non-reserved `.md` file has parseable YAML frontmatter.
2. Every frontmatter has a non-empty `type` field.
3. Reserved files follow their defined structure when present.

For full spec details, see [OKF v0.1 Specification](./references/okf-v0.1.md).

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

# Find backlinks to a concept (extension is optional)
okf-schema backlinks --path my-bundle concepts/react-pattern
```

## Create a Bundle

Step-by-step workflow to build a conformant bundle from scratch:

```bash
# 1. Initialize the bundle directory
okf-schema init my-bundle

# 2. Add concepts
okf-schema new --path my-bundle --name metrics/mrr --type Metric --title "Monthly Recurring Revenue"
okf-schema new --path my-bundle --name metrics/churn --type Metric --title "Monthly Churn Rate"

# 3. Edit the generated files, then regenerate indexes
okf-schema index --path my-bundle

# 4. Lint frontmatter for compactness
okf-schema lint --path my-bundle

# 5. Validate strictly before shipping
okf-schema validate --path my-bundle --strict
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
| `backlinks --path <bundle> <target>...` | List concepts that link to the given target(s) |

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

### Errors (E1–E7)

| Code | Rule | Description |
|------|------|-------------|
| E1 | Parseable frontmatter | Every concept file must have valid YAML frontmatter |
| E2 | Non-empty `type` field | Frontmatter must contain a non-empty `type` field |
| E3 | Reserved file frontmatter | Only bundle-root `index.md` may have frontmatter; `log.md` must not |
| E4 | Schema validation | Frontmatter must validate against its type's JSONSchema |
| E5 | Flat lists | Frontmatter lists must not be nested (e.g. `tags: [[a], b]`) |
| E6 | Reserved file location | `log.md` must exist only at bundle root |
| E7 | Loose root file | Non-reserved `.md` files must not be placed at bundle root; move them into subdirectories |

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

## Recommended Workflows

### Shipping a bundle
Run these three commands in order and fix all warnings before packaging:
```bash
okf-schema index --path <bundle>    # regenerate all index.md files
okf-schema lint --path <bundle>     # convert block lists to inline for compact frontmatter
okf-schema validate --path <bundle> --strict # check structure, schema, and links; fail on warnings
```
Only zip or distribute the bundle once `validate --strict` reports zero errors **and** zero warnings.

### Iterative authoring
1. Create or edit concepts.
2. Run `okf-schema validate --path <bundle>` to catch structural issues early.
3. Use `okf-schema lint --path <bundle> --check` to preview changes before applying them.
4. Use `okf-schema backlinks --path <bundle> <concept>` to see which concepts reference a target before editing it.
5. Fix errors, then re-validate.

### Schema development
1. Place `.schema.json`, `.schema.json5`, or `.schema.yaml` files in a `_schema/` directory inside the bundle root.
2. Run `okf-schema validate --path <bundle>` — schemas are auto-discovered.
3. Iterate on schema definitions; JSON5 allows comments and trailing commas.

## Guardrails

1. **Never invent schema fields.** If a type lacks a schema, report a W6 warning — do not hallucinate constraints.
2. **Preserve unknown frontmatter keys.** OKF allows extensions; the linter and validator must not strip them.
3. **Preserve YAML comments.** The linter uses ruamel.yaml round-trip mode; comments and formatting must survive.
4. **Broken links are permitted by spec.** Report them as W2 warnings, not errors, unless `--strict` is used.
5. **Don't impose taxonomy.** Type values are free-form strings; okf-schema validates structure, not semantics.
6. **Ask before assuming bundle scope.** If the user mentions a bundle but no path, ask for the directory location.

## Output Format

When reporting validation results or presenting a bundle, use this structure:

1. **Directory tree** showing the bundle structure.
2. **Validation report** with errors and warnings grouped by code.
3. **Conformance verdict**: "Bundle is OKF conformant ✅" or "Bundle has N errors, M warnings ⚠️".

Example:
```
my-bundle/
├── index.md
├── _schema/
│   └── metric.schema.json
└── metrics/
    ├── mrr.md
    └── churn.md

Validation: 2 errors, 1 warning
- E2: metrics/mrr.md — missing 'type' field
- E7: root-concept.md — non-reserved file at bundle root
- W4: metrics/ — directory missing index.md
```

## References

- **[OKF v0.1 Specification](./references/okf-v0.1.md)** — The base format that `okf-schema` validates and extends. All OKF structural rules (bundle layout, frontmatter syntax, reserved files, linking conventions) are defined here.
- **[Conversions Guide](./references/conversions.md)** — Quick reference for converting existing content into OKF format (Obsidian vaults, CSV/spreadsheets, wikilinks, inline tags).
