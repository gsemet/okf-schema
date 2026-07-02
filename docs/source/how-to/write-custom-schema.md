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

## Tips

* Start with `additionalProperties: true` while iterating, then lock down to `false` when stable.
* Use `enum` for fields with a fixed set of values (e.g., `status: [draft, review, published]`).
* Add `description` to every property: it becomes documentation for bundle authors.
