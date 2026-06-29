# Wrap-Up Specification: okf-schema

## 1. Commit Scope

Run `uv run --no-sync craftsman agent show --prd .agents/changes/request/init` to read `initial_sha1`.
Use: `git log --oneline <initial_sha1>..HEAD`
to capture ALL commits across ALL phases from the start of implementation.
Do NOT generate messages covering only the latest phase.

## 2. Achievement Report Template

The achievement report MUST contain exactly these 7 sections (in order):

### Activity Report
Timeline of the implementation:
- Started: `{progress.started}`
- Each phase: started → completed date and duration
- Each task: status, rework count (from `inspection_history`)
- Total tasks: N completed, N reworked, N skipped
- Total elapsed: X hours/days

### Inspection History Summary
Per-phase inspection outcomes (reference each phase report):
- Phase 1: N tasks, M rework cycles, K first-pass approvals
- Phase 2: N tasks, M rework cycles, K first-pass approvals
- Phase 3: N tasks, M rework cycles, K first-pass approvals
- Phase 4: N tasks, M rework cycles, K first-pass approvals
Aggregate: total inspections, total rework, overall pass rate

### Main Issues Encountered
Patterns extracted from all `inspection_history` entries with
`verdict == "fail"`:
- Group similar issues together
- Note frequency (how many tasks had this type of issue)

### Recommendations
Based on recurring issues and rework patterns:
- [Actionable recommendation 1]
- [Actionable recommendation 2]

### Tech Debt Report
Identify tech debt from three sources:
1. **TODO/FIXME/HACK comments** added in this PRD's commits:
   `git log --oneline {initial_sha1}..HEAD --name-only | xargs grep -n "TODO\|FIXME\|HACK" 2>/dev/null`
2. **Recurring inspector issues** (patterns from Main Issues section above)
3. **Tasks with ≥3 rework cycles** (high-friction areas)

Format each tech debt item as:
- **[Area]**: Description — Priority: Low/Medium/High

### Campaigns Not In Preflight
List any test campaigns or quality checks that exist in the project
but are NOT part of the preflight harness (the checks that run in
the Coder/Inspector loop). Examples:
- E2E screenshot campaigns (`just dashboard-e2e`)
- Demo video generation (`just dashboard-video`)
- VHS CLI recordings (`just record-readiness`)
- Performance benchmarks or coverage threshold checks
If none exist, write: "None identified."

### Requirements Impacted
Read `git diff {initial_sha1}..HEAD` on files under
`.agents/requirements/tiers/`. Build a table of requirements that
were added, updated, or removed in this delivery:

| Requirement ID | Title | Status |
|----------------|-------|--------|
| `SwRS-XYZ-0001` | Description | Implemented & tested |

If no requirements were modified: write "None — no requirement files
were changed in this delivery."

## 3. Harness Coverage Check

Before generating final reports, identify any test campaigns or quality checks
that exist in the project but are NOT part of the preflight harness
(the checks that run in the Coder/Inspector loop).

Examples of campaigns that might exist outside preflight:
- E2E screenshot campaigns (`just dashboard-e2e`)
- Demo video generation (`just dashboard-video`)
- VHS CLI recordings (`just record-readiness`)
- Performance benchmarks
- Coverage threshold checks beyond basic tests

List any such campaigns found and note them in the achievement report
under a "## Campaigns Not In Preflight" section. If the user should
decide whether to run them before finalizing, ask for confirmation.

## 4. Stale Pattern Sweep

No renames in this PRD — skip sweep.

## 5. Finalization Templates reference

Invoke `craftsman-internal-finalization-templates` for the
`07-commit-msg.md`, `07-git-squash-commits.sh`, and
`08-gitlab-mr-description.md` templates.
