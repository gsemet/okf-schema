# Validation Error & Warning Codes

This reference documents all validation codes returned by okf-schema's validation commands (`validate` and `validate-md`).

## Error Codes (E1–E7)

Errors represent conformance violations that must be fixed before the validation passes.

### E1: Missing or Unparseable Frontmatter

**Severity**: Error

**Description**: A markdown file lacks YAML frontmatter (the `---` delimiter at the start) or contains unparseable YAML.

**Example**:
```markdown
# My Document

This file has no frontmatter.
```

**How to Fix**:
Add proper YAML frontmatter at the beginning of the file:
```markdown
---
type: concept
title: My Document
description: A brief description
---

# My Document

Document content here.
```

---

### E2: Missing or Empty `type` Field

**Severity**: Error

**Description**: The frontmatter is valid YAML, but the `type` field is missing, null, or empty.

**Example**:
```yaml
---
title: My Concept
description: A concept without a type
---
```

**How to Fix**:
Add a non-empty `type` field to the frontmatter:
```yaml
---
type: concept
title: My Concept
description: A concept without a type
---
```

---

### E3: Reserved File with Unexpected Frontmatter

**Severity**: Error

**Description**: A reserved file (`index.md` or `log.md`) has frontmatter when it should not.

**Rule**:
- `log.md` must NEVER have frontmatter (applies only to OKF bundle validation)
- Non-root `index.md` files must NOT have frontmatter
- Only the bundle-root `index.md` may optionally have frontmatter (with `okf_version` field)

**How to Fix**:
For `log.md`: Remove the frontmatter block and keep only dated headings.

For non-root `index.md`: Remove the `---` delimiters and frontmatter, keeping only the body content.

---

### E4: Schema Validation Failed

**Severity**: Error

**Description**: The frontmatter failed validation against the corresponding JSON Schema.

**Example**:
```
[type] 'unknown_type' is not one of the allowed values: ['concept', 'principle', 'reference']
[required_field] 'title' is a required property
```

**How to Fix**:
Examine the schema error message and adjust the frontmatter to match the schema requirements. Common issues:
- Missing required fields (check your schema for `required` list)
- Invalid enum values (must match allowed values exactly)
- Wrong data types (e.g., string when number expected)

---

### E5: Nested List Structures in Frontmatter

**Severity**: Error

**Description**: The frontmatter contains nested list structures, which indicate flatten-able content. This is considered an error because coding agents typically load only the first N lines of a file, and nested structures expand the frontmatter unnecessarily.

**Example**:
```yaml
---
type: concept
tags: [[common, important], [ai, llm]]  # Nested lists
---
```

**How to Fix**:
Flatten nested lists into a single level:
```yaml
---
type: concept
tags: [common, important, ai, llm]
---
```

---

### E6: Reserved File Not at Bundle Root

**Severity**: Error (OKF bundle validation only)

**Description**: A reserved file is located in an unexpected directory. Specifically, `log.md` must be at the bundle root.

**How to Fix**:
Move the file to the correct location. For `log.md`, it must be at the root of your OKF bundle.

---

### E7: Non-Reserved File at Bundle Root

**Severity**: Error (OKF bundle validation only)

**Description**: A non-reserved markdown file (not `index.md` or `log.md`) exists at the bundle root. All concept files must be in subdirectories.

**How to Fix**:
Move the markdown file into a subdirectory (e.g., `concepts/`, `principles/`, etc.):
```
bundle/
  concepts/
    my-concept.md      # Correct location
  index.md
  log.md
```

---

## Warning Codes (W1–W7)

Warnings indicate best-practice violations or missing metadata. Validation passes with warnings unless `--strict` mode is enabled.

### W1: Missing Recommended Fields

**Severity**: Warning

**Description**: Recommended frontmatter fields (`title` or `description`) are missing or empty.

**Why It Matters**:
- `title`: Provides a human-readable name for the concept
- `description`: Summarizes the concept's purpose in 1–2 sentences

These fields are important for browsing and searching knowledge bases.

**How to Fix**:
Add the missing fields:
```yaml
---
type: concept
title: My Important Concept
description: A brief, one-sentence summary of what this concept is about
---
```

---

### W2: Broken Cross-Link

**Severity**: Warning (OKF bundle validation only)

**Description**: A markdown link in the file body points to a file that does not exist.

**Example**:
```markdown
See also [related concept](../concepts/related.md) for more details.
```

If `related.md` does not exist, this triggers a W2 warning.

**How to Fix**:
Either:
1. Create the referenced file, or
2. Update the link to point to a file that exists, or
3. Remove the broken link

---

### W3: Missing Timestamp Field

**Severity**: Warning

**Description**: The frontmatter lacks an ISO 8601 timestamp field, which is useful for tracking when a concept was last updated.

