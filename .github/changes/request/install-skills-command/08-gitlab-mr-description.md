Add consistent installation of packaged agent skills from the `okf-schema`
Python wheel.

## Context

The wheel now distributes seven complete agent skill trees, but each console
entry point previously exposed a different installation behavior. Users could
not reliably choose a skill family or destination, and the legacy `okfkb`
installer also modified project guidance outside the requested skill folders.

## Requirements Impacts

The project stores its requirement documents under `requirements/tiers/`.
The implementation range updated the following traceability records.

### SwRS

| ID | Title | Action | Rationale |
|---|---|---|---|
| `SwRS-OKFSCHEMA-CORE-001` | Validate generic OKF bundles | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFKB-001` | Provide deterministic knowledge-base operations | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFKB-002` | Scaffold and install knowledge bases | Updated | Added the shared installer implementation and its integration and installer test evidence. |
| `SwRS-OKFSCHEMA-OKFKB-003` | Capture immutable knowledge findings | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFKB-004` | Navigate knowledge-base evidence | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFKB-005` | Consolidate knowledge findings | Updated | Removed coverage for the retired installation behavior. |
| `SwRS-OKFSCHEMA-OKFKB-006` | Materialize reciprocal knowledge derivations | Updated | Regenerated implementation and test coverage after the project scope refresh. |
| `SwRS-OKFSCHEMA-OKFREQ-001` | Provide requirements traceability operations | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFREQ-002` | Author and validate requirements | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFREQ-003` | Trace requirements to source and tests | Regenerated | Normalized generated metadata during coverage refresh. |
| `SwRS-OKFSCHEMA-OKFREQ-004` | Report requirement health | Regenerated | Normalized generated metadata during coverage refresh. |

### StRS

| ID | Title | Action | Rationale |
|---|---|---|---|
| `StRS-OKFSCHEMA-OKFKB-001` | Maintain trustworthy engineering knowledge | Updated | Added the reciprocal derivation relationship exposed by the regenerated traceability layer. |
| `StRS-OKFSCHEMA-OKFREQ-001` | Maintain auditable software requirements | Regenerated | Wrapped generated metadata to preserve the requirement document format. |

## Changes

- Package all seven skill families, including nested references and assets, in
the Python wheel and access them through `importlib.resources`.
- Add the same `install-skills` interface to `okf-schema`, `okfkb`, and
`okfreq`, with default, selector-based, relative, and explicit destinations.
- Keep family ownership isolated so each command installs only its own skills.
- Stage a complete family before mutation, report `installed` or `updated`,
preserve unrelated content, replace normal directories safely, and reject
owned symbolic-link destinations.
- Remove the retired `okfkb` installation options and side effects, including
`--force`, guideline installation, `AGENTS.md` patching, and destination
inference.
- Document Python CLI installation separately from agent skill deployment.

## Usage

Install the Python CLI tool and expose all three console commands:

```bash
uv tool install okf-schema
uv tool upgrade okf-schema
```

Install one owned skill family into the default global Copilot location:

```bash
okf-schema install-skills
okfkb install-skills
okfreq install-skills
```

Use a project-local selector or an explicit destination when needed:

```bash
okfkb install-skills --local-agents
okfreq install-skills --local-copilot
okf-schema install-skills /path/to/project
```

An explicit destination takes precedence over a selector. Relative destinations
are resolved from the current working directory.

## Impact

The three entry points now have one predictable, skills-only installation
contract. Existing authored files and unrelated skill families remain outside
the installer's ownership. Existing owned normal directories are replaced and
reported as updated; an owned symbolic link is rejected rather than followed.
Projects that relied on the retired `okfkb` guideline installation, `AGENTS.md`
patching, destination inference, or `--force` option must use their own project
setup for those behaviors.

## Examples

```text
$ okfkb install-skills --local-agents
Installing okfkb skills into .agents/skills
okfkb: installed
okfkb-distill: installed
okfkb-gardening: installed
okfkb-record-findings: installed
```

## Testing

- Resource tests verify all seven complete skill trees are packaged and
available from an installed wheel.
- Installer tests cover family isolation, all destination selectors,
precedence, parent creation, status reporting, replacement, unrelated-content
preservation, staging failures, and symlink rejection.
- CLI and integration tests cover all three entry points and the removed legacy
`okfkb` behavior.
- Documentation and distribution tests verify the distinction between Python
CLI installation and agent skill deployment.
- The final quality gate passed with 765 tests and 95.04% coverage through
`just preflight`.

## Checklist

- [x] Tests pass (`just preflight`)
- [x] Documentation updated
- [x] Requirement traceability annotations updated
- [x] Breaking changes documented

Assisted-by: Claude:Opus-4.7 Craftsman
