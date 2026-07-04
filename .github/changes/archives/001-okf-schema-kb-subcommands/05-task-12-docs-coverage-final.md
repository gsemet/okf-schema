# Task 12 — Documentation, README Update, and Final Quality Gate

**Phase**: Phase 4 — Tests, Documentation, and Quality Gate
**Depends on**: 10, 11

## Objective

Update project documentation (README, Sphinx docs), verify the wheel contains
bundled assets, and run the full quality gate to ensure ≥ 96% coverage and no
regressions.

## Files to Modify/Create

- Modify `README.md` (add Knowledge Base section)
- Create `docs/source/kb-commands.rst`
- Modify `docs/source/index.rst` (add kb-commands to toctree if needed)

## Acceptance Criteria

- [ ] `README.md` has a new "Knowledge Base" section explaining `okfkb init` and `okfkb install`
- [ ] `docs/source/kb-commands.rst` documents the `kb` subcommand group
- [ ] `docs/source/index.rst` includes `kb-commands` in the toctree
- [ ] `uv build` produces a wheel containing all bundled KB assets
- [ ] `just preflight` passes with ≥ 96% coverage
- [ ] `just typecheck` passes with no new errors
- [ ] `just lint` passes with no new errors
- [ ] `just style-check` passes with no new errors

## Applicable Guidelines

| Source | Rule |
|--------|------|
| `AGENTS.md` | Update `README.md` or `docs/` if public APIs change |
| `AGENTS.md` | Quality gate: `just preflight` |
| `02-interview-responses.md` | README gets a new top-level "Knowledge Base" section |
| `02-interview-responses.md` | Dedicated Sphinx page for kb commands |
| `03-specification.md` | `pip install okf-schema && okfkb init my-kb` works without source tree |

## Detailed Steps

1. **Update README.md**:
   Add a "Knowledge Base" section after the main usage examples:
   ```markdown
   ## Knowledge Base

   `okf-schema` includes a dedicated knowledge-base subcommand group (`okfkb`)
   for managing OKF bundles designed for agent-facing experimental findings:

   ```bash
   # Scaffold a new knowledge base
   okfkb init my-kb

   # Install KB skills and guidelines into a project
   okfkb install /path/to/project
   ```

   See the [full documentation](https://okf-schema.readthedocs.io/en/stable/kb-commands.html)
   for details.
   ```

2. **Create docs/source/kb-commands.rst**:
   ```rst
   Knowledge Base Commands
   =======================

   The ``kb`` subcommand group (also available as the standalone ``okfkb``
   command) provides tools for managing OKF knowledge-base bundles.

   .. code-block:: bash

      okfkb init [PATH]       # Scaffold a new knowledge base
      okfkb install [PATH]    # Install skills and guidelines

   init
   ----

   Scaffold a canonical knowledge-base folder layout with 8 content
   directories, 8 schema YAML files, ``index.md``, and ``log.md``.

   install
   -------

   Deploy bundled skills (``record-finding``, ``consolidate-knowledge-base``)
   and the ``knowledge-base.guidelines.md`` guideline into a target project.
   Patches or creates ``AGENTS.md`` with a reference to the guideline.
   ```

3. **Update docs/source/index.rst**:
   Add `kb-commands` to the toctree.

4. **Verify wheel packaging**:
   ```bash
   uv build
   unzip -l dist/okf_schema-*.whl | grep "data/kb"
   ```
   Confirm all 8 schemas, 2 skills, and 1 guideline are present.

5. **Run full quality gate**:
   ```bash
   just preflight
   ```

6. **If coverage is below 96%**, identify uncovered lines and add tests.

7. Update progress:
   ```bash
   craftsman agent update-task --prd .github/changes/request/okf-schema-kb-subcommands --task 12 --status done
   ```

## Testing Strategy

- Documentation is verified by building Sphinx docs:
  ```bash
  just docs
  ```
- Wheel packaging is verified by inspecting the wheel contents.
- Coverage is verified by the `just preflight` command.

## Notes

- The README update should be concise but informative — point to Sphinx docs for
  full details.
- The Sphinx page should use `sphinx-click` directives if available, or plain
  RST if not.
- If `docs/source/index.rst` does not have a toctree, just create the RST file
  — it will be picked up by the build system.
