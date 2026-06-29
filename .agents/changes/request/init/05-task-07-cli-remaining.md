# Task 07: CLI Remaining Subcommands — list, show, index, search, graph, stats

**Depends on**: Task 06
**Estimated complexity**: High
**Type**: Feature
**Phase**: Phase 3 — Python API & CLI Wiring

## ⚠️ Important information

Before coding, Read FIRST -> Load [05-task-00-READBEFORE.md](05-task-00-READBEFORE.md)

## Applicable Guidelines

| Rule file | What it enforces | Applies to |
|-----------|-----------------|------------|
| `pyproject.toml` [tool.ruff] | Linting and formatting rules | `**/*.py` |
| `pyproject.toml` [tool.coverage.run] | Coverage settings (95% min) | `src/okf_schema/` |

## Objective

Implement the remaining six CLI subcommands: `list`, `show`, `index`, `search`, `graph`, `stats`.

## Files to Modify/Create
- `src/okf_schema/cli.py` (add subcommands)
- `tests/test_cli_remaining.py`

## Detailed Steps
1. Update `progress.json` via CLI:
   `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 07 --status in_progress --started-at now`
2. Add `list <bundle-path>` to `cli.py`:
   - Call `api.list_bundle()`
   - Output: one concept per line, format: `<relative-path>  <type>  <title>`
   - Sorted by path
3. Add `show <bundle-path> <concept-path>` to `cli.py`:
   - Call `api.show_bundle()`
   - Output frontmatter as YAML, then body markdown
   - Exit 2 if concept not found
4. Add `index <bundle-path>` to `cli.py`:
   - Call `api.index_bundle()`
   - Print summary: "N updated, M unchanged, K skipped"
   - Exit 2 if bundle path invalid
5. Add `search <bundle-path> <query>` to `cli.py`:
   - Call `api.search_bundle()`
   - Output table with columns: `Path`, `Type`, `Title`
   - Exit 0 even if no matches (print "No matches found")
6. Add `graph <bundle-path>` to `cli.py`:
   - Call `api.graph_bundle()`
   - Output ASCII adjacency list:
     ```
     concept-a
       → concept-b
       → concept-c
     ```
   - Exit 2 if bundle path invalid
7. Add `stats <bundle-path>` to `cli.py`:
   - Call `api.stats_bundle()`
   - Output format matches the user's provided example exactly:
     ```
     Bundle Statistics
       Bundle root:    <path>
       Total files:     <N>
       Concepts:        <N>
       No frontmatter:  <N>
       Total size:      <size>

       By Type:
         <Type>           <N>  <bar>

       Tags Cloud:
         <tag>      <N>  <bar>

       Links:            <N> total, <N> broken
     ```
   - Bar charts use `█` character, scaled to max 20 chars wide
   - Exit 2 if bundle path invalid
8. Write `tests/test_cli_remaining.py`:
   - Test `list` outputs correct tabular format
   - Test `show` outputs frontmatter and body
   - Test `index` creates/regenerates index.md files
   - Test `search` finds matching concepts, handles no matches
   - Test `graph` outputs adjacency list format
   - Test `stats` outputs all sections
   - Test all commands exit 2 on invalid bundle path
9. Run `just preflight` and fix any issues
10. Update `progress.json` via CLI:
    `uv run --no-sync craftsman agent update-task --prd .agents/changes/request/init --id 07 --status coded_not_reviewed --completed-at now`
11. Commit with a conventional commit message:
    `feat: add list, show, index, search, graph, stats CLI subcommands`

## Acceptance Criteria
- [ ] `list` outputs one concept per line with path, type, title
- [ ] `show` displays frontmatter as YAML followed by body
- [ ] `index` regenerates all index.md files and prints summary
- [ ] `search` outputs table of matching concepts
- [ ] `graph` outputs ASCII adjacency list of concept links
- [ ] `stats` outputs all metrics with bar charts matching the spec example
- [ ] All commands exit 2 on invalid bundle path
- [ ] `tests/test_cli_remaining.py` covers all six subcommands
- [ ] Project quality gate passes (complete and successful execution after all coding done)

## Testing Strategy
Follow TDD and the red-green cycle on this task: write a failing test first, confirm it fails, then implement minimal code to make it pass.
- **Test file**: `tests/test_cli_remaining.py`
- **Test cases**:
  - `list` on bundle with 3 concepts outputs 3 lines
  - `show` on existing concept outputs frontmatter YAML and body
  - `show` on missing concept exits 2
  - `index` on bundle creates missing index.md files
  - `search` with matching query returns results table
  - `search` with non-matching query prints "No matches found"
  - `graph` on bundle with cross-links outputs adjacency list
  - `graph` on bundle with no links outputs concept names only
  - `stats` outputs Bundle Statistics header
  - `stats` includes By Type section with bars
  - `stats` includes Tags Cloud section with bars
  - `stats` includes Links line
  - All commands exit 2 on nonexistent bundle path

## Notes
- For `stats` bar charts, scale bars so the largest count gets 20 `█` characters, and others are proportional
- For `graph`, only show outgoing links that point to other concepts within the same bundle
- For `search`, case-insensitive substring match across `title`, `description`, `type`, `tags`
- The `index` command should preserve existing descriptions in index.md entries when regenerating (adapted from `index_okf.py`)
