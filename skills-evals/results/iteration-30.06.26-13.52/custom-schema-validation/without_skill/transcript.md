# A/B Skill Evaluation — Custom Schema Validation (WITHOUT skill access)

**Date:** 2026-06-30  
**Task:** Create a minimal OKF bundle with a custom concept type `api-endpoint` and a custom JSONSchema that validates `method` and `path` are strings. The bundle must pass `okf-schema validate --strict` with zero errors and zero warnings.

---

## Step 1: Read the OKF specification

**File:** `skills/okf-schema/references/okf-v0.1.md`

Key findings from the spec:
- A bundle is a directory tree of markdown files with YAML frontmatter.
- Every concept must have a `type` field (required).
- Reserved filenames: `index.md`, `log.md`.
- Producers MAY include any additional keys in frontmatter.
- Schema validation is supported via a `_schema/` directory inside the bundle.

---

## Step 2: Discover CLI commands

**Command:**
```bash
uv run -- okf-schema --help
```

**Output:**
```
Usage: okf-schema [OPTIONS] [COMMAND] [ARGS]...

  CLI tool and Python library for OKF bundle management.

Options:
  --version      Show the version and exit.
  -v, --verbose  Increase verbosity (up to 3).
  -q, --quiet    Suppress non-error output.
  -h, --help     Show this message and exit.

Commands:
  index     Regenerate all index.md files in an OKF bundle.
  init      Create a new OKF bundle directory structure.
  lint      Lint frontmatter: flatten nested lists and convert...
  list      List all concepts in an OKF bundle.
  new       Create a new OKF concept file with frontmatter template.
  show      Show a single concept's frontmatter and body.
  stats     Show compact statistics for an OKF bundle.
  validate  Validate an OKF bundle.
```

---

## Step 3: Discover validate command options

**Command:**
```bash
uv run -- okf-schema validate --help
```

**Output:**
```
Usage: okf-schema validate [OPTIONS]

  Validate an OKF bundle.

Options:
  --path DIRECTORY       Root directory of the OKF bundle.  [required]
  --schema-db DIRECTORY  Override the built-in _schema directory inside the
                         bundle.
  --strict               Treat warnings as errors (exit 1 if any warning is
                         present).
  -h, --help             Show this message and exit.
```

---

## Step 4: Inspect existing schema examples

**Command:**
```bash
find /Users/az02065/Projects/DevTools/okf-schema -type f -name "*.schema.json" | head -10
```

**Output:**
```
/Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/schema-db/metric.schema.json
/Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/schema-db/table.schema.json
/Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/bootstrap-output/_schema/Concept.schema.json
/Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/bootstrap-output/_schema/reference.schema.json
/Users/az02065/Projects/DevTools/okf-schema/tests/fixtures/schema/concept.schema.json
```

Key findings from existing schemas:
- Schema files are named `<type>.schema.json`.
- They use JSON Schema Draft 2020-12.
- The `type` property uses `const` to match the concept type.
- `additionalProperties: true` allows extra fields.

---

## Step 5: Inspect existing bundle structure

**Command:**
```bash
ls -la /Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/bootstrap-output/
```

**Output:**
```
_schema/
cells/
index.md
log.md
safety/
thermal/
```

**Command:**
```bash
ls -la /Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/bootstrap-output/_schema/
```

**Output:**
```
Concept.schema.json
reference.schema.json
```

---

## Step 6: Create the bundle directory structure

**Command:**
```bash
mkdir -p /Users/az02065/Projects/DevTools/okf-schema/skills-evals/fixtures/schema-output/_schema
```

**Output:** *(no output — command succeeded)*

---

## Step 7: Create the custom JSONSchema

**File:** `skills-evals/fixtures/schema-output/_schema/api-endpoint.schema.json`

**Content:**
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

---

## Step 8: Create the concept file

**File:** `skills-evals/fixtures/schema-output/get-user.md`

**Content:**
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

```json
{
  "id": "123",
  "name": "Alice"
}
```
```

---

## Step 9: Validate the bundle

**Command:**
```bash
uv run -- okf-schema validate --path skills-evals/fixtures/schema-output --strict
```

**Output:**
```
```

*(No output — validation passed with 0 errors and 0 warnings.)*

---

## Final Result

✅ **Validation passed** — `okf-schema validate --strict` returned exit code 0 with zero errors and zero warnings.

### Bundle structure

```
skills-evals/fixtures/schema-output/
├── _schema/
│   └── api-endpoint.schema.json
└── get-user.md
```

### Schema highlights

- Validates `method` and `path` are strings.
- Uses `const: "api-endpoint"` to match the concept type.
- `additionalProperties: true` allows extra fields (permissive).
- `required: ["type", "method", "path"]` ensures both custom fields are present.

### Concept highlights

- Frontmatter includes `type: api-endpoint`, `method: GET`, and `path: /api/v1/users/{id}`.
- Includes recommended fields (`title`, `description`, `timestamp`) to avoid W1/W3 warnings.
- No broken cross-links (avoids W2).
- No block-style lists (avoids W7).
