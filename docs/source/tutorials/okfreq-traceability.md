# Add requirements traceability to an existing project

`okfreq` stores requirements as Markdown files with structured metadata. It
connects a stakeholder outcome to software behavior, then to implementation and
test files. Its commands validate the documents, discover declared links and
produce navigation indexes and reports.

This tutorial starts with a working CSV exporter and adds requirements around
it. You will backfill one existing feature, configure a coding agent, add checks
to the project harness and maintain the links through a subsequent change. You
can follow the complete workflow manually; a coding agent is optional.

## Decide what the requirements layer is for

Use the layer when your team needs to answer questions such as:

- What behavior have we agreed to support, and why?
- Which implementation and tests should we inspect when that behavior changes?
- Which agreed behaviors have no declared implementation or test evidence?

A requirement states expected behavior. An issue tracks work; an implementation
note explains a design choice; a test checks particular cases. They can refer to
one another, but serve different purposes. Keep requirements for behavior you
intend to maintain, not for every helper function or completed task.

The cost is maintaining the statements and links when the project changes.
Start with one bounded feature whose behavior can be reviewed. An existing
implementation is evidence of current behavior, not proof that every behavior
is wanted. Record uncertainties rather than turning incidental details or known
bugs into requirements.

`okfreq` checks document structure and declared file links. It does not run tests,
interpret their results, approve requirements or establish compliance with an
engineering standard. A linked test can still fail or exercise the wrong thing.
You will run the actual tests separately throughout this tutorial.

## Prepare a small existing feature

You need Python 3.10+, `uv` and a text editor. The harness example uses `just`;
you can use equivalent Make targets, package scripts or CI steps. Run commands
from the project root. If you are following in a real repository, work on a
branch and preserve its existing dependency management and test conventions.

For an isolated walkthrough, create a directory and install the development tools:

```bash
mkdir okfreq-demo
cd okfreq-demo
uv init --bare
uv add --dev okf-schema pytest
```

Use the package release matching this documentation. This walkthrough requires
`okfreq lint --check` and generated requirement indexes. When reading unreleased
documentation, replace the registry installation of `okf-schema` with the source
checkout you are evaluating, for example `uv add --dev /path/to/okf-schema`.
The [installation guide](../installation.md) covers other environments.

Create the following files. The empty `src/__init__.py` makes the demo source
importable; a real project should keep its own package layout.

```{code-block} python
:caption: src/__init__.py

```

```{code-block} python
:caption: src/export.py

import csv
import io


def export_rows(rows: list[list[str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()
```

```{code-block} python
:caption: tests/test_export.py

from src.export import export_rows


def test_export_rows() -> None:
    assert export_rows([["name", "value"], ["Ada", "1"]]) == "name,value\nAda,1\n"


def test_export_quotes_commas_and_quotes() -> None:
    assert export_rows([["Ada", "uses, commas", 'says "yes"']]) == (
        'Ada,"uses, commas","says ""yes"""\n'
    )
```

```{code-block} bash
:caption: Run the existing tests

uv run python -m pytest tests -q
```

Both tests should pass before adding requirements. The exporter returns a
Python string, not an encoded file; this tutorial makes no UTF-8 file-writing
claim. The CSV writer handles quoting and fixes the record terminator to `\n`.

## Initialize and configure the requirements bundle

Choose a visible, explicit bundle location for this walkthrough:

```{code-block} bash
:caption: Initialize requirements

uv run okfreq init requirements
```

The bundle contains:

```text
requirements/
├── config.yml
├── guidelines/requirements.guidelines.md
└── tiers/
    ├── _schema/
    ├── strs/
    ├── swrs/
    ├── index.md
    └── log.md
```

Read the installed guideline and the schemas under `tiers/_schema/` before
editing requirements. The guideline describes authored content, generated
fields, navigation and change-history duties. Existing project guidance takes
precedence over generic skill examples.

In `requirements/config.yml`, check this scope mapping:

```yaml
scopes:
  default: {source_dirs: [src], test_dirs: [tests]}
```

These paths are relative to the project root, not to `requirements/`. The
defaults match our files. In an existing project, change them to its actual
locations before scanning. Each scope can list directories or individual files;
keep source and test locations distinct.

The default stakeholder coverage policy is `strs_test_coverage_mode: linked-swrs`.
Keep it for the main walkthrough. We will discuss the stricter option later.

## Backfill a reviewed stakeholder outcome and software behavior

The demo project's agreed outcome is that users can obtain portable tabular
reports for offline review. The existing exporter is one way to support it.
For a real project, confirm the outcome with its owner or existing agreed
specification before recording it as expected behavior.

`okfreq` starts with two requirement levels:

- **StRS — stakeholder requirements specification:** the outcome and user need.
- **SwRS — software requirements specification:** observable software behavior
  derived from that outcome, with scenarios and verification notes.

