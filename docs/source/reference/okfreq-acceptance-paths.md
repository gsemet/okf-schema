# Acceptance paths and scenario markers

## Verbs and modes

| Marker | Meaning | Cost recommendation |
| --- | --- | --- |
| `@tests_req` | A SwRS transition or StRS main-path test | Prefer a cheap pull/merge-request test |
| `@accepts_req` | Acceptance of a StRS path | Prefer the test closest to the final product, even if it runs on the main branch |

The recommendation is not enforced.

| Mode | SwRS | StRS |
| --- | --- | --- |
| `linked-swrs` | Any `@tests_req` link covers it | Linked SwRS rule only |
| `linked-swrs-and-validation-test` | Any `@tests_req` link covers it | Linked SwRS plus a direct `@tests_req` StRS validation link |
| `linked-swrs-and-acceptance-paths` | Every declared transition needs its fragment | Linked SwRS plus complete acceptance, or a justified whole-StRS waiver |

Outside the new mode `@accepts_req` is scanned by `trace`, but counts toward no
coverage. Suffixes on any marker retain the old ignored-suffix behavior.

## Marker combinations

`@implements_req` retains its existing SwRS source behavior and never reads a
fragment. In the new mode:

| Target | Declared scenarios | Marker | Result |
| --- | --- | --- | --- |
| StRS | yes | `@tests_req ID#S<n>` | Tests that declared path |
| StRS | yes | `@accepts_req ID#S<n>` | Accepts that declared path |
| SwRS | yes | `@tests_req ID#S<n>` | Tests that transition |
| StRS or SwRS | yes | fragmentless `@tests_req` or `@accepts_req` | Error; does not count |
| StRS | no | fragmentless `@tests_req` / `@accepts_req` | Tests / accepts whole StRS |
| SwRS | no | fragmentless `@tests_req` | Covers whole SwRS |
| Any target | either | unknown `#S<n>` | Error |
| StRS or SwRS | none | `#S<n>` | Error |
| SwRS | either | `@accepts_req` | Schema-driven error |
| Other configured tier | either | scenario marker | Existing leaf/parent handling; no new scenario behavior |
| Any | either | suffix `#path1`, `#s1`, `#S1a`, or `#` | Read as fragmentless |

Configure the three keywords under `markers.implements`, `markers.tests`, and
`markers.accepts`. The custom `id_pattern` must not admit `#`. A valid fragment
is glued to the ID and has the form `#S1`, `#S2`, and so on.

## Worked examples

### Independent tested and accepted counters

```{code-block} yaml
:caption: Example 1 frontmatter
type: StRS
id: StRS-EXPORT-001
scenarios:
  - id: S1
    title: Export rows
  - id: S2
    title: Review the export
  - id: S3
    title: Recover an invalid selection
```

```{code-block} python
:caption: Example 1 markers
# @tests_req StRS-EXPORT-001#S1
# @tests_req StRS-EXPORT-001#S2
# @accepts_req StRS-EXPORT-001#S3
```

```{code-block} json
:caption: Example 1 JSON result
{"paths": {"total": 3, "tested": 2, "accepted": 1}, "tested": false, "accepted": false}
```

```{code-block} text
:caption: Example 1 Markdown row
| export | StRS | StRS-EXPORT-001 | Export rows | ❌ missing | ❌ 2/3 | ❌ 1/3 |
```

S3 is accepted but not tested: the counters are independent.

### Missing transition

```{code-block} yaml
:caption: Example 2 frontmatter
type: SwRS
id: SwRS-EXPORT-001
scenarios:
  - {id: S1, title: Export selected rows}
  - {id: S2, title: Export an empty selection}
```

```{code-block} python
:caption: Example 2 marker
# @tests_req SwRS-EXPORT-001#S1
```

```{code-block} json
:caption: Example 2 JSON result
{"transitions": {"tested": ["S1"], "missing": ["S2"]}, "tests": {"status": "missing"}}
```

```{code-block} text
:caption: Example 2 Markdown row
| export | SwRS | SwRS-EXPORT-001 | Export rows | ✅ covered | ❌ missing | S2 |
```

### Fragmentless fallback and both warnings

```{code-block} yaml
:caption: Example 3 frontmatter
type: StRS
id: StRS-EXPORT-002
title: Publish a report
```

```{code-block} python
:caption: Example 3 marker
# @tests_req StRS-EXPORT-002
```

```{code-block} json
:caption: Example 3 JSON result
{"paths": {"total": 0, "tested": 0, "accepted": 0}, "tested": true, "accepted": false}
```

```{code-block} text
:caption: Example 3 Markdown row
| export | StRS | StRS-EXPORT-002 | Publish a report | ❌ missing | ✅ no paths | ❌ no paths |
```

Validation prints `W003` with a pasteable `scenarios:` block and `W004` because
there is no counting acceptance test.

## Findings and repair

- A missing fragment: write `@tests_req ID#S<n>` or `@accepts_req ID#S<n>`;
  invalid markers do not count.
- An unknown fragment: use one of the IDs currently declared by the target.
- Malformed `scenarios:`: use a non-empty list of `{id, title}` mappings with
  unique `S<n>` IDs and non-empty titles.
- `@accepts_req` on a SwRS: replace it with `@tests_req`.
- A pre-0.18 SwRS schema: add the shipped `accepted_in_files` declaration with
  `maxItems: 0`; okfreq does not migrate an existing schema silently.
- `W003`: declare main paths from the headings shown in the message.
- `W004`: add a counting acceptance marker or, when genuinely impossible, a
  justified whole-StRS waiver.

## Whole-StRS acceptance waiver

```yaml
acceptance_exemption: true
acceptance_exemption_reason: Interactive consolidation requires human review and has no deterministic acceptance command.
```

The owner reviews the exemption, and removes it when acceptance becomes
possible. It suppresses `W004`, not `W003`, fragment errors, or linked-SwRS
coverage. It does not change `accepted`, `acceptance_tests`, `paths.accepted`,
or any evidence counter. A SwRS `annotation_exemption` is separate and only
exempts that SwRS's source/test annotations when its own reason is justified.

## Report fields

Per StRS, `stakeholder_test_coverage.paths` reports total/tested/accepted,
alongside `tested`, `accepted`, `tests`, `acceptance_tests`, and
`validation_tests`. In the new mode `validation_tests` equals
`acceptance_tests`; the StRS record's `tests` follows it and therefore lists
`@accepts_req` files. By contrast, `stakeholder_test_coverage.tests` lists
`@tests_req` files, and `okfreq trace --json` keeps its raw `validation_tests`
meaning.

`marker_coverage.tested` is a marker-link count. `totals.tested` is the number of
test-covered SwRS. A SwRS with transitions also exposes
`transitions.tested` and `transitions.missing`. Reports use format version 2.
