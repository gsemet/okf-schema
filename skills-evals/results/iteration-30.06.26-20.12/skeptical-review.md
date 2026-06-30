# Skeptical Review: okf-schema Skill A/B Evaluation

**Date:** 2026-06-30
**Reviewer:** Skeptical Agent
**Verdict:** The skill shows **no measurable advantage** and in one eval performs worse than the baseline.

---

## Verdict

**No skill advantage detected.**

- Two evals scored perfectly in both conditions (fix-non-conformant-bundle, bootstrap-knowledge-base) — these are dead weight.
- One eval shows the skill condition underperforming the baseline (init-structure-trap: 4/8 vs 5/8).
- One eval is a flat tie (schema-composition-trap: 4/8 vs 4/8).

The skill does not help agents solve harder problems, avoid traps, or produce better outcomes. The evaluation as designed cannot distinguish skill value from random variance.

---

## Root Causes

### 1. Fixture Bugs Render Two Evals Meaningless

**fix-non-conformant-bundle:** The fixture is *already conformant*. Both conditions ran `validate --strict` on the copied workspace and immediately got "0 errors, 0 warnings." The files `missing-frontmatter.md` and `no-type.md` already had valid frontmatter with `type` fields. This eval tests nothing — it is a no-op that burns an eval slot.

**init-structure-trap:** The fixture places all content inside a `bundle/` subdirectory (`bundle/cells/`, `bundle/thermal/`, etc.), but the grader assertions expect files directly at the workspace root (`workspace/cells/cell-chemistry.md`). The "trap" is that the agent must recognize the bundle is nested and move files up. Neither prompt explicitly instructs this, and the with-skill agent validated the empty workspace root (getting 0 errors, 0 warnings) then validated `workspace/bundle/` (also conformant after fixes), never moving files. The without-skill agent at least diagnosed the real issues inside `bundle/` and moved `log.md` to the workspace root, scoring one point higher. This is a fixture–assertion mismatch, not a skill test.

### 2. Tasks Are Too Easy for the Baseline

**bootstrap-knowledge-base:** Both conditions scored 8/8. The without-skill agent read the OKF spec, explored the CLI help, examined the reference fixture, and produced a fully conformant bundle. The OKF spec and CLI `--help` are sufficiently clear that an unskilled agent can bootstrap a knowledge base from scratch. The skill adds no marginal value here.

### 3. Assertions Test Implementation Details, Not Outcomes

**schema-composition-trap:** Both agents correctly diagnosed the schema mismatch (`powertrain` and `sensors` declared as `string` instead of `object` and `array`) and fixed it *inline* in `vehicle-config.schema.json`. The grader, however, asserts that separate files `powertrain.schema.json` and `sensors.schema.json` must exist. The with-skill prompt says "fix the schema files" but does not explicitly mandate separate files. The without-skill prompt gives no hint about file splitting. The agents achieved the functional outcome (strict validation passes) but failed because they didn't guess the grader's preferred file layout. This is an assertion bug, not an agent failure.

### 4. The Skill's Unique Knowledge Is Never Exercised

The SKILL.md highlights several value-adds that never appear in the evals:
- The `index` → `lint` → `validate --strict` workflow is only partially used.
- `ruamel.yaml` round-trip comment preservation is never tested.
- Reserved-file rules (E3, E6) appear in init-structure-trap but the fixture design obscures them.
- Auto-discovery of `_schema/` files is never tested as a differentiator.

---

## Actionable Fixes

### Fix Fixtures

- **fix-non-conformant-bundle:** Make the fixture actually broken. Remove all frontmatter from `missing-frontmatter.md`. Remove the `type` field from `no-type.md`. Add block-style YAML lists to trigger W7. Add a broken cross-link to trigger W2. Add a non-ISO date heading in `log.md` to trigger W5. Put `log.md` in a subdirectory to trigger E6. Give `index.md` frontmatter to trigger E3.
- **init-structure-trap:** Either flatten the fixture (place `cells/`, `thermal/` directly at workspace root) and introduce real traps (missing `index.md`, block-style lists, broken links, `log.md` in wrong place), OR change assertions to expect the nested `bundle/` structure and update prompts to explicitly say "the bundle is inside a `bundle/` subdirectory — fix it in place."

### Fix Assertions

- **schema-composition-trap:** Either accept inline fixes in `vehicle-config.schema.json` as passing (the functional outcome is correct), OR rewrite the prompt to explicitly say: "Create two new schema files: `_schema/powertrain.schema.json` and `_schema/sensors.schema.json`. Do not modify `vehicle-config.schema.json`." Do not test for file names the agent was never told to create.

### Make Evals Harder for the Baseline

- **bootstrap-knowledge-base:** Add constraints that require skill knowledge: require block-style lists that must be linted, require specific schema naming conventions (case-sensitive matching to `type` field), require reserved-file handling. Or remove this eval and replace it with a repair task.

### Add Skill-Specific Evals

Introduce evals that test the skill's actual differentiators:
- **Comment-preservation trap:** A bundle with YAML comments in frontmatter that must survive `okf-schema lint`. Without the skill, an agent might hand-edit with PyYAML and destroy comments.
- **Reserved-file trap:** A bundle where `index.md` has frontmatter or `log.md` is in the wrong directory. The skill explicitly documents E3 and E6.
- **Schema auto-discovery trap:** A bundle with schemas in `_schema/` but with case-mismatch filenames (e.g., `Concept.schema.json` vs `type: concept`). The skill documents case-sensitive auto-discovery.
- **Workflow trap:** An eval where the agent must run `index` then `lint` then `validate --strict` in the correct order to catch all issues. A naive agent might skip `lint` and fail on W7 in strict mode.

### Re-run with Fixed Evals

After applying the above fixes, re-run the A/B evaluation. If the skill still shows no delta, consider whether the skill content itself needs revision or whether the OKF tool is simply too self-documenting for a skill to add value.
