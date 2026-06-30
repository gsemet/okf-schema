# Simplified OKF Schema Skill Evals Campaign — Plan

## Context

The `okf-schema` skill evaluation campaign in `skills-evals/` currently runs **5 eval cases** with **39 assertions** across with-skill and without-skill conditions. The latest iteration (`iteration-30.06.26-17.05`) and its skeptical review revealed serious methodology flaws:

- **Evals 3–5 showed zero delta** — both conditions scored identically, providing no signal.
- **Evals 1–2 showed inflated delta** — the advantage came from circular process assertions (e.g., testing for `lint --check`, which is literally a SKILL.md tip), not genuine capability differences.
- **Process was weighted over outcomes** — a bundle passing strict validation in both conditions still scored differently based on which commands were run.
- **Single-agent execution** — the same agent ran both conditions with full knowledge of both resources, violating true A/B independence.

## Desired Outcome

A **simpler, more meaningful evals campaign** with:
- Fewer eval cases (drop redundant zero-delta evals).
- Outcome-weighted grading (functional results > process checks).
- One new eval testing untested knowledge (schema composition).
- Parallel subagent execution for better A/B isolation.
- Preservation of existing reporting and iteration conventions.

## Scope

**In scope:**
- Redesign `evals.json` — drop Evals 3–5, redesign assertions for Evals 1–2, add 1 new schema-composition eval.
- Update `grade-eval.py` — add outcome-weighted scoring (strict validation pass = primary metric).
- Update `eval.prompt.md` — reflect new eval set, parallel subagent execution, and updated workflow.
- Update `eval-viewer.py` — display primary vs secondary scores if tiered scoring is used.
- Update `METHODOLOGY.md` — document the simplified methodology.
- Update `justfile` eval targets if needed.

**Out of scope:**
- Changing the HTML report format (keep existing).
- Removing iteration directories (keep timestamped history).
- Removing the skeptical review step (keep it).
- Converting to a single `just` command (keep prompt-based system).

---

## Resolved Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | **Evals to keep** | Keep Eval 1 (`fix-non-conformant-bundle`) and Eval 2 (`bootstrap-knowledge-base`). **Drop Evals 3–5** (`migrate-and-validate`, `custom-schema-validation`, `lint-comment-preservation`). |
| 2 | **Process assertions** | **Remove entirely**. No more `lint --check`, workflow order, or `index` command execution checks. |
| 3 | **Outcome weighting** | **Yes** — strict validation pass (0 errors, 0 warnings) is the primary success criterion and carries the most weight. |
| 4 | **New eval** | **Add one schema composition eval** testing multiple custom JSONSchemas for a single concept — an untested knowledge area. |
| 5 | **Subagent execution** | Use **parallel subagents** (max 2 in parallel) for with-skill vs without-skill conditions. |
| 6 | **Skeptical review** | **Keep it** — run after grading to catch methodology flaws. |
| 7 | **Iteration directories** | **Keep timestamped iterations** (`iteration-DD.MM.YY-HH.MM/`). |
| 8 | **Automation** | **Keep existing prompt-based system** (`eval.prompt.md` + Copilot chat). |
| 9 | **Report format** | **Keep HTML report** (`eval-result.html`). |
| 10 | **Eval 1 assertions** | Implementer designs meaningful outcome-focused assertions (validation pass, conformant status, specific file fixes). |
| 11 | **Eval 2 assertions** | Implementer designs meaningful outcome-focused assertions (validation pass, structure checks for complexity). |
| 12 | **Schema composition eval design** | Implementer designs a test with multiple custom types, each with auto-discovered schema, validated together. |

## UNRESOLVED Items

None.

---

## Recommended Implementation Steps

### Phase 1 — Redesign `evals.json`

1. **Drop Evals 3–5** entirely from `evals.json`.
2. **Redesign Eval 1 assertions** — remove all process assertions (`f1_lint`, `f1_index`, `f1_lint_check`, `f1_workflow_order`). Keep:
   - `f1_strict_pass` (0 errors)
   - `f1_strict_pass2` (0 warnings)
   - `f1_conformant` (bundle declared conformant)
   - Optionally add assertions checking that specific broken files were actually fixed (e.g., a file that was missing frontmatter now has it).
3. **Redesign Eval 2 assertions** — remove all process assertions (`b2_lint`, `b2_index`, `b2_lint_check`, `b2_workflow_order`, `b2_init`, `b2_new`). Keep:
   - `b2_strict_pass` (0 errors)
   - `b2_strict_pass2` (0 warnings)
   - `b2_concepts_count` (≥8 concepts)
   - `b2_subdirs` (≥3 subdirectories with index.md)
   - `b2_crosslinks` (≥3 cross-links)
   - `b2_schema_dir` (≥2 schema files)
   - `b2_log_iso` (ISO 8601 dates in log.md)
