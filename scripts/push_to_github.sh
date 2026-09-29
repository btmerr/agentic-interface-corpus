#!/usr/bin/env bash
# Commit corpus changes and push to origin/main. Idempotent if nothing changed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-Brian Merritt}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-btmorders@gmail.com}"
export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-$GIT_AUTHOR_NAME}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-$GIT_AUTHOR_EMAIL}"
git add -A
if git diff --cached --quiet; then
  echo "No corpus changes to push."
  exit 0
fi
DATE=$(date +%F)
git commit -m "Brief update ${DATE}: sync corpus items and archives"
git push origin HEAD:main
echo "Pushed to https://github.com/btmerr/agentic-interface-corpus"
