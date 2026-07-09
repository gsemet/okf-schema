# Release Notes Generator (Git Diff Based)

Generate **end-user friendly** release notes by analyzing actual code changes between releases.
No scripts required — uses git commands to understand what changed and why it matters.

The output is meant to be **copy-pasted into a GitHub Release** (or similar).

---

## Quick Start

Provide your repository and range:

```
Generate release notes from v1.0.0 to v1.1.0 in /path/to/repo
```

Or reference the last release:

```
What changed since the last release tag?
```

---

## What It Does

1. **Reads actual diffs** — examines code changes, not just commit messages
2. **Interprets for end-users** — no technical jargon, functions, or variable names
3. **Categorizes intelligently** — Features, Enhancements, Bug Fixes, Breaking Changes
4. **Adds concrete examples** — shows what users see or can do after the change
5. **Links to public docs** — points to published documentation, not repo paths
6. **Consolidates related changes** — groups related diffs, eliminates back-and-forth noise
7. **Outputs clean markdown** — ready to paste into a GitHub Release note

---

## Input

Accept either:

- **Natural language**: "Show release notes from v1.2.0 to v1.3.0"
- **Range spec**: `from_tag=v1.2.0 to_tag=v1.3.0 repo_path=/path/to/repo`
- **Last release**: `since_tag=v1.2.0` (everything from tag to HEAD)

Required:
- Repository path (optional: defaults to current directory)
- Range: `from_tag` + `to_tag`, OR `since_tag`, OR `last_n_commits`

---

## Analysis Process

### Step 1: Collect Commits
```bash
git log v1.0.0..v1.1.0 --oneline --no-merges
```
Gather all commits in the specified range with their messages.

### Step 2: Examine Diffs
```bash
git diff v1.0.0..v1.1.0 -- src/
```
Read actual code changes line-by-line to understand what changed.

### Step 3: Interpret Changes

Translate technical changes into user impact:

| Code Change | User Impact |
|-------------|------------|
| `+ const darkMode = true` in settings | "Dark mode toggle now available in settings" |
| Deleted login retry logic | "Removed automatic retry on login timeout" |
| `+ validateEmail()` function | "Email validation improved during signup" |
| Updated database schema version | "Database schema upgraded (run migration)" |
| Added 10+ calls to cache layer | "Improved performance on large operations" |
| Removed old CSV export code | "CSV export removed; use Excel or PDF instead" |

**Key: Focus on the user's experience, not the code implementation.**

### Step 4: Identify Breaking Changes

Breaking changes come from:
- **Commit messages** containing: "BREAKING", "Breaking", "!:"
- **Diffs showing**: removed public APIs, changed file formats, data migrations
- **Config changes**: renamed settings, changed defaults

### Step 5: Consolidate
- If a feature was added then removed → don't mention it
- If something changed multiple times → only note the final state
- If multiple commits fix the same issue → merge into one bullet

### Step 6: Categorize & Format

Organize changes into buckets. **Only include sections that have content.** Omit empty sections entirely.

```markdown
# Release Notes - v1.1.0

## New Features
- Added dark mode toggle in settings
- New PDF export option

## Enhancements
- Improved search performance (now supports partial matches)
- Faster file opening for large documents

## Bug Fixes
- Fixed login failures on slow connections
- Resolved crash when uploading 10MB+ files

## Breaking Changes
- Database schema updated — run migration before upgrading
- CSV export removed; use Excel or PDF instead

## Examples
- Dark mode can be enabled in Settings → Appearance → Theme
- CSV export is no longer available; choose Excel or PDF from Export menu

## Documentation
- [Dark mode guide](https://docs.example.com/settings#dark-mode)
- [Migration notes](https://docs.example.com/upgrade#database)
```

---

## Workflow for Agent

