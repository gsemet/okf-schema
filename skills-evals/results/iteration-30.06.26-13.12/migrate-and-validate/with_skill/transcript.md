# Eval 3: migrate-and-validate — With Skill

## Commands Executed

### 1. Create output directory
```
$ rm -rf skills-evals/fixtures/migrate-output && mkdir -p skills-evals/fixtures/migrate-output
```

### 2. Migrate 5 legacy files to OKF concepts with frontmatter
- readme.md (from README.md) — type: Concept, title, description, tags, timestamp
- architecture.md — type: Concept, title, description, tags, timestamp
- api-reference.md — type: Concept, title, description, tags, timestamp
- deployment-guide.md — type: Concept, title, description, tags, timestamp
- troubleshooting.md — type: Concept, title, description, tags, timestamp

### 3. Create log.md with ISO 8601 date headings

### 4. Regenerate indexes
```
$ uv run -- okf-schema index --path skills-evals/fixtures/migrate-output
0 updated, 1 created, 0 unchanged, 0 skipped
```

### 5. Lint
```
$ uv run -- okf-schema lint --path skills-evals/fixtures/migrate-output
Linted: skills-evals/fixtures/migrate-output/deployment-guide.md
Linted 1 file(s).
```

### 6. Final Validation
```
$ uv run -- okf-schema validate --path skills-evals/fixtures/migrate-output --strict
Bundle is conformant (0 errors, 0 warnings).
```
