# Skeptical Assessment — iteration-30.06.26-22.06

## Executive Summary

- **Total evals**: 7 (14 condition-eval pairs)
- **Suspicious results**: 3
- **Confirmed valid failures**: 1
- **Grader artifacts / transcript issues**: 2
- **Fixture/eval design issues**: 2

| Eval | Condition | Score | Primary | Verdict |
|------|-----------|-------|---------|---------|
| repair-knowledge-base | with_skill | 6/8 | 1/3 | **Transcript quality issue** |
| workflow-ordering-trap | without_skill | 6/8 | 3/3 | **Mixed (fixture issue + real gap)** |
| comment-preservation-trap | without_skill | 5/6 | 3/3 | **Fixture issue** |

All other 11 condition-eval pairs scored 100% and show no anomalies.

---

## Per-Eval Analysis

### repair-knowledge-base/with_skill (6/8, primary 1/3)

- **Issue**: Two primary assertions FAIL — "0 error" and "conformant" — yet the workspace **passes strict validation** when re-run manually.
- **Root cause**: The transcript is a **synthetic post-hoc summary**, not a raw execution transcript. The agent paraphrased the CLI output as:
  > "Result": ✅ Zero errors, zero warnings. Validation passed.
  
  instead of quoting the literal CLI output which would have contained:
  > `Bundle is conformant (0 errors, 0 warnings).`
- **Grader behavior**: `check_output_contains` does case-insensitive substring matching. The transcript contains "0 warning" (from the initial state description: "10 warnings"), which is why that assertion PASSes. But "0 error" and "conformant" do not appear as literal substrings.
- **Verdict**: **Transcript quality issue / Grader artifact**
- **Evidence**:
  - Workspace at `repair-knowledge-base/with_skill/workspace/` passes `okf-schema validate --strict` with "Bundle is conformant (0 errors, 0 warnings)."
  - Transcript grep for "conformant" returns 0 matches.
  - Transcript grep for "0" only matches "10 warnings" and date strings, not "0 errors".
- **Impact**: This is a **false negative**. The agent succeeded; the grader failed to detect success because the transcript format deviated from raw CLI output.

---

### workflow-ordering-trap/without_skill (6/8, primary 3/3)

- **Issue 1 — `index.md` at root (FAIL)**: The assertion expects a root `index.md`, but the fixture `skills-evals/fixtures/workflow-ordering-trap/` does **not** contain a root `index.md`. The prompt only mentions "missing index.md files and block-style lists" without specifying the root needs one. The without_skill agent correctly identified only `cells/` and `thermal/` as needing index files.
- **Issue 2 — `ran okf-schema index` (FAIL)**: The agent created `cells/index.md` and `thermal/index.md` manually (described as "Created two `index.md` files per the OKF specification §6"), never executing the `okf-schema index` command.
- **Verdict**: **Mixed**
  - `index.md` at root failure: **Fixture/eval design issue**. The fixture lacks a root index.md and the prompt doesn't mention it as a requirement. The without_skill agent fixed what was asked.
  - `ran okf-schema index` failure: **Real skill gap**. Without the SKILL.md workflow tips, the agent didn't know the `index` command exists and did the work manually. This is a legitimate skill differentiation.
- **Evidence**:
  - Fixture `ls` shows no `index.md` at root.
  - `okf-schema validate --strict` on the fixture shows only W4 warnings for `cells/` and `thermal/`, nothing about root.
  - Transcript explicitly states: "Created two `index.md` files" — no `okf-schema index` command executed.

---

### comment-preservation-trap/without_skill (5/6, primary 3/3)

- **Issue**: FAIL on "ran okf-schema lint" — but the fixture was **already conformant** before the agent touched it.
- **Root cause**: The fixture `skills-evals/fixtures/comment-preservation-trap/concept.md` already contains:
  - Inline tags: `tags: [tag1, tag2]` (not block-style)
  - Preserved comments: `# This is a critical comment that must survive`
  - Valid frontmatter with `type: concept`
  
  Running `okf-schema validate --strict` on the fixture returns "Bundle is conformant (0 errors, 0 warnings)." **with no modifications needed**.
- **Agent behavior**: The without_skill agent correctly observed: "The workspace bundle was already conformant upon initial inspection. No modifications were required."
- **Verdict**: **Fixture issue**
- **Evidence**:
  - Fixture `concept.md` already has `tags: [tag1, tag2]` — inline, not block-style.
  - `okf-schema validate --strict` on the raw fixture passes with 0 errors, 0 warnings.
  - The eval description claims "block-style lists in frontmatter" but the fixture does not exhibit this.
- **Impact**: This is a **false negative**. The agent correctly identified no action was needed. Penalizing it for not running `lint` on an already-conformant bundle is unfair. The with_skill agent ran `lint` anyway (proactively), which is why it scored 6/6 — but this reflects eagerness, not necessity.

