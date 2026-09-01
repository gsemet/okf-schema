# Specification: packaged agent skill installation

## Objective

Distribute the repository's agent skills in the `okf-schema` Python wheel and
provide a consistent `install-skills` command from each console entry point.
The commands install only their owned skills into global, repository-local, or
explicit destinations using package resources rather than repository-relative
filesystem paths.

## Packaged resources

The wheel must contain these complete skill directories, including each
directory's nested references and assets:

- `okf-schema`
- `okfkb`
- `okfkb-distill`
- `okfkb-gardening`
- `okfkb-record-findings`
- `okfreq`
- `okfreq-gardening`

Runtime access to these resources must use `importlib.resources`. Installation
must work from an installed wheel and must not depend on a source checkout.

## Command ownership

| Command | Installed skills |
|---|---|
| `okf-schema install-skills` | `okf-schema` |
| `okfkb install-skills` | `okfkb` and every packaged `okfkb-*` skill |
| `okfreq install-skills` | `okfreq` and every packaged `okfreq-*` skill |

The family membership above is defined by the packaged resources. Each command
must leave skill directories owned by the other commands untouched.

## Command interface

Each command accepts an optional positional `DESTINATION` and these selector
flags:

- `--agent-copilot`: install under `~/.copilot/skills`.
- `--local-copilot`: install under `.github/skills` relative to the current
  working directory.
- `--local-agents`: install under `.agents/skills` relative to the current
  working directory.

When `DESTINATION` is omitted and no selector is supplied, the behavior is
equivalent to `--agent-copilot`. A supplied `DESTINATION` takes precedence over
any supplied selector flag. Relative explicit destinations resolve against the
current working directory. The destination directory and missing parents are
created as needed.

The selector naming deliberately leaves room for additional agent-specific
destinations in later changes.

## Installation behavior

1. Resolve and display the effective destination.
2. Identify the complete skill family owned by the invoked command.
3. Stage the complete family from `importlib.resources` before mutating the
   destination.
4. If staging fails, return a nonzero exit status and leave the destination's
   owned skill directories unchanged.
5. For each owned skill, install a new directory or atomically replace the
   existing normal directory.
6. Do not alter unrelated directories or files in the destination.
7. If an owned destination path is a symbolic link, fail clearly with a
   nonzero exit status; do not follow, unlink, or replace it.
8. Report each skill as `installed` when newly created or `updated` when an
   existing owned directory was replaced.

No `--force`, `--quiet`, or `--dry-run` option is required.

Staging the full family is mandatory. A complex rollback guarantee after a
rare failure during final replacement is not required, but any such failure
must be reported clearly and return a nonzero status.

## Existing command migration

The current `okfkb install-skills` behavior is replaced by this specification.
The command must no longer:

- install `knowledge-base.guidelines.md`;
- create or patch `AGENTS.md`;
- infer `.agents` versus `.github` from existing project directories;
- skip existing owned skills by default; or
- expose `--force`.

This is an intentional command-contract change in favor of consistent,
skills-only installation across all three entry points.

## Skill documentation

Update the base `okf-schema`, `okfkb`, and `okfreq` skill documents with a
concise prerequisite section that explains:

```bash
uv tool install okf-schema
uv tool upgrade okf-schema
```

The documentation must state that this tool installation exposes
`okf-schema`, `okfkb`, and `okfreq`. It should distinguish installing the
Python CLI tool from subsequently installing agent skill folders with the new
commands.

## Verification expectations

Automated tests must cover at least:

- wheel/package resources contain all seven complete skill directories;
- each entry point installs exactly its owned family;
- the default global Copilot destination;
- all three destination selectors and an explicit absolute or relative path;
- explicit destination precedence over a selector;
- creation of missing destination parents;
- installed versus updated reporting;
- replacement of existing owned normal directories without changing unrelated
  skills;
- rejection of owned symbolic links;
- no destination mutation when family staging fails; and
- the removed legacy `okfkb` guideline, `AGENTS.md`, and `--force` behavior.

The repository's final validation gate remains `just preflight`.

## Resolved decisions

All interview decisions Q1 through Q12 are incorporated above. No unresolved
items remain.