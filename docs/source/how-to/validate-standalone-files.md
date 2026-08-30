# How to Validate Standalone Markdown Files

This guide shows how to use the `validate-md` command to validate individual markdown files or collections of files against JSON schemas, without requiring a full OKF bundle.

## Quick Start

Validate all markdown files in a directory against schemas:

```bash
okf-schema validate-md \
  --input 'docs/**/*.md' \
  --schemas-dir ./schemas
```

## Common Use Cases

### Validate a Single File

```bash
okf-schema validate-md \
  --input 'notes/my-document.md' \
  --schemas-dir ./schemas
```

**Expected output** (success):
```
All files validated successfully (0 errors, 0 warnings).
```

**Expected output** (with warnings):
```
notes/my-document.md
  WARNING [W1] Missing recommended field 'title' in 'notes/my-document.md'
  WARNING [W3] No provenance timestamp in 'notes/my-document.md'. Add 'generated.at: <ISO-8601-datetime>' to the frontmatter.

Validation passed: 2 warning(s).
```

### Validate Multiple Patterns

Combine patterns using multiple `--input` flags:

```bash
okf-schema validate-md \
  --input '*.md' \
  --input 'docs/**/*.md' \
  --input 'notes/**/*.md' \
  --schemas-dir ./schemas
```

This validates all `.md` files in the current directory, plus all markdown files under `docs/` and `notes/` recursively.

### Validate with Strict Mode

Enable strict mode to treat warnings as errors:

```bash
okf-schema validate-md \
  --input 'docs/**/*.md' \
  --schemas-dir ./schemas \
  --strict
```

With `--strict`:
- Exit code is 1 if warnings are found (in addition to errors)
- Useful for CI/CD pipelines where best practices must be enforced

**Without `--strict`** (default):
- Exit code is 0 as long as no errors exist (warnings are allowed)

## Schema Setup

The `--schemas-dir` directory should contain schema files named `<type>.schema.{json|json5|yaml|yml}`.

### Example Schema Structure

```
schemas/
  concept.schema.json        # Schema for type: concept
  principle.schema.json      # Schema for type: principle
  reference.schema.yaml      # Schema for type: reference
  _base.schema.json          # (optional) Base schema with $ref
```

### Example Schema File

**`schemas/concept.schema.json`**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type": { "enum": ["concept"] },
    "title": { "type": "string" },
    "description": { "type": "string" },
    "category": { "enum": ["AI", "Engineering", "Process"] },
    "tags": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["type", "title", "description"]
}
```

### Referencing Other Schemas

You can use `$ref` to reference other schema files:

**`schemas/concept.schema.json`**:
```json
{
  "$ref": "_base.schema.json",
  "properties": {
    "category": { "enum": ["AI", "Engineering", "Process"] }
  },
  "required": ["category"]
}
```

The `$ref` path is resolved relative to the schemas directory.

## File Format Requirements

Each markdown file must have YAML frontmatter:

```markdown
---
type: concept
title: My Concept
description: A brief description
---

# My Concept

The document content goes here.
```

### Frontmatter Rules

- Must start with `---` on line 1
- Contains YAML key-value pairs
- Must end with `---` before the document body
- Must have a `type` field (to match a schema)

### Minimal Structurally Valid File

```markdown
---
type: concept
title: My Concept
---

Content here.
```

This passes structural checks but still reports W1 for a missing
`description` and W3 for missing `generated.at`.

## Validation Checks

The `validate-md` command checks the following (unless noted as bundle-only):

| Code | Check | Example Fix |
|------|-------|-------------|
| **E1** | Frontmatter exists and is valid YAML | Add `---` and valid YAML |
| **E2** | `type` field is non-empty | Add `type: concept` |
| **E4** | Frontmatter matches the schema | Match schema requirements |
| **E5** | Lists in frontmatter are flattened | Use `[a, b, c]` not `[[a], [b], [c]]` |
| **E7** | `generated` has valid structure | Use a mapping with `at` and optional `by` |
| **E8** | Source IDs are unique | Give every `sources[]` item a distinct `id` |
| **E9** | Lifecycle dates are valid | Use ISO 8601 values and a valid date order |
| **W1** | Recommended fields (`title`, `description`) are present | Add `title:` and `description:` |
| **W3** | Provenance timestamp is present | Add `generated: {at: "2024-07-06T00:00:00Z"}` |
| **W6** | Schema exists for the `type` value | Create or use an existing schema |
| **W7** | Lists use inline notation, not block style | Use `tags: [a, b]` not `tags:\n  - a\n  - b` |
| **W8** | Legacy `timestamp` is absent | Run bundle lint or migrate it to `generated.at` |
| **W9** | Legacy `# Citations` section is absent | Use `sources` and footnotes |
| **W10** | Verification actors are well formed | Use `<prefix>:<identifier>` |
| **W11** | Content is not stale | Refresh or revise `stale_after` |
| **W12** | Footnotes match source IDs | Add the corresponding `sources[].id` |
| **W13** | Local source resources resolve | Correct `sources[].resource` |