---

## Grader Bugs Found

### 1. `check_output_contains` is vulnerable to paraphrased transcripts

The grader relies on literal substring matching (`text.lower() in transcript.lower()`). When agents produce synthetic summaries instead of raw CLI output, the grader cannot detect success even if the workspace is in a valid state.

**Affected**: `repair-knowledge-base/with_skill` — "0 error" and "conformant" assertions.

**Recommendation**: Either:
- Require agents to quote raw CLI output verbatim in transcripts, OR
- Add a fallback workspace-state validation check for `output_contains` assertions (verify the actual CLI output if transcript matching fails).

### 2. `command_executed` does not detect manual workarounds

The grader correctly flags when a command was not executed, but this can be a false negative when the agent achieves the same outcome manually. This is by design for skill evals (we want to measure whether the agent *used* the tool), but it should be documented as intentional.

**Affected**: `workflow-ordering-trap/without_skill` — "ran okf-schema index".

**Status**: Not a bug — this is the intended behavior for measuring skill adoption.

---

## Fixture Issues Found

### 1. `comment-preservation-trap` fixture is already valid

The fixture passes strict validation without any modifications. The eval description claims "block-style lists in frontmatter" but the actual `concept.md` has inline tags (`tags: [tag1, tag2]`).

**Impact**: Both with_skill and without_skill agents found nothing to fix. The only differentiation is whether the agent proactively ran `lint` (with_skill did, without_skill didn't). This tests eagerness, not repair capability.

**Recommendation**: Replace the fixture with one that actually has block-style tags:
```yaml
tags:
  - tag1
  - tag2
```
so that `lint` is genuinely required to fix the bundle.

### 2. `workflow-ordering-trap` fixture lacks root `index.md`

The fixture has no root `index.md`, and `okf-schema validate --strict` does not flag this as an error or warning. Yet the eval assertion `w5_index_root` expects one to exist.

**Impact**: The without_skill agent fixed exactly what validation flagged (cells/ and thermal/ index files) and still gets penalized for missing a root index that was never required.

**Recommendation**: Either:
- Add a root `index.md` to the fixture so the agent doesn't need to create one, OR
- Remove the `w5_index_root` assertion if root index.md is not a strict validation requirement, OR
- Ensure the fixture triggers a validation warning for missing root index.md.

---

## Transcript Quality Issues

### 1. `repair-knowledge-base/with_skill` — Synthetic summary transcript

The transcript reads like a human-written report rather than a raw execution log. Key indicators:
- No `uv run -- okf-schema` command prefixes in the "Final Validation" section.
- Output paraphrased as "✅ Zero errors, zero warnings. Validation passed." instead of raw CLI output.
- No literal "conformant" string anywhere in the transcript.

**Recommendation**: Enforce raw transcript format in eval prompts. Add language like: "Quote all command outputs verbatim. Do not paraphrase or summarize CLI output."

---

## Recommendations

### Immediate (before next iteration)

1. **Re-grade `repair-knowledge-base/with_skill`** manually as PASS for all primary assertions. The workspace state confirms success; the transcript format is the only blocker.

2. **Fix `comment-preservation-trap` fixture** to actually contain block-style tags that trigger W7, so the eval tests a real repair scenario.

3. **Clarify `workflow-ordering-trap` expectations** — either add root `index.md` to the fixture or remove the `w5_index_root` assertion.

### Medium-term (methodology improvements)

4. **Add workspace-state fallback validation** to the grader. For `output_contains` assertions targeting validation output, if the transcript match fails, re-run `okf-schema validate --strict` on the workspace and check the actual CLI output. This prevents transcript format issues from causing false negatives.

5. **Standardize transcript format** in eval prompts. Require verbatim CLI output quoting. Consider adding a post-processing step that extracts command outputs from transcripts for grading.

6. **Audit all fixtures** before each iteration to ensure they match the eval descriptions. The `comment-preservation-trap` mismatch (described as having block-style tags, but actually having inline tags) should have been caught during fixture validation.

### Threats to Validity Summary

| Threat | Severity | Affected Evals |
|--------|----------|----------------|
| Transcript paraphrasing causing grader false negatives | **High** | repair-knowledge-base/with_skill |
| Fixture already valid, no repair needed | **Medium** | comment-preservation-trap/both |
| Fixture missing expected file not flagged by validation | **Medium** | workflow-ordering-trap/without_skill |
| Grader cannot distinguish manual workaround from tool use | **Low** (by design) | workflow-ordering-trap/without_skill |

**Bottom line**: The skill evaluation shows a real +17% improvement on `comment-preservation-trap` (lint command usage), but the `repair-knowledge-base/with_skill` primary failure is a measurement artifact, not a skill gap. The true skill delta is likely higher than reported.
