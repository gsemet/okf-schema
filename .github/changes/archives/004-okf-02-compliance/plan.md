# Plan — OKF 0.2 Compliance for `okf-schema`

## Request context

`okf-schema` is an opinionated OKF **0.1** implementation (validator E0–E7 / W0–W7,
formatter/linter, and a bundled `okfkb` knowledge base). OKF **0.2** has been
released (GoogleCloudPlatform/knowledge-catalog `okf/SPEC.md`). 0.2 is a
backward-compatible minor bump — existing bundles stay *conformant* — but it makes
provenance (`sources`), trust (`generated`/`verified`), lifecycle
(`status`/`stale_after`), and attestation (`Attested Computation`) first-class, and
renames two things: `timestamp` → `generated.at`, and the body `# Citations` list →
`sources` frontmatter + markdown footnotes.

A grill-me interview established how far to take 0.2 support and how to build it.
The unifying principle: **`okf-schema` is an agent-oriented advisor, not an
exhaustive enforcer** — it auto-fixes the mechanical and, for anything structural or
schema-dependent, emits a stable, greppable remediation contract (code + one-line
`Fix:` directive + exact command) so a coding agent reading stdout/stderr can close
the loop and re-lint to green.

### Scope boundaries

- **In scope now:** consumer tolerance + producer parity for provenance, trust, and
  lifecycle; agent-facing remediation output; migration of bundled data; derived
  trust/staleness surfacing; provenance-integrity checks; version/reference
  housekeeping.
- **Deferred:** the `Attested Computation` type (§10) and its
  `runtime`/`parameters`/`computation`/`executor`/`attester` contract and
  `# Computation` heading.

## Resolved decisions

| # | Topic | Resolution | Rationale |
|---|-------|-----------|-----------|
| Q1 | Scope | Staged: consumer tolerance + producer parity now; defer `Attested Computation` | Highest value/lowest risk first; §10 is the largest surface |
| Q2 | Driver | Proactive future-proofing; no external 0.2 bundle | Deliberate, doc-first alignment with the moved spec |
| Q3 | Rollout | 0.2 becomes the **default** validation mode | Tool follows the current spec by default |
| Q4 | Back-compat | Accept legacy `timestamp`/`# Citations` but **warn with actionable stdout** so an agent auto-fixes and re-lints | Honors 0.2 fallbacks while driving migration via the agent loop |
| Q5 | Auto-fix mechanism | **Mechanical renames auto-fixed** by lint; structural rewrites emit **clear guidance**, not auto-applied | Safe automation; humans/agents own structural intent |
| Q6 | Severity | Never error on absent optional family; error only on **internal violations of a present block** | Matches §11 MUST-NOT-reject while enforcing required-within-block fields |
| Q7 | `status` collision | Namespace KB to **`kb_status`**; free `status` for OKF lifecycle; **emit guidance for the copied JSON Schemas** rather than auto-supporting every case | Preserves KB semantics; respects customizable schemas via the advisor model |
| Q8 | Surfacing | Derive **trust tier + staleness** in `show`/`stats`; staleness flag in `list` | Delivers the real 0.2 consumer payoff |
| Q10 | Output contract | Stable **code + one-line `Fix:` + exact command**, consistent greppable prefix | Makes the agent-remediation loop deterministic |
| Q11 | Bundled migration | Migrate `okfkb` schemas + `finding.py` + `examples/` **now** | Shipped product must pass its own default-0.2 lint |
| Q12 | Actor convention | **Warn (never error)** on malformed actors; derive trust only from well-formed `human:` actors | Consistent advisor model; protects trust-tier accuracy |
| Q13 | Linter | **Exempt list-of-mapping fields** (`sources`, `verified`, `parameters`) from inline-forcing; still flatten nested scalar lists | Keeps 0.2 provenance/trust blocks readable |
| Q15 | Footnote integrity | **Warn** on `[^id]` with no matching `sources[].id`; optionally note uncited sources; never error | Catches provenance defects without rejecting |
| Q16 | Frontmatter paths | **Warn** on broken `resource` / path-form `sources[].resource`; skip scope descriptors and URLs; never error | Extends checks while preserving 0.2 link tolerance |
| Q17 | Housekeeping | Add `okf-v0.2.md`, repoint `AGENTS.md`/docs, validate `okf_version`, scaffold declares `0.2`, and **discard the inline v0.1 spec entirely** | Grounding and docs must reflect 0.2-only |
| Q18 | Warning codes | **New stable codes (W8+)**, one per distinct deprecation/violation | Preserves the deterministic greppable contract |

