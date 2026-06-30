---
agent: agent
description: 'Run the complete okf-schema skill A/B evaluation end-to-end: setup, parallel subagent execution, automated grading, skeptical review, report generation, and README update.'
model: gpt-5.4
name: okf-schema-eval-orchestrator
---

# OKF Schema Skill Evaluation -- Full Orchestrator

Run the **complete** controlled A/B evaluation for the `okf-schema` skill in one shot.
This prompt orchestrates setup, execution, grading, skeptical review, report generation,
and README update. Do not stop for human confirmation between steps.

## Methodology

| Condition | Input |
|-----------|-------|
| **With Skill** | `skills/okf-schema/SKILL.md` + CLI help |
| **Without Skill** | `okf-schema --help` + `skills/okf-schema/references/okf-v0.1.md` spec |

**Grading**: Automated, deterministic, identical assertions for both conditions.
**Outcome-weighted**: Strict validation pass (0 errors, 0 warnings, conformant) is the
**primary metric**. Structure and content checks are secondary.

## Phase 1 -- Setup

1. Read `skills-evals/evals.json` to discover eval cases.
2. Determine iteration name: `iteration-$(date +%d.%m.%y-%H.%M)`.
3. Verify `okf-schema` is available: `uv run -- okf-schema --version`.
4. Create `skills-evals/results/<iteration_name>/<eval_name>/{with_skill,without_skill}/workspace/` for each eval.
5. Copy fixture data for repair evals:
   - `cp -r skills-evals/fixtures/fix-non-conformant-bundle/ skills-evals/results/<iteration_name>/fix-non-conformant-bundle/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/fix-non-conformant-bundle/ skills-evals/results/<iteration_name>/fix-non-conformant-bundle/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/repair-knowledge-base/ skills-evals/results/<iteration_name>/repair-knowledge-base/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/repair-knowledge-base/ skills-evals/results/<iteration_name>/repair-knowledge-base/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/init-structure-trap/ skills-evals/results/<iteration_name>/init-structure-trap/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/init-structure-trap/ skills-evals/results/<iteration_name>/init-structure-trap/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/schema-composition-trap/ skills-evals/results/<iteration_name>/schema-composition-trap/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/schema-composition-trap/ skills-evals/results/<iteration_name>/schema-composition-trap/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/workflow-ordering-trap/ skills-evals/results/<iteration_name>/workflow-ordering-trap/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/workflow-ordering-trap/ skills-evals/results/<iteration_name>/workflow-ordering-trap/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/reserved-files-trap/ skills-evals/results/<iteration_name>/reserved-files-trap/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/reserved-files-trap/ skills-evals/results/<iteration_name>/reserved-files-trap/without_skill/workspace/`
   - `cp -r skills-evals/fixtures/comment-preservation-trap/ skills-evals/results/<iteration_name>/comment-preservation-trap/with_skill/workspace/`
   - `cp -r skills-evals/fixtures/comment-preservation-trap/ skills-evals/results/<iteration_name>/comment-preservation-trap/without_skill/workspace/`

## Phase 2 -- Parallel Execution (7 Evals x 2 Conditions = 14 Subagents)

Spawn **fresh subagents in parallel** (max 4 concurrent) for all evals and conditions.

For each eval, resolve the workspace path from `evals.json` by replacing:
- `{{iteration_dir}}` -> `skills-evals/results/<iteration_name>`
- `{{condition}}` -> `with_skill` or `without_skill`

**With Skill subagent** -- provide:
- `skills/okf-schema/SKILL.md`
- `uv run -- okf-schema --help`
- Fixture paths from the `files` array
- The eval's `prompt_with_skill` (with resolved `{{workspace}}` path)

**Without Skill subagent** -- provide:
- `uv run -- okf-schema --help`
- `skills/okf-schema/references/okf-v0.1.md`
- Fixture paths from the `files` array
- The eval's `prompt_without_skill` (with resolved `{{workspace}}` path)

> **CRITICAL -- Fixture Immutability**: Subagents MUST NOT modify any file under
> `skills-evals/fixtures/`. All writes must go to the resolved workspace directory only.

> **Blinding**: Each subagent is fresh and blinded to the other condition's resources.

Capture transcripts to:
- `skills-evals/results/<iteration_name>/<eval_name>/with_skill/transcript.md`
- `skills-evals/results/<iteration_name>/<eval_name>/without_skill/transcript.md`

## Phase 3 -- Automated Grading

After ALL transcripts are captured, run:

```bash
uv run -- python skills-evals/grade-eval.py --iteration skills-evals/results/<iteration_name> --evals skills-evals/evals.json
```

This generates `grading.json` for both conditions per eval.

## Phase 4 -- Skeptical Assessment (Devil's Advocate)

**Before generating the report**, spawn a fresh subagent to critique the raw grading results.

> You are a skeptical reviewer analyzing an A/B skill evaluation for the `okf-schema` CLI tool.
> Read the grading JSON files under `skills-evals/results/<iteration_name>/` and provide a
> concise critique (max 400 words) covering:
> - **Verdict**: Does the skill show measurable advantage? State clearly.
> - **Root causes**: Why is the delta flat (or not)? Grader bugs? Tasks too easy? Untested knowledge?
> - **Actionable fixes**: Specific changes to evals, assertions, or grader.
> Be ruthless. If the skill shows no improvement, say so.
> Save your critique to `skills-evals/results/<iteration_name>/skeptical-review.md`.
> Use headings and bullet points. No tables.

## Phase 5 -- Report Generation

Run the report generator:

```bash
python3 skills-evals/eval-viewer.py --iteration skills-evals/results/<iteration_name>
```

This reads all `grading.json` files **and** `skeptical-review.md` from the iteration directory, then generates `skills-evals/results/<iteration_name>/eval-result.html` with the skeptical assessment embedded at the top.

> **CRITICAL**: The skeptical assessment (Phase 4) MUST complete before this step.
> If the report was generated earlier, regenerate it now by re-running the command above.

**Verify**: Confirm the HTML contains the skeptical review:
```bash
grep -q "Skeptical Assessment" skills-evals/results/<iteration_name>/eval-result.html && echo "✅ Review embedded" || echo "❌ Missing — re-run Phase 5"
```

## Phase 6 -- Publish

Update `README.md` to point to the latest result. Preserve the simple one-line format:

```markdown
**Latest eval result:** [iteration-DD.MM.YY-HH.MM](https://htmlpreview.github.io/?https://github.com/gsemet/okf-schema/blob/master/skills-evals/results/<iteration_name>/eval-result.html) -- [skeptical review](skills-evals/results/<iteration_name>/skeptical-review.md)
```

Replace the previous iteration link. Do NOT add tables, score breakdowns, or verdict blocks.

## Completion Checklist

- [ ] All 14 subagents completed (7 evals x 2 conditions)
- [ ] All transcripts captured
- [ ] Grading JSON generated for all evals
- [ ] Skeptical review written
- [ ] HTML report generated
- [ ] README.md updated with latest iteration link
