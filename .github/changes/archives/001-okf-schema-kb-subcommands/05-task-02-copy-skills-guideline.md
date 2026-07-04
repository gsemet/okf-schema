# Task 02 — Copy Skills and Guideline into Bundled Data Directory

**Phase**: Phase 1 — Bundled Assets and Package Data
**Depends on**: 01

## Objective

Copy the two bundled skills (`record-finding`, `consolidate-knowledge-base`) and
the `knowledge-base.guidelines.md` guideline into the bundled data directory
`src/okf_schema/data/kb/`. These assets are deployed into target projects by
`okfkb install`.

## Files to Modify/Create

- Create `src/okf_schema/data/kb/skills/consolidate-knowledge-base/SKILL.md`
- Create `src/okf_schema/data/kb/skills/record-finding/SKILL.md`
- Create `src/okf_schema/data/kb/guidelines/knowledge-base.guidelines.md`

## Acceptance Criteria

- [ ] Both skill directories exist with `SKILL.md` files
- [ ] `knowledge-base.guidelines.md` exists under `guidelines/`
- [ ] All files are verbatim copies from the reference implementation
- [ ] `importlib.resources.files("okf_schema.data.kb").joinpath("skills/record-finding/SKILL.md")` resolves
- [ ] `importlib.resources.files("okf_schema.data.kb").joinpath("guidelines/knowledge-base.guidelines.md")` resolves

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Line length: 100 chars |
| `AGENTS.md` | Python 3.10+, stdlib + existing deps only |
| `03-specification.md` | Skills and guidelines stored under `src/okf_schema/data/kb/` |
| `03-specification.md` | All files packaged via hatchling; loading uses `importlib.resources.files` |

## Detailed Steps

1. Create the directory structure:
   ```bash
   mkdir -p src/okf_schema/data/kb/skills/consolidate-knowledge-base
   mkdir -p src/okf_schema/data/kb/skills/record-finding
   mkdir -p src/okf_schema/data/kb/guidelines
   ```

2. Copy the skill and guideline files:
   ```bash
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/.github/skills/record-finding/SKILL.md src/okf_schema/data/kb/skills/record-finding/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/.github/skills/consolidate-knowledge-base/SKILL.md src/okf_schema/data/kb/skills/consolidate-knowledge-base/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/.github/guidelines/knowledge-base.guidelines.md src/okf_schema/data/kb/guidelines/
   ```

3. Verify the files are accessible via importlib.resources:
   ```python
   from importlib.resources import files
   kb_root = files("okf_schema.data.kb")
   assert (kb_root / "skills" / "record-finding" / "SKILL.md").is_file()
   assert (kb_root / "skills" / "consolidate-knowledge-base" / "SKILL.md").is_file()
   assert (kb_root / "guidelines" / "knowledge-base.guidelines.md").is_file()
   ```

4. Run `just preflight` to ensure no regressions.

5. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 02 --status done
   ```

## Testing Strategy

- Smoke test: verify all 3 bundled assets are accessible via `importlib.resources`.
- Verify file contents are non-empty and match the source files.

## Notes

- These are **verbatim copies** — do not edit content.
- The skills use frontmatter with `name` and `description` fields.
- The guideline uses `applyTo` and `description` in its frontmatter.
