# Interview Responses — okf-schema-kb-subcommands

---

## Round 1 — Testing, Documentation, UX (Q1–Q5)

**Date**: 2026-07-03T00:00:00

### Q1 — Testing approach for scaffold + install logic
**Question.** The project has a 96% coverage threshold. The new KB scaffold code will copy
directories and write files. What testing approach do you prefer?
**Answer.** Real temp dirs (tmp_path) for scaffold; mock shutil for install unit tests.

### Q2 — Integration test for install-skills that patches AGENTS.md
**Question.** Should `okfkb install-skills` have an end-to-end integration test that actually
copies skills into a temp project dir and verifies AGENTS.md is patched?
**Answer.** Yes — happy path + conflict cases.

### Q3 — Documentation: dedicated Sphinx page for kb commands
**Question.** Should the `kb` subcommand group get a dedicated Sphinx documentation page
(e.g., `docs/source/kb-commands.rst`), or just extend the existing CLI reference page?
**Answer.** Yes — dedicated kb-commands page.

### Q4 — Add a new '## Knowledge Base' section to README
**Question.** Should the README get a new top-level section "Knowledge Base" explaining
`okfkb init` and `okfkb install`?
**Answer.** Yes. Explain concisely this opinionated knowledge base dedicated at experiment
and building trustful knowledges. and point to sphinx doc page.

### Q5 — What should the install command be called
**Question.** What should the install command be named?
**Answer.** `okfkb install [PATH]` (install everything at once — skills + guideline together).

---

## Round 2 — UX + Feature-Specific (Q6–Q10)

**Date**: 2026-07-03T00:00:00

### Q6 — Conflict resolution when okfkb install finds existing files
**Question.** When `okfkb install [PATH]` finds that skills or guidelines already exist in the
target project, what should happen?
**Answer.** Skip existing + warn; --force to overwrite.

### Q7 — Behavior when no AGENTS.md exists in the target project
**Question.** If the target project has no `AGENTS.md`, should `okfkb install` create a minimal
one (with just the guideline reference), or skip the AGENTS.md step entirely?
**Answer.** Create a minimal AGENTS.md with the reference.

### Q8 — Is --pattern kb a one-off or extensible for future patterns
**Question.** Should `--pattern` on `okf-schema init` be designed for future extensibility
(e.g., `--pattern library` later), or is `kb` the only pattern?
**Answer.** Extensible — registry/plugin dict for future patterns.

### Q9 — Relationship between okfkb init and the base okf-schema init scaffold
**Question.** Should `okfkb init` build on top of the base scaffold (layered), or create a
completely independent KB structure from scratch?
**Answer.** Independent — KB owns its own full layout incl. schemas (not the base OKF schemas).

### Q10 — Shared understanding check
**Question.** Do we have shared understanding, or shall I dig deeper into any area?
**Answer.** Yes — shared understanding, proceed to spec.
