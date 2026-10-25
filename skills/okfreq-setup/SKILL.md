---
name: okfreq-setup
description: 'Install okfreq in a project that has no requirements bundle yet and deliver, without asking the user anything, a complete baseline: every current behaviour specified as StRS and SwRS, anchored to the code with markers, untested behaviour covered by tests, all in one pull request. Use when the user asks to set up, install, bootstrap or adopt okfreq or living requirements in a project.'
metadata:
  keywords: [okfreq, setup, bootstrap, baseline, requirements, traceability]
  url: https://github.com/gsemet/okf-schema
---

# okfreq setup

<!-- @implements_req SwRS-OKFSCHEMA-OKFREQ-010 -->

Take a project with no requirements bundle to a pull request that adds okfreq and specifies
everything the project does today. Run it to the end without asking the user anything: every
choice below has a fixed default. Stop only on the stop rules.

## Precedence and companions

1. The project's `requirements/guidelines/requirements.guidelines.md` wins over this skill, and
   this skill wins over the other okfreq skills. The guideline is installed in step 3; from then
   on, read it again before each step and follow it.
2. Use the `okfreq` skill for how the CLI works. If it is not installed, use `okfreq --help`,
   `okfreq <command> --help` and the installed guideline.
3. Do not use `okfreq-gardening` during setup. Name it in the final report as the recurring
   maintenance workflow.

## Stop rules

- A file named `config.yml` already exists under `requirements/`, `.agents/requirements/` or
  `.github/requirements/`: do not set up. Report that the project already has a bundle and that
  `okfreq-gardening` applies.
- The directory is not a git repository, or the default branch cannot be determined: stop and
  report.
- Never modify, stage or revert changes that were in the worktree before you started.

## Fixed defaults

| Choice | Default |
|---|---|
| Branch | `okfreq-setup` from the default branch; one commit at the end |
| Bundle | `requirements/` at the project root (`okfreq init requirements`) |
| Install, Python project (`pyproject.toml` exists) | `uv add --group requirements okf-schema`; run as `uv run --group requirements okfreq` |
| Install, other project | `uvx --from okf-schema==<latest> okfreq`, pinned in the task runner |
| Scopes | The project's own feature grouping: test groups or suites if they exist, else top-level feature folders. 6 to 20 scopes, `id_token` in upper case, at most 12 characters |
| Scan folders | Each scope scans the project's source and test roots (not per-feature sub-folders), so shared files can carry markers of several scopes |
| Delivery | Push the branch and open a pull request when a remote and `gh` are available; otherwise leave the commit on the branch. Never merge, never push to the default branch |

## Steps

1. **Read the project.** `AGENTS.md` (or `CLAUDE.md`, `.github/copilot-instructions.md`), the
   README, the task runner, CI, the test layout and the source layout. Note the commands that
   build, test and check.
2. **Install** okf-schema as in the table. Commit the lock file change with the rest.
3. **Initialise.** Run `okfreq init requirements`. Keep the generated
   `requirements/guidelines/requirements.guidelines.md` as is, and append one section
   `## Project rules` with: the bundle path, the okfreq command line, the scope list with what
   each covers, the marker comment syntax for each language in the project, and the project's
   check and test commands. Project-specific rules go only there, never in a skill.
4. **Configure** `requirements/config.yml`: the scopes and scan folders from the table.
5. **Point to it.** Add this section to `AGENTS.md`, creating the file if it does not exist:

   ```markdown
   ## Requirements (okfreq)

   Read `requirements/guidelines/requirements.guidelines.md` before any of these: adding,
   changing or fixing a behaviour; moving, renaming or deleting code or tests that carry
   `@implements_req` or `@tests_req` markers; editing anything under `requirements/`.
   Requirements state what the code does today, tied to it by those markers.
   ```

6. **Wire the gates.** Add task-runner targets (or scripts) for
   `okfreq validate requirements --prose --check-links --project-root .`,
   `okfreq lint requirements --check`, `okfreq update-coverage requirements --check`, and call
   them from the project's existing check command and CI.
7. **Inventory each scope.** List every observable behaviour from the code, the tests and the
   docs, each with the file and symbol that produce it. Read code, never guess.
8. **Write the StRS**: 3 to 8 per scope, each a user use case.
9. **Write the SwRS**, following the guideline: one SwRS per observable behaviour with all its
   scenarios; a rule that applies to many features (refusals, validation, limits) written once
   and cited; behaviour that looks wrong specified as it is, with "Known issue: …". Expect about
   one SwRS per 150 lines of product code; far more means behaviours are split, far fewer means
   behaviours are missing.
10. **Review each scope** with a reader who did not write it: every claim checked against the
    code, no bundled behaviours, no desired state. Fix what the review finds, once.
11. **Mark.** Add `@implements_req` at the code that produces each behaviour and `@tests_req` at
    the test that checks it. Markers are comments only: do not change code.
12. **Close test gaps.** For each SwRS with no test, add a test in the existing suites that
    passes on the current code and asserts today's behaviour, known issues included. Never fix a
    known issue during setup. When a behaviour cannot be tested in the repository, set
    `annotation_exemption: true` with the reason.
13. **Audit.** Check that each inventory item maps to an SwRS, an implementation marker and a
    test marker. Run `okfreq update-coverage requirements`, then every gate of step 6 and the
    project's full check and test commands. All must pass.
14. **Deliver.** Append a dated entry to `requirements/tiers/log.md`, commit everything in one
    commit, then deliver as in the table.

When sub-agents are available, run steps 7 to 12 with one agent per scope in parallel, each in
its own scratch directory, and the review of step 10 with a separate agent. Never let two agents
edit the same file at the same time.

## Final report

- Pull request link (or branch name) and check status.
- StRS and SwRS counts per scope; implementation and test marker coverage.
- Every known issue found, one line each with its SwRS id: these are bug candidates for the
  user to schedule.
- Exemptions and remaining gaps.
- Next: run `okfreq-gardening` regularly to keep the requirements in sync with the code.
