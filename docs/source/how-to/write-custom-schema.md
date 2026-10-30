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

Schemas may also add optional navigation hints to `x-okf-link`:

| Key | Value | Meaning |
|---|---|---|
| `basename_marker` | `string` | Marker prefix associated with basename-based navigation in the resolved target file. A basename is the filename without its extension. |
| `id_marker` | `string` | Frontmatter field whose value supplies the identity for navigation. `id` is the normal value when a stable frontmatter identity is available. |
| `tooltip_shows_fields` | `array[string]` | Linked frontmatter fields that a consumer may show in a hover tooltip. |
| `preview_shows_fields` | `array[string]` | Linked frontmatter fields that a consumer may show in a preview. |
| `show_line_number` | `boolean` | Whether a consumer should preserve the source line for marker navigation. |

These are `x-okf-link` metadata, not JSON Schema validation keywords. They let an
editor or other consumer resolve a file and then search for a line such as
`@implements_req SwRS-demo-001` or `@tests_req SwRS-demo-001`, opening the file
at that line. In the requirement defaults, the marker prefix comes from
`basename_marker` and the requirement identity comes from `id_marker: id`;
for requirement-to-requirement links, `id_marker: id` identifies the target
requirement's `id` line. The generic checker resolves the target file, but does
not parse marker lines or claim that a marker proves coverage.
Presentation hints are advisory and are not rendered by the generic CLI.

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
workspace. An unavailable root or inaccessible matching candidate produces `W15`, identifying
the skipped item and the reason. A missing exact target or bundle-local stem, ambiguous bundle-local
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

## Project metadata for plain OKF consumers

A consumer that knows only the OKF specification reads relations from Markdown
links in the body (section 6.1) and the lifecycle from `status` (section 5.4).
When your bundle keeps relations as frontmatter IDs or uses its own lifecycle
words, declare in the schema how they are projected; `okf-schema lint` and
`okfkb update` then maintain the projection:

```yaml
properties:
  state:
    type: string
    enum: [wip, done, gone]
    x-okf-status-projection: {wip: draft, done: stable, gone: deprecated}
  parents:
    type: array
    items:
      type: string
      x-okf-link: {resolution: filename-stem, syntax: plain, link-projection: Parents}
```

```bash
okf-schema lint --path bundle
okf-schema lint --path bundle --check   # exit 1 when a projection is stale
```

A document with `state: wip` and `parents: [root, missing]` becomes:

```markdown
---
type: note
state: wip
status: draft
parents: [root, missing]
---

# Child

<!-- okf:links:start -->
### Links

<!-- Generated from the frontmatter relations; edit them instead. -->

- Parents:
  - [root](root.md): Root note
  - `missing`
<!-- okf:links:end -->
```

- One group per annotated field, in schema order (an `allOf` base schema first),
  one relative link per value followed by the target title. A value that does
  not resolve stays as code, so no broken link is written.
- Renaming a label renames its group; removing it removes the group, and a
  section without groups is removed, on the next lint.
- Only `filename-stem`, `bundle-relative` and `bundle-relative-stem` targets can be
  projected; `okf-schema validate` reports `E11` for a label on another resolution
  and for a status mapping that misses an `enum` value or maps to anything other
  than `draft`, `stable` or `deprecated`.
- `lint --links` skips the generated section, so `links`/`backlinks` keep listing
  authored links only. `--no-link-projection` turns the projection off for one run.

## Check that your schema is loaded

Validation tells you when a schema file yields no schema, so a new or broken file
never makes a type silently unchecked:

```console
$ : > _schema/task.schema.yaml
$ echo '{"type": "object",' > _schema/note.schema.json
$ okf-schema validate --path bundle
bundle/_schema/note.schema.json
  WARNING [W17] schema file 'note.schema.json' cannot be parsed: Expecting property name enclosed in double quotes: line 2 column 1 (char 19)

bundle/_schema/task.schema.yaml
  INFO    [I1] schema file 'task.schema.yaml' is empty
```

An empty (or comment-only) file is informational (`I1`) and never fails `--strict`.
A syntax error, an unreadable file or a non-mapping value is warning `W17`.
In both cases the type stays without schema. See the
[validation codes](../reference/validation-codes.md).

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

### Composed schemas and conditional links

The checker follows local `$ref` definitions, object `properties`, array
`items`/`prefixItems`, `allOf`, applicable `anyOf`/`oneOf` branches, and the
selected branch of `if`/`then`/`else`. A referenced constraint and its siblings
both apply; a sibling does not overwrite the definition's constraint.

For example, only local-file records below require a target file:

```yaml
if:
  properties:
    kind: {const: local-file}
  required: [kind]
then:
  properties:
    target:
      type: string
      x-okf-link: {resolution: document-relative, syntax: plain}
```

Put annotations in these supported locations. Schema keywords such as
`patternProperties`, `additionalProperties`, `dependentSchemas`, and `contains`
do not currently contribute file-link annotations; ordinary JSON Schema
validation still applies to those keywords. Move link declarations to explicit
properties/items or an applicable composition branch when target inspection is
required. External `$ref` files are inlined by the bundle schema loader; the
direct inspection API follows local references within the supplied schema.
