# Write a Custom Schema

OKF-Schema validates frontmatter against JSONSchema files in `_schema/`.
This guide shows how to write schemas for your own concept types.

## Schema file naming

Place schema files in `bundle/_schema/` with the naming convention:

```text
_schema/
  _base.schema.yaml      # Optional shared constraints
  table.schema.yaml      # Applied when type: table
  metric.schema.yaml     # Applied when type: metric
```

The `type` field selects the schema: `type: table` → `table.schema.yaml`.

## Supported file extensions

You can use YAML (`.yaml`, `.yml`), JSON (`.json`), or JSON5 (`.json5`)
for schema files. `_base.schema.yaml` is not applied implicitly; reference it
from each type schema that should inherit its constraints.

## Minimal schema example

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
properties:
  type:
    const: "table"
  title:
    type: string
  description:
    type: string
  owner:
    type: string
  columns:
    type: array
    items:
      type: object
      properties:
        name: { type: string }
        type: { type: string }
      required: [name, type]
required:
  - type
  - title
additionalProperties: false
```

## `$ref` between schemas

The resolver supports whole-file relative references. Compose shared
constraints with `allOf`:

```yaml
# _schema/_base.schema.yaml
type: object
properties:
  type: { type: string }
  title: { type: string }
required: [type, title]
```

```yaml
# _schema/table.schema.yaml
allOf:
  - $ref: "_base.schema.yaml"
  - type: object
    properties:
      type: { const: table }
      owner: { type: string }
```

Paths in `$ref` are relative to the `_schema/` directory.

## Declare file links with `x-okf-link`

A string's JSON Schema type does not tell a parser whether its value is prose,
an identifier, or a file link. The optional `x-okf-link` annotation makes that
meaning explicit for parsers, editors, and other consumers of OKF documents.
The annotation and checker belong to generic `okf-schema`; `okfkb` and `okfreq`
use that same contract in their default schemas, rather than defining link types
or separate resolution engines.
Consumers can identify file references and choose the correct resolution rule
without guessing from field names. An annotation on a string property declares
one file link; an annotation on an array's string `items` declares a list of
file links. The values remain ordinary strings, not a new JSON Schema type.

For example, save this schema as `bundle/_schema/artifact.schema.yaml`:

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
type: object
properties:
  type:
    const: artifact
  design:
    type: string
    x-okf-link:
      resolution: document-relative
      syntax: plain
  overview:
    type: string
    x-okf-link: {resolution: bundle-relative, syntax: plain}
  evidence:
    type: string
    x-okf-link: {resolution: bundle-relative-stem, syntax: plain}
  attachments:
    type: array
    items:
      type: string
      x-okf-link:
        resolution: project-relative
        syntax: plain
  related_notes:
    type: array
    items:
      type: string
      x-okf-link:
        resolution: filename-stem
        syntax: wikilink
required: [type]
```

An artifact document at `bundle/artifacts/report.md` can then contain:

```yaml
---
type: artifact
title: Export report
design: ../design/export.md
overview: design/overview.md
evidence: observations/export-run
attachments:
  - reports/export.csv
  - reports/summary.pdf
related_notes:
  - '[[Export-design#Decisions|Export design]]'
---
```

With project root `project/` and bundle root `project/bundle/`, the consumer
can resolve these values without guessing from property names:

| Field | Target file |
|---|---|
| `design` | `project/bundle/design/export.md` |
| `overview` | `project/bundle/design/overview.md` |
| `evidence` | `project/bundle/observations/export-run.md` |
| Each `attachments` item | `project/reports/export.csv`, `project/reports/summary.pdf` |
| Each `related_notes` item | The unique `Export-design.md` in the bundle, ignoring label and fragment |

Place the annotation on `items`, not on the array itself. Unannotated strings
do not acquire file-link semantics merely because they look like paths.

Both annotation keys are required:

| Key | Value | Meaning |
|---|---|---|
| `resolution` | `document-relative` | Exact file path from the Markdown document's parent directory; `../` is allowed. |
| `resolution` | `bundle-relative` | Exact file path from the bundle root. |
| `resolution` | `bundle-relative-stem` | Exact bundle-relative Markdown path without `.md`; append `.md`, preserving folders and dots in the stem. |
| `resolution` | `project-relative` | Exact file path from an explicit project root, or the containing Git root. |
| `resolution` | `filename-stem` | Case-sensitive Markdown basename lookup without the `.md` extension. |
| `syntax` | `plain` | The string directly contains the target path or stem. |
| `syntax` | `wikilink` | The string uses `[[target]]`, optionally with `#heading`, `#^block`, or `|label`. |

Syntax and resolution are independent: `[[Export-design]]` is wikilink syntax
with filename-stem resolution, while `[[../design/export.md]]` can use
document-relative resolution. Exact-path modes keep their extensions; no `.md`
suffix is added. Only `bundle-relative-stem` appends `.md`: `notes/cache` means
`notes/cache.md`, not any file named `cache.md` elsewhere in the bundle.
Heading and block existence is not checked. Consumers must
not treat labels or fragments as part of the target filename.

### Optional target checks

Ordinary JSON Schema validation ignores this custom keyword. File-target
checking is separately enabled with:

```bash
okf-schema validate --path bundle --check-links --project-root .
```

The CLI checks filename stems inside the bundle; it cannot discover an editor's
workspace. An unresolved stem or unavailable root produces `W15`, identifying
the skipped item and the reason. A missing exact target, ambiguous bundle-local
stem, malformed annotation, or rooted path escape produces `E10`. Project-root
lookup never falls back to the current working directory or workspace folders.
Bundle/project-relative paths reject absolute paths and escapes through `../`
or symlinks, including extensionless bundle paths. Existing schemas and bundles
are not upgraded or rewritten, and unannotated values are not checked as file
links. New scaffolds include the defaults for their layer; no migration is needed.
See the [Python API](../reference/api.md) for direct parser integration and the
[CLI reference](../reference/cli.md)
for standalone-file options and the
[okfreq frontmatter reference](../reference/okfreq-frontmatter.md)
for requirement-field conventions.
For Finding evidence and derivation links, see
[Set up an OKFKB](setup-okfkb.md).

The implementation's own requirements use this contract too: requirement IDs
are annotated filename stems, while generated source/test references are exact
project-relative links. See the
[requirements frontmatter example](../reference/okfreq-frontmatter.md)
for the repository's StRS/SwRS contract and its link-enabled validation command.

## Schema metadata for index generation

`okf-schema index` reads two optional top-level fields to produce richer
`index.md` files. These fields are **JSONSchema extensions** — they do not
affect validation, only the generated documentation.

| Field | Type | Purpose |
|-------|------|---------|
| `title` | `string` | Short heading used as the H1 in subdirectory `index.md` files |
| `description` | `string` | Intro text for a type-specific subdirectory |
| `x-okf-summary` | `string` | One-line description used in the root directory listing |

When either field is absent, the other is used as its fallback. When a
directory contains a mix of concept types, a generic fallback description is
used for the subdirectory intro.

### Example

```yaml
# _schema/metric.schema.yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
title: "Metric"
x-okf-summary: "Business and engineering metrics with targets and owners."
description: "Schema for KPIs, SLIs, and other measurable indicators."
properties:
  type:
    const: "metric"
  # ...
```

Running `okf-schema index` on a bundle with this schema produces:

- Root `index.md` entry: `[metrics](./metrics/) — Business and engineering metrics with targets and owners.`
- `metrics/index.md` heading: `# Metric`
- `metrics/index.md` intro paragraph: `Schema for KPIs, SLIs, and other measurable indicators.`

## Tips

* Start with `additionalProperties: true` while iterating, then lock down to `false` when stable.
* Use `enum` for fields with a fixed set of values (e.g., `status: [draft, review, published]`).
* Add `description` to every property: it becomes documentation for bundle authors.

## See also

- [OKF-Schema vs. OKF Specification](../reference/okf-schema-vs-spec) — how schema validation differs from the base spec.
- [Migrate Existing Documentation](migrate-existing-docs) — applying custom schemas to an existing docs folder.
- [Design Principles](../explanation/design-principles) — why self-describing bundles matter.
- [CLI Reference](../reference/cli.md) — `validate` command options.
