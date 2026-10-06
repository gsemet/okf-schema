# How this project exercises its own requirements tool

The repository uses `okfreq` for its own requirements, rather than maintaining a
parallel spreadsheet. The bundle is `requirements/`; its source and test scans
are scoped to `core`, `okfkb`, and `okfreq`. The following map connects supported
capabilities to real usage and executable demonstrations.

| Capability | Repository usage or demonstration |
|---|---|
| Split bundle, StRS/SwRS, stable IDs and UUIDs | `requirements/config.yml` and `requirements/tiers/`; creation and preservation tests in `tests/test_okfreq.py`. |
| Scope tokens, scope folders and per-scope source/test ownership | The three repository scopes allocate uppercase ID tokens into lowercase folders and scan their actual deliverables. |
| Authored parents, generated reverse links, dependencies | Project requirements derive from stakeholder outcomes; selected SwRS declare real `depends_on` links. `update-coverage` computes reverse links. |
| Nominal/failure scenarios, user needs, verification criteria | StRS documents preserve needs; SwRS documents specify observable behavior and verification. Prose checks expose unfinished scaffolds. |
| Source/test evidence and generated-field ownership | Real markers in implementation and tests drive `requirements-report`; `update-coverage --check` detects drift. |
| Stakeholder validation tests | The project uses `linked-swrs-and-validation-test`, with direct markers on real stakeholder workflow tests. The showcase compares it with default linked-SwRS coverage. |
| Schema-declared links and navigation hints | Relationship IDs use filename stems; generated evidence uses project-relative paths. Custom documentation/skill/example fields are also checked against real files. |
| All five resolution modes and both syntaxes | The disposable showcase resolves one manifest's local document, bundle path, extensionless path, source file and labelled wikilink. |
| Local refs, unions, conditions and stable result identities | `tests/test_file_links.py` exercises applicable branches and JSON Pointer identities, including punctuation collisions and invalid targets. |
| Config merge, custom markers, external metadata and unknown fields | The showcase uses a shipping project, custom markers, scoped IDs, a clearly fictional external tracker reference and conflict-preserving config merge. |
| Lifecycle and exemptions | The showcase requires confirmation, archives/supersedes a disposable requirement and preserves its UUID/body; an explicit exemption is reported separately. Live project requirements are not deprecated or exempted merely to demonstrate a feature. |
| JSON, JSON Schema and Markdown reports | `just requirements-report` emits all three; the showcase validates JSON against its emitted schema. |
| Generated navigation and authored history | `lint` maintains marked indexes at every tier/scope ancestor; `lint --check` detects drift. Agents maintain `requirements/tiers/log.md` under the same packaged guideline installed into other projects. |
| Inspection and recovery | The showcase exercises index/search/in-file/scope/graph/trace/status, a missing-ID failure, target failure, skipped-root warning and repaired validation. |
| Knowledge-base learning path | The single OKFKB tutorial teaches document roles and both existing illustrations, then executes capture, bounded synthesis, derivation and navigation. `tests/test_tutorial_okfkb.py` checks the actual snippets and preservation of recorded Finding bodies. |
| Existing-project adoption | The traceability tutorial runs an existing CSV feature, backfills reviewed drafts, links evidence and exercises its actual task-runner recipes. `tests/test_tutorial_okfreq.py` executes the published snippets in a disposable project. |
| Standalone agent distribution | `okfreq install-skills` ships the operations guide and gardening skill; wheel tests install resources without the source checkout. |

## Try the concrete scenarios

From this repository root:

```bash
uv run python examples/okfreq-examples/showcase.py
just refresh-okfreq-examples
just requirements-lint
just requirements-report
```

The showcase creates a temporary shipping-manifest project, verifies each
scenario and prints a compact list of outcomes. It leaves the checked-in CSV
example unchanged. The checked-in example separately runs Python behavior tests
and provides Rust source/test linkage; a Rust marker is not a claim that Rust
compiled or ran during the Python workflow.

Generated reports distinguish source linkage, test linkage, stakeholder test
definition and execution evidence. `execution_evidence.status: not_collected`
means exactly that; a 100% linkage figure does not assert test success or human
approval. The showcase's marker fixtures demonstrate scanning, not production
shipping behavior.

## Keeping this map accurate

Every behavior change must review runtime, human docs, standalone agent skills,
scaffold guidance, requirements, examples and verification together. Repository
contributors follow the product maintenance guideline registered in `AGENTS.md`.
Alternative policies belong in disposable examples when activating them on the
live requirements would misrepresent project decisions. Add a row or update its
evidence when a feature changes; never add fictional metadata just to populate it.
