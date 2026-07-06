# Contributing to okf-schema

Thank you for your interest in contributing to `okf-schema`!

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gsemet/okf-schema.git
   cd okf-schema
   ```

2. **Install dependencies**:
   ```bash
   just dev
   ```
   This installs all runtime and development dependencies using `uv`.

3. **Verify your setup**:
   ```bash
   just preflight
   ```

## Development Workflow

### Running Tests

```bash
just test          # Run tests with coverage
just test-fast     # Run tests in parallel
```

### Code Quality

```bash
just style         # Auto-format code
just style-check   # Check formatting without modifying files
just lint          # Run linters
just typecheck     # Run type checkers
```

### Full Preflight

Before committing, always run:

```bash
just preflight
```

This runs the complete quality gate: formatting check, linting, type checking,
and tests with coverage.

## Coding Standards

- **Python version**: 3.10+
- **Line length**: 100 characters
- **Formatter**: `ruff`
- **Type checker**: `ty` (primary), `mypy` (secondary)
- **Test framework**: `pytest` with `pytest-cov`
- **Minimum coverage**: 95%

## Pull Request Process

1. Ensure `just preflight` passes locally.
2. Write tests for new functionality.
3. Update documentation if needed.
4. Submit your PR with a clear description.

## Release Process

This project uses [hatch-vcs](https://github.com/ofek/hatch-vcs) for versioning.
Versions are derived from Git tags automatically — no manual version bumping
in source files is required.

To publish a release, maintainers shall:

1. **Ensure `main` is green**: Verify the latest commit passes CI.

2. **Create and push a tag**:
   ```bash
   git checkout main
   git pull origin main
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. **Create a GitHub Release**: Go to
   [Releases](https://github.com/gsemet/okf-schema/releases) and draft a new
   release from the tag. The `publish.yml` workflow will automatically build
   and upload to PyPI once the release is published.

4. **Verify**: Check [PyPI](https://pypi.org/project/okf-schema/) for the new
   version.

## Evaluation

`okf-schema` includes an automated skill evaluation campaign in `skills-evals/` that validates the tool against a suite of fixture bundles. These evals verify that the validator correctly identifies conformant bundles, catches structural errors (E1–E6), reports warnings (W1–W7), and handles JSONSchema validation with both JSON and YAML schema databases.

| Eval | Description |
|------|-------------|
| `validate-conformant-bundle` | Validates a fully conformant OKF bundle (0 errors, 0 warnings) |
| `validate-non-conformant-bundle` | Validates a bundle with known errors (E1–E3) and warnings (W1–W7) |
| `create-okf-bundle` | Creates a new OKF bundle from scratch and validates it |
| `validate-with-schema-database` | Tests JSONSchema validation with `--schema-db` |
| `validate-with-yaml-schema-database` | Tests YAML schema file support in schema DB |

Run the eval campaign by asking in Copilot Chat `Execute instructions in skills-evals/eval.prompt.md`, or via Copilot-CLI:

```bash
# Trigger eval via Copilot-CLI
just copilot-cli-eval-okf-schema
# Open eval review in browser
just eval-view-okf-schema
```

The eval system supports A/B comparison (`with_skill` vs `without_skill`) across iteration directories. Results are rendered as an interactive HTML dashboard.

**Latest eval result:** [iteration-30.06.26-22.06](https://htmlpreview.github.io/?https://github.com/gsemet/okf-schema/blob/master/skills-evals/results/iteration-30.06.26-22.06/eval-result.html) — [skeptical review](skills-evals/results/iteration-30.06.26-22.06/skeptical-review.md)

## Reporting Issues

Please use [GitHub Issues](https://github.com/gsemet/okf-schema/issues) to report
bugs or request features.
