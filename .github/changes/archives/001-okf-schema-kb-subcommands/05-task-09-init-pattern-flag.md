# Task 09 — Add --pattern Flag to Existing init Command

**Phase**: Phase 3 — CLI Integration and --pattern kb
**Depends on**: 06, 08

## Objective

Extend the existing `okf-schema init` command with an optional `--pattern <name>`
flag. When `--pattern kb` is supplied, delegate to `scaffold_kb`. Use the
`INIT_PATTERNS` registry for extensible dispatch.

## Files to Modify/Create

- Modify `src/okf_schema/cli.py` (existing `init` command)
- Modify `tests/test_cli_core.py` (add pattern tests)

## Acceptance Criteria

- [ ] `init` command has `--pattern` option with `default=None`
- [ ] When `--pattern kb` is provided, delegates to `scaffold_kb(name, force=False)`
- [ ] When `--pattern` is omitted, existing behaviour is preserved exactly
- [ ] Unknown pattern produces error listing available patterns
- [ ] Pattern registry is imported and `kb` is auto-registered
- [ ] All new code paths covered by tests
- [ ] `just preflight` passes

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `pyproject.toml` | Coverage threshold: 96%; line length: 100; Google docstrings |
| `pyproject.toml` | mypy strict: `disallow_untyped_defs=true` |
| `AGENTS.md` | TDD: write failing test first, then implement |
| `03-specification.md` | Pattern dispatch uses `INIT_PATTERNS` registry dict |
| `03-specification.md` | Unknown pattern names produce clear error listing available patterns |
| `03-specification.md` | Default behaviour (no `--pattern`) is unchanged |

## Detailed Steps

1. **Red**: Add failing tests in `tests/test_cli_core.py`:
   ```python
   def test_init_with_pattern_kb_scaffolds_kb(self, tmp_path: Path) -> None:
       """init --pattern kb creates KB structure."""
       runner = CliRunner()
       name = tmp_path / "mykb"
       result = runner.invoke(cli, ["init", str(name), "--pattern", "kb"])
       assert result.exit_code == 0
       assert (name / "concepts").is_dir()
       assert (name / "_schema" / "Base.schema.yaml").exists()

   def test_init_unknown_pattern_errors(self, tmp_path: Path) -> None:
       """init --pattern unknown exits with error."""
       runner = CliRunner()
       name = tmp_path / "mybundle"
       result = runner.invoke(cli, ["init", str(name), "--pattern", "unknown"])
       assert result.exit_code == 1
       assert "unknown" in result.output.lower()
       assert "available patterns" in result.output.lower()

   def test_init_without_pattern_is_unchanged(self, tmp_path: Path) -> None:
       """init without --pattern still creates standard bundle."""
       runner = CliRunner()
       name = tmp_path / "mybundle"
       result = runner.invoke(cli, ["init", str(name)])
       assert result.exit_code == 0
       assert (name / "bundle").is_dir()
       assert (name / "bundle" / "_schema" / "_base.schema.yaml").exists()
   ```

2. **Green**: Modify the `init` command in `src/okf_schema/cli.py`:
   ```python
   from okf_schema.kb.patterns import INIT_PATTERNS, list_patterns
   from okf_schema.kb.scaffold import scaffold_kb

   # Auto-register the kb pattern
   register_pattern("kb", scaffold_kb)

   @cli.command()
   @click.argument("name")
   @click.option("--pattern", default=None, help="Init pattern to use.")
   @click.pass_context
   def init(ctx: click.Context, name: str, pattern: str | None) -> None:
       """Create a new OKF bundle directory structure."""
       if pattern is not None:
           if pattern not in INIT_PATTERNS:
               available = ", ".join(list_patterns()) or "none"
               click.echo(
                   f"Error: Unknown pattern '{pattern}'. "
                   f"Available patterns: {available}.",
                   err=True,
               )
               ctx.exit(1)
           INIT_PATTERNS[pattern](Path(name), force=False)
           _echo(ctx, f"Created OKF bundle '{name}' using pattern '{pattern}'.")
           return

       # existing init logic...
   ```

3. Run tests: `uv run pytest tests/test_cli_core.py::TestInit -v`

4. Run `just preflight`.

5. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 09 --status done
   ```

## Testing Strategy

- Test `--pattern kb` creates KB structure (not standard bundle).
- Test unknown pattern exits 1 with helpful message.
- Test default (no `--pattern`) still creates the standard bundle structure.
- Ensure the `kb` pattern is auto-registered at import time.

## Notes

- The `register_pattern("kb", scaffold_kb)` call should happen at module level
  in `cli.py` or in `okf_schema/kb/__init__.py` to ensure it's always available.
- Consider placing the registration in `okf_schema/kb/__init__.py` to keep
  `cli.py` cleaner:
  ```python
  from okf_schema.kb.patterns import register_pattern
  from okf_schema.kb.scaffold import scaffold_kb
  register_pattern("kb", scaffold_kb)
  ```
