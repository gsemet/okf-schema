# Goal: OKF 0.2 Compliance for `okf-schema`

## User Request

Implement the complete OKF 0.2 compliance brief described in `plan.md` for the
`okf-schema` project. Treat `plan.md` as the implementation brief, leave it
unchanged, and preserve unrelated working-tree changes.

## Refined Goal

Bring `okf-schema` from its current OKF 0.1-oriented implementation to the
resolved OKF 0.2 behavior described in `plan.md`. Make 0.2 the default while
remaining tolerant of the specified legacy forms, provide deterministic
agent-facing remediation output, migrate bundled producers/data/docs, and
surface derived trust and staleness information through the public APIs and CLI.
The Attested Computation type and its related contract remain explicitly
 deferred.

## Acceptance Criteria

- [ ] OKF 0.2 is the default validation/scaffold version, with version/reference
      housekeeping updated to 0.2-only as specified: add `okf-v0.2.md`, repoint
      project documentation and guidance, validate `okf_version`, and remove the
      inline v0.1 specification.
- [ ] Validation accepts absent optional 0.2 families, but validates present
      `generated`, `sources`, `verified`, `status`, and `stale_after` blocks
      according to the plan; internal violations of present blocks are errors,
      while malformed actors and provenance/path integrity issues are warnings.
- [ ] Legacy `timestamp` and body `# Citations` remain tolerated but produce
      stable W8+ (or later) actionable warnings; mechanical timestamp migration
      is lint-autofixable, while structural citations migration emits guidance
      rather than silently rewriting intent.
- [ ] Every actionable deprecation/violation uses a stable greppable output
      contract containing a stable code, one single-line `Fix:` directive, and
      the exact remediation command.
- [ ] Provenance behavior supports `sources` and `usage_window`, checks footnote
      references and applicable resource paths without rejecting advisory issues,
      and preserves the specified URL/scope-descriptor exceptions.
- [ ] Trust behavior supports `verified`, normalizes a bare mapping to a
      one-element list, derives conservative unverified/machine-confirmed/
      human-reviewed tiers only from well-formed `human:` actors, and never
      promotes malformed actor data.
- [ ] Lifecycle behavior supports `status` and `stale_after`, derives staleness,
      and exposes trust tier plus staleness through `show` and `stats`, with a
      staleness flag in `list`.
- [ ] The formatter exempts list-of-mapping fields such as `sources`, `verified`,
      and `parameters` from inline forcing while continuing to flatten genuine
      nested scalar lists.
- [ ] Bundled `okfkb` schemas, Finding generation/navigation, examples, fixtures,
      and related producer content are migrated to the 0.2 shape, using
      `kb_status` for KB lifecycle vocabulary and providing guidance rather than
      automatic migration for copied/customizable schemas.
- [ ] Tests and documentation cover the changed behavior, including stable
      warning/error codes and public API/CLI output, and the complete repository
      quality gate `just preflight` passes (including the configured 96% coverage
      threshold and warnings-as-errors documentation build).
- [ ] Attested Computation remains out of scope: no implementation of its
      `runtime`, `parameters`, `computation`, `executor`, `receipt`, `attester`,
      or `# Computation` contract is required by this goal.

## Scope Boundaries

**In scope:**
- Consumer tolerance and producer parity for OKF 0.2 provenance, trust, and lifecycle.
- Agent-facing remediation output, mechanical migration autofix, and structural guidance.
- Derived trust-tier and staleness surfacing in validator/API/CLI behavior.
- Formatter readability rules for list-of-mapping fields.
- Migration of bundled `okfkb` data, schemas, Finding/navigation behavior, examples,
  fixtures, skills, and relevant documentation.
- Version/reference housekeeping and tests required for the above.
- Goal workflow artifacts under this request directory.

**Out of scope:**
- The OKF 0.2 Attested Computation type and its `runtime`, `parameters`,
  `computation`, `executor`/`receipt`, `attester`, and `# Computation` contract.
- Editing `plan.md`.
- Changes unrelated to this migration or the preserved existing working-tree artifacts.

## Applicable Project Conventions

**Quality gate command:**
- `just preflight`

**Commit convention:**
- Conventional Commits with a concise user-impact subject, as supported/enforced by
  Commitizen. Goal workflow commits must also use the required `[B]`/`[I]` role marker,
  stay within 72 characters, and include the required Assisted-by trailer.
- Assisted-by trailer required: `Assisted-by: Claude:Sonnet-4.6`

**Guidelines:**
- `AGENTS.md`
- `CONTRIBUTING.md`
- `justfile`
- `pyproject.toml`
- No `CONSTITUTION.md` or `.agents/guidelines/` files were present during discovery;
  use the available project guidance as the operational baseline.

**Rules:**
- Preserve unrelated working-tree changes and inspect diffs before committing.
- Put package changes under `src/okf_schema/` and matching tests under `tests/`.
- Update documentation for public behavior/API changes.
- Keep warning codes stable and machine-greppable; keep optional-block absence
  non-erroring and provenance/path integrity advisory as specified.
- Do not manually edit generated indexes or derived artifacts unless the project
  workflow requires it.
