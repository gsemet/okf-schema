# Validation Error & Warning Codes

This reference documents all validation codes returned by okf-schema's validation commands (`validate` and `validate-md`).

## Error Codes (E0–E10)

Errors represent conformance violations that must be fixed before the validation passes.

### E0: Invalid Bundle Path

**Severity**: Error

**Description**: The path passed to bundle validation is not a directory.

**How to Fix**: Pass the bundle directory itself, such as
`okf-schema validate --path my-bundle/bundle`.

---

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

### E7: Retired

`E7` formerly rejected non-reserved Markdown files at the bundle root. It is no
longer emitted: OKF 0.2 explicitly permits concept documents both at the root
and in subdirectories.

For example, this structure is valid:
```
bundle/
  index.md
  log.md
  overview.md
  concepts/
    details.md
```

---

### E8: `generated` Block Missing `at` Field

**Severity**: Error (OKF 0.2)

**Description**: A frontmatter `generated` block is present but the required `at` field is missing.

**Example**:
```yaml
---
type: concept
generated:
  by: "human:alice"    # missing `at`
---
```

**How to Fix**:
Add the required `at` field:
```yaml
---
type: concept
generated:
  at: "2026-08-10T14:00:00Z"
  by: "human:alice"
---
```

Fix: `okf-schema lint --path <bundle>`

---

### E9: `sources` Entry Missing `resource` Field

**Severity**: Error (OKF 0.2)

**Description**: A `sources` list entry is missing the required `resource` field.

**Example**:
```yaml
sources:
  - id: paper-1
    title: "My Paper"   # missing `resource`
```

**How to Fix**:
Add the required `resource` field:
```yaml
sources:
  - id: paper-1
    resource: "https://example.com/paper.pdf"
    title: "My Paper"
```

Fix: add `resource: <URI-or-path>` to the sources entry.

---

### E10: `verified` Entry Missing `by` or `at` Field

**Severity**: Error (OKF 0.2)

**Description**: A `verified` list entry is missing the required `by` or `at` field.

**Example**:
```yaml
verified:
  - method: "peer-review"   # missing `by` and `at`
```

**How to Fix**:
Add the required fields:
```yaml
verified:
  - by: "human:alice"
    at: "2026-08-10"
    method: "peer-review"
```

Fix: add `by: <actor>` and `at: <ISO-8601-date>` to the verified entry.

---

## Warning Codes (W0–W13)

Warnings indicate best-practice violations or missing metadata. Validation passes with warnings unless `--strict` mode is enabled.

### W0: Standalone Path Is Not a File

**Severity**: Warning (`validate-md` only)

**Description**: A resolved standalone input path is not a regular markdown
file. Correct or narrow the input pattern.

---

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

### W3: Missing Provenance Timestamp

**Severity**: Warning

**Description**: The frontmatter lacks `generated.at`, which records document
provenance. A legacy `timestamp` suppresses W3 but separately triggers W8.

**How to Fix**:
Add `generated.at` in ISO 8601 format:
```yaml
---
type: concept
title: My Concept
generated:
  at: "2024-07-06T00:00:00Z"
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

> **Note (OKF 0.2)**: The `sources`, `verified`, and `parameters` list-of-mapping
> fields are **exempted** from inline-forcing by `okf-schema lint`. Their block style
> is preserved for readability.

---

### W8: Deprecated `timestamp` Field

**Severity**: Warning (OKF 0.2 migration)

**Description**: The frontmatter uses the deprecated OKF 0.1 `timestamp` field instead
of the OKF 0.2 `generated.at` field.

**Example**:
```yaml
timestamp: "2026-08-10T14:00:00Z"   # deprecated
```

**How to Fix**:
Replace `timestamp` with a `generated` block:
```yaml
generated:
  at: "2026-08-10T14:00:00Z"
  by: "human:alice"
