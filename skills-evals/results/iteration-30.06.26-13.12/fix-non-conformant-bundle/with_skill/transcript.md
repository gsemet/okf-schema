# Eval 1: fix-non-conformant-bundle — With Skill

## Commands Executed

### 1. Initial Validation
```
$ uv run -- okf-schema validate --path skills-evals/fixtures/fix-non-conformant-bundle --strict
```
Output: 3 errors, 7 warnings
- E1: missing-frontmatter.md has no YAML frontmatter
- E2: no-type.md has frontmatter but no 'type' field
- E3: subdir/index.md has unexpected frontmatter
- W5: log.md date heading not ISO 8601
- W7: block-lists.md has block-style lists
- W1, W2, W3: subdir/item.md missing title/description/timestamp, broken link

### 2. Fix E1 — Add frontmatter to missing-frontmatter.md
Added type, title, description, tags, timestamp.

### 3. Fix E2 — Add type and timestamp to no-type.md
Added type: concept, timestamp.

### 4. Fix E3 — Remove frontmatter from subdir/index.md
Only bundle-root index.md may have frontmatter.

### 5. Fix W1/W2/W3 — Fix subdir/item.md
Added title, description, timestamp. Fixed broken link to ../block-lists.md.

### 6. Fix W5 — Fix log.md date format
Changed "June 20, 2026" to "2026-06-20".

### 7. Fix W7 — Lint block-lists.md
```
$ uv run -- okf-schema lint --path skills-evals/fixtures/fix-non-conformant-bundle
Linted 1 file(s).
```

### 8. Fix W4 — Regenerate index files
```
$ uv run -- okf-schema index --path skills-evals/fixtures/fix-non-conformant-bundle
1 updated, 1 created, 0 unchanged, 0 skipped
```

### 9. Final Validation
```
$ uv run -- okf-schema validate --path skills-evals/fixtures/fix-non-conformant-bundle --strict
Bundle is conformant (0 errors, 0 warnings).
```
