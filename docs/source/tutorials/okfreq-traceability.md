# Create Your First Traceable Requirement with OKFREQ

OKFREQ stores each requirement as a Markdown document and connects software
requirements to implementation and test files. In this tutorial, you will
create a small export requirement and inspect its traceability.

**Time:** about 15 minutes

**Prerequisite:** Follow the [installation guide](../installation.md) to install
`okf-schema` and manually add the `okfreq` skill to a small project where you
can add a source file and a test file.

## Understand the two requirement levels

A useful requirement states observable behavior and how the team can decide
whether that behavior is present. “The export should be fast” is a wish. “When
exporting 10,000 rows, the service shall finish within two seconds on the CI
benchmark machine” is measurable.

OKFREQ starts with two levels:

- **StRS** describes a stakeholder outcome in language the stakeholder can
  validate.
- **SwRS** refines that outcome into behavior software can implement and a test
  can observe.

One StRS can lead to several SwRS requirements. This tutorial creates one of
each.

```{image} ../_static/okfreq-layered-requirements.svg
:alt: A stakeholder requirement is refined into a software requirement, which is then linked to implementation and test evidence
:width: 100%
```

The two levels serve different conversations. A product owner can review the
StRS without having to approve technical details. Developers and testers can
then split that outcome into precise SwRS behaviors without changing the
original user need. The derivation link preserves why each software behavior
exists and makes change impact visible in both directions.

## Initialize OKFREQ

From the project root, run:

```bash
okfreq init .
```

This creates `.agents/requirements/` with configuration, schemas, agent
guidance, and folders for the two requirement levels:

```text
.agents/requirements/
├── config.yml
├── guidelines/
└── tiers/
    ├── _schema/
    ├── strs/
    ├── swrs/
    ├── index.md
    └── log.md
```

Open `config.yml` and confirm that the default scope scans the source and test
directories used by your project.

## Create the stakeholder requirement

```bash
okfreq new strs "Export report" \
    --description "When export is requested, the reporting capability SHALL make a portable report available." \
    --user-need "Users need a portable report for offline review." \
    --project demo
```

The command prints the generated ID, such as `StRS-default-001`. Keep the ID
shown on your machine for the next command.

## Derive software behavior

Create a software requirement linked to the stakeholder requirement:

```bash
okfreq new swrs "Write CSV" \
    --description "When export is requested, the service SHALL write selected rows as UTF-8 CSV." \
    --project demo \
    --derives-from StRS-default-001
```

Open the generated SwRS document. Replace its scenario placeholders and add
objective verification notes. You are turning a broad outcome, “make a portable
report available,” into one behavior that code can implement and a test can
observe: “write selected rows as UTF-8 CSV.” Other SwRS requirements could later
cover filtering, filenames, or error handling while still referring to the same
stakeholder outcome.

The SwRS authors the relationship to its parent:

```yaml
type: SwRS
id: SwRS-default-001
title: Write CSV
derives_from: [StRS-default-001]
```

OKFREQ computes the reverse relationship on the StRS:

```yaml
type: StRS
id: StRS-default-001
title: Export report
derived_by: [SwRS-default-001]
```

This is one relationship shown from both documents. Author `derives_from` on
the more specific requirement; do not edit `derived_by` by hand. The reverse
field lets a product owner start from a changed stakeholder need and discover
every software behavior that may need review.

These authoring steps require judgment. Instead of filling the documents by
hand, tell your coding agent:

> Use the `okfreq` skill to review `StRS-default-001` and
> `SwRS-default-001`. Preserve the stakeholder need, replace every generated
> scenario placeholder with observable CSV behavior, add objective verification
> notes, and validate the requirements. Do not mark either requirement as
> approved.

Use the actual IDs printed by your commands. The skill keeps stakeholder intent
separate from software behavior and avoids claiming approval or test evidence
that has not occurred.

## Connect code and tests

Ask the coding agent to implement and test the SwRS in one request:

> Use the `okfreq` skill to implement `SwRS-default-001` in the existing export
> module and add focused tests. Add `@implements_req SwRS-default-001` once in
> the implementation file and `@tests_req SwRS-default-001` once in the test
> file. Run the project tests, refresh requirement coverage, and validate the
> requirements. Do not change requirement lifecycle values.

The agent changes code and tests using the project's normal engineering rules.
The skill adds traceability markers and checks, but the real test suite still
decides whether the implementation works.

If you are editing manually, add the software requirement ID once in the
relevant implementation file:

```python
# @implements_req SwRS-default-001
def export_rows(rows: list[list[str]]) -> str:
    return "\n".join(",".join(row) for row in rows)
```

Add the same ID once in the relevant test file:

```python
# @tests_req SwRS-default-001
def test_export_rows() -> None:
    assert export_rows([["a", "b"]]) == "a,b"
```

Use the actual SwRS ID printed by your command. An implementation marker says
where behavior is implemented. A test marker says where it is checked. Neither
marker proves that the implementation is correct or that the test passed.

Run your project's test suite separately.

## Inspect traceability

Scan configured source and test directories:

```bash
okfreq trace .
```

Preview the generated coverage fields:

```bash
okfreq update-coverage . --check
okfreq update-coverage . --diff
```

When the diff is correct, apply it:

```bash
okfreq update-coverage .
```

Finally, validate the requirement structure and prose:

```bash
okfreq validate . --prose
```

You now have a stakeholder outcome, a derived software behavior, and explicit
links from that behavior to implementation and test files.

## If markers are not found

Run `okfreq scope .` and compare its configured directories with the location
of your source and test files. Then check that the marker uses the exact SwRS
ID, including capitalization and hyphens. Mark leaf software requirements, not
only the parent stakeholder requirement.

## Next steps

- [Build a Requirement Base](../how-to/okfreq-build-requirement-base.md) covers
  project configuration, reports, lifecycle commands, and agent collaboration.
- [Why OKFREQ Is Separate](../explanation/okfreq-choices.md) explains layered
  requirements, storage choices, and comparisons with other tools.
- [OKFREQ CLI Reference](../reference/okfreq-cli.md) lists all commands.
- [OKFREQ Frontmatter Reference](../reference/okfreq-frontmatter.md) documents
  authored and generated fields.
