# OKF Schema Skill Evaluation Methodology

## Overview

This document describes the controlled A/B evaluation framework used to measure the effectiveness of the `okf-schema` skill for AI coding agents. The methodology is designed for reproducibility, statistical validity, and publication in a scientific paper.

## Research Question

**Does providing an AI agent with a structured skill definition (SKILL.md) improve its ability to correctly use the `okf-schema` CLI tool compared to relying solely on CLI help text and general knowledge?**

## Experimental Design

### Conditions

| Condition | Treatment | N (assertions) |
|-----------|-----------|----------------|
| **With Skill** | Agent receives `SKILL.md` + CLI help | ~26 (4 evals) |
| **Without Skill** | Agent receives CLI help + OKF spec | ~26 (same assertions) |

Both conditions are evaluated against the **identical assertion set** for each eval case, ensuring an apples-to-apples comparison.

### Independent Variable

- **Skill Access** (binary): Whether the agent has read access to `skills/okf-schema/SKILL.md`

### Dependent Variables

1. **Primary Pass Rate** (primary): Proportion of *outcome* assertions passing per condition -- strict validation pass (0 errors, 0 warnings, conformant). These measure whether the agent produced a correct result.
2. **Overall Pass Rate** (secondary): Proportion of *all* assertions passing, including structure and content checks.
3. **Delta**: Difference in pass rates between conditions per eval.

### Controlled Variables

- Same LLM model (GPT-5.4) for both conditions
- Same fixture bundles
- Same project directory and environment
- Same grading script (`grade-eval.py`) -- no human in the scoring loop

## Eval Cases

| ID | Name | Category | Assertions | Description |
|----|------|----------|------------|-------------|
| 1 | fix-non-conformant-bundle | Repair | 5 | Fix a broken bundle to pass `validate --strict` |
| 2 | repair-knowledge-base | Repair | 8 | Repair an existing EV Battery Management KB with multiple issues |
| 3 | init-structure-trap | Repair | 8 | Fix a bundle created with `okf-schema init` where concepts were placed inside `bundle/` instead of root |
| 4 | schema-composition-trap | Skill-specific | 8 | Fix a bundle where the schema declares wrong types for custom fields (strings instead of object/array) |
| 5 | workflow-ordering-trap | Skill-specific | 8 | Fix a bundle with missing index files and block-style tag lists |
| 6 | reserved-files-trap | Skill-specific | 7 | Fix a bundle with reserved filename violations (log.md in wrong place, index.md with frontmatter) |
| 7 | comment-preservation-trap | Skill-specific | 6 | Fix a bundle with block-style tags while preserving YAML comments |

**Total assertions**: ~50

### Design Rationale

The evals are designed to test **failure modes** where the skill provides specific guidance that is not obvious from the CLI help or OKF spec alone:

- **Eval 3 (init-structure-trap)**: Tests whether the agent knows that `okf-schema init` creates a `bundle/` subdirectory and that the actual bundle root is one level deeper. Without SKILL.md, agents validate from the wrong path and get confusing errors about reserved files.
- **Eval 4 (schema-composition-trap)**: Tests whether the agent understands that `_schema/` files must be named `<field>.schema.json` (not `<type>.schema.json`) for per-field validation, and that auto-discovery works without `--schema-db`. Without SKILL.md, agents may try to fix the concept data instead of the schema, or use `--schema-db` unnecessarily.
- **Eval 5 (workflow-ordering-trap)**: Tests whether the agent knows the recommended workflow (index → lint → validate) and uses `okf-schema index` to generate missing index files rather than creating them manually.
- **Eval 6 (reserved-files-trap)**: Tests whether the agent understands reserved filename rules (e.g., `log.md` only at root, subdirectory `index.md` must not have frontmatter).
- **Eval 7 (comment-preservation-trap)**: Tests whether the agent uses `okf-schema lint` to auto-fix block-style tags while preserving YAML comments, rather than manual editing that might strip comments.

### Dropped Evals

The following evals were removed after previous skeptical reviews showed they produced **zero delta** (both conditions scored identically):

- **bootstrap-knowledge-base (creation)**: Replaced by `repair-knowledge-base`. The creation task was too open-ended; both agents independently discovered the same correct approach.
- **migrate-and-validate**: Both conditions scored 7/11. The failed assertions were identical in both conditions due to execution flaws, not skill deficiency.
- **custom-schema-validation**: Both conditions scored 8/8. The task was straightforward enough that the without-skill condition discovered the naming convention through trial and error.
- **Original lint-comment-preservation**: Both conditions scored 6/6. The grader could not distinguish "lint run because SKILL.md said so" from "lint run because it seemed right."

## Grading Protocol

### Automated Deterministic Grading

All grading is performed by `grade-eval.py`, a deterministic script with no human judgment in the loop. This eliminates:
- Inter-rater reliability issues
- Confirmation bias
- Inconsistent standards between conditions

### Assertion Tiers

Each assertion is classified by **tier** to distinguish outcome validity from structural checks:

| Tier | Purpose | Weight |
|------|---------|--------|
| **primary** | Strict validation outcomes -- e.g., "0 errors", "0 warnings", "conformant" | High |
| **secondary** | Structure, content, and completeness checks | Standard |

**Rationale**: Process assertions (e.g., "ran `okf-schema lint`") were removed because they produced circular scoring -- the grader could not distinguish "ran lint because SKILL.md said so" from "ran lint because it seemed right." Primary assertions measure only whether the final result is correct.

### Assertion Types