**Not checked in `validate-md`** (bundle-only):

- W2: Broken cross-links (no common bundle root)
- W4: Missing `index.md` in directories
- E3, E6: Bundle structure rules

For full reference, see [Validation Error & Warning Codes](../reference/validation-codes).

## Interpreting Results

### Successful Validation

```bash
$ okf-schema validate-md --input 'docs/**/*.md' --schemas-dir ./schemas
All files validated successfully (0 errors, 0 warnings).
```

Exit code: **0** ✅

### Validation with Warnings

```bash
$ okf-schema validate-md --input 'docs/**/*.md' --schemas-dir ./schemas
docs/concept-a.md
  WARNING [W1] Missing recommended field 'title' in 'docs/concept-a.md'

docs/concept-b.md
  WARNING [W3] No provenance timestamp in 'docs/concept-b.md'. Add 'generated.at: <ISO-8601-datetime>' to the frontmatter.

Validation passed: 2 warning(s).
```

Exit code: **0** ✅ (warnings allowed by default)

### Validation with Errors

```bash
$ okf-schema validate-md --input 'docs/**/*.md' --schemas-dir ./schemas
docs/bad-file.md
  ERROR   [E2] File 'docs/bad-file.md' has frontmatter but no 'type' field
  ERROR   [E4] Schema validation failed for 'docs/bad-file.md': [category] 'unknown' is not one of the allowed values: ['AI', 'Engineering']

Validation failed: 2 error(s), 0 warning(s).
```

Exit code: **1** ❌

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/validate.yml`:

```yaml
name: Validate Markdown

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install okf-schema
      - run: |
          okf-schema validate-md \
            --input 'docs/**/*.md' \
            --schemas-dir ./schemas \
            --strict
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
validate:markdown:
  image: python:3.10
  script:
    - pip install okf-schema
    - okf-schema validate-md
      --input 'docs/**/*.md'
      --schemas-dir ./schemas
      --strict
```

## Troubleshooting

### "Schemas directory does not exist"

**Problem**: The `--schemas-dir` path is incorrect or doesn't exist.

**Solution**: Verify the path and ensure it contains schema files:
```bash
ls -la ./schemas/    # Check what's in the directory
okf-schema validate-md --input 'docs/**/*.md' --schemas-dir ./schemas
```

### "No schema found for type"

**Problem**: A file declares `type: mytype` but there is no `mytype.schema.json` file.

**Solution**: Either create the schema or use an existing type:
```bash
# List available schemas
ls schemas/*.schema.*

# Or check your file's type
grep "^type:" docs/my-file.md
```

### No files matched the pattern

**Problem**: The `--input` glob pattern didn't match any files.

**Solutions**:
- Check the pattern: `ls docs/**/*.md` (same pattern outside okf-schema)
- Use a simpler pattern first: `--input '*.md'`
- Verify files exist in the expected location

### Validation fails on CI/CD but passes locally

**Problem**: File paths may differ (absolute vs. relative, or working directory mismatch).

**Solution**: Use consistent working directories and relative paths:
```bash
cd /path/to/project
okf-schema validate-md --input 'docs/**/*.md' --schemas-dir ./schemas
```

---

## Next Steps

- See [Validation Error & Warning Codes](../reference/validation-codes) for details on each error/warning
- Explore [CLI Reference](../reference/cli) for all available commands
