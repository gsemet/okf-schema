# Requirements report

Generated: 2026-09-01T00:00:00+00:00

## Summary

- Requirements: 3 (2 coverage targets)
- SwRS source coverage: 100.0% (2/2)
- SwRS test-link coverage: 100.0% (2/2)
- StRS test coverage: 100.0% (1/1)
- StRS paths: tested 1/1, accepted 1/1
- Combined traceability: 100.0% (2/2)

## By scope

| Scope | Requirements | Source | Tests | Combined |
| --- | ---: | ---: | ---: | ---: |
| Core | 2 | 100.0% | 100.0% | 100.0% |

## By stakeholder requirement

| Scope | Tier | ID | Name | Tests | Tested | Accepted |
| --- | --- | --- | --- | --- | --- | --- |
| Core | StRS | StRS-CORE-001 | Export a report | ✅ covered | ✅ 1/1 | ✅ 1/1 |

*Note: current configuration is that an StRS is considered as covered when it is linked to at least one SwRS, every linked SwRS is test-covered (one test per declared transition), and every declared main path has an acceptance test (@accepts_req) (when it declares no paths, at least one @accepts_req names the StRS). Paths with a test marker are reported as tested.*

## By software requirement

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| Core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | — |
| Core | SwRS | SwRS-CORE-002 | Format Rust CSV rows | ✅ covered | ✅ covered | — |