1. **Parse input** — extract `from_tag`, `to_tag`, `repo_path`, and optional filters
2. **Discover public docs URL** — inspect `README.md`, `pyproject.toml`, `mkdocs.yml`, `docs/conf.py`, or `.readthedocs.yml` for the published documentation URL. Prefer ReadTheDocs, GitHub Pages, or the project's public docs site. If none is found, omit doc links.
3. **Fetch commits** — run `git log` with range, collect hashes & messages
4. **Read diffs per file** — `git show <hash>` for each commit, examine changed files
5. **Interpret impact** — what does each change mean to users?
6. **Detect breaking changes** — scan for BREAKING markers, API removals, schema changes
7. **Group by category** — assign each change to **New Features**, **Enhancements**, **Bug Fixes**, **Breaking Changes**, **Examples**, or **Documentation**
8. **Build examples** — for each user-facing change, look at README, docs, tests, or CLI help in the diff and add a short "what the user gets" example when it clarifies the change
9. **Consolidate** — merge related items, remove duplicates and flip-flops
10. **Format markdown** — generate clean bullet points with proper headings
11. **Omit empty sections** — do not print a section if it has no bullets
12. **Use public docs links** — every Documentation bullet and every feature/enhancement docs reference must use the public URL with a fragment identifier, not a repo-relative path

---

## Output Format

**Clean markdown** for a GitHub Release:

```markdown
# Release Notes - v1.1.0

## New Features
- Added dark mode toggle in settings
- New PDF export option

## Enhancements
- Improved search performance (supports partial matches)
- Faster file opening for large documents

## Bug Fixes
- Fixed login failures on slow connections
- Resolved crash when uploading 10MB+ files

## Breaking Changes
- Database schema updated — run migration before upgrading

## Examples
- Enable dark mode from Settings → Appearance → Theme
- Export a report as PDF from the File → Export menu

## Documentation
- [Dark mode guide](https://docs.example.com/settings#dark-mode)
- [Upgrade instructions](https://docs.example.com/upgrade#database)
```

**Key Rules:**
- One line per bullet point
- No sub-bullets or elaborate descriptions
- User impact only (not implementation details)
- Use public documentation URLs; never use repo-relative paths like `docs/...` or `README.md`
- Use fragment identifiers (`#section-name`) to point to specific docs sections
- Add an **Examples** section when the diff shows a CLI command, API call, config snippet, or before/after behavior
- Add a **Documentation** section when docs were added or updated, linking to the published page
- Multiple links OK if they point to different topics
- Omit any section that has no bullets
- Do not add a "Notes", "Miscellaneous", or "Other" catch-all section

---

## How to Use This Skill in a Session

**User Query:**
```
Generate release notes from v2.1.0 to v2.2.0 for /path/to/my-app
```

**Agent Workflow:**
1. Navigate to repo: `cd /path/to/my-app`
2. Fetch commits: `git log v2.1.0..v2.2.0 --oneline --no-merges`
3. For each commit, examine changes: `git show <hash>`
4. Interpret: What's the user impact? (not the code details)
5. Categorize: Feature? Bug fix? Breaking change?
6. Consolidate: Merge similar items
7. Format: Clean markdown with categories
8. Output: Save to RELEASE_NOTES.md

---

## Best Practices

✅ **Do:**
- Read actual diffs to understand changes
- Use end-user language ("improved performance" not "optimized O(n) loop")
- Include breaking changes prominently
- Group related changes
- Add concrete examples drawn from README, docs, tests, or CLI help in the diff
- Link to the project's public documentation site (ReadTheDocs, GitHub Pages, etc.)
- Omit empty sections

❌ **Don't:**
- Copy commit messages verbatim
- Include function/variable names
- Mention internal refactors users won't notice
- Include dependency bumps or build changes unless they are user-visible
- Include secrets, passwords, or internal URLs
- Use repo-relative paths like `docs/source/how-to/...` or `README.md`
- Make up changes not shown in diffs

---

## Common Patterns

**Performance improvements:**
> "Improved search speed when filtering 1000+ records"

**New integrations:**
> "Added support for OAuth login via GitHub"

**Data format changes:**
> "Settings file now uses JSON instead of YAML (auto-converted on first run)"

**Removed features:**
> "Removed IE 11 support to modernize codebase"

**API changes:**
> "Changed user profile endpoint response format (see migration guide)"

---

## Limitations

- Requires git repository with proper tags
- Complex changes may need human interpretation
- Very large diffs (1000+ files) summarized by file count
- Works best with semantic versioning (v1.0.0 format)
- Needs meaningful commit messages for best results
