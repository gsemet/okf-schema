# Skeptical Review — okf-schema Skill Evaluation

**Date:** 2026-06-30  
**Iteration:** iteration-30.06.26-13.52

## Verdict

**No measurable advantage.** The skill shows a delta in only 1 of 4 evals (+27.3% on `migrate-and-validate`). The other three evals are flat (0% delta), with two scoring 100% on both sides. A single partial win on a workflow-ordering task is not evidence that the skill transfers meaningful knowledge.

## Root Causes

**1. Tasks are too easy; CLI is self-documenting.**  
Evals 1 and 2 hit 100% pass rates with and without the skill. The `okf-schema --help` output and the OKF v0.1 spec are sufficient for an agent to discover `init`, `new`, `validate`, `lint`, and `index` on its own. When the baseline agent can reverse-engineer the workflow from built-in docs, the skill adds no marginal value.

**2. Grader bug masks delta in Eval 4.**  
The `--schema-db` assertion uses `output_matches` with a negative-lookahead regex (`^(?!.*--schema-db).*$`) against the **entire transcript**. Both transcripts contain `--schema-db` inside `validate --help` output and SKILL.md quotes. This is a false failure — neither agent actually used the flag. The grader should check only executed command lines, not the full transcript.

**3. Assertions are shallow and redundant.**  
Most checks verify "was command X run?" rather than "was the output correct?" There is no quality gate on lint correctness (did block lists become inline?), index accuracy (do links resolve?), or schema semantics. Evals 1 and 2 test nearly identical command-sequencing behavior.

**4. Untested skill-specific knowledge.**  
The SKILL.md highlights ruamel.yaml round-trip comment preservation, JSON5 schema support, the Python API, and `lint --check` as differentiators. None of these are exercised. The evals only test basic CLI choreography, which is discoverable.

**5. Ceiling effect.**  
100% pass rates on three of four with-skill runs leave no headroom to measure improvement. If the skill is already "perfect" on trivial tasks, the evaluation cannot distinguish expertise from luck.

## Actionable Fixes

| Priority | Fix |
|----------|-----|
| **P0** | **Fix Eval 4 grader**: Change the `--schema-db` assertion to a `command_executed` inversion or regex scoped to command lines only, not the full transcript. |
| **P1** | **Add a hard eval**: Test YAML comment preservation during lint (create a bundle with comments, lint it, assert comments survive). This is skill-specific and not discoverable from `--help`. |
| **P1** | **Deepen quality assertions**: Replace "command executed" checks with output validation — e.g., assert linted frontmatter uses inline lists, or that `index.md` contains correct relative paths. |
| **P2** | **Consolidate redundant evals**: Drop or merge Evals 1 and 2; replace one with a custom-schema eval that requires JSON5 trailing-comma support or `--schema-db` override behavior. |
| **P2** | **Introduce expected-failure scenarios**: Create a bundle with W5 (nested lists) or W7 (block-style lists) warnings and assert that the agent runs `lint` and the warnings disappear. |

## Bottom Line

The current eval suite is too easy and too buggy to detect whether the skill actually helps. Fix the grader, raise the difficulty, and test skill-unique knowledge before claiming the skill is effective.
