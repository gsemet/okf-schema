# Write a Custom Schema

OKF-Schema validates frontmatter against JSONSchema files in `_schema/`.
This guide shows how to write schemas for your own concept types.

## Schema file naming

Place schema files in `bundle/_schema/` with the naming convention:

```
_schema/
  _base.schema.yaml      # Applied to all concepts
  table.schema.yaml      # Applied when type: table
  metric.schema.yaml     # Applied when type: metric
```

The `type` field selects the schema: `type: table` → `table.schema.yaml`.

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

Reference shared definitions across schemas:

```yaml
# _schema/_common.schema.yaml
definitions:
  timestamp:
    type: string
    format: date-time
```

```yaml
# _schema/table.schema.yaml
properties:
  created_at:
    $ref: "_common.schema.yaml#/definitions/timestamp"
```

Paths in `$ref` are relative to the `_schema/` directory.

## Schema metadata for index generation

`okf-schema index` reads two optional top-level fields to produce richer
`index.md` files. These fields are **JSONSchema extensions** — they do not
affect validation, only the generated documentation.

| Field | Type | Purpose |
|-------|------|---------|
| `title` | `string` | Short heading used as the H1 in subdirectory `index.md` files |
| `x-okf-summary` | `string` | One-line description shown in the subdirectory intro and in the root directory listing |

When `x-okf-summary` is absent, `description` is used as a fallback. When a
directory contains a mix of concept types, a generic fallback description is
used instead.

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
- `metrics/index.md` intro paragraph: `Business and engineering metrics with targets and owners.`

## Tips

* Start with `additionalProperties: true` while iterating, then lock down to `false` when stable.
* Use `enum` for fields with a fixed set of values (e.g., `status: [draft, review, published]`).
* Add `description` to every property: it becomes documentation for bundle authors.
