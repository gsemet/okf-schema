# OKF-Schema vs. OKF Specification

`okf-schema` is an opinionated implementation of the
[Open Knowledge Format (OKF) specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).
Every bundle that passes `okf-schema` validation is a valid OKF bundle, but the
reverse is not always true: `okf-schema` enforces additional constraints that go
beyond the spec.

This page documents those differences so you can decide whether `okf-schema`'s
stricter model fits your use case.

---

## 1. Frontmatter is validated against JSONSchema

### What the spec says

The OKF spec requires only that every concept have a `type` field. The value can
be any string, and consumers must tolerate unknown types gracefully:

> Type values are **not** registered centrally. Producers SHOULD pick values
> that are descriptive and self-explanatory; consumers MUST tolerate unknown
> types gracefully.

The spec also permits any additional frontmatter keys beyond the standard fields:

> Producers MAY include any additional keys. Consumers SHOULD preserve unknown
> keys when round-tripping and SHOULD NOT reject documents with unrecognized
> fields.

### What OKF-Schema does

`okf-schema` treats the `type` field as a **schema selector**. A concept with
`type: concept` is validated against `_schema/concept.schema.yaml` (or `.json`,
`.json5`). Every field in the frontmatter is checked against the schema:

* **Required fields** missing → validation error
* **Wrong types** (e.g., string where integer expected) → validation error
* **Unknown fields** → controlled by the schema's `additionalProperties` setting
  (see §3 below)

This makes `okf-schema` bundles self-describing and machine-enforceable. The
trade-off is that you must maintain a schema for every concept type you use.

---

## 2. No root concepts

### What the spec says

The OKF spec places no restriction on where concept files live. A bundle may
contain `.md` files at the root level:

```
my_bundle/
├── index.md
├── overview.md          # ← valid in plain OKF
└── tables/
    └── orders.md
```

### What OKF-Schema does

`okf-schema` enforces **E7**: non-reserved `.md` files at the bundle root are
errors. The only files allowed at the root are:

* `index.md` — directory listing
* `log.md` — update history

All concepts must live inside subdirectories:

```
my_bundle/
├── index.md
├── log.md
└── tables/
    └── orders.md        # ← correct placement
```

This rule encourages a namespaced structure from the start and prevents
root-level clutter as the bundle grows.

---

## 3. Additional properties are schema-controlled

### What the spec says

The spec is permissive: producers may add any keys they like, and consumers must
not reject them.

### What OKF-Schema does

`okf-schema` delegates this decision to JSONSchema's `additionalProperties`
keyword:

* If the schema sets `additionalProperties: true` (or omits the key), extra
  fields are allowed.
* If the schema sets `additionalProperties: false`, extra fields are rejected as
  validation errors.

This gives bundle authors explicit control over frontmatter strictness. A tightly
governed bundle (e.g., a production data catalog) can lock down fields; an
experimental bundle can remain open.

---

## 4. Relative paths are preferred over bundle-relative paths

### What the spec says

The OKF specification allows both relative paths (`../tables/orders.md`) and
bundle-relative paths (`/tables/orders.md`) for internal links. Both are valid
according to the spec.

### What OKF-Schema recommends

`okf-schema` resolves both styles correctly, but **relative paths are preferred**
for internal links:

* **Portability** — Relative paths work correctly when a subdirectory is copied
  or symlinked into another bundle.
* **Tooling compatibility** — More markdown renderers and editors handle
  relative paths natively.
* **Clarity** — A relative path like `../tables/orders.md` makes the directory
  relationship explicit at a glance.

Bundle-relative paths (starting with `/`) are still fully supported and
validated, but authors should default to relative paths unless there is a
specific reason to anchor to the bundle root.

---

## Summary of differences

| Aspect | OKF Spec | OKF-Schema |
|--------|----------|------------|
| `type` field | Required, any string | Must match a schema file in `_schema/` |
| Frontmatter fields | Any keys allowed | Validated against JSONSchema |
| Extra / unknown keys | Always tolerated | Controlled by `additionalProperties` |
| Root `.md` files | Allowed | Forbidden (E7); only `index.md` and `log.md` |
| Internal link style | Relative or bundle-relative | Both supported; **relative preferred** |
| Schema location | None (spec does not use schemas) | `_schema/*.schema.{yaml,json,json5}` |

---

## What the linter does

The `okf-schema lint` command normalizes frontmatter without destroying human
edits. It uses `ruamel.yaml` in round-trip mode, which preserves:

* **Comments** — inline and block comments are kept intact
* **Key order** — frontmatter keys stay in their original sequence
* **Custom quotes** — single-quoted, double-quoted, and literal-block styles are
  retained

### Transformations applied

1. **Flatten nested lists**

   A nested YAML list like:

   ```yaml
   tags:
     - [sales, orders]
     - revenue
   ```

   becomes:

   ```yaml
   tags: [sales, orders, revenue]
   ```

2. **Convert block-style to inline (flow) style**

   The `lint` command (as opposed to `format`) also converts multi-line block
   lists into compact inline notation:

   ```yaml
   # Before
   tags:
     - sales
     - orders
     - revenue

   # After
   tags: [sales, orders, revenue]
   ```

   This keeps frontmatter compact, which matters for coding agents that often
   load only the first *n* lines of a file.

### Safety

The linter modifies files in place. Use `--check` to see which files would
change without writing anything, or `--diff` to preview the changes:

```bash
okf-schema lint --path my-bundle/bundle --check
okf-schema lint --path my-bundle/bundle --diff
```

Run `lint` before every commit to keep frontmatter formatting consistent across
the bundle.
