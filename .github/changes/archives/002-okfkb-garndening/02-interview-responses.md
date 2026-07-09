# Interview Responses — okfkb-gardening

**Date:** 2026-07-09
**Conducted by:** GitHub Copilot (grill-me skill)
**Codebase explored:** okf-schema CLI, `okfkb` subcommands, bundle structure

---

## Round 1

**Q1: How is the gardening skill invoked — on-demand by the user, periodically (scheduled), or automatically after `okfkb update`?**
> **Answer:** On-demand only (user calls it explicitly)

**Q2: When a broken link is detected (file moved/renamed/deleted), what should the skill do?**
> **Answer:** Auto-fix if confident (git history), report if ambiguous

**Q3: How should the skill identify that a Finding is obsolete or superseded — via a frontmatter field, via AI analysis, or both?**
> **Answer:** Hybrid — status field is authoritative + AI flags active candidates

**Q4: For the project-version dimension (e.g., 26.2 vs 28.2), where should the context metadata live?**
> **Answer:** DEFERRED — "do not decide now, just prepare all the rest"

**Q5: Should the gardening feature require new `okfkb` CLI subcommands, or should it work purely as a Copilot agent skill (SKILL.md) orchestrating existing commands?**
> **Answer:** Skill-only — no new CLI commands
> *(Note: This decision was later reopened by Q8/Q11)*

---

## Round 2

**Q6: What exactly should the small-model subagent verify for each link?**
> **Answer:** A — pairwise source-target coherence check

**Q7: Which small model should be the default for the coherence subagent?**
> **Answer:** Kimi K2.7 Code first, then Haiku as fallback

**Q8: How does the skill determine the replacement target when removing a link to a superseded finding?**
> **Answer:** "`superseded_by` should be updated at the same time as backlinks during `okfkb update`. this is a `okfkb` specific update[d]."
> *(This answer reopens Q5 — implies a CLI extension to `okfkb update`)*

**Q9: What format and location for the coherency report produced at the end?**
> **Answer:** Chat summary only (no file written)

**Q10: Would you like me to stop the interview here?**
> **Answer:** No — continue the interview

---

## Round 3

**Q11: How should superseded-link rewriting be delivered — extend `okfkb update`, add `okfkb garden`, or keep it skill-only?**
> **Answer:** A — extend `okfkb update` with superseded-link rewriting
> *(This supersedes Q5's "skill-only" decision — a CLI change IS required)*

**Q12: Should the skill run in interactive mode (pause per ambiguity) or batch mode (collect all decisions, present at end)?**
> **Answer:** Batch — auto-fix + collect decisions, present at end

**Q13: Should coherence subagent calls run in parallel or sequentially?**
> **Answer:** Parallel, max 4 concurrent

**Q14: What trigger phrase should invoke this gardening skill?**
> **Answer:** `okfkb garden /path/to/kb`

**Q15: Would you like me to stop the interview here?**
> **Answer:** Yes — stop, present the summary
