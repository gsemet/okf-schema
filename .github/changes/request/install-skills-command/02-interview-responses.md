# Install packaged agent skills: interview responses

## Grounding findings

- `pyproject.toml` exposes three console entry points: `okf-schema`, `okfkb`,
  and `okfreq`.
- The wheel build currently includes `src/okf_schema`; the seven canonical
  skill directories are currently under the repository-level `skills/`
  directory.
- Existing package code already uses `importlib.resources` for schemas,
  guidelines, and a smaller set of bundled skills.
- The existing `okfkb install-skills` operation installs two skills and a
  guideline, edits `AGENTS.md`, defaults its path to `.`, skips existing files,
  and accepts `--force`.
- Repository-level skills are `okf-schema`, `okfkb`, `okfkb-distill`,
  `okfkb-gardening`, `okfkb-record-findings`, `okfreq`, and
  `okfreq-gardening`.

## Questions and answers

| Question | Decision | Rationale |
|---|---|---|
| Q1: Which skills should each command install? | Include base routers and companions. | Each CLI family remains coherent. |
| Q2: What should happen when an owned skill folder exists? | Atomically replace owned folders. | Packaged skills upgrade predictably while unrelated skills remain untouched. |
| Q3: How should path and destination flags interact? | An explicit path takes precedence. | A provided destination is authoritative even when a selector is also present. |
| Q4: How should users provide a custom destination? | Optional positional `DESTINATION`. | It is the command's primary operand and remains concise. |
| Q5: What should relative and local paths resolve against? | Current working directory. | Resolution is transparent and does not depend on repository discovery. |
| Q6: How transactional should a family install be? | Stage the full family first. | Resource-preparation failures leave the destination unchanged. |
| Q7: Which `uv` guidance belongs in the base skills? | PyPI install and upgrade, plus all three commands. | Covers first installation and subsequent updates. |
| Q8: Stop after the second round? | No, continue. | Compatibility and failure behavior still needed resolution. |
| Q9: Replace the old `okfkb install-skills` contract? | Yes. | All three installers become consistent, skills-only operations. |
| Q10: How should owned destination symlinks be handled? | Fail clearly. | Avoid following or replacing paths that may point outside the destination. |
| Q11: What output and extra modes are required? | Resolved destination plus per-skill status; no quiet or dry-run mode. | The operation is auditable without expanding scope. |
| Q12: Stop and summarize? | Yes. | All identified decision nodes were resolved. |
| Q13: Which handoff? | Option A. | Persist the complete interview and specification in the backlog. |

## Explicitly rejected alternatives

- Excluding the base `okfkb` and `okfreq` router skills from their families.
- Skipping, merging, or failing on ordinary existing owned directories.
- Rejecting a destination path merely because a selector flag is also present.
- Searching upward for a repository root when resolving local destinations.
- Installing family members independently without staging.
- Retaining guideline installation or `AGENTS.md` mutation in
  `okfkb install-skills`.
- Following or silently replacing symbolic links.
- Adding `--quiet` or `--dry-run` as part of this change.

## Unresolved items

None.
