# OKF Bundle Fix Transcript

## Initial Validation

Command:
```bash
uv run okf-schema validate --path . --strict
```

Output:
```
/Users/az02065/Projects/DevTools/okf-schema/skills-evals/results/iteration-30.06.26-22.06/reserved-files-trap/with_skill/workspace/cells/index.md
  ERROR   [E3] Reserved file '.../cells/index.md' has unexpected frontmatter (only bundle-root index.md may have frontmatter)

/Users/az02065/Projects/DevTools/okf-schema/skills-evals/results/iteration-30.06.26-22.06/reserved-files-trap/with_skill/workspace/cells/log.md
  ERROR   [E6] Reserved file '.../cells/log.md' is not at bundle root (log.md must be at bundle root)

/Users/az02065/Projects/DevTools/okf-schema/skills-evals/results/iteration-30.06.26-22.06/reserved-files-trap/with_skill/workspace/thermal/index.md
  ERROR   [E3] Reserved file '.../thermal/index.md' has unexpected frontmatter (only bundle-root index.md may have frontmatter)

Validation failed: 3 error(s), 0 warning(s).
```

## Issues Found

1. **E3** in `cells/index.md`: Subdirectory `index.md` had frontmatter (`type: index`, `title: Cells Index`). Only bundle-root `index.md` may have frontmatter.
2. **E6** in `cells/log.md`: `log.md` existed in a subdirectory. `log.md` must exist only at bundle root.
3. **E3** in `thermal/index.md`: Subdirectory `index.md` had frontmatter (`type: index`, `title: Thermal Index`). Only bundle-root `index.md` may have frontmatter.

## Fixes Applied

1. Removed frontmatter from `cells/index.md` — stripped the `---` delimiters and `type`/`title` fields, leaving only the markdown heading and link list.
2. Removed frontmatter from `thermal/index.md` — same treatment as above.
3. Deleted `cells/log.md` entirely — reserved `log.md` must only live at bundle root.

## Final Validation

Command:
```bash
uv run okf-schema validate --path . --strict
```

Output:
```
Bundle is conformant (0 errors, 0 warnings).
```

## Summary

All 3 errors were caused by **reserved-file violations** in subdirectories:
- Subdirectory `index.md` files incorrectly contained frontmatter.
- A `log.md` was placed outside the bundle root.

Removing the offending frontmatter and deleting the misplaced `log.md` brought the bundle to full conformance under `--strict`.
