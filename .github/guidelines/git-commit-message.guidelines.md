---
name: Git Commit Message Guideline 2.2
description: Guidelines for writing conventional commits that communicate intent and user impact
metadata:
  owner: Gaetan Semet <gaetan.semet@ampere.cars>
  guideline-id: 566d8c89-0f00-4390-a64e-caa3dc425267
  keywords: [git, commits, conventional-commits, version-control, developer-workflow]
---

# Git Commit Message Guideline

Write a user-impact-focused Conventional Commit. State what users gain or
which limitation is resolved, not implementation details.

## Rules

1. Format the subject as `type(scope): description`; `scope` is optional. Use
   only `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `ci`,
   `chore`, `build`, or `revert`. Keep it at most 71 characters.
2. Apply limits to the final physical Git lines, not visual wrapping. Body
   lines must be at most 79 characters; 80 is invalid. Keep every trailer on
   one unwrapped, unindented line. Blank lines are exempt. Unbreakable URLs,
   hashes, and similar strings may exceed 79 characters only on their own
   line. A workflow may be stricter, never looser or conflicting.
3. Prefer `git commit -F <message-file>`. With `-m`, the first value is the
   subject and each later value is a paragraph separated by a blank line; use
   one value per paragraph, never per wrapped line.
4. Body text must describe user benefits, required user knowledge, or the
   resolved limitation. Do not describe refactoring, internal functions,
   changed files, methods, tests, or the number of checks run. Rewrite any
   diff summary so it says what users can now do or what limitation was fixed.
5. For breaking changes, put `!` in the subject and include a
   `BREAKING CHANGE:` section with explicit migration steps.
6. Do not add `Signed-off-by` unless a human requests it. Do not use
   `git commit -s` or add it implicitly. If requested, add and verify it
   deliberately. A human may use it to indicate ownership of AI-generated
   content.
7. If AI generated most of the message, append this body trailer:
   `Assisted-by: MODEL_PROVIDER:MODEL_NAME FRAMEWORK`. Use the underlying
   model family/vendor, never the interface or IDE; use the specific model
   version; and include the optional SDD framework only when it drove the
   implementation. Determine provider and model from current harness/session
   metadata. For Craftsman, use `Craftsman-Session-Main-Model` or its
   equivalent usage record. Never copy attribution or guess. If it cannot be
   verified, stop and obtain it.

For Craftsman workflow commits, do not hand-author session or PRD-scoping
trailers. The centralized amendment command owns exactly:
`Craftsman-Change-Request-Name`, `Craftsman-Session-ID`,
`Craftsman-Session-Main-Model`, `Craftsman-Session-Acc-Usage`, and
`Craftsman-Session-Acc-AIC`. Missing session context is warn-only, but the PRD
marker remains required to scope current history. Former session-trailer
vocabulary is not a compatibility alias.

Valid attribution uses forms such as `Assisted-by: Claude:Sonnet-4.6`,
`Assisted-by: Claude:Sonnet-4.6 Craftsman`, and `Assisted-by: GPT:4o`.
`GitHub Copilot`, `Cursor`, and `AI` are invalid attribution values.

## Positive example

```text
fix(auth): show which credential field is invalid

Users can identify the invalid field without retrying valid credentials.
```
