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
okf-schema init NAME [--pattern PATTERN]
```

Creates a directory `NAME/bundle/` with `index.md`, `log.md`, and `_schema/_base.schema.yaml`.

| Option | Description |
|--------|-------------|
| `--pattern` | Use a named scaffold pattern. `kb` creates the opinionated knowledge-base layout. |

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
	[--check-links] [--project-root DIR]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | ✅ | — | Root directory of the OKF bundle. |
| `--schema-db` | — | `_schema/` inside bundle | Override schema directory. |
| `--strict` | — | `False` | Treat warnings as errors. |
| `--check-links` | — | `False` | Check opt-in `x-okf-link` annotations. |
| `--project-root` | — | — | Explicit root for `project-relative` targets. |

---

## `okf-schema validate-md`

Validate standalone markdown files without requiring an OKF bundle.

```bash
okf-schema validate-md --input 'notes/**/*.md' --schemas-dir ./schemas [--strict]
	[--check-links] [--bundle-root DIR] [--project-root DIR]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--input` | ✅ | Glob for markdown files. Repeat the option to supply multiple patterns. |
| `--schemas-dir` | ✅ | Directory containing `<type>.schema.{json,json5,yaml,yml}` files. |
| `--strict` | — | Treat warnings as errors. |
| `--check-links` | — | Check opt-in `x-okf-link` annotations. |
| `--bundle-root` | — | Root for `bundle-relative`, `bundle-relative-stem`, and `filename-stem` targets. |
| `--project-root` | — | Explicit root for `project-relative` targets. |

## `x-okf-link` annotations

Schemas may attach the non-validating `x-okf-link` annotation to a string schema,
including an array's `items` schema. It lets parsers and editors distinguish a
single file link or a list of file links from ordinary string values, without
changing the JSON Schema type or guessing from property names. See
[Declare file links](../how-to/write-custom-schema.md)
for a complete schema and matching frontmatter example. It has two required keys:

```yaml
type: string
x-okf-link:
  resolution: project-relative
  syntax: plain
```

For example, a schema can describe a scalar design file and a list of source
files while keeping both values as ordinary strings:

```yaml
properties:
  design:
    type: string
    x-okf-link: {resolution: document-relative, syntax: plain}
  implemented_in_files:
    type: array
    items:
      type: string
      x-okf-link: {resolution: project-relative, syntax: plain}
```

The matching frontmatter is then unambiguous to a parser or editor:

```yaml
design: ../design/export.md
implemented_in_files:
  - src/export.py
  - src/report.py
```

`resolution` is one of `document-relative`, `bundle-relative`,
`bundle-relative-stem`, `project-relative`, or `filename-stem`. Document-relative paths start at the
Markdown document's parent directory. Bundle-relative paths start at the bundle
root. Bundle-relative stems resolve a precise extensionless Markdown path:
`findings/cache-observation` means `findings/cache-observation.md` under the
bundle root, not a basename search. Project-relative paths use `--project-root`, then the document's containing
Git root; they never fall back to the current working directory or an editor
workspace. Filename stems search Markdown basenames inside the bundle, without
the `.md` suffix, and matching is case-sensitive. Duplicate stems are errors.

`syntax` is either `plain` or `wikilink`. Wikilinks may include a heading or
block fragment and a display label, such as `[[notes.md#heading|Read this]]`.
Only the target file is checked; fragment existence is not checked. Exact paths
keep their extensions and do not receive an automatic `.md` suffix.
Only `bundle-relative-stem` appends `.md` to the full relative target.

Checking is disabled by default, so ordinary JSON Schema validation is unchanged.
With `--check-links`, missing exact targets, root escapes, ambiguous stems, and
malformed annotations produce `E10`. An unavailable root or an unresolved stem
produces `W15`, explicitly identifying the skipped field and reason. Bundle and
project-relative paths reject absolute paths and symlink escapes; document-relative
paths may use `../`.
The generic API owns this behavior and both opinionated layers reuse it.
New scaffolds annotate their default link fields; existing schemas and bundles
are left unchanged, with no migration required.

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

## `okf-schema kb`

Run the opinionated knowledge-base command group. It includes `init`,
`install-skills`, `new-finding`, `update`, `validate`, `read`, `get`,
`search`, and `query`.

```bash
okf-schema kb --help
```

The same commands are also available through the `okfkb` executable. See
[KB Commands](kb-commands) for their complete syntax. Generic bundle search
is available through `okf_schema.api.search_bundle`, not as a top-level CLI
command.

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
