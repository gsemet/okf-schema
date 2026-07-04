# Task 01 — Copy KB Schema YAML Files into Bundled Data Directory

**Phase**: Phase 1 — Bundled Assets and Package Data
**Depends on**: none

## Objective

Copy all 8 knowledge-base schema YAML files from the reference implementation
(`copilot-session-usage/knowledge/_schema/`) into the bundled data directory
`src/okf_schema/data/kb/_schema/`. These schemas define the canonical KB
frontmatter structure and are loaded at runtime via `importlib.resources`.

## Files to Modify/Create

- Create `src/okf_schema/data/kb/__init__.py` (empty package marker)
- Create `src/okf_schema/data/kb/_schema/Base.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Concept.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Experiment.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Finding.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Playbook.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Principle.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Reference.schema.yaml`
- Create `src/okf_schema/data/kb/_schema/Structure.schema.yaml`

## Acceptance Criteria

- [ ] All 8 schema files exist under `src/okf_schema/data/kb/_schema/`
- [ ] Each schema file is a verbatim copy from the reference implementation
- [ ] `src/okf_schema/data/kb/__init__.py` exists (empty file)
- [ ] All schema files are valid YAML (can be parsed by `yaml.safe_load`)
- [ ] `importlib.resources.files("okf_schema.data.kb").joinpath("_schema/Base.schema.yaml")` resolves successfully

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Line length: 100 chars |
| `AGENTS.md` | Python 3.10+, stdlib + existing deps only |
| `03-specification.md` | Schema files loaded from `importlib.resources` (`okf_schema.data.kb`) |
| `03-specification.md` | The data directory contains an `__init__.py` so it is a valid package |

## Detailed Steps

1. Create the directory structure:
   ```bash
   mkdir -p src/okf_schema/data/kb/_schema
   touch src/okf_schema/data/kb/__init__.py
   ```

2. Copy each schema file from the reference:
   ```bash
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Base.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Concept.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Experiment.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Finding.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Playbook.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Principle.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Reference.schema.yaml src/okf_schema/data/kb/_schema/
   cp /Users/az02065/Projects/DevTools/copilot-session-usage/knowledge/_schema/Structure.schema.yaml src/okf_schema/data/kb/_schema/
   ```

3. Write a quick smoke test to verify importlib.resources can locate the files:
   ```python
   from importlib.resources import files
   kb_root = files("okf_schema.data.kb")
   assert (kb_root / "_schema" / "Base.schema.yaml").is_file()
   ```

4. Run `just preflight` to ensure no regressions.

5. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 01 --status done
   ```

## Testing Strategy

- Smoke test: verify `importlib.resources.files("okf_schema.data.kb")` resolves
  and all 8 schema files are accessible.
- YAML validity: parse each schema with `yaml.safe_load` to ensure well-formed.

## Notes

- These files are **verbatim copies** from the reference — do not modify content.
- The schemas use JSON Schema Draft 07 (`$schema: "http://json-schema.org/draft-07/schema#"`).
- `Base.schema.yaml` is referenced by all other schemas via `$ref`.
