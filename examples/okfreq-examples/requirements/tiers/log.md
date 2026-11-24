# Update Log

## 2026-11-24

- Moved the example to `strs_test_coverage_mode: linked-swrs-and-acceptance-paths`.
  `StRS-CORE-001` declares its main path `S1`; both SwRS declare `scenarios:` with
  matching `### Scenario S<n>:` headings; the tests carry `#S<n>` fragments.
  `tests/test_acceptance_export.py` is the real acceptance test of `S1` (the export run
  as a separate process); its slow variant is commented out and is not evidence.
  `test_export_rows` also carries `@tests_req StRS-CORE-001#S1`.

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
