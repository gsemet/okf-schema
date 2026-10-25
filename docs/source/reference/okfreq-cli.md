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
| `okfreq validate [PATH] [--json] [--prose] [--check-links] [--project-root DIR]` | Validate metadata, configuration, IDs, hierarchy, exemptions, derivation links, and optionally annotated file targets. Prose and skipped-root findings are advisory. Requirement schema files that are unparsable or not mappings produce `W17`; empty ones produce informational `I1` (listed, never counted as errors, and `--json` has an `infos` list). |
| `okfreq lint [PATH] [--prose] [--check-links] [--project-root DIR] [--check|--diff]` | Validate, then regenerate requirement-directory navigation. `--check` fails on stale indexes without writing; `--diff` previews changes. |
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

Every non-reserved Markdown document under `tiers/` must have mapping
frontmatter and a non-empty string `id`. Missing or malformed documents fail
with their file path before indexing or reporting; they are never silently
omitted from requirement counts. Repair them rather than deleting them to
make validation pass. `index.md`, `log.md`, schemas and guidelines are excluded.

### Maintain requirement navigation and history

`okfreq lint requirements` validates first, then creates or refreshes
`tiers/index.md`, every configured tier's index, and every scope/ancestor index
needed to reach the requirements. For example, `tiers/swrs/okfreq/index.md`
lists the scope's requirements with their IDs, titles and descriptions; parent
indexes link to child indexes.

```bash
okfreq lint requirements --diff   # preview, no writes
okfreq lint requirements          # refresh generated navigation
okfreq lint requirements --check  # fail if navigation is missing or stale
```

The generator owns only the block between `<!-- okfreq:index:start -->` and
`<!-- okfreq:index:end -->`. It preserves all authored content outside the block,
including frontmatter and existing introductions. A new block is appended to an
existing index without replacing its content. Broken delimiters fail before any
index is written. Requirement mutations and coverage generation remain separate.
`okfreq index` continues to print requirement IDs; it does not generate files.

An optional `requirements/index.md` is a human-authored overview and is preserved.
Agents maintain dated change records in `requirements/tiers/log.md` (singular):
affected requirements, rationale, decisions and verification evidence. Lint
never rewrites logs or invents change history.

### Check annotated file targets

`okfreq init` writes `x-okf-link` annotations into the generated requirement
schemas. The defaults include filename-stem links for requirement relationships,
project-relative links for generated source and test evidence, marker navigation
hints, requirement description hints for tooltips/previews, and line-number
hints for source/test markers. These presentation hints are advisory: `okfreq`
does not render the UI. Existing schemas are preserved and are not migrated.
Checking targets is deliberately opt-in:

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
unavailable. A missing stem in a known bundle is `E10`. Warnings do not make `okfreq lint` fail on their own.

## Generated coverage and reports

| Command | Purpose |
|---|---|
| `okfreq update-coverage [PATH] [--check|--diff]` | Recompute only configured generated fields. `--check` reports drift and exits non-zero when stale; `--diff` prints previews; both are read-only. |
| `okfreq generate-report [PATH] [--output-json FILE] [--output-summary-md FILE]` | Generate a detailed JSON report and concise Markdown summary with SwRS source/test-link coverage, configured StRS test coverage, and combined leaf traceability coverage. StRS source coverage is not applicable. |

Without output options, the command writes JSON, JSON Schema and Markdown
under the resolved bundle's parent directory in `dist/` and prints their paths.
Use explicit output paths when reports must live in the project root's `dist/`.
Generated artifacts should be regenerated rather than edited manually.

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
