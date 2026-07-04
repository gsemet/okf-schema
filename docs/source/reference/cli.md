# CLI Reference

The `okf-schema` command-line tool provides subcommands for managing OKF bundles.

## Global options

```bash
okf-schema [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit. |
| `--version` | Show version and exit. |
| `-v, --verbose` | Increase verbosity (up to 3). |
| `-q, --quiet` | Suppress non-error output. |

---

## `okf-schema init`

Create a new OKF bundle directory structure.

```bash
okf-schema init NAME
```

Creates a directory `NAME/bundle/` with `index.md`, `log.md`, and `_schema/_base.schema.yaml`.

---

## `okf-schema new`

Create a new OKF concept file with frontmatter template.

```bash
okf-schema new --path ROOT --name CONCEPT [--type TYPE] [--title TITLE]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | ✅ | — | Root directory for the new concept. |
| `--name` | ✅ | — | Relative path of the concept (without `.md`). |
| `--type` | — | `concept` | Concept type. |
| `--title` | — | (derived from name) | Concept title. |

---

## `okf-schema validate`

Validate an OKF bundle against its schemas.

```bash
okf-schema validate --path BUNDLE [--schema-db DIR] [--strict]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | ✅ | — | Root directory of the OKF bundle. |
| `--schema-db` | — | `_schema/` inside bundle | Override schema directory. |
| `--strict` | — | `False` | Treat warnings as errors. |

---

## `okf-schema lint`

Lint frontmatter: flatten nested lists, convert block-style to inline, and
auto-update `links` and `backlinks` fields from markdown body content.

```bash
okf-schema lint --path BUNDLE [--check] [--diff] [--links|--no-links]
```

| Option | Description |
|--------|-------------|
| `--check` | Report files that would change without modifying. |
| `--diff` | Show unified diff without modifying. |
| `--links` | Update `links` and `backlinks` from markdown body (default). |
| `--no-links` | Skip updating `links` and `backlinks`. |

---

## `okf-schema list`

List all concepts in an OKF bundle.

```bash
okf-schema list --path BUNDLE
```

Output format: `path  type  title`

---

## `okf-schema show`

Show a single concept's frontmatter and body.

```bash
okf-schema show --path BUNDLE CONCEPT_PATH
```

---

## `okf-schema index`

Regenerate all `index.md` files in an OKF bundle.

```bash
okf-schema index --path BUNDLE
```

---

## `okf-schema stats`

Show compact statistics for an OKF bundle.

```bash
okf-schema stats --path BUNDLE
```

---

## `okf-schema backlinks`

List all concepts that link to the given target concept(s).

```bash
okf-schema backlinks --path BUNDLE TARGETS...
```

One line is printed per backlink in the form `target ← source`.
Multiple target paths may be provided. The `.md` extension is optional.

---

## `okf-schema search`

Search concepts by title, description, type, or tags.

```bash
okf-schema search --path BUNDLE QUERY
```

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success. |
| `1` | Validation or lint failure. |
| `2` | Runtime error (file not found, etc.). |

## See also

- [KB Commands](kb-commands) — knowledge-base specific commands (`okfkb`).
- [Python API](api) — programmatic interface to the same operations.
- [Getting Started](../tutorials/getting-started) — tutorial using these commands.
- [Validate in CI](../how-to/validate-in-ci) — CI examples for `validate --strict`.
- [Lint Before Commit](../how-to/lint-before-commit) — pre-commit hook for `lint`.