One StRS can lead to several SwRS. Their relationship records why each software
behavior exists without placing implementation details in the stakeholder need.

```{image} ../_static/okfreq-layered-requirements.svg
:alt: A stakeholder outcome for portable offline reports is refined into CSV output and boundary behavior requirements
:width: 100%
```

If using an agent for backfilling, start with a proposal rather than an instruction
to document everything it finds:

> Use the installed `okfreq` skill to inspect the export documentation,
> `src/export.py` and `tests/test_export.py`. Propose a draft stakeholder outcome
> and bounded software requirements. Identify supporting source/test evidence,
> assumptions and disagreements between the documents and implementation. Do not
> change code, create requirements or claim approval until the proposed intent
> has been reviewed.

Once the proposed intent is accepted for drafting, create the two documents:

```{code-block} bash
:caption: Create the draft requirements

uv run okfreq new strs "Export portable reports" --path requirements \
  --description "The reporting capability SHALL provide portable tabular reports." \
  --user-need "Users need to review tabular reports offline." --project demo
uv run okfreq new swrs "Serialize selected rows as CSV" --path requirements \
  --description "When selected string rows are exported, the service SHALL return CSV text that quotes fields containing commas or double quotes and ends each record with a newline." \
  --project demo --derives-from StRS-default-001
```

The commands print the created file paths. In this empty bundle the IDs are
`StRS-default-001` and `SwRS-default-001`. If using an existing bundle, use the
actual allocated IDs in every later command and marker. IDs and UUIDs remain
stable when wording changes; do not renumber them to rearrange files.

The statements use EARS-style wording: a condition or trigger, followed by one
observable `SHALL` response. The generated headings repeat the frontmatter titles.
Creation leaves both requirements in `draft`; writing `SHALL` is not approval.

Complete **both** generated bodies. Preserve their generated frontmatter and
replace the Markdown below it with these reviewed examples:

```{code-block} markdown
:caption: requirements/tiers/strs/StRS-default-001.md — body

## Export portable reports

### Normative behavior

The reporting capability SHALL provide portable tabular reports.

## User Need

Users need to review tabular reports offline.

### Rationale and constraints

The report must be readable outside the running application. This stakeholder
outcome does not prescribe a file encoding, filename or implementation language.
```

```{code-block} markdown
:caption: requirements/tiers/swrs/SwRS-default-001.md — body

## Serialize selected rows as CSV

### Normative behavior

When selected string rows are exported, the service SHALL return CSV text that
quotes fields containing commas or double quotes and ends each record with a newline.

### Scenario: Export selected rows

- GIVEN two selected rows of string fields
- WHEN export_rows serializes them
- THEN their field values and ordering are preserved in newline-terminated CSV

### Scenario: Preserve CSV delimiters within a field

- GIVEN a field containing a comma or a double quote
- WHEN export_rows serializes the row
- THEN the field is quoted and embedded quotes are doubled

### Verification notes

- Method: automated tests in tests/test_export.py.
- Criteria: exact output matches the nominal and quoted-field examples.
```

`derives_from` on the SwRS is authored. `derived_by` on its parent is computed
by `update-coverage`; do not fill it manually. Metadata excerpts in the
[frontmatter reference](../reference/okfreq-frontmatter.md) explain the other
fields. Remove every scaffold placeholder or record it as an unresolved gap:
`--prose` findings are advisory and do not by themselves fail validation.

## Link the existing source and tests

Add one implementation marker immediately above `export_rows`:

```{code-block} python
:caption: Implementation marker for src/export.py

# @implements_req SwRS-default-001
```

Add one test marker above the first relevant test in `tests/test_export.py`:

```{code-block} python
:caption: Test marker for tests/test_export.py

# @tests_req SwRS-default-001
```

Several test cases in one file can address the same requirement. Put a marker
beside each test that checks it; the file is listed once in the coverage fields.
One requirement can also link to several files, and one file can address several
requirements. Place markers in comments appropriate for the source language.

This step connects existing evidence; it does not require rewriting working
code. The links help a reviewer find the relevant files when the requirement
changes. The reviewer still needs to check whether those files address the
statement adequately.

```{code-block} bash
:caption: Inspect and refresh declared links

uv run okfreq scope requirements
uv run okfreq trace requirements --json
uv run okfreq update-coverage requirements --diff
```

`trace` should find `SwRS-default-001` under both `implemented` and `tested`,
with no unknown IDs. Review the diff, then apply and validate it:

```{code-block} bash
:caption: Apply generated metadata and navigation

uv run okfreq update-coverage requirements
uv run okfreq lint requirements --prose --check-links --project-root .
uv run python -m pytest tests -q
```

