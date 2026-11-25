# CLI Reference

The `okf-schema` command-line tool provides subcommands for managing OKF bundles.

## Global options

```bash
okf-schema [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit. |
| `--version` | Show version and exit. |
| `-v, --verbose` | Increase verbosity (up to 3). |
| `-q, --quiet` | Suppress non-error output. |

---

## `okf-schema init`

Create a new OKF bundle directory structure.

```bash
okf-schema init NAME [--pattern PATTERN]
```

Creates a directory `NAME/bundle/` with `index.md`, `log.md`, and `_schema/_base.schema.yaml`.

| Option | Description |
|--------|-------------|
| `--pattern` | Use a named scaffold pattern. `kb` creates the opinionated knowledge-base layout. |

---

## `okf-schema new`

Create a new OKF concept file with frontmatter template.

```bash
okf-schema new --path ROOT --name CONCEPT [--type TYPE] [--title TITLE]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | ✅ | — | Root directory for the new concept. |
| `--name` | ✅ | — | Relative path of the concept (without `.md`). |
| `--type` | — | `concept` | Concept type. |
| `--title` | — | (derived from name) | Concept title. |

---

## `okf-schema validate`

Validate an OKF bundle against its schemas.

```bash
okf-schema validate --path BUNDLE [--schema-db DIR] [--strict]
	[--check-links] [--project-root DIR]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | ✅ | — | Root directory of the OKF bundle. |
| `--schema-db` | — | `_schema/` inside bundle | Override schema directory. |
| `--strict` | — | `False` | Treat warnings as errors. |
| `--check-links` | — | `False` | Check opt-in `x-okf-link` annotations. |
| `--project-root` | — | — | Explicit root for `project-relative` targets. |

A schema file that is empty prints `INFO [I1] schema file '<name>' is empty` and
never fails validation, even with `--strict`. A schema file that cannot be
parsed or is not a mapping prints `WARNING [W17] schema file '<name>' cannot be
parsed: <reason>`; `--strict` turns it into a failure. Either way the type stays
without schema. See [validation codes](validation-codes.md).

---

## `okf-schema validate-md`

Validate standalone markdown files without requiring an OKF bundle.

```bash
okf-schema validate-md --input 'notes/**/*.md' --schemas-dir ./schemas [--strict]
	[--check-links] [--bundle-root DIR] [--project-root DIR]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--input` | ✅ | Glob for markdown files. Repeat the option to supply multiple patterns. |
| `--schemas-dir` | ✅ | Directory containing `<type>.schema.{json,json5,yaml,yml}` files. |
| `--strict` | — | Treat warnings as errors. |
| `--check-links` | — | Check opt-in `x-okf-link` annotations. |
| `--bundle-root` | — | Root for `bundle-relative`, `bundle-relative-stem`, and `filename-stem` targets. |
| `--project-root` | — | Explicit root for `project-relative` targets. |

## `x-okf-link` annotations

Schemas may attach the non-validating `x-okf-link` annotation to a string schema,
including an array's `items` schema. It lets parsers and editors distinguish a
single file link or a list of file links from ordinary string values, without
changing the JSON Schema type or guessing from property names. See
[Declare file links](../how-to/write-custom-schema.md)
for a complete schema and matching frontmatter example. It has two required keys:

```yaml
type: string
x-okf-link:
  resolution: project-relative
  syntax: plain
```

For example, a schema can describe a scalar design file and a list of source
files while keeping both values as ordinary strings:

```yaml
properties:
  design:
    type: string
    x-okf-link: {resolution: document-relative, syntax: plain}
  implemented_in_files:
    type: array
    items:
      type: string
      x-okf-link: {resolution: project-relative, syntax: plain}
```

The matching frontmatter is then unambiguous to a parser or editor:

```yaml
design: ../design/export.md
implemented_in_files:
  - src/export.py
  - src/report.py