Each assertion specifies:
- `check`: The check type (`command_executed`, `command_not_executed`, `output_contains`, `output_matches`, `file_exists`, `file_contains`, `file_glob_contains`, `file_glob_min_count`, `file_glob_max_count`)
- `target`: The string, regex, or file path to check
- `params`: Additional parameters for file-based checks (glob patterns, min/max counts, exclusions)
- `text`: Human-readable description (used in reports)
- `tier`: `"primary"` or `"secondary"`

### Scoring

- **PASS**: The check condition is satisfied in the transcript
- **FAIL**: The check condition is not satisfied
- **Primary Pass Rate**: `primary_passed / primary_total` per eval, per condition
- **Overall Pass Rate**: `passed / total` per eval, per condition

## Statistical Analysis

### Primary Metric: Delta Primary Pass Rate

For each eval case:
\[
\Delta_i = \text{PrimaryPassRate}_{\text{with},i} - \text{PrimaryPassRate}_{\text{without},i}
\]

### Aggregate Metrics

- **Mean Primary Delta**: $\bar{\Delta} = \frac{1}{n} \sum_{i=1}^{n} \Delta_i$
- **Improvement Ratio**: Proportion of evals where $\Delta_i > 0$
- **Overall Delta**: Same calculation using overall pass rates (reported for completeness)

### Effect Size

For publication, report:
- Cohen's $h$ for proportional differences (if sample size permits)
- Confidence intervals for pass rates (Clopper-Pearson exact method)
- Primary and overall metrics reported separately

## Reproducibility

### Iteration Directories

Each evaluation run produces an `iteration-XXX/` directory:

```
iteration-DD.MM.YY-HH.MM/
├── fix-non-conformant-bundle/
│   ├── with_skill/
│   │   ├── transcript.md
│   │   └── grading.json
│   └── without_skill/
│       ├── transcript.md
│       └── grading.json
├── repair-knowledge-base/
│   └── ...
├── init-structure-trap/
│   └── ...
├── schema-composition-trap/
│   └── ...
├── workflow-ordering-trap/
│   └── ...
├── reserved-files-trap/
│   └── ...
├── comment-preservation-trap/
│   └── ...
├── eval-result.html
└── skeptical-review.md
```

### Execution Protocol

To minimize cross-condition contamination and ordering bias:

1. **Parallel Execution**: Spawn two fresh subagents in parallel (max 2 concurrent) -- one for each condition
2. **Blinding**: Neither subagent has access to the other's resources or transcript
3. **Fresh Context**: Each subagent starts with a clean context (no prior conversation history)
4. **Same Model**: Both conditions use the same LLM model and temperature settings
5. **Immutable Fixtures**: Subagents MUST NOT modify any file under `skills-evals/fixtures/`. These directories are sacred, version-controlled reference data. Any eval that requires writing output must use a temporary working directory under the iteration's result folder (e.g., `results/iteration-DD.MM.YY-HH.MM/<eval_name>/<condition>/workspace/`).

### Re-running an Evaluation

1. Create a new iteration directory
2. Run the eval prompt for both conditions in parallel
3. Grade with: `just eval-grade-okf-schema iteration-DD.MM.YY-HH.MM`
4. **Spawn skeptical assessment subagent** (MUST happen before report generation)
5. View report with: `just eval-view-okf-schema` (regenerates report, now includes skeptical review)
6. Update `README.md` with the latest iteration link (one line only -- no tables or score blocks)

> **CRITICAL**: The skeptical assessment must run **before** the HTML report is generated.
> The report embeds the skeptical review. Generating it first bakes unchallenged
> results into the published artifact. Always regenerate the report after the skeptical review.
>
> **README format constraint**: The README must preserve the simple one-line link format:
> `**Latest eval result:** [iteration-...](...) -- [skeptical review](...)`
> Do NOT add score tables, delta breakdowns, or verdict blocks to the README.
> The HTML report and `CONSOLIDATED-REPORT.md` contain the full analysis.

### Version Control

- `evals.json`: Defines all eval cases and assertions
- `grade-eval.py`: Deterministic grader (versioned)
- `eval-viewer.py`: Report generator (versioned)
- Transcripts and grading outputs: Stored per iteration for audit

## Threats to Validity

### Internal Validity

- **Prompt wording**: `prompt_with_skill` and `prompt_without_skill` differ slightly to avoid priming the without-skill agent with skill-specific terminology. However, both ask for the same outcome.
- **Model temperature**: Not explicitly controlled; assumes default deterministic behavior.
- **Transcript completeness**: Relies on the agent logging all commands and outputs.
- **Parallel execution**: Running both conditions in parallel subagents reduces ordering bias but introduces the risk of shared environment state (mitigated by using separate working directories).
- **Blinding**: Subagents are blinded to each other's resources, but the orchestrator (human or top-level agent) is not -- this could introduce subtle bias in prompt construction.

### External Validity

- **Generalization**: Results apply to GPT-5.4 with this specific skill. Other models or skills may show different effect sizes.
- **Task selection**: Eval cases cover repair, creation, and schema debugging -- but not all possible `okf-schema` use cases.

### Construct Validity

- **Assertion coverage**: Assertions focus on observable behavior (commands run, output text) rather than internal reasoning. This is intentional for reproducibility but may miss nuanced understanding.

## Publication Checklist

For inclusion in a scientific paper, ensure:

- [ ] Multiple iterations (N >= 3) to assess variance
- [ ] Report mean +/- std dev of delta across iterations
- [ ] Include full `evals.json` and `grade-eval.py` in supplementary materials
- [ ] Report per-assertion breakdown, not just aggregate scores
- [ ] Discuss limitations (model-specific, task-specific)
- [ ] Make iteration directories available for independent verification

## References

- OKF Specification: `skills/okf-schema/references/okf-v0.1.md`
- Skill Definition: `skills/okf-schema/SKILL.md`
- Grader Source: `skills-evals/grade-eval.py`
