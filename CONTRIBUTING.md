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
3. Follow the [product maintenance contract](.github/guidelines/product-maintenance.guidelines.md):
   update affected human docs, standalone skills, scaffold guidance, requirements,
   concrete examples and verification together. Record evidence in the
   [feature map](docs/source/explanation/project-feature-coverage.md).
4. Submit your PR with a clear description.

## How to Release

Releases start with a committed version change, not a manually created tag.
The package version lives in `pyproject.toml` (`[project] version`); the root `okf-schema`
entry of `uv.lock` must match it.

1. Fetch release tags and commit the changes to include in the release:

	```bash
	git fetch origin --tags
	```

2. Calculate the next version with Python Commitizen:

	```bash
	just bump-version
	```

	`feat:` commits produce a minor bump. A `!` before the colon or a
	`BREAKING CHANGE:` footer produces a major bump, including before version 1.0.
	Fixes, documentation, maintenance, other changes, and an empty release range produce
	a patch bump. Classification uses committed history since the baseline release tag;
	uncommitted feature changes do not count. The baseline is the newer of the current
	manifest version and the latest reachable stable release tag.

	To choose a version instead:

	```bash
	just version 1.2.3
	```

	Both commands update `pyproject.toml` and `uv.lock` and create a signed-off commit
	with subject `chore: version X.Y.Z`, using `git commit -s`. Neither creates a local tag.
	Only these two files are committed; unrelated staged work stays staged.
	Commit or stash existing edits to either version file before running the command.
	Explicit versions must be stable `X.Y.Z`, newer than the baseline, and not already tagged.

3. Validate the version commit, then push it and merge it into `main`:

	```bash
	just preflight
	git show --stat HEAD
	```

4. After successful main-branch CI, the tagging job checks whether the pushed version
	changed and whether `vX.Y.Z` exists remotely. It verifies matching lockfile versions
	and an increasing version, then tags the exact tested commit. Ordinary pushes and
	existing tags are left unchanged. It never commits files back to `main`.

5. CI starts **Release** (`publish.yml`) explicitly with that tag. A tag pushed by
	`GITHUB_TOKEN` does not trigger another push workflow, so this step is required. The
	release job verifies the tag, manifest, and default-branch ancestry, generates user-facing
	notes from the previous reachable release's Git diff through `gh copilot`, builds the
	package, publishes to PyPI, and attaches the distributions and notes to a GitHub release.

	CI starts the workflow with `gh workflow run publish.yml -f tag=vX.Y.Z` (the tagging
	job has `actions: write`) rather than calling it as a reusable workflow, because PyPI
	Trusted Publishing is bound to the `publish.yml` workflow file and does not support
	reusable workflows.
	A first release uses all history. Note generation must succeed before publication.

### GitHub Configuration

Create a GitHub environment named `pypi`, allowing releases from the default branch
and `v*` tags, and register `publish.yml` with environment `pypi` as the PyPI Trusted
Publisher of `okf-schema`. Configure this secret in that environment or at repository level:

- `COPILOT_GITHUB_TOKEN`: a GitHub token with Copilot access for `gh copilot`.
  The workflow's normal `GITHUB_TOKEN` is used for tags and GitHub releases, not Copilot.

The runner must provide `gh` with Copilot CLI support for `gh copilot --`.
GitHub-hosted Ubuntu runners supply `gh`; authentication uses the Copilot secret above.
Repository rules must permit the CI token to create version tags. Environment approval
rules, when configured, pause publication after tagging. All committed dependency settings
and GitHub jobs use the public PyPI registry; corporate proxy and CA settings belong
only in the developer's local environment, never in workflow files or lockfile URLs.

### Recovery and Release Notes

If tagging succeeded but publication failed, rerun the failed release job or dispatch
**Release** with the existing `vX.Y.Z` tag. Do not move the tag or bump again just
to retry. PyPI publication skips already uploaded files, allowing a retry
to finish the GitHub release. Manual pushes of valid `vX.Y.Z` tags also run this workflow.

To generate notes without publishing the package, dispatch **Generate release notes
(manual)** from the default branch with an existing tag reachable from that branch.
It uploads the validated Markdown and creates a draft GitHub release, refusing to overwrite
an existing release. A later **Release** run publishes that draft with the distributions.

Local generation uses the same diff-grounded generator:

```bash
just release-notes v0.13.0 v0.13.1
uv run python scripts/release_notes.py --validate release-notes.md
```

Set `COPILOT_GITHUB_TOKEN` locally before generation. `release-notes.md` contains only
validated final-answer Markdown, not Copilot progress or tool output. The generator retries
invalid output up to three times and fails closed rather than substituting invented notes.

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
