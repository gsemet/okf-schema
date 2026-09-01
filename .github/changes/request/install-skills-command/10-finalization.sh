#!/usr/bin/env bash
# Generated manual finalization commands for install-skills-command.

#  1. CAPTURE & INJECT COSTS (do this BEFORE squash) 
cd /Users/az02065/Projects/DevTools/okf-schema

set -e

craftsman agent capture-usage \\
  --prd /Users/az02065/Projects/DevTools/okf-schema/.github/changes/request/install-skills-command

craftsman agent inject-cost \\
  --prd /Users/az02065/Projects/DevTools/okf-schema/.github/changes/request/install-skills-command

git add . && git commit --amend --no-edit

#  2. SQUASH ALL COMMITS TO TAKE 'OWNERSHIP' OF THE IMPLEMENTATION 
# This means the user takes full accountability for the implementation,
# 'as if' he/she wrote it all.
bash /Users/az02065/Projects/DevTools/okf-schema/.github/changes/request/install-skills-command/07-git-squash-commits.sh

#  3. AMEND SQUASH COMMIT WITH SESSION TRAILERS 
# Degraded warn-only: missing session context emits a warning and exits 0.
craftsman agent amend-commit --commit-type Finalization \\
  --prd /Users/az02065/Projects/DevTools/okf-schema/.github/changes/request/install-skills-command --session-id 3cca5fb2-e390-422c-8d83-6f8fd02e5bd4

#  4. ARCHIVE THE PRD 
craftsman agent archive \\
  --prd /Users/az02065/Projects/DevTools/okf-schema/.github/changes/request/install-skills-command/ \\
  --project-root /Users/az02065/Projects/DevTools/okf-schema

#  5. RESOLVE ARCHIVED PATH 
ARCHIVED_PATH=$(craftsman agent get-archive-folder \\
  --prd-name install-skills-command \\
  --project-root /Users/az02065/Projects/DevTools/okf-schema \\
  | uv run python -c "import sys,json; print(json.load(sys.stdin)['archive_path'])")

#  6. AMEND COMMIT WITH ARCHIVED PRD 
git add . && git commit --amend --no-edit

#  7. PUSH & CREATE MR 
git push origin HEAD --force \\
  -o merge_request.create \\
  -o merge_request.target=master \\
  -o "merge_request.description=$(awk '{printf "%s\\\\n", $0}' \\
       "${ARCHIVED_PATH}/08-gitlab-mr-description.md")"