The SwRS now has generated `implemented_in_files: [src/export.py]` and
`tested_in_files: [tests/test_export.py]`. Its StRS has the reverse
`derived_by` relationship. `--check-links` checks annotated file targets;
`--project-root .` makes the project-relative source/test paths explicit.

Lint validates first and updates navigation blocks in `tiers/index.md` and each
requirement directory. Read those indexes to navigate from the stakeholder
outcome to its software behavior. Preserve text outside the generated markers.
An optional `requirements/index.md` is your authored overview.

```{image} ../_static/okfreq-authored-generated.svg
:alt: Authors maintain requirement intent, relationships and the change log; okfreq computes reverse links, evidence paths, navigation blocks and reports; the test runner produces execution results separately
:width: 100%
```

Append a dated entry to `requirements/tiers/log.md` recording the two IDs, the
existing source/test evidence, the review assumptions and the test command you
actually ran. Preserve earlier entries. Logs are authored history, not generator
output. Do not record approval or stakeholder review that has not happened.

## Make the workflow part of the project harness

Install the requirements skill family into a directory your coding agent reads.
For an agent configured to discover `.agents/skills/`:

```{code-block} bash
:caption: Install project agent skills

uv run okfreq install-skills --local-agents
```

For GitHub Copilot project skills, use `--local-copilot` instead. Both install
`okfreq`, `okfreq-setup` and `okfreq-gardening`. Use `okfreq` for ongoing
requirement work; use `okfreq-setup` once, to create a baseline in a project
without a bundle; use gardening for an explicitly requested drift audit. Skill instructions guide
the agent but do not establish correctness or approval.

Add the following to the project's existing `AGENTS.md` or equivalent persistent
instructions, adapting paths to the chosen bundle:

```{code-block} markdown
:caption: AGENTS.md — requirements workflow

## Requirements

Before changing expected behavior, read
requirements/guidelines/requirements.guidelines.md, requirements/config.yml,
the relevant schemas and affected requirements.

Use the installed okfreq skill for requirement work. For existing features,
inspect source, tests and agreed documentation before proposing requirements;
report uncertainties instead of inventing stakeholder intent.

Keep the first Markdown heading equal to the frontmatter title. Preserve IDs,
UUIDs, authored intent and lifecycle values. Add markers near real implementation
and tests. Preview generated metadata, then refresh coverage and navigation.
Record substantive changes, rationale and real verification in
requirements/tiers/log.md.

Run the project tests and requirements checks. Report missing evidence and
unresolved assumptions; marker coverage is not proof of successful verification.
```

Add targets to the project's task runner. These `justfile` recipes assume the
`uv` development environment created earlier:

```{code-block} make
:caption: justfile

test:
    uv run python -m pytest tests -q

requirements-preview:
    uv run okfreq update-coverage requirements --diff
    uv run okfreq lint requirements --diff --prose --check-links --project-root .

requirements-refresh:
    uv run okfreq update-coverage requirements
    uv run okfreq lint requirements --prose --check-links --project-root .

requirements-check:
    uv run okfreq lint requirements --check --prose --check-links --project-root .
    uv run okfreq update-coverage requirements --check

requirements-report:
    uv run okfreq generate-report requirements --output-json dist/requirements-report.json --output-summary-md dist/requirements-report.md

preflight: test requirements-check
```

Merge these into existing targets rather than replacing the project's other
checks. `requirements-preview` writes nothing. Refresh updates generated fields
and indexes; check mode fails if they are missing or stale. Prose warnings remain
advisory. `validate` checks structure without generating navigation.

Run the combined check locally:

```{code-block} bash
:caption: Run project preflight

just preflight
```

In CI, install the locked development dependencies
with `uv sync --locked --group dev`, then run `just preflight` or its equivalent
commands. Install `uv`, Python and `just` through the project's usual CI setup.
Commit the dependency declaration and lockfile so local checks and CI use the
same resolved package versions.

These targets check structural validity, annotated file targets, navigation and
metadata freshness, plus actual tests. They do **not** require every project
feature to have a requirement, or every requirement to have implementation/test
markers. Inspect reports for those gaps; define an additional explicit policy
if missing links must block delivery. Do not infer complete feature coverage
from a successful preflight.

## Maintain the layer through a subsequent change

Suppose the team now decides to make the empty-export behavior an explicit
contract: exporting zero rows returns an empty string. The current implementation
already does this; a new test and requirement will preserve the decision. No
implementation change is necessary just to create activity.

```{code-block} bash
:caption: Record the empty-export behavior

uv run okfreq new swrs "Export an empty selection" --path requirements \
  --description "When no rows are selected, the service SHALL return an empty CSV string." \
  --project demo --derives-from StRS-default-001
```

For this walkthrough the new ID is `SwRS-default-002`. Preserve its generated
frontmatter and complete its body:

