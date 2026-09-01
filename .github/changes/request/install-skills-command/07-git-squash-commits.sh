#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
COMMIT_MSG_FILE="${SCRIPT_DIR}/07-commit-msg.md"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ ! -f "$COMMIT_MSG_FILE" ]]; then
  printf 'error: commit message file not found: %s\n' "$COMMIT_MSG_FILE" >&2
  exit 1
fi

if grep -Eq '<!-- COST_PLACEHOLDER -->|CRAFTSMAN_COST_BLOCK_(START|END)|Craftsman-Cost-|Usage report captured in metrics\\.json\\.|Exact trailer tokens:|API session total:' "$COMMIT_MSG_FILE"; then
  printf 'error: commit message contains unresolved Craftsman cost markers: %s\n' \\
    "$COMMIT_MSG_FILE" >&2
  exit 1
fi

if grep -Eiq 'chore\\(wrap-up\\)|generate[[:space:]]+finalization[[:space:]]+artifacts|finalization[[:space:]]+bundle' "$COMMIT_MSG_FILE"; then
  printf 'error: implementation squash message contains artifact-only finalization wording: %s\n' \\
    "$COMMIT_MSG_FILE" >&2
  exit 1
fi

PRD_NAME="install-skills-command"
TRAILER_CHANGE_REQUEST_NAME="Craftsman-Change-Request-Name"
COMMIT_COUNT=0
while IFS=$'\t' read -r COMMIT_SHA MARKER; do
  [[ -n "$COMMIT_SHA" ]] || continue
  [[ "$MARKER" == "$PRD_NAME" ]] || break
  COMMIT_COUNT=$((COMMIT_COUNT + 1))
done < <(git log --first-parent \\
  --format='%H%x09%(trailers:key=Craftsman-Change-Request-Name,valueonly)' HEAD)

if [[ "$COMMIT_COUNT" -eq 0 ]]; then
  printf 'error: no exact %s: %s marker exists in first-parent history; '\\
    "$TRAILER_CHANGE_REQUEST_NAME" "$PRD_NAME" >&2
  printf 'amend the workflow commit with Craftsman metadata, then rerun finalization.\n' >&2
  exit 1
fi

printf 'squashing %d commit(s) for %s\n' "$COMMIT_COUNT" "$PRD_NAME"

# HEAD~COMMIT_COUNT is the parent of the oldest marked commit.
if REBASE_UPSTREAM="$(git rev-parse --verify "HEAD~${COMMIT_COUNT}" 2>/dev/null)"; then
  :
else
  REBASE_UPSTREAM="--root"
fi

# Keep the first commit and fold every later commit into it.
GIT_SEQUENCE_EDITOR='sed -i.bak "2,\\$s/^pick /fixup /"' \\
  git rebase -i --autosquash "$REBASE_UPSTREAM"
git commit --amend -s -F "$COMMIT_MSG_FILE"
