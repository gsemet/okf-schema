# Update Log

## 2026-11-24

- The example runs in mode `linked-swrs-and-acceptance-paths`. `StRS-CORE-001`
  declares its main path `S1` and both SwRS declare their transitions `S1`/`S2`;
  each test marker names one with a `#S<n>` fragment.
  `tests/test_acceptance_export.py` accepts `StRS-CORE-001#S1` by running
  `src/export.py` in a separate process.

## 2026-10-30

- The lifecycle field is `req_lifecycle`; regenerated requirements carry the OKF
  `status` and a generated Links section declared by the scaffold schema.

## 2026-10-19

- Aligned each requirement body heading with its frontmatter title; future
  regenerations use the updated authoring template.
- Added generated tier indexes to the CSV example workflow; authored history
  is preserved when fixture schemas and requirement documents are refreshed.
  Python CSV tests cover populated and empty inputs. Rust markers demonstrate
  linkage only; the refresh command does not execute a Rust test runner.
