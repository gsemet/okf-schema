---
agent: agent
description: 'Trigger the okf-schema skill evaluation campaign. Runs all evals in skills-evals/evals.json against the skill.'
model: gpt-5.4
name: okf-schema-eval-trigger
---

# OKF Schema Skill Evaluation Trigger

You are running the evaluation campaign for the **okf-schema** skill (Open Knowledge Format bundle validation and management).

## Setup

1. Read `skills-evals/evals.json` to discover all eval cases.
2. Ensure the project root is at the okf-schema repository root.
3. Verify `okf-schema` is available via `uv run -- okf-schema --version`.

## Pre-flight

- Confirm `okf-schema` is available (`uv sync` if needed).
- Confirm the fixture directories exist under `skills-evals/`:
  - `skills-evals/fixtures/conformant-bundle/`
  - `skills-evals/fixtures/non-conformant/`
  - `skills-evals/fixtures/schema-valid-bundle/`
  - `skills-evals/fixtures/schema-invalid-bundle/`
  - `skills-evals/fixtures/schema-db/`
  - `skills-evals/fixtures/schema-db-yaml/`

## Execution

For each eval case in `skills-evals/evals.json`:

1. Spawn a **fresh subagent** (use the default agent) with the eval's `prompt`.
2. Provide the subagent with:
   - The skill's `SKILL.md` (`skills/okf-schema/SKILL.md`)
   - The `okf-schema` CLI reference (`uv run -- okf-schema --help`)
   - Any fixture paths listed in the eval's `files` array
3. The subagent must execute the task and return its full transcript + any generated files.
4. Capture the subagent output into `skills-evals/results/<eval_name>/transcript.md`.
5. Grade the result by checking each assertion in the eval case:
   - For each assertion, mark PASS or FAIL with a one-line justification.
   - Save the grading report to `skills-evals/results/<eval_name>/grading.json`.

## Grading Format (`grading.json`)

```json
{
  "eval_id": 1,
  "eval_name": "validate-conformant-bundle",
  "overall": "PASS",
  "assertions": [
    {
      "assertion": "The agent executed okf-schema validate...",
      "result": "PASS",
      "justification": "Transcript shows okf-schema validate --path ..."
    }
  ],
  "notes": "Any additional observations"
}
```

## Completion

After all evals are graded:

1. Summarize results in `skills-evals/results/summary.md`:
   - Total evals, passed, failed
   - Per-eval verdict with link to grading.json
2. Report the final summary to the user.
