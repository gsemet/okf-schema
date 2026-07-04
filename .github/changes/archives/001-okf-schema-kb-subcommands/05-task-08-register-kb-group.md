# Task 08 — Register kb Group on Top-Level CLI

**Phase**: Phase 3 — CLI Integration and --pattern kb
**Depends on**: 07

## Objective

Register the `kb` Click command group on the top-level `okf-schema` CLI in
`src/okf_schema/cli.py`, and verify `okf-schema kb --help` works.

## Files to Modify/Create

- Modify `src/okf_schema/cli.py`
- Modify `tests/test_cli_core.py` (add kb group tests)

## Acceptance Criteria

- [ ] `src/okf_schema/cli.py` imports `kb` from `okf_schema.kb.cli`
- [ ] `cli.add_command(kb)` is called after existing commands
- [ ] `okf-schema kb --help` lists `init` and `install` subcommands
- [ ] `okfkb --help` produces identical output to `okf-schema kb --help`
- [ ] Existing CLI commands are unaffected
- [ ] All new code paths covered by tests
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `AGENTS.md` | Click CLI framework |
| `03-specification.md` | `okf-schema kb --help` lists `init` and `install` subcommands |

## Detailed Steps

1. **Red**: Add failing test in `tests/test_cli_core.py`:
   ```python
   def test_kb_group_is_available(self) -> None:
       """kb group appears in top-level help."""
       runner = CliRunner()
       result = runner.invoke(cli, ["--help"])
       assert result.exit_code == 0
       assert "kb" in result.output

   def test_kb_help_lists_subcommands(self) -> None:
       """kb --help lists init and install."""
       runner = CliRunner()
       result = runner.invoke(cli, ["kb", "--help"])
       assert result.exit_code == 0
       assert "init" in result.output
       assert "install" in result.output
   ```

2. **Green**: Modify `src/okf_schema/cli.py`:
   - Add import: `from okf_schema.kb.cli import kb`
   - Add `cli.add_command(kb)` after the last `@cli.command()` definition
     (after `backlinks` or at the end of the file before `if __name__` block).

3. Run tests: `uv run pytest tests/test_cli_core.py -v`

4. Verify `okfkb` alias works:
   ```bash
   uv run -- okfkb --help
   ```

5. Run `just preflight`.

6. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 08 --status done
   ```

## Testing Strategy

- Use `CliRunner` to invoke `cli` with `["kb", "--help"]`.
- Verify the top-level help includes "kb" in the command list.
- Verify `okfkb` entry point by running it via `uv run -- okfkb --help`.

## Notes

- The import must be placed carefully to avoid circular imports. Since `kb.cli`
  imports `scaffold` and `install`, which import from `okf_schema.data.kb`,
  there should be no circular dependency with `cli.py`.
- If importing at module level causes issues, consider lazy import inside the
  `cli()` function or at the bottom of the file.
