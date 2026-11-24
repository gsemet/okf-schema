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
| --- | --- | --- | --- | --- | ---: | ---: |
| Core | StRS | StRS-CORE-001 | Export a report | ✅ covered | ✅ 1/1 | ✅ 1/1 |

*Note: current configuration is that an StRS is considered covered when it has at least one linked SwRS, every linked SwRS is covered or has a justified annotation exemption, and its declared paths are accepted (or the whole StRS has a justified acceptance waiver). When paths are declared, separate tested and accepted counters use counting scenario fragments; without declared paths, fragmentless tests and acceptance tests cover the whole StRS.*

## By software requirement

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| Core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | — |
| Core | SwRS | SwRS-CORE-002 | Format Rust CSV rows | ✅ covered | ✅ covered | — |
