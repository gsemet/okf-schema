# Skeptical Review: iteration-30.06.26-13.12

**Verdict: Zero measurable skill advantage.** Both conditions scored 22/29 (75.9%). The delta is flat.

## Root Causes

1. **Grader false negatives**: 5 `output_matches` assertions in Eval 1 scanned the full transcript, catching initial validation errors before fixes. The cross-link check inspected transcript prose instead of actual concept files.
2. **Tasks too easy**: Adding frontmatter, fixing dates, and running `lint`/`index`/`validate` are discoverable from CLI help and the OKF spec. No edge cases or deep reasoning required.
3. **Skill-specific knowledge untested**: Workflow sequencing (`index → lint → validate`), `lint --check`, schema auto-discovery (`_schema/` naming), and round-trip YAML preservation were never exercised.

## What Was Fixed

- Removed 5 brittle full-transcript regex checks (Eval 1)
- Cross-link check now inspects files, not transcript (Eval 2)
- Removed `okf_version` quirk check (Eval 2)
- Added `file_glob_min_count` grader check type
- Added Eval 4 (`custom-schema-validation`) testing schema auto-discovery — genuinely skill-specific

## What Is Still Needed

- **Obsidian migration eval**: Test wikilink conversion from skill references
- **Error-interpretation eval**: Subtle errors (nested lists, schema mismatch) without running validate first
- **Workflow-sequence eval**: Explicitly ask for "recommended workflow"; with-skill should run `index → lint → validate`

## Conclusion

The flat result is methodological, not substantive. Fix the grader bugs, add harder evals, re-run. Target: 20–40% improvement on non-trivial tasks.