4. **Add Eval 6 — Schema Composition**:
   - **Prompt (with skill)**: Create an OKF bundle at `skills-evals/fixtures/schema-composition-output/` with a custom concept type `vehicle-config` that has frontmatter fields `powertrain` and `sensors`. Create TWO custom schemas: one for `powertrain` (validating it is an object with `type` and `capacity_kwh` fields) and one for `sensors` (validating it is an array of sensor objects with `id` and `location`). The bundle must pass `okf-schema validate --strict` with zero errors. Use SKILL.md tips about schema placement and auto-discovery.
   - **Prompt (without skill)**: Same task, but only `okf-schema --help` and `okf-v0.1.md` spec provided.
   - **Assertions**:
     - Strict validation pass (0 errors, 0 warnings)
     - Bundle is conformant
     - `_schema/` directory exists with 2 schema files
     - Concept file declares `type: vehicle-config`
     - Concept frontmatter includes `powertrain` and `sensors` fields
     - `powertrain.schema.json` validates `type` and `capacity_kwh` as strings/numbers
     - `sensors.schema.json` validates array items with `id` and `location`
     - Agent did NOT use `--schema-db` flag (auto-discovery test)

### Phase 2 — Update `grade-eval.py`

1. Add **outcome-weighted scoring**:
   - Primary tier: `strict_pass` assertions (validation 0 errors, 0 warnings, conformant).
   - Secondary tier: all other assertions (structure, content, file checks).
   - Report **primary pass rate** and **overall pass rate** separately.
2. Update `grade_eval()` to return both `primary_pass_rate` and `overall_pass_rate`.
3. Update `grade_iteration()` to write both metrics to `grading.json`.

### Phase 3 — Update `eval.prompt.md`

1. Update the methodology table to reflect **3 evals** (not 5).
2. Update the execution section:
   - Spawn with-skill and without-skill subagents **in parallel** (max 2).
   - Emphasize that subagents must be **fresh** and **blinded** to the other condition.
3. Update the grading section to reference the new outcome-weighted scoring.
4. Update the report generation section to reference the new primary/secondary metrics.

### Phase 4 — Update `eval-viewer.py`

1. Update `load_grading()` to read `primary_pass_rate` and `overall_pass_rate`.
2. Update the HTML template to display:
   - Primary pass rate (strict validation outcomes) prominently.
   - Overall pass rate (all assertions) as secondary.
   - Delta per eval for both metrics.

### Phase 5 — Update `METHODOLOGY.md`

1. Update the eval cases table to 3 evals.
2. Update the assertion count (from 39 to ~20–25).
3. Document the outcome-weighted scoring protocol.
4. Document the parallel subagent execution model.
5. Add a note about why Evals 3–5 were dropped (zero delta, execution flaws).

### Phase 6 — Create new fixture directory

1. Create `skills-evals/fixtures/schema-composition-output/` (empty, for the new eval).

### Phase 7 — Validation

1. Run `just eval-view-okf-schema` to verify the viewer still works.
2. Run `python skills-evals/grade-eval.py --help` to verify the grader works.
3. Do a dry-run of the eval prompt to verify the new eval structure is coherent.

---

## Files to Modify

| File | Change |
|------|--------|
| `skills-evals/evals.json` | Drop Evals 3–5, redesign Evals 1–2 assertions, add Eval 6 |
| `skills-evals/grade-eval.py` | Add outcome-weighted scoring (primary + overall pass rates) |
| `skills-evals/eval.prompt.md` | Update for 3 evals, parallel subagents, outcome-weighted grading |
| `skills-evals/eval-viewer.py` | Display primary and overall pass rates |
| `skills-evals/METHODOLOGY.md` | Document simplified methodology |
| `justfile` | Update eval target descriptions if needed |
| `skills-evals/fixtures/schema-composition-output/` | Create empty fixture directory |

## Acceptance Criteria

- [ ] `evals.json` contains exactly 3 eval cases with no process assertions.
- [ ] `grade-eval.py` reports both `primary_pass_rate` and `overall_pass_rate`.
- [ ] `eval.prompt.md` reflects the 3-eval structure and parallel subagent execution.
- [ ] `eval-viewer.py` displays primary and overall metrics in the HTML report.
- [ ] `METHODOLOGY.md` documents the simplified methodology.
- [ ] All existing scripts (`eval-runner.sh`, `grade-eval.py`, `eval-viewer.py`) run without errors.
