# OKF Schema Skill Evaluation — bootstrap-knowledge-base (with_skill)

**Eval**: bootstrap-knowledge-base
**Condition**: with_skill
**Date**: 2026-06-30
**Agent**: okf-schema-eval-trigger

---

## Task

Create a complete OKF knowledge base about 'Electric Vehicle Battery Management' from scratch under `skills-evals/fixtures/bootstrap-output/`.

Requirements:
- At least 8 concepts across 3 subdirectories (cells/, thermal/, safety/)
- Each with type, title, description, tags, timestamp
- At least 3 cross-links between concepts
- index.md at root and in each subdirectory
- log.md at root with ISO 8601 date headings
- Custom _schema/ directory with at least 2 JSONSchema files
- Follow SKILL.md workflow: init → new → index → lint → validate --strict

---

## Commands and Outputs

### 1. Verify okf-schema availability

```bash
uv run okf-schema --version
```

**Output:**
```
okf-schema, version 0.2.1.dev2+gb06c47363
```

---

### 2. Initialize the bundle

```bash
rm -rf skills-evals/fixtures/bootstrap-output
uv run okf-schema init skills-evals/fixtures/bootstrap-output
```

**Output:**
```
Created OKF bundle 'skills-evals/fixtures/bootstrap-output'.
```

---

### 3. Create subdirectories

```bash
mkdir -p skills-evals/fixtures/bootstrap-output/{cells,thermal,safety,_schema}
```

**Output:** *(no output, success)*

---

### 4. Check `okf-schema new` options

```bash
uv run okf-schema new --help
```

**Output:**
```
Usage: okf-schema new [OPTIONS]

  Create a new OKF concept file with frontmatter template.

Options:
  --path TEXT   Root directory for the new concept.  [required]
  --name TEXT   Relative path of the concept (without .md).  [required]
  --type TEXT   Concept type.
  --title TEXT  Concept title.
  -h, --help    Show this message and exit.
```

---

### 5. Create 9 concepts using `okf-schema new`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name cells/lithium-ion --type Concept --title "Lithium-Ion Battery Cell"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/cells/lithium-ion.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name cells/soc-estimation --type Concept --title "State of Charge Estimation"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/cells/soc-estimation.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name cells/cell-balancing --type Concept --title "Cell Balancing"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/cells/cell-balancing.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name thermal/cooling-systems --type Concept --title "Battery Cooling Systems"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/thermal/cooling-systems.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name thermal/heat-generation --type Concept --title "Heat Generation in Cells"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/thermal/heat-generation.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name thermal/thermal-modeling --type Concept --title "Thermal Modeling"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/thermal/thermal-modeling.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name safety/thermal-runaway --type Concept --title "Thermal Runaway"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/safety/thermal-runaway.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name safety/failure-modes --type Concept --title "Battery Failure Modes"
```
**Output:** `Created concept 'skills-evals/fixtures/bootstrap-output/safety/failure-modes.md'.`

```bash
uv run okf-schema new --path skills-evals/fixtures/bootstrap-output --name safety/asil-ratings --type Concept --title "ASIL Safety Ratings"
```
**Output:** `Bundle is conformant (0 errors, 0 warnings).`

---

### 6. Enrich concept files with descriptions, tags, timestamps, and cross-links

Manually edited all 9 concept files to add:
- `description`: meaningful one-line summaries
- `tags`: relevant keyword lists
- `timestamp`: ISO 8601 datetimes
- Body content with cross-links between related concepts

Cross-links added:
- `cells/lithium-ion.md` → `../thermal/cooling-systems.md`, `../safety/thermal-runaway.md`
- `cells/soc-estimation.md` → `cell-balancing.md`
- `thermal/cooling-systems.md` → `thermal-modeling.md`
- `thermal/heat-generation.md` → `cooling-systems.md`
- `thermal/thermal-modeling.md` → `../safety/thermal-runaway.md`
- `safety/thermal-runaway.md` → `failure-modes.md`, `asil-ratings.md`
- `safety/failure-modes.md` → `asil-ratings.md`
- `safety/asil-ratings.md` → `thermal-runaway.md`

---

### 7. Create custom JSONSchema files in `_schema/`

Created `skills-evals/fixtures/bootstrap-output/_schema/Concept.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "type": { "type": "string" },
    "title": { "type": "string" },
    "description": { "type": "string" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["type"]
}
```

Created `skills-evals/fixtures/bootstrap-output/_schema/Reference.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "type": { "type": "string" },
    "title": { "type": "string" },
    "description": { "type": "string" },
    "resource": { "type": "string", "format": "uri" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["type", "resource"]
}
```

---

### 8. Create `log.md` with ISO 8601 date headings

Created `skills-evals/fixtures/bootstrap-output/log.md`:
```markdown
# Directory Update Log

## 2026-06-30
* **Creation**: Initialized EV Battery Management knowledge base.
* **Added**: 9 concepts across cells/, thermal/, and safety/ directories.
* **Added**: Custom JSONSchema definitions in _schema/.
```

---

### 9. Regenerate index files

```bash
uv run okf-schema index --path skills-evals/fixtures/bootstrap-output
```

**Output:**
```
0 updated, 4 created, 0 unchanged, 0 skipped
```

Index files created:
- `skills-evals/fixtures/bootstrap-output/index.md`
- `skills-evals/fixtures/bootstrap-output/cells/index.md`
- `skills-evals/fixtures/bootstrap-output/thermal/index.md`
- `skills-evals/fixtures/bootstrap-output/safety/index.md`

---

### 10. Check lint (dry-run)

```bash
uv run okf-schema lint --path skills-evals/fixtures/bootstrap-output --check
```

**Output:**
```
All files are properly linted.
```

---

### 11. Apply lint

```bash
uv run okf-schema lint --path skills-evals/fixtures/bootstrap-output
```

**Output:**
```
All files are already linted.
```

---

### 12. Final strict validation

```bash
uv run okf-schema validate --path skills-evals/fixtures/bootstrap-output --strict
```

**Output:**
```
Bundle is conformant (0 errors, 0 warnings).
```

---

## Final Bundle Structure

```
skills-evals/fixtures/bootstrap-output/
├── _schema/
│   ├── Concept.schema.json
│   └── Reference.schema.json
├── cells/
│   ├── index.md
│   ├── cell-balancing.md
│   ├── lithium-ion.md
│   └── soc-estimation.md
├── thermal/
│   ├── index.md
│   ├── cooling-systems.md
│   ├── heat-generation.md
│   └── thermal-modeling.md
├── safety/
│   ├── index.md
│   ├── asil-ratings.md
│   ├── failure-modes.md
│   └── thermal-runaway.md
├── index.md
└── log.md
```

## Summary

- **Concepts created**: 9 (3 in cells/, 3 in thermal/, 3 in safety/)
- **Cross-links**: 8+ markdown links between concepts
- **Index files**: 4 (root + 3 subdirectories)
- **Log file**: 1 with ISO 8601 date heading
- **Schema files**: 2 in `_schema/`
- **Final validation**: ✅ 0 errors, 0 warnings — conformant
