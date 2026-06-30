# Eval 2: bootstrap-knowledge-base — Without Skill

## Commands Executed

### 1. Initialize bundle
```
$ uv run -- okf-schema init skills-evals/fixtures/bootstrap-output
Created OKF bundle 'skills-evals/fixtures/bootstrap-output'.
```

### 2. Create subdirectories
```
$ mkdir -p skills-evals/fixtures/bootstrap-output/{cells,thermal,safety}
```

### 3. Create 9 concept files with YAML frontmatter per OKF spec §4.1
- cells/lithium-ion.md
- cells/cell-balancing.md
- cells/soc-estimation.md
- thermal/cooling-systems.md
- thermal/heat-generation.md
- thermal/thermal-modeling.md
- safety/thermal-runaway.md
- safety/asil-ratings.md
- safety/failure-modes.md

Each with: type, title, description, tags, timestamp.

### 4. Create cross-links between concepts
- lithium-ion → thermal/cooling-systems.md, safety/thermal-runaway.md
- cooling-systems → safety/thermal-runaway.md
- soc-estimation → cells/cell-balancing.md
- heat-generation → thermal/cooling-systems.md
- failure-modes → safety/thermal-runaway.md, safety/asil-ratings.md

### 5. Create log.md with ISO 8601 date headings per OKF spec §7

### 6. Create _schema/ directory with 2 JSONSchema files
- concept.schema.json
- reference.schema.json

### 7. Regenerate indexes
```
$ uv run -- okf-schema index --path skills-evals/fixtures/bootstrap-output
0 updated, 4 created, 0 unchanged, 0 skipped
```

### 8. Lint
```
$ uv run -- okf-schema lint --path skills-evals/fixtures/bootstrap-output
All files are already linted.
```

### 9. Fix init artifact — remove extra bundle/ directory
```
$ rm -rf skills-evals/fixtures/bootstrap-output/bundle
```

### 10. Fix schema case — rename to Concept.schema.json
```
$ mv skills-evals/fixtures/bootstrap-output/_schema/concept.schema.json skills-evals/fixtures/bootstrap-output/_schema/Concept.schema.json
```

### 11. Final Validation
```
$ uv run -- okf-schema validate --path skills-evals/fixtures/bootstrap-output --strict
Bundle is conformant (0 errors, 0 warnings).
```
