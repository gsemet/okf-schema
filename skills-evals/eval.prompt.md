---
agent: agent
description: 'Trigger the okf-schema skill evaluation campaign. Runs controlled A/B evals with deterministic automated grading.'
model: gpt-5.4
name: okf-schema-eval-trigger
---

# OKF Schema Skill Evaluation Trigger

Run a **controlled A/B evaluation** for the `okf-schema` skill.
Both conditions use the same assertions, graded deterministically by `grade-eval.py`.

## Methodology

| Condition | Input |
|-----------|-------|
| **With Skill** | `skills/okf-schema/SKILL.md` + CLI help |
| **Without Skill** | `okf-schema --help` + `skills/okf-schema/references/okf-v0.1.md` spec |

**Grading**: Automated, deterministic, identical assertions for both conditions.

## Setup

1. Read `skills-evals/evals.json` to discover eval cases.
2. Determine iteration name: `iteration-$(date +%d.%m.%y-%H.%M)` (e.g., `iteration-26.06.30-11.57`).
3. Verify `okf-schema` is available: `uv run -- okf-schema --version`.

## Pre-flight

- Confirm fixture directories exist under `skills-evals/fixtures/`.
- Confirm `skills-evals/grade-eval.py` exists.
- Create `skills-evals/results/iteration-DD.MM.YY-HH.MM/<eval_name>/{with_skill,without_skill}/` for each eval.

## Execution

For each eval case in `skills-evals/evals.json`:

### 1. With Skill

Spawn a fresh subagent with the eval's `prompt_with_skill`, providing:
- `skills/okf-schema/SKILL.md`
- `uv run -- okf-schema --help`
- Fixture paths from the `files` array

Capture transcript to `results/iteration-DD.MM.YY-HH.MM/<eval_name>/with_skill/transcript.md`.

### 2. Without Skill

Spawn a fresh subagent with the eval's `prompt_without_skill`, providing:
- `uv run -- okf-schema --help`
- `skills/okf-schema/references/okf-v0.1.md` (the OKF specification)
- Fixture paths from the `files` array

Capture transcript to `results/iteration-DD.MM.YY-HH.MM/<eval_name>/without_skill/transcript.md`.

### 3. Automated Grading

Run the grader after all transcripts are captured:

```bash
python skills-evals/grade-eval.py --iteration skills-evals/results/iteration-DD.MM.YY-HH.MM --evals skills-evals/evals.json
```

This generates `grading.json` for both conditions using the same assertion set.

### 4. Skeptical Assessment (Devil's Advocate Review)

**Before generating the report**, spawn a fresh subagent to critique the raw grading results. This catches methodology flaws before they are baked into the published report.

> You are a skeptical reviewer analyzing an A/B skill evaluation for the `okf-schema` CLI tool. Challenge assumptions and expose weaknesses.
>
> Read the grading JSON files under `skills-evals/results/iteration-DD.MM.YY-HH.MM/` and provide a concise critique (max 400 words) covering:
>
> - **Verdict**: Does the skill show measurable advantage? State clearly.
> - **Root causes**: Why is the delta flat (or not)? Grader bugs? Tasks too easy? Untested knowledge?
> - **Actionable fixes**: Specific changes to evals, assertions, or grader.
>
> Be ruthless. If the skill shows no improvement, say so. Save your critique to `skills-evals/results/iteration-DD.MM.YY-HH.MM/skeptical-review.md`.

### 5. Report Generation

Run `just eval-view-okf-schema` to generate the HTML report at `results/iteration-DD.MM.YY-HH.MM/eval-result.html`.

### 6. Publish

1. Update `README.md` to point to the latest result via `htmlpreview.github.io`.
2. Summarize: total evals, per-condition pass rates, delta per eval, and a link to the skeptical review.
