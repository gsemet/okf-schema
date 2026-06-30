# Custom Schema Validation — With Skill Transcript

**Date**: 2026-06-30
**Task**: Create a minimal OKF bundle at `skills-evals/fixtures/schema-output/` with a custom concept type `api-endpoint`, a custom JSONSchema in `_schema/`, and validate it passes `okf-schema validate --strict` with 0 errors and 0 warnings.

---

## Step 1: Read SKILL.md for schema placement and naming conventions

**File**: `skills/okf-schema/SKILL.md`

Key findings:
- Custom schemas go in a `_schema/` directory inside the bundle root.
- Schema files are auto-discovered by `validate`.
- Files must be named `<type>.schema.json`, `<type>.schema.json5`, or `<type>.schema.yaml`.
- The *type* key is the stem before `.schema`.
- The `_schema/` directory is automatically used when it exists (no `--schema-db` needed).

## Step 2: Read OKF v0.1 specification

**File**: `skills/okf-schema/references/okf-v0.1.md`

Key findings:
- Bundle structure: `index.md`, `log.md`, concept files, subdirectories.
- Reserved files: `index.md` and `log.md`.
- Frontmatter requires `type` field; recommended fields include `title`, `description`, `timestamp`, `tags`.
- Body is standard markdown.

## Step 3: Inspect validator source code for auto-discovery logic

**File**: `src/okf_schema/validator.py`

Key findings:
- `load_schema_database(schema_db)` loads files named `<type>.schema.json`, `<type>.schema.json5`, or `<type>.schema.yaml`.
- `validate_bundle()` in `api.py` auto-discovers `_schema/` inside the bundle when `schema_db` is not provided.

## Step 4: Inspect existing fixture files

The fixture directory `skills-evals/fixtures/schema-output/` already contained:
- `get-user.md` — concept file with `type: api-endpoint`, `method: GET`, `path: /api/v1/users/{id}`
- `_schema/api-endpoint.schema.json` — custom JSONSchema validating `method` and `path` as strings
- `index.md` — bundle root index
- `log.md` — bundle root log

## Step 5: Run validation

### Command
```bash
uv run -- okf-schema validate --path skills-evals/fixtures/schema-output --strict
```

### Output
```
Bundle is conformant (0 errors, 0 warnings).
```

---

## Result

✅ **PASS** — The bundle passes `okf-schema validate --strict` with **0 errors** and **0 warnings**.

## Files in the bundle

```
skills-evals/fixtures/schema-output/
├── index.md
├── log.md
├── get-user.md
└── _schema/
    └── api-endpoint.schema.json
```

### `get-user.md`
```markdown
---
type: api-endpoint
title: Get User
description: Retrieve a user by their unique identifier.
timestamp: 2026-06-30T13:52:00Z
method: GET
path: /api/v1/users/{id}
---

# Get User

Retrieve detailed information about a user.

## Request

```http
GET /api/v1/users/{id}
```

## Response
```

### `_schema/api-endpoint.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OKF API Endpoint Concept",
  "description": "Schema for an API endpoint concept in an OKF bundle.",
  "type": "object",
  "additionalProperties": true,
  "properties": {
    "type": {
      "type": "string",
      "description": "OKF concept type",
      "const": "api-endpoint"
    },
    "title": {
      "type": "string",
      "description": "Human-readable name of the endpoint"
    },
    "description": {
      "type": "string",
      "description": "What the endpoint does"
    },
    "timestamp": {
      "type": "string",
      "description": "ISO 8601 timestamp of last modification",
      "format": "date-time"
    },
    "method": {
      "type": "string",
      "description": "HTTP verb (GET, POST, PUT, DELETE, etc.)"
    },
    "path": {
      "type": "string",
      "description": "URL path of the endpoint"
    }
  },
  "required": ["type", "method", "path"]
}
```
