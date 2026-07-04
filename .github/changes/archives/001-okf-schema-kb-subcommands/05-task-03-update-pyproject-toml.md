# Task 03 — Update pyproject.toml with Entry Points and Packaging Rules

**Phase**: Phase 1 — Bundled Assets and Package Data
**Depends on**: 01, 02

## Objective

Update `pyproject.toml` to add the `okfkb` console-scripts entry point and ensure
hatchling includes the new `src/okf_schema/data/kb/` directory in the wheel.

## Files to Modify/Create

- Modify `pyproject.toml`

## Acceptance Criteria

- [ ] `[project.scripts]` contains `okfkb = "okf_schema.kb.cli:kb"`
- [ ] `tool.hatch.build.targets.wheel.include` covers `src/okf_schema/data/` (or is broad enough)
- [ ] `uv build` produces a wheel that contains the bundled KB assets
- [ ] `just preflight` passes with no regressions

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Build tool: hatchling + hatch-vcs |
| `03-specification.md` | New `console_scripts` entry point `okfkb = "okf_schema.kb.cli:kb"` |
| `03-specification.md` | Bundled assets must be accessible after `pip install okf-schema` |
| `AGENTS.md` | Run `just preflight` before committing |

## Detailed Steps

1. Read the current `[project.scripts]` and `[tool.hatch.build.targets.wheel]` sections.

2. Add the `okfkb` entry point:
   ```toml
   [project.scripts]
   okf-schema = "okf_schema.cli:cli"
   okfkb = "okf_schema.kb.cli:kb"
   ```

3. Verify the wheel include directive. The current config is:
   ```toml
   [tool.hatch.build.targets.wheel]
   include = ["src/okf_schema"]
   ```
   This already covers `src/okf_schema/data/kb/` since it's under `src/okf_schema`.
   No change needed unless the include is too restrictive.

4. Build the wheel and inspect its contents:
   ```bash
   uv build
   unzip -l dist/okf_schema-*.whl | grep "data/kb"
   ```
   Verify all 8 schemas, 2 skills, and 1 guideline are present.

5. Run `just preflight`.

6. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 03 --status done
   ```

## Testing Strategy

- Build inspection: unzip the wheel and assert all bundled assets are present.
- Install test: `pip install dist/okf_schema-*.whl` in a fresh venv, then verify
  `importlib.resources.files("okf_schema.data.kb")` resolves.

## Notes

- The `okfkb` entry point targets `okf_schema.kb.cli:kb`, which does not exist yet
  (created in Task 07). This is fine — the entry point is declared now and the
  module will exist before the wheel is built for real.
- If `include = ["src/okf_schema"]` is already present, no packaging change is needed.
