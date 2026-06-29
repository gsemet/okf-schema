# Task 06: CLI Core — init, new, validate, format

**Depends on**: Task 01, Task 05
**Estimated complexity**: High
**Type**: Feature
**Phase**: Phase 3 — Python API & CLI Wiring

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Implement the Click CLI entry point and the first four subcommands: `init`, `new`, `validate`, `format`. Include global options `--version`, `--verbose`, `--quiet`.

## Files to Modify/Create
- `src/okf_schema/cli.py`
- `tests/test_cli_core.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 06 --status in_progress --started-at now`
2. Create `src/okf_schema/cli.py`:
   - Define `cli` click group with `invoke_without_command=True`
   - Global options: `--version` (show version and exit), `--verbose` / `-v` (count, up to 3), `--quiet` / `-q` (suppress non-error)
   - When no subcommand given, show help
3. Implement `init <name>`:
   - Create `<name>/bundle/` directory
   - Create `<name>/bundle/index.md` with minimal frontmatter (`okf_version: "0.1"`)
   - Create `<name>/bundle/log.md` with no frontmatter, initial heading `## YYYY-MM-DD`
   - Create `<name>/schema/` directory (empty)
   - Exit 1 if `<name>` already exists
4. Implement `new --path <root> --name <relative-path> [--type <type>] [--title <title>]`:
   - Validate `--path` and `--name` are provided (exit 2 with usage if missing)
   - Create `<root>/bundle/<relative-path>.md` with frontmatter template:
     ```yaml
     ---
     type: <type or "concept">
     title: <title or stem>
     description: ""
     tags: []
     ---
     ```
   - Exit 1 if file already exists
5. Implement `validate <bundle-path> [--schema-db <schema-dir>]`:
   - Call `api.validate_bundle()`
   - Print findings grouped by file (errors first, then warnings)
   - Exit 0 if conformant, 1 if errors, 2 on usage error
   - Support `--schema-db` optional flag
6. Implement `format <bundle-path> [--check] [--diff]`:
   - Call `api.format_bundle()`
   - Default: modify files in-place, print summary
   - `--check`: exit 1 if any file would change, print which files
   - `--diff`: print unified diff for each changed file, no modifications
7. Write `tests/test_cli_core.py` using `click.testing.CliRunner`:
   - Test `init` creates correct directory structure
   - Test `init` exits 1 when directory exists
   - Test `new` creates file with correct frontmatter
   - Test `new` exits 2 when required flags missing
   - Test `new` exits 1 when file exists
   - Test `validate` exits 0 for valid bundle, 1 for invalid
   - Test `format` modifies files in-place
   - Test `format --check` exits 1 when changes needed
   - Test `--version` shows version
8. Run `just preflight` and fix any issues
9. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 06 --status coded_not_reviewed --completed-at now`
10. Commit with a conventional commit message:
    `feat: add CLI entry point with init, new, validate, format subcommands`

## Acceptance Criteria
- [ ] Click CLI group `cli` is defined with global options
- [ ] `init` creates bundle directory structure with index.md and log.md
- [ ] `init` exits 1 if target directory already exists
- [ ] `new` creates concept file with frontmatter template
- [ ] `new` exits 2 if required flags missing
- [ ] `new` exits 1 if file already exists
- [ ] `validate` prints grouped findings and exits 0/1 correctly
- [ ] `format` supports in-place, --check, and --diff modes
- [ ] `tests/test_cli_core.py` covers all four subcommands
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_cli_core.py`
- **Test cases**:
  - `init mybundle` creates `mybundle/bundle/`, `mybundle/bundle/index.md`, `mybundle/bundle/log.md`, `mybundle/schema/`
  - `init` on existing dir exits 1
  - `new --path root --name concepts/idea` creates file with frontmatter
  - `new` without `--path` exits 2
  - `new` on existing file exits 1
  - `validate` on valid bundle exits 0 with conformant message
  - `validate` on invalid bundle exits 1 with error list
  - `format` flattens nested lists in bundle
  - `format --check` exits 1 when changes needed
  - `format --diff` prints diff without modifying
  - `--version` outputs version string

## Notes
- Use `click.echo()` for all output to respect `--quiet`
- Use `click.get_current_context().exit(code)` for proper exit codes
- The `new` command frontmatter template should use `ruamel.yaml` to generate properly formatted YAML
- For `validate` output, group findings by file path for readability
