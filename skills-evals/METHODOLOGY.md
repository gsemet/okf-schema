# OKF Schema Skill Evaluation Methodology

## Overview

This document describes the controlled A/B evaluation framework used to measure the effectiveness of the `okf-schema` skill for AI coding agents. The methodology is designed for reproducibility, statistical validity, and publication in a scientific paper.

## Research Question

**Does providing an AI agent with a structured skill definition (SKILL.md) improve its ability to correctly use the `okf-schema` CLI tool compared to relying solely on CLI help text and general knowledge?**

## Experimental Design

### Conditions

| Condition | Treatment | N (assertions) |
|-----------|-----------|----------------|
| **With Skill** | Agent receives `SKILL.md` + CLI help | 39 (4 evals) |
| **Without Skill** | Agent receives CLI help + OKF spec | 39 (same assertions) |

Both conditions are evaluated against the **identical assertion set** for each eval case, ensuring an apples-to-apples comparison.

### Independent Variable

- **Skill Access** (binary): Whether the agent has read access to `skills/okf-schema/SKILL.md`

### Dependent Variables

1. **Pass Rate** (primary): Proportion of assertions passing per condition
2. **Command Correctness**: Whether the agent invoked the correct `okf-schema` subcommand with correct flags
3. **Output Interpretation**: Whether the agent correctly interpreted validator output

### Controlled Variables

- Same LLM model (GPT-5.4) for both conditions
- Same fixture bundles (`fix-non-conformant-bundle`, `legacy-docs`)
- Same project directory and environment
- Same grading script (`grade-eval.py`) — no human in the scoring loop

## Eval Cases

| ID | Name | Category | Assertions | Description |
|----|------|----------|------------|-------------|
| 1 | fix-non-conformant-bundle | Repair | 7 | Fix a broken bundle to pass `validate --strict` |
| 2 | bootstrap-knowledge-base | Creation | 13 | Create an EV Battery Management KB from scratch |
| 3 | migrate-and-validate | Migration | 11 | Migrate 5 plain markdown files into a conformant OKF bundle |
| 4 | custom-schema-validation | Skill-specific | 8 | Create a custom type with auto-discovered JSONSchema |

**Total assertions**: 39

## Grading Protocol

### Automated Deterministic Grading

All grading is performed by `grade-eval.py`, a deterministic script with no human judgment in the loop. This eliminates:
- Inter-rater reliability issues
- Confirmation bias
- Inconsistent standards between conditions

### Assertion Types

Each assertion specifies:
- `check`: The check type (`command_executed`, `output_contains`, `output_matches`, `file_exists`, `file_contains`, `file_glob_contains`, `file_glob_min_count`)
- `target`: The string, regex, or file path to check
- `params`: Additional parameters for file-based checks (glob patterns, min counts, exclusions)
- `text`: Human-readable description (used in reports)

### Scoring

- **PASS**: The check condition is satisfied in the transcript
- **FAIL**: The check condition is not satisfied
- **Pass Rate**: `passed / total` per eval, per condition

## Statistical Analysis

### Primary Metric: Delta Pass Rate

For each eval case:
$$
\Delta_i = \text{PassRate}_{\text{with},i} - \text{PassRate}_{\text{without},i}
$$

### Aggregate Metrics

- **Mean Delta**: $\bar{\Delta} = \frac{1}{n} \sum_{i=1}^{n} \Delta_i$
- **Improvement Ratio**: Proportion of evals where $\Delta_i > 0$

### Effect Size

For publication, report:
- Cohen's $h$ for proportional differences (if sample size permits)
- Confidence intervals for pass rates (Clopper-Pearson exact method)

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
├── bootstrap-knowledge-base/
│   └── ...
├── migrate-and-validate/
│   └── ...
└── eval-result.html
```

### Re-running an Evaluation

1. Create a new iteration directory
2. Run the eval prompt for both conditions
3. Grade with: `just eval-grade-okf-schema iteration-DD.MM.YY-HH.MM`
4. View report with: `just eval-view-okf-schema`

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

### External Validity

- **Generalization**: Results apply to GPT-5.4 with this specific skill. Other models or skills may show different effect sizes.
- **Task selection**: Eval cases cover repair, creation, and migration — but not all possible `okf-schema` use cases.

### Construct Validity

- **Assertion coverage**: Assertions focus on observable behavior (commands run, output text) rather than internal reasoning. This is intentional for reproducibility but may miss nuanced understanding.

## Publication Checklist

For inclusion in a scientific paper, ensure:

- [ ] Multiple iterations (N ≥ 3) to assess variance
- [ ] Report mean ± std dev of delta across iterations
- [ ] Include full `evals.json` and `grade-eval.py` in supplementary materials
- [ ] Report per-assertion breakdown, not just aggregate scores
- [ ] Discuss limitations (model-specific, task-specific)
- [ ] Make iteration directories available for independent verification

## References

- OKF Specification: `skills/okf-schema/references/okf-v0.1.md`
- Skill Definition: `skills/okf-schema/SKILL.md`
- Grader Source: `skills-evals/grade-eval.py`
