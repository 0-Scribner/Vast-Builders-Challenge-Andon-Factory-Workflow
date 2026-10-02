#!/usr/bin/env bash
# Push HEAD to every configured remote. Fail closed. Never push clips or secrets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

refuse() {
  echo "push_both: refuse: $*" >&2
  exit 1
}

# Staged + unstaged paths about to be committed are not this script's job;
# refuse if the index currently contains forbidden files.
if git diff --cached --name-only | grep -E '\.(mp4|mov|webm|mkv|avi|zip)$' >/dev/null; then
  refuse "staged video/zip — clips never go in git"
fi
if git diff --cached --name-only | grep -E '(^|/)\.env$|\.config$' | grep -v 'config.example' >/dev/null; then
  refuse "staged secrets (.env or *.config)"
fi

HEAD="$(git rev-parse HEAD)"
pushed=0
failed=0

push_one() {
  local name="$1"
  git remote get-url "$name" >/dev/null 2>&1 || return 0
  echo "push_both: pushing $HEAD → $name $(git rev-parse --abbrev-ref HEAD)"
  if git push -u "$name" HEAD; then
    pushed=$((pushed + 1))
  else
    echo "push_both: $name push failed" >&2
    failed=$((failed + 1))
  fi
}

push_one origin
push_one github

if [[ "$failed" -gt 0 ]]; then
  refuse "one or more remotes failed"
fi
if [[ "$pushed" -eq 0 ]]; then
  refuse "no remotes (need origin and/or github)"
fi
echo "push_both: ok ($pushed remote(s))"
