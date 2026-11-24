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
| Core | StRS | StRS-CORE-001 | Export a report | ✅ covered | 1/1 ✅ | 1/1 ✅ |

*Note: current configuration is that an StRS is considered as covered when it is linked to at least one SwRS, every linked SwRS is test-covered (every declared transition has a test marker with its fragment, or at least one test marker when none is declared) or carries its own justified annotation exemption, and the StRS is accepted: every declared main path has an acceptance marker with its fragment, or at least one fragmentless acceptance marker when no path is declared; a justified whole-StRS acceptance waiver replaces acceptance without counting as acceptance. The separate tested counter follows the test markers of the StRS paths and does not change its coverage status.*

## By software requirement

| Scope | Tier | ID | Name | Source | Tests | Missing transitions |
| --- | --- | --- | --- | --- | --- | --- |
| Core | SwRS | SwRS-CORE-001 | Write CSV output | ✅ covered | ✅ covered | — |
| Core | SwRS | SwRS-CORE-002 | Format Rust CSV rows | ✅ covered | ✅ covered | — |
