# `okfreq` CLI reference

`okfreq` creates and maintains the requirements subset. Commands accept either
a project root or a requirements-bundle root; bundle discovery finds
`.agents/requirements/` or `requirements/` where applicable.

```bash
okfreq COMMAND --help
```

## Setup and authoring

| Command | Purpose |
|---|---|
| `okfreq init [PATH] [--force]` | Create or merge the default requirements scaffold. Existing files are not replaced. |
| `okfreq new strs TITLE --description TEXT --project TEXT [--scope NAME] [--origin NAME] [--derives-from ID]... [--user-need TEXT] [--path PATH]` | Create a stakeholder requirement with a stable allocated ID and UUID. |
| `okfreq new swrs TITLE --description TEXT --project TEXT --derives-from ID [--derives-from ID]... [--scope NAME] [--origin NAME] [--path PATH]` | Create a software requirement derived from one or more configured parent requirements. `--user-need` is rejected for derived levels. |
| `okfreq import SOURCE [--path PATH]` | Merge configuration while preserving destination values on conflicts and preserving unknown keys. |
| `okfreq config-merge SOURCE [--path PATH]` | Explicit spelling of the same conflict-preserving configuration merge. |

The configured `id_policy` controls allocation. The current implementation
supports `scope-prefix-sequence`; it never renumbers existing documents.

## Inspect and validate

| Command | Purpose |
|---|---|
| `okfreq validate [PATH] [--json] [--prose] [--check-links] [--project-root DIR]` | Validate metadata, configuration, IDs, hierarchy, exemptions, derivation links, and optionally annotated file targets. Prose and skipped-root findings are advisory. |
| `okfreq lint [PATH] [--prose] [--check-links] [--project-root DIR]` | Run the same read-only structural checks with optional EARS prose and file-link checks. |
| `okfreq index [PATH]` | Print the stable requirement ID index. |
| `okfreq search QUERY [PATH]` | Search IDs, titles, and descriptions. |
| `okfreq in-file FILE` | Print one requirement document. |
| `okfreq scope [PATH]` | Print configured scope-to-source/test mappings as JSON. |
| `okfreq graph [PATH] [--json]` | Show authored `derives_from` and computed `derived_by` relationships; exit non-zero for broken targets. |
| `okfreq trace [PATH] [--json]` | Scan configured source and test locations for markers. |
| `okfreq status [PATH]` | Print lifecycle counts and structural health. |

`trace` separates valid leaf coverage, unknown IDs, repeated markers in one
file, non-leaf markers, and scan warnings. Marker spellings and the ID regular
expression come from `config.yml`.

### Check annotated file targets

`okfreq init` writes `x-okf-link` annotations into the generated requirement
schemas, but checking is deliberately opt-in:

```bash
okfreq validate . --check-links --project-root .
```

The `--project-root` option controls `project-relative` source and test paths.
Without it, the containing Git root of each requirement document is used. The
checker does not use the current working directory or an editor workspace as an
implicit root. Requirement relationships use case-sensitive Markdown filename
stems; source and test evidence uses exact project-relative paths. `E10` reports
malformed annotations, missing exact files, root escapes, and ambiguous stems.
`W15` reports a skipped check when a required root or filename-stem workspace is
unavailable. Warnings do not make `okfreq lint` fail on their own.

## Generated coverage and reports

| Command | Purpose |
|---|---|
| `okfreq update-coverage [PATH] [--check|--diff]` | Recompute only configured generated fields. `--check` lists changed files; `--diff` prints previews; both are read-only. |
| `okfreq generate-report [PATH] [--output-json FILE] [--output-summary-md FILE]` | Generate a detailed JSON report and concise Markdown summary with SwRS source/test-link coverage, configured StRS test coverage, and combined leaf traceability coverage. StRS source coverage is not applicable. |

Without `--output`, report data is printed to standard output. Generated
artifacts should be regenerated rather than edited manually.

## Lifecycle changes

| Command | Purpose |
|---|---|
| `okfreq archive TARGET [--path PATH] --yes` | Set the target lifecycle to `deprecated` without deleting it. |
| `okfreq supersede TARGET REPLACEMENT [--path PATH] --yes` | Set the target to `superseded` and record `superseded_by`. Both IDs must exist and must differ. |

Lifecycle mutations require explicit `--yes`. They preserve the requirement
body, stable ID, UUID, and unrelated frontmatter.

## See also

- [Configuration](okfreq-configuration) — hierarchy, scopes, markers, and generated fields.
- [Frontmatter](okfreq-frontmatter) — authored and generated field ownership.
- [Requirements traceability tutorial](../tutorials/okfreq-traceability) — end-to-end workflow.
- [Coverage boundaries](../explanation/okfreq-coverage-boundaries) — why test execution and pass/fail results are not parsed yet.