## Derived work items (non-binding, for implementation planning)

These follow from the decisions above; they are a map, not an implementation directive.

1. **Trust/freshness fields (Q4, Q5, Q6, Q18)**
   - Repurpose/extend the freshness check: warn when neither `generated.at` nor legacy
     `timestamp` is present; when `timestamp` is present but `generated` is absent, emit a
     deprecation warning (new W8+ code) whose `Fix:` names the lint autofix command.
   - Lint autofix: mechanical `timestamp` → `generated.at` (and seed `generated.by`).
   - Error only on internal violations of a *present* `generated` block (missing `by`).

2. **Provenance `sources` + footnotes (Q4, Q5, Q15, Q16, Q18)**
   - Recognize `sources` (entries: `resource` required; optional `id`, `title`,
     `author`, `usage_count`, `last_modified`) and the `usage_window` sibling.
   - Structural guidance (not autofix) for legacy body `# Citations` → `sources` + footnotes.
   - Warn on `[^id]` footnotes with no matching `sources[].id`; optionally note uncited sources.
   - Warn on broken `resource` / path-form `sources[].resource`; skip scope descriptors and URLs.

3. **Trust `verified` + tiers (Q6, Q8, Q12)**
   - Parse `verified`; **normalize a bare mapping to a one-element list** (§11 MUST).
   - Error only on present-but-malformed entries (missing `by`/`at`).
   - Derive trust tier (unverified / machine-confirmed / human-reviewed) from well-formed
     `human:` actors; warn (never error) on malformed actor strings.

4. **Lifecycle `status` / `stale_after` (Q6, Q8)**
   - Recognize `status` (`draft|stable|deprecated`, default `stable`) and `stale_after`.
   - Surface staleness (`today >= stale_after`) and trust tier in `show`/`stats`; add a
     staleness flag to `list`.

5. **Linter readability (Q13)**
   - Exempt list-of-mapping fields (`sources`, `verified`, `parameters`) from
     inline-forcing (W7); keep flattening genuine nested scalar lists.

6. **Bundled data migration (Q7, Q11)**
   - `okfkb` Base/Finding schemas + `finding.py`: `timestamp` → `generated`, add
     `verified`/`status`; move KB lifecycle vocabulary to `kb_status`.
   - Migrate `examples/` bundles to 0.2 shape so they pass default-0.2 lint.
   - For copied/customizable `_schema/*` JSON Schemas, emit guidance (don't auto-migrate).

7. **Version & docs housekeeping (Q3, Q17)**
   - Add `skills/okf-schema/references/okf-v0.2.md`; **remove the inline v0.1 spec**.
   - Repoint `AGENTS.md` and docs to 0.2; validate the declared `okf_version`; have
     scaffold/init declare `"0.2"`.
   - Update `docs/.../validation-codes.md` with the new W8+ codes.

8. **Remediation output contract (Q10, Q18)**
   - Every deprecation/violation carries a stable code, a single `Fix:` directive line,
     and the exact command, behind a consistent greppable prefix.

## Out of scope (deferred)

- `Attested Computation` type (§10): `runtime`, `parameters`, `computation`,
  `executor` (+ `receipt`), `attester`, the `# Computation` heading, and
  path-checking of `computation`/`executor.resource`/`attester.resource`.

## Unresolved items

None.