```

`resolution` is one of `document-relative`, `bundle-relative`,
`bundle-relative-stem`, `project-relative`, or `filename-stem`. Document-relative paths start at the
Markdown document's parent directory. Bundle-relative paths start at the bundle
root. Bundle-relative stems resolve a precise extensionless Markdown path:
`findings/cache-observation` means `findings/cache-observation.md` under the
bundle root, not a basename search. Project-relative paths use `--project-root`, then the document's containing
Git root; they never fall back to the current working directory or an editor
workspace. Filename stems search Markdown basenames inside the bundle, without
the `.md` suffix, and matching is case-sensitive. Duplicate stems are errors.

`syntax` is either `plain` or `wikilink`. Wikilinks may include a heading or
block fragment and a display label, such as `[[notes.md#heading|Read this]]`.
Only the target file is checked; fragment existence is not checked. Exact paths
keep their extensions and do not receive an automatic `.md` suffix.
Only `bundle-relative-stem` appends `.md` to the full relative target.

Checking is disabled by default, so ordinary JSON Schema validation is unchanged.
With `--check-links`, missing exact targets, root escapes, ambiguous stems, and
malformed annotations produce `E10`. An unavailable root or inaccessible matching candidate
produces `W15`, explicitly identifying the skipped field and reason. Bundle and
project-relative paths reject absolute paths and symlink escapes; document-relative
paths may use `../`.
The generic API owns this behavior and both opinionated layers reuse it.
New scaffolds annotate their default link fields; existing schemas and bundles
are left unchanged, with no migration required.

An annotation may also include optional navigation metadata:

```yaml
x-okf-link:
  resolution: project-relative
  syntax: plain
  basename_marker: '@implements_req'
  id_marker: id
```

`basename_marker` records the marker prefix a consumer can search for in the
resolved file. `id_marker` names the frontmatter field supplying the
requirement identity, normally `id`; a basename is the filename without its
extension. Together, these hints let an editor open directly on the line containing
`@implements_req <requirement-id>` or `@tests_req <requirement-id>`. They are
advisory metadata: `--check-links` resolves files but does not validate marker
locations or test execution.

---

## `okf-schema lint`

Lint frontmatter: flatten nested lists, convert block-style to inline,
auto-update `links` and `backlinks` fields from markdown body content, and
maintain the projections the schemas declare for plain OKF consumers.

```bash
okf-schema lint --path BUNDLE [--check] [--diff] [--links|--no-links] \
    [--link-projection|--no-link-projection]
```

| Option | Description |
|--------|-------------|
| `--check` | Report files that would change without modifying. |
| `--diff` | Show unified diff without modifying. |
| `--links` | Update `links` and `backlinks` from markdown body (default). |
| `--no-links` | Skip updating `links` and `backlinks`. |
| `--link-projection` | Maintain the generated `### Links` body section of every field whose `x-okf-link` carries a `link-projection` label, and `status` from an `x-okf-status-projection` mapping (default). |
| `--no-link-projection` | Leave the generated section and `status` untouched. |

The `--links` body scan ignores the generated section, so `links`/`backlinks`
reflect authored links only. Every `log.md` heading must be exactly
`## YYYY-MM-DD`, newest first, one per date: lint prints `W5`/`W18` warnings and
`--check` exits 1 on them, as it does on files that would change. An incomplete or
repeated generated section fails with an error and nothing is written. See
{doc}`../how-to/write-custom-schema`.

---

## `okf-schema list`

List all concepts in an OKF bundle.

```bash
okf-schema list --path BUNDLE
```

Output format: `path  type  title`

---

## `okf-schema show`

Print a concept file exactly as stored.

```bash
okf-schema show --path BUNDLE CONCEPT_PATH
```

### Output

Standard output is the file byte for byte: frontmatter style, comments, line
endings, encoding and body. It writes no file.

`show` does not parse or validate the file. A file without frontmatter, with
invalid YAML or that is not valid UTF-8 is printed as is, with exit code `0`.
Use `okf-schema validate` to check it.

Nothing is added to the file, in particular no trust tier and no staleness line:
use {ref}`okf-schema trust <cli-trust>`.

The Python API `show_bundle` returns `trust_tier`, `stale` and `raw` (the stored
text). It raises `UnicodeDecodeError` for a file that is not valid UTF-8.

(cli-show-concept-path)=

### `CONCEPT_PATH`

`CONCEPT_PATH` is one of the following:

- A name from the bundle root, with or without a leading `/`: `api/health-check`
  and `/api/health-check` name the same concept, from any terminal folder. A name
  is never read from the current working directory.
- An absolute disk path inside the bundle. It is inside the bundle when one of its
  folders, symbolic links followed, is the real path of `--path` (links followed
  too), so a path spelled through a symlinked folder (macOS `/tmp`, a symlinked
  `--path`) is accepted.

A `/` path that is not a disk path inside the bundle is read from the bundle root,
so on POSIX `/etc/passwd` is searched in the bundle and not found.

The `.md` extension is optional. The exact path is used when it is a file, else
`<name>.md`. A directory is never a concept: with both `api/` and `api.md`,
`api` shows `api.md`.

```bash
# A name from the bundle root, with or without ".md"
okf-schema show --path my-bundle api/health-check
okf-schema show --path my-bundle api/health-check.md

# The same concept, with a leading "/"
okf-schema show --path my-bundle /api/health-check

# An absolute disk path inside the bundle
okf-schema show --path /home/me/my-bundle /home/me/my-bundle/api/health-check
```

### Errors

`show` exits with code `2` and reads nothing outside the bundle when the concept
cannot be shown:

| Message | Meaning |
|---------|---------|
| `Error: Concept not found: <path>` | No file matches the name inside the bundle. A directory with no matching `.md` file gets this error too. |
| `Error: Concept path is outside the bundle: <name> (bundle: <bundle>)` | The real path leaves the bundle, for example `../outside`, a Windows drive path elsewhere, or a symbolic link whose target is outside the bundle (a linked file, or a file reached through a linked directory). The error is the same whether or not something exists there. |

A path with `..` or a symbolic link whose real path stays inside the bundle works.

For the bundle root (`.` or `/`), `show` reports "not found", unless a file
`<bundle name>.md` exists beside the bundle: that file is outside the bundle, so
the "outside the bundle" error is reported.

### Limits

- Following links does not change letter case. On a case-insensitive file system
  such as macOS, an absolute `CONCEPT_PATH` whose bundle part is spelled in
  another case than the real path of `--path` (for example `/Users/me/KB/x.md`
  when that real path is `/Users/me/kb`) is not recognized as inside the bundle:
  it is read from the bundle root and reported as
  `Error: Concept not found: ...`. Spell the bundle part as its real path does,
  or pass a name from the bundle root.
- The bundle-root reading is for a leading `/` only. On Windows, a `CONCEPT_PATH`
  starting with `\` (for example `\api\status`) is a path from the root of the
  drive, as Windows reads it, and gets
  `Error: Concept path is outside the bundle: ...` unless that path is inside the
  bundle.
- Git Bash on Windows rewrites an argument starting with `/` into a path under its
  install folder before `okf-schema` receives it (`/api/status` becomes
  `C:/Program Files/Git/api/status`), which is then refused as outside the bundle.
  Write the name without `/` (`api/status`), or set `MSYS_NO_PATHCONV=1`.

---

(cli-trust)=

## `okf-schema trust`

Print a concept's trust tier and staleness.

```bash
okf-schema trust --path BUNDLE CONCEPT_PATH
```

`CONCEPT_PATH` is read as for `show`: see
{ref}`CONCEPT_PATH <cli-show-concept-path>`.

### Output

The first line is `trust: <tier>`. The tier is one of `unverified`,
`machine-confirmed` or `human-reviewed`, and is derived from the concept's
`verified` field only; a single mapping counts as one entry. For the actor forms,
see W10 in the [validation codes](validation-codes.md).

A second line, `stale: true`, follows when `stale_after` has been reached: an
instant with its offset, or a bare date from that day on. There is no such line
when `stale_after` is absent or unparseable (`okf-schema validate` reports W16).

No score is printed.

```console
$ okf-schema trust --path my-bundle api/health-check
trust: unverified
```

```console
$ okf-schema trust --path my-bundle api/old-endpoint
trust: human-reviewed
stale: true
```

### Exit codes

| Code | Case |
|------|------|
| `0` | Every tier, including `unverified`. A file without frontmatter or with invalid YAML gives `trust: unverified`. |
| `2` | A missing concept, or a path leaving the bundle: `Error: ...`, as for `show`. |
| `2` | A file that is not valid UTF-8, which `show` prints as is: the single line `Error: Concept file is not valid UTF-8: <path>`. |

The command writes no file.

---

## `okf-schema index`

Regenerate all `index.md` files in an OKF bundle.

```bash
okf-schema index --path BUNDLE
```

The bundle root always gets an `index.md`. Another directory gets one when it
directly holds a Markdown file and also holds a concept (a Markdown file other
than `index.md` and `log.md`) or a direct, non-hidden subdirectory with Markdown
files at any depth. So a non-root directory that holds only `index.md` or
`log.md`, without such a subdirectory, is skipped: its index is not regenerated.
A non-root directory with no Markdown file of its own, only subdirectories, gets
no `index.md`.

Each index lists the concepts of its directory and those subdirectories, one
`- [<dir>](./<dir>/) — <summary>` line per subdirectory.
The command prints how many indexes it updated, created and left unchanged.

### Subdirectory summaries

The summary of a `./<dir>/` entry comes from the first of these that applies:

1. **The schema.** When all concepts of `<dir>` share one type with a schema, the
   schema `x-okf-summary` is used, else its `description` (cut at 120
   characters). It replaces any text already written.
2. **The summary already written** in the parent index, kept exactly as written,
   a trailing `[...]` included, whether the entry links `<dir>/`, `./<dir>/` or
   `./<dir>`. The line is rewritten in the `- [<dir>](./<dir>/) — <summary>`
   form. Two kinds of summary are recomputed instead (point 3):
   - the generic sentence ``Auto-generated index for concepts in `<dir>`.``,
     so that an introduction written later reaches the parent index;
   - a summary damaged by an earlier version: it starts with a relative link
     that is broken from the parent index but valid from `<dir>/`.
3. **The introduction** of `<dir>/index.md`, else the generic sentence.

The introduction is all the text before the first list of the subdirectory
index (a line starting with `- `, `* `, `+ `, or a number followed by `. ` or
`) `), or the whole body when it has no list. Blank lines, headings and lines
starting with `<!--` are skipped, and the remaining lines are joined with spaces
into one line. A list entry or a heading is never used as a summary. Then:

- Relative links are rewritten to work from the parent index: in `api/index.md`,
  `[guide](guide.md#setup)` becomes `[guide](api/guide.md#setup)`,
  `[up](../README.md)` becomes `[up](README.md)` and `[top](#top)` becomes
  `[top](api/index.md#top)`. External and `/`-prefixed links are kept as
  written. A link already broken stays broken, and `validate` reports it (W2).
- A result longer than 120 characters is cut at character 117 and ends with
  `...`. A link is never split: the cut moves to its start. When nothing is left
  before that link, the generic sentence is written.

For example, with `api/index.md` holding only a list of concepts, an earlier
version copied its first entry, with a link broken from the bundle root:

```markdown
- [api](./api/) — [Health Check](health-check.md)  [API Endpoint]
```

`okf-schema index` now writes, and repairs the line above into:

```markdown
- [api](./api/) — Auto-generated index for concepts in `api`.
```

The bundle root is processed before its subdirectories. On the first run of a new
bundle, an introduction is only picked up if the subdirectory `index.md` already
exists; otherwise the next run picks it up.

**Limit:** an introduction once copied into a parent index is then kept as an
authored summary. It is not refreshed when the subdirectory introduction changes
later; delete the entry line and run `index` again to recompute it.

---

## `okf-schema stats`

Show compact statistics for an OKF bundle.

```bash
okf-schema stats --path BUNDLE
```

Broken links are counted in concept bodies with the same check as the
[W2 warning](validation-codes.md): `#...` anchors are ignored and paths are
percent-decoded. Each one costs 10 health points (at most 30). Links in
`index.md` and `log.md` are not counted; run `validate` for those.

---

## `okf-schema backlinks`

List all concepts that link to the given target concept(s).

```bash
okf-schema backlinks --path BUNDLE TARGETS...
```

One line is printed per backlink in the form `target ← source`.
Multiple target paths may be provided. The `.md` extension is optional.

---

## `okf-schema kb`

Run the opinionated knowledge-base command group. It includes `init`,
`install-skills`, `new-finding`, `update`, `validate`, `read`, `get`,
`search`, and `query`.

```bash
okf-schema kb --help
```

The same commands are also available through the `okfkb` executable. See
[KB Commands](kb-commands) for their complete syntax. Generic bundle search
is available through `okf_schema.api.search_bundle`, not as a top-level CLI
command.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success. |
| `1` | Validation or lint failure. |
| `2` | Runtime error (file not found, etc.). |

## See also

- [KB Commands](kb-commands) — knowledge-base specific commands (`okfkb`).
- [Python API](api) — programmatic interface to the same operations.
- [Getting Started](../tutorials/getting-started) — tutorial using these commands.
- [Validate in CI](../how-to/validate-in-ci) — CI examples for `validate --strict`.
- [Lint Before Commit](../how-to/lint-before-commit) — pre-commit hook for `lint`.
