# Build a requirement base

```{admonition} Want to understand the why first?
:class: tip

Read the full [Requirements traceability tutorial](../tutorials/okfreq-traceability.md)
to learn what requirements are, why traceability is useful, and how the `StRS`
and `SwRS` layers connect implementation to test evidence. This page is the
short, procedural setup path.
```

This guide sets up a small, agent-friendly requirements base. The examples use
an export feature: the stakeholder describes the user outcome, the software
requirement describes observable behavior, and source and test markers connect
that behavior to evidence.

1. Install `okf-schema` in the project environment.
   Install it in the same development environment used by local checks so the
   command is also available in CI.
2. Initialize the requirements bundle with `okfreq init .`.
   This creates `.agents/requirements/` with `config.yml` at its root, a
   `guidelines/` folder holding the installed `requirements.guidelines.md`, and
   a `tiers/` folder holding the schema, the `strs/` and `swrs/` folders, an
   index, and a log. Existing files are never overwritten.
3. Review `.agents/requirements/config.yml` (or `requirements/config.yml` for
   this repository).
   Add scopes for each independently scanned part of the project and adjust
   `source_dirs` and `test_dirs` before scanning. Keep these mappings scoped:
   implementation and test evidence can belong to different directories.
4. Create a stakeholder requirement:
   `okfreq new strs "Export report" --description "When report export is requested, the reporting capability SHALL make a portable report available." --user-need "Users need a portable report for offline review." --project demo`.
   This creates a draft `StRS` with a generated UUID and stable ID such as
   `StRS-default-001`. Its body separates normative stakeholder-observable
   behavior, the preserved user need, and rationale/constraints. It does not
   contain software scenarios or verification notes.
5. Create a software requirement with its parent:
   `okfreq new swrs "Write CSV" --description "When export is requested, the service SHALL write the selected rows as UTF-8 CSV." --project demo --derives-from StRS-default-001`.
   Native `SwRS` documents must derive from at least one `StRS`. Keep the
   `derives_from` relationship authored; reverse `derived_by` links are computed.
   Fill both generated GIVEN-WHEN-THEN scenarios and the verification notes.
   SwRS documents do not contain a stakeholder `user_need` section.
6. Ask your coding agent to implement the software requirement and add tests.
   Explicitly name the requirement ID and ask the agent to add
   `@implements_req SwRS-default-001` in the implementation and
   `@tests_req SwRS-default-001` in the corresponding test file. Use one marker
   per requirement ID per file, even when that file contains several relevant
   test cases. The markers make the links discoverable without claiming that
   the tests passed.
7. Run `okfreq trace .` to inspect marker references and missing IDs, then run
   `okfreq update-coverage . --check` to preview generated coverage fields.
   Use `--diff` to review the exact changes; only run without a preview flag
   when you intend to update `implemented_in_files` and `tested_in_files`.
8. Run `okfreq validate . --prose` before committing. Structural failures make
   the command fail; advisory prose findings expose unfinished template gaps.
   Use the [`okfreq` CLI reference](../reference/okfreq-cli.md) and the
   [tutorial](../tutorials/okfreq-traceability.md)
   for the concepts behind the workflow.

In CI, run `okfreq validate .` as a required job after the environment is
installed. Keep generated indexes and coverage updates explicit; preview
generated changes before applying them. A typical CI job is equivalent to:

```console
$ okfreq validate . --prose
2 requirements, 0 errors
```

The command exits non-zero for missing required metadata, invalid UUIDs,
unknown derivation targets, invalid lifecycle values, or invalid configured
levels. It does not turn a marker into a claim that the implementation or test
is correct: run the normal project test suite as well.

See the [design explanation](../explanation/okfreq-choices.md) and the
[`okfreq` CLI reference](../reference/okfreq-cli.md) for rationale and commands.

For this repository, the maintained requirements bundle is `requirements/`: its
configuration is `requirements/config.yml`, its documents are under
`requirements/tiers/`, and its requirements-specific guidance is in
`requirements/guidelines/requirements.guidelines.md`.

For an existing or brownfield requirements base, use the `okfreq-gardening`
skill from the repository's `skills/okfreq-gardening/SKILL.md` package to audit
gaps and configuration drift while preserving authored requirement content.