```

Fix: `okf-schema lint --path <bundle>`. Lint preserves the legacy value as
`generated.at`; it does not invent a `generated.by` actor.

Stable code: `W8`

---

### W9: Deprecated Body `# Citations` Section

**Severity**: Warning (OKF 0.2 migration)

**Description**: The document body contains a `# Citations` heading. In OKF 0.2,
citations move to the `sources` frontmatter field with markdown footnotes.

**How to Fix**:
1. Add a `sources:` frontmatter list with entries having `resource` and optional `id`.
2. Reference sources in the body using footnote syntax `[^id]`.
3. Remove the body `# Citations` section.

```yaml
sources:
  - id: ref-1
    resource: "https://example.com/paper.pdf"
    title: "Example Paper"
```

```markdown
This claim is supported by the literature.[^ref-1]
```

Fix: Manually migrate citations to `sources:` frontmatter and `[^id]` footnotes.

Stable code: `W9`

---

### W10: Malformed Actor String in `verified[].by`

**Severity**: Warning (OKF 0.2)

**Description**: A `verified` entry has a `by` value that does not conform to the
OKF actor string format `<prefix>:<identifier>`. Only well-formed `human:` actors
promote the trust tier; malformed actors are ignored for tier derivation.

**Example**:
```yaml
verified:
  - by: "Alice"     # malformed — should be "human:alice"
    at: "2026-08-10"
```

**How to Fix**:
Use the `<prefix>:<identifier>` format:
```yaml
verified:
  - by: "human:alice"
    at: "2026-08-10"
```

Stable code: `W10`

---

### W11: Stale File

**Severity**: Warning (OKF 0.2)

**Description**: The `stale_after` date has passed, meaning the document may contain
outdated information.

**Example**:
```yaml
stale_after: "2025-01-01"   # past date → W11
```

**How to Fix**:
Either update the content and set a new `stale_after` date, or remove the field:
```yaml
stale_after: "2027-01-01"   # updated future date
```

Stable code: `W11`

---

### W12: Unmatched Footnote Reference

**Severity**: Warning (OKF 0.2)

**Description**: A body footnote reference `[^id]` has no corresponding entry in the
`sources` frontmatter list with a matching `id`.

**Example**:
```markdown
See the paper.[^ref-1]
```
Without a `sources` entry having `id: ref-1`.

**How to Fix**:
Add the corresponding `sources` entry:
```yaml
sources:
  - id: ref-1
    resource: "https://example.com/paper.pdf"
```

Stable code: `W12`

---

### W13: Broken Path in `resource` Field

**Severity**: Warning (OKF 0.2)

**Description**: A `sources[].resource` value contains a path-form string that
does not resolve to an existing file. URL and scope-descriptor forms are skipped.

**Example**:
```yaml
sources:
  - resource: "docs/missing-file.pdf"   # file does not exist
```

**How to Fix**:
Correct the path or use a full URL:
```yaml
sources:
  - resource: "https://example.com/paper.pdf"
```

Stable code: `W13`

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

**All Markdown files**: E1, E2, E4, E5, E8-E10, W1, W2, W3, W6-W13
**Reserved files**: E3, E6
**Bundle structure**: W4

Non-Markdown files are not concept documents and are ignored by document
validation. They may be stored in the bundle and referenced as attachments from
Markdown concepts.

### Standalone Validation (`validate-md`)

When validating standalone markdown files without a bundle, the following checks are applied:

**All files**: E1, E2, E4, E5, E8-E10, W1, W3, W6-W13

**Not applied** (bundle-specific):
- W2 (broken links require a common root for resolution)
- W4 (directory structure validation)
- E3, E6 (bundle structure rules)

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

**Problems**: Missing `title` (W1), missing `description` (W1), and missing
`generated.at` (W3)

**Fixed**:
```yaml
---
type: principle
title: Keep Frontmatter Compact
description: Coding agents load the first N lines; block-style lists reduce visible content
generated:
  at: "2024-07-06T00:00:00Z"
---
```
