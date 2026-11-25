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

| Scope | Tier | ID | Name | Tested | Accepted | Tests |
| --- | --- | --- | --- | --- | --- | --- |
| Core | StRS | StRS-CORE-001 | Export a report | 1/1 ✅ | 1/1 ✅ | ✅ covered |

*Note: current configuration is that an StRS is considered as covered when it is linked to at least one SwRS, every linked SwRS is test-covered or individually exempted with a non-blank exemption_reason, and either every declared main path has an acceptance test marker (or at least one fragmentless acceptance test marker when no paths are declared) or the whole StRS carries a justified acceptance_exemption; tested paths are reported separately.*

## By software requirement

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| Core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | — |
| Core | SwRS | SwRS-CORE-002 | Format Rust CSV rows | ✅ covered | ✅ covered | — |
