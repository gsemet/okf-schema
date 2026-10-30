# Update Log

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
