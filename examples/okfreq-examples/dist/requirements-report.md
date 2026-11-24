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

*Note: current configuration is that an StRS is considered as covered when it is linked to at least one SwRS, every linked SwRS has at least one test marker (or is individually exempted), and either every declared main path is accepted by an @accepts_req marker (or, when it declares no scenarios:, at least one fragmentless @accepts_req marker exists) or the whole StRS carries a justified acceptance waiver. A separate tested counter reports declared paths covered by an @tests_req marker. When scenarios are declared, every test marker on the requirement must name one with a #S<n> fragment.*

## By software requirement

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| Core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | — |
| Core | SwRS | SwRS-CORE-002 | Format Rust CSV rows | ✅ covered | ✅ covered | — |