```{code-block} markdown
:caption: requirements/tiers/swrs/SwRS-default-002.md — body

## Export an empty selection

### Normative behavior

When no rows are selected, the service SHALL return an empty CSV string.

### Scenario: Export no rows

- GIVEN an empty list of selected rows
- WHEN export_rows is called
- THEN it returns the empty string without raising an exception

### Scenario: Preserve the non-empty export behavior

- GIVEN a row containing a field with a comma
- WHEN export_rows is called
- THEN it still returns correctly quoted, newline-terminated CSV

### Verification notes

- Method: automated tests in tests/test_export.py.
- Criteria: an empty selection returns exactly an empty string and the existing
  populated/quoted-field tests continue to pass.
```

Add this beside the existing implementation marker:

```{code-block} python
:caption: Second implementation marker for src/export.py

# @implements_req SwRS-default-002
```

Append this test, with its own marker, to the existing test file:

```{code-block} python
:caption: tests/test_export.py — append

# @tests_req SwRS-default-002
def test_export_empty_selection() -> None:
    assert export_rows([]) == ""
```

```{image} ../_static/okfreq-change-workflow.svg
:alt: Inspect evidence, review expected behavior, update requirements and relevant code/tests, then run tests and refresh links before read-only checks and report review
:width: 100%
```

With an agent, use a bounded maintenance request:

> Use the installed `okfreq` skill to add the reviewed empty-export contract.
> Preserve the existing export requirement, ID and UUID. Add the second source
> marker and the focused test, complete the new requirement body, run the tests,
> preview generated changes and refresh coverage/navigation. Record the change
> and actual results in the log. Report remaining gaps and keep lifecycle values
> unchanged.

Preview the proposed changes, then refresh and check:

```{code-block} bash
:caption: Refresh and check the second requirement

just requirements-preview
just requirements-refresh
just preflight
```

The same source/test files
will now link to two SwRS, and their common StRS will list both reverse links.
Review the wording, markers and test results; do not limit review to percentages.
Append the change and its rationale to the authored log.

## Generate reports and investigate gaps

Write reports to explicit project paths:

```{code-block} bash
:caption: Generate traceability reports

uv run okfreq generate-report requirements \
  --output-json dist/requirements-report.json \
  --output-summary-md dist/requirements-report.md
```

This produces JSON, a sibling `requirements-report.schema.json` and a Markdown
summary. The report separates source linkage, test linkage and stakeholder
coverage. With the default policy, an StRS is covered when it has at least one
linked SwRS and every linked SwRS has a test marker. StRS source coverage is not
applicable. `execution_evidence.status: not_collected` means `okfreq` has not
collected test-run results, even though you ran pytest separately.
Keep reports as generated review/CI artifacts and regenerate them rather than
editing them. Choose whether to version or publish them according to the
project's existing artifact policy.

| Finding | What to inspect |
|---|---|
| No discovered marker | Use `scope` to check scan paths, then check the exact ID and marker spelling. |
| Unknown ID | Correct the marker or create the reviewed missing requirement; do not invent a link just to remove the finding. |
| Missing source/test coverage | Find real evidence, implement the missing behavior/test, or leave the gap explicit for review. Structural validity alone does not resolve it. |
| Stale generated fields/indexes | Preview, refresh and rerun check mode. `--check` exits non-zero on drift; `--diff` previews without writing. |
| E10 | Fix a missing/ambiguous target, malformed annotation or disallowed root escape. |
| W15 | Supply the correct root or restore filesystem access. The check was skipped, not verified. |
| Prose warning | Complete the draft's scenarios or rationale; warnings do not by themselves fail validation. |

If the project needs a direct stakeholder validation-test definition, select
`strs_test_coverage_mode: linked-swrs-and-validation-test` and put a test marker
on the StRS ID in a real stakeholder-level test. This adds a defined validation
link; it still does not establish test execution or approval. Keep the default
unless this additional policy fits the project's review process.

## Further reading

- [Configuration](../reference/okfreq-configuration.md): scopes, ID allocation,
  generated-field ownership and stakeholder coverage policies.
- [Frontmatter](../reference/okfreq-frontmatter.md): complete document metadata,
  authored relationships and generated source/test links.
- [CLI reference](../reference/okfreq-cli.md): command options and failure behavior.
- [Coverage boundaries](../explanation/okfreq-coverage-boundaries.md): what file
  linkage establishes and what executed-test evidence would require.
- [Build a requirement base](../how-to/okfreq-build-requirement-base.md): a shorter
  procedural path for applying the workflow to another repository.
- [Design choices](../explanation/okfreq-choices.md): why requirements are separate
  from the knowledge base and how the storage model is organized.
- [Project feature/evidence map](../explanation/project-feature-coverage.md):
  concrete examples and how this repository maintains its own requirements.
