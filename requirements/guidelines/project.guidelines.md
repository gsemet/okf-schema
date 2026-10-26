# Project requirements guidelines

This file holds only what is specific to this repository. Read the
[shipped baseline](requirements.guidelines.md) first: it is the guidance `okfreq init` installs
into every bundle, a copy of the single maintained source (minus its own requirement marker) at
[`src/okf_schema/data/requirements/guidelines/requirements.guidelines.md`](../../src/okf_schema/data/requirements/guidelines/requirements.guidelines.md).
Never edit that installed copy: `okfreq init requirements --force` replaces it, and this file is
never touched. Our paths, scopes and checks follow; where they specialize the baseline, they win.

## Before editing

- Resolve the requirements bundle as `requirements/` in this repository, with its
  documents under `requirements/tiers/`.
- Read `requirements/config.yml` and every schema under
  `requirements/tiers/_schema/` before changing requirement documents.
- Use the configured scopes: `core`, `okfkb`, and `okfreq`.

## While editing

- Store requirements under `requirements/tiers/strs/<scope>/` and
  `requirements/tiers/swrs/<scope>/`, named like `SwRS-OKFSCHEMA-OKFREQ-002.md`.
- This project uses `linked-swrs-and-validation-test`: add a direct StRS marker
  only to a real stakeholder validation test.
- Keep core `okf-schema`, knowledge-base `okfkb`, and requirements `okfreq`
  concerns in their configured scopes rather than combining unrelated claims.

## After editing

Run the following from the repository root:

```console
okfreq update-coverage requirements
okfreq validate requirements --prose --check-links --project-root .
okfreq lint requirements --prose --check-links --project-root .
okfreq trace requirements --json
```

Then run the complete project quality gate:

```console
just preflight
```

Do not claim complete traceability when a non-exempt leaf requirement lacks
source or test markers, when markers reference unknown IDs, or when
validation/tests fail.

## Exercise the project contract

- Keep the three supported generated fields enabled and refresh them through
  `okfreq update-coverage`; `--check` must fail when they are stale.
- Keep the strict StRS coverage mode and direct validation-test evidence current.
- Maintain authored `documentation_files`, `agent_skill_files`, `example_files`,
  dependencies and verification criteria as actual existing project evidence.
- Review `docs/source/explanation/project-feature-coverage.md` for feature usage.
  Use the disposable showcase for conflicting policies, external demo metadata,
  lifecycle operations and exemptions rather than inventing live project states.
- Follow the registered product maintenance guideline for every behavior change.

## Navigation and history in this repository

- Preserve the authored overview at `requirements/index.md`.
- Run `okfreq lint requirements` to regenerate marked navigation blocks in
  `requirements/tiers/index.md`, tier folders and all scope folders, including
  `requirements/tiers/swrs/okfreq/index.md`.
- Append substantive requirement changes, affected IDs/links, rationale and
  verification results to `requirements/tiers/log.md`. Preserve earlier entries.
- CI runs `okfreq lint requirements --check --check-links --project-root .`;
  do not hand-maintain generated lists or treat the log as generated content.
