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
- This project uses `linked-swrs-and-acceptance-paths`: every StRS declares its
  main paths in `scenarios:` and every SwRS its transition scenarios, and each
  test marker names the scenario it really exercises with `#S<n>`. A StRS path's
  acceptance test carries `@accepts_req`; a cheaper test of the same path carries
  `@tests_req`. Never add a fragmentless test marker to a requirement that
  declares `scenarios:`.
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

- Keep the supported generated fields enabled and refresh them through
  `okfreq update-coverage`; `--check` must fail when they are stale. On a StRS
  that now includes `tested_in_files` and `accepted_in_files`.
- Keep the acceptance-paths StRS coverage mode current: every main path of every
  live StRS either has a counting `@accepts_req` marker or the StRS carries a
  justified `acceptance_exemption` with a non-blank reason, and no finding
  reports a missing or undeclared fragment.
- This repository's acceptance tests (`@accepts_req`) run the product as a user
  gets it. Each one builds the wheel (`uv build --offline --wheel`), installs it
  in an isolated environment and exercises the installed console scripts
  (`okf-schema`, `okfkb`, `okfreq`) in subprocesses in a fresh temporary project,
  with no source checkout on `PYTHONPATH`. The navigation path is the exception:
  it calls the installed wheel's Python API in an isolated subprocess and asserts
  the returned file-link targets, without importing the checkout or inventing a
  navigation CLI. They live in `tests/test_acceptance_core.py`,
  `tests/test_acceptance_okfkb.py` and `tests/test_acceptance_okfreq.py`, share
  the wheel and environment through the `installed_distribution` fixture, and
  skip on Windows. The in-process tests (`CliRunner`, API calls, `runpy`) that
  walk a path keep `@tests_req`: an acceptance marker belongs only on a test that
  exercises the installed product.
- `StRS-OKFSCHEMA-OKFKB-001` carries the one justified whole-StRS acceptance
  waiver (interactive consolidation for human review), and
  `SwRS-OKFSCHEMA-OKFKB-005` carries the one SwRS annotation exemption. Do not
  copy either to hide a test that can be written.
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