**How to Fix**:
Add a `timestamp` field in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ):
```yaml
---
type: concept
title: My Concept
timestamp: "2024-07-06"
---
```

---

### W4: Missing index.md in Directory

**Severity**: Warning (OKF bundle validation only)

**Description**: A directory contains markdown files but no `index.md` file. The `index.md` serves as a directory listing and introduction.

**How to Fix**:
Create an `index.md` file in the directory:
```markdown
---
okf_version: "0.1"
---

# Category Name

Overview of this category...

## Contents

- [Concept A](./concept-a.md)
- [Concept B](./concept-b.md)
```

---

### W5: Non-ISO 8601 Date in log.md

**Severity**: Warning (OKF bundle validation only)

**Description**: A `log.md` file has a level-2 heading that is not in ISO 8601 date format (YYYY-MM-DD).

**Example**:
```markdown
## July 6, 2024      # Wrong format

- Added new concept
```

**How to Fix**:
Use ISO 8601 format for all `log.md` headings:
```markdown
## 2024-07-06

- Added new concept
```

---

### W6: No Schema Found for Type

**Severity**: Warning

**Description**: A file's `type` field does not match any schema in the schema directory, so schema validation cannot proceed.

**Why This Happens**:
- You declared `type: my_custom_type` but there is no `my_custom_type.schema.json` file
- The schema file exists but has a different name

**How to Fix**:

Option 1: Create a schema file matching your type:
```
schemas/
  my_custom_type.schema.json    # Create this file
```

Option 2: Change the `type` to match an existing schema:
```yaml
---
type: concept      # Use an existing schema
---
```

---

### W7: Block-Style Lists in Frontmatter

**Severity**: Warning

**Description**: The frontmatter uses block-style (multi-line) lists instead of inline notation. While valid, this expands the frontmatter vertically, reducing the amount of content visible to coding agents that load only the first N lines of a file.

**Example**:
```yaml
---
type: concept
tags:              # Block-style list
  - important
  - ai
  - llm
---
```

**How to Fix**:
Convert to inline notation:
```yaml
---
type: concept
tags: [important, ai, llm]    # Inline list is more compact
---
```

To automatically fix all W7 warnings in an OKF bundle, run:
```bash
okf-schema lint --path <bundle>
```

---

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| **0** | Validation passed (no errors; warnings allowed unless `--strict` mode) |
| **1** | Validation failed (errors found, or warnings in `--strict` mode) |

---

## Using `--strict` Mode

By default, validation passes as long as there are no errors (warnings are allowed):
```bash
okf-schema validate --path my-bundle          # Exit 0 (2 warnings, 0 errors)
```

With `--strict` mode, even warnings cause validation to fail:
```bash
okf-schema validate --path my-bundle --strict # Exit 1 (2 warnings, 0 errors)
```

Use `--strict` in CI/CD pipelines to enforce best practices.

---

## Validation Scope

### Bundle Validation (`validate`)

When validating an OKF bundle, the following checks are applied:

**All files**: E1, E2, E4, E5, W1, W2, W3, W6, W7
**Reserved files**: E3, E6
**Bundle structure**: E7, W4

### Standalone Validation (`validate-md`)

When validating standalone markdown files without a bundle, the following checks are applied:

**All files**: E1, E2, E4, E5, W1, W3, W6, W7

**Not applied** (bundle-specific):
- W2 (broken links require a common root for resolution)
- W4 (directory structure validation)
- E3, E6, E7 (bundle structure rules)

---

## Examples

### Example 1: Fix E1 + E2

**Original**:
```markdown
# My Concept

Description of the concept.
```

**Problem**: No frontmatter (E1)

**Fixed**:
```markdown
---
type: concept
title: My Concept
description: Description of the concept
---

# My Concept

Description of the concept.
```

---

### Example 2: Fix E4 (Schema Error)

**Schema** (`concept.schema.json`):
```json
{
  "type": "object",
  "properties": {
    "type": { "enum": ["concept"] },
    "title": { "type": "string" },
    "category": { "enum": ["AI", "Engineering", "Other"] }
  },
  "required": ["type", "title", "category"]
}
```

**File with E4 error**:
```yaml
---
type: concept
title: My Concept
category: Biology     # Not in allowed enum
---
```

**Fixed**:
```yaml
---
type: concept
title: My Concept
category: AI          # Must match allowed values
---
```

---

### Example 3: Fix W1 + W3

**Original**:
```yaml
---
type: principle
---
```

**Problems**: Missing `title` (W1), missing `description` (W1), missing `timestamp` (W3)

**Fixed**:
```yaml
---
type: principle
title: Keep Frontmatter Compact
description: Coding agents load the first N lines; block-style lists reduce visible content
timestamp: "2024-07-06"
---
```
