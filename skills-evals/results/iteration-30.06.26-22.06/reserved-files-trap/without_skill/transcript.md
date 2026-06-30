# OKF Bundle Fix — reserved-files-trap

## Initial Validation

Command:
```bash
uv run -- okf-schema validate --path skills-evals/results/iteration-30.06.26-22.06/reserved-files-trap/without_skill/workspace --strict
```

Result: **3 errors, 0 warnings**

### Issues Found

1. **E3** — `cells/index.md` has unexpected frontmatter  
   Only the bundle-root `index.md` may have frontmatter. Subdirectory `index.md` files must not have frontmatter.

2. **E3** — `thermal/index.md` has unexpected frontmatter  
   Same issue as above.

3. **E6** — `cells/log.md` is not at bundle root  
   `log.md` must be at the bundle root only.

## Fixes Applied

### Fix 1: Remove frontmatter from `cells/index.md`

**Before:**
```markdown
---
type: index
title: Cells Index
---

# Cells

- [cell-chemistry](./cell-chemistry.md)
```

**After:**
```markdown
# Cells

- [cell-chemistry](./cell-chemistry.md)
```

### Fix 2: Remove frontmatter from `thermal/index.md`

**Before:**
```markdown
---
type: index
title: Thermal Index
---

# Thermal

- [thermal-mgmt](./thermal-mgmt.md)
```

**After:**
```markdown
# Thermal

- [thermal-mgmt](./thermal-mgmt.md)
```

### Fix 3: Remove `cells/log.md`

`log.md` is a reserved filename that must only exist at the bundle root. The subdirectory `cells/log.md` was deleted.

## Final Validation

Command:
```bash
uv run -- okf-schema validate --path skills-evals/results/iteration-30.06.26-22.06/reserved-files-trap/without_skill/workspace --strict
```

Result: **Bundle is conformant (0 errors, 0 warnings).**

## Summary

The OKF specification (§3.1, §6, §11) defines `index.md` and `log.md` as reserved filenames with special rules:
- `index.md` files in subdirectories must NOT have frontmatter (only the bundle-root `index.md` may have frontmatter, and only for `okf_version`).
- `log.md` must only exist at the bundle root.

All three violations were corrected, and the bundle now passes strict validation.
