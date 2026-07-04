# Task 07 — Create kb/cli.py Click Command Group

**Phase**: Phase 2 — kb Subpackage Core Logic
**Depends on**: 04, 05, 06

## Objective

Implement `src/okf_schema/kb/cli.py` containing the Click command group `kb` with
`init` and `install` subcommands. This is the CLI surface for `okf-schema kb` and
`okfkb`.

## Files to Modify/Create

- Create `src/okf_schema/kb/cli.py`
- Create `tests/test_kb_cli.py`

## Acceptance Criteria

- [ ] Click group `kb` exists with `init` and `install` subcommands
- [ ] `init` accepts optional `PATH` argument (defaults to `.`) and `--force` flag
- [ ] `install` accepts optional `PATH` argument (defaults to `.`) and `--force` flag
- [ ] Both commands delegate to `scaffold_kb` and `install_kb` respectively
- [ ] Both commands print confirmation summaries
- [ ] `okf-schema kb --help` lists `init` and `install`
- [ ] All commands exit with appropriate codes (0 on success, 1 on error)
- [ ] All code paths covered by tests
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `AGENTS.md` | Click CLI framework |
| `03-specification.md` | `okfkb --help` produces identical output to `okf-schema kb --help` |

## Detailed Steps

1. **Red**: Write failing tests in `tests/test_kb_cli.py`:
   - `test_kb_help_lists_init_and_install`
   - `test_kb_init_creates_bundle`
   - `test_kb_init_errors_on_nonempty_dir`
   - `test_kb_init_force_overwrites`
   - `test_kb_install_creates_files`
   - `test_kb_install_errors_when_target_missing`

2. **Green**: Implement `src/okf_schema/kb/cli.py`:
   ```python
   from __future__ import annotations

   from pathlib import Path

   import click

   from okf_schema.kb.scaffold import scaffold_kb
   from okf_schema.kb.install import install_kb


   @click.group()
   def kb() -> None:
       """Knowledge base management commands."""


   @kb.command()
   @click.argument("path", default=".", type=click.Path())
   @click.option("--force", is_flag=True, help="Overwrite existing files.")
   def init(path: str, force: bool) -> None:
       """Scaffold a new knowledge-base bundle."""
       target = Path(path)
       scaffold_kb(target, force=force)
       click.echo(f"Created knowledge base at {target}.")


   @kb.command()
   @click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True))
   @click.option("--force", is_flag=True, help="Overwrite existing files.")
   def install(path: str, force: bool) -> None:
       """Install KB skills and guidelines into a project."""
       target = Path(path)
       install_kb(target, force=force)
       click.echo(f"Installed KB tooling at {target}.")
   ```

3. Handle error cases gracefully (e.g., catch exceptions from `scaffold_kb` and
   exit with code 1 using `click.echo(..., err=True)` and `raise click.ClickException`).

4. Run tests: `uv run pytest tests/test_kb_cli.py -v`

5. Run `just preflight`.

6. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 07 --status done
   ```

## Testing Strategy

- Use `click.testing.CliRunner` for all CLI tests.
- Test help output to verify subcommands are listed.
- Test error cases by invoking with invalid arguments.
- Test `okfkb` alias by invoking the `kb` group directly (the alias is just an
  entry point to the same group).

## Notes

- The `kb` group does not need `@click.version_option` — version is handled by
  the top-level `okf-schema` group.
- The `init` command's `PATH` argument defaults to `"."` (current directory).
- The `install` command uses `click.Path(exists=True)` to validate the target.
