# Baseline requirements maintenance

- Use the frontmatter `title` verbatim as the first Markdown heading (`## Title`).
  Keep the heading synchronized when renaming a requirement; EARS describes
  the statement format, not the document title.

Use this fallback only when the target bundle has no local requirements guideline.
Resolve actual paths and scopes from its config; do not assume this package's
repository layout applies to another project.

- Read the project's AGENTS.md, `<bundle>/config.yml`, and all schemas under
  `<bundle>/tiers/_schema/` before editing.
- Preserve stable IDs, UUIDs, authored intent, comments, unknown metadata and bodies.
- An ID is never reused: `okfreq new` numbers after the highest number ever used,
  including `retired_ids` in `config.yml`. Discard a never-published draft with
  `okfreq retire ID --yes`, never by deleting the file; published requirements are
  archived or superseded.
- Use `okfreq new strs` for stakeholder intent and user need; use `new swrs`
  for one observable behavior with a valid parent and nominal/failure scenarios.
- Complete scaffold placeholders before review. Prose warnings remain advisory.
- Use configured markers near real implementation and tests. Direct StRS tests
  are legitimate when the configured coverage mode calls for validation tests;
  StRS implementation coverage is not applicable.
- Preview `update-coverage --diff`, then regenerate owned fields. Never author
  reverse relationships or coverage arrays by hand.
- Run validate/lint with `--prose`, inspect graph/trace, and explicitly opt into
  file checks with `--check-links --project-root <project>` when roots are known.
- Write reports to explicit project `dist/` paths with `--output-json` and
  `--output-summary-md`. Run the project's real tests separately.
- Lifecycle, exemptions, external ownership and imported content require an
  explicit decision; missing evidence cannot be repaired by inventing markers.

For concrete commands, configuration, file-link semantics and failure handling,
read the bundled [operations reference](operations.md).

## OKF navigation and history duties

Run `okfreq lint <bundle>` after requirement changes to refresh marked navigation
blocks in `tiers/index.md`, each tier and all scope/ancestor directories. Preserve
introductions and frontmatter outside the generated markers and preserve the
authored `<bundle>/index.md`. Use `lint --check` in CI and `--diff` to preview.
Append substantive changes, affected IDs, rationale and real validation results
to `<bundle>/tiers/log.md`, with newest date sections first. This authored log
is never regenerated; the canonical name is `log.md`, not `logs.md`.
