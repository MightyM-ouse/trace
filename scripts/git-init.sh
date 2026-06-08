#!/usr/bin/env bash
# One-time helper: initialize git, make the first commit, and push to GitHub.
# Run this on your own machine (not inside the sandbox).
#
#   bash scripts/git-init.sh <your-github-username> [public|private]
#
set -euo pipefail

USER_HANDLE="${1:-}"
VISIBILITY="${2:-public}"
REPO="trace"

if [ -z "$USER_HANDLE" ]; then
  read -r -p "Your GitHub username/org: " USER_HANDLE
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Fresh, clean repo.
rm -rf .git
git init -b main
git add -A
git commit -m "feat: scaffold TRACE v1 — TRACE methodology + FastAPI/React observability dashboard"

# Fill in CODEOWNERS with the real handle.
if [ -f .github/CODEOWNERS ]; then
  printf '* @%s\n' "$USER_HANDLE" >> .github/CODEOWNERS
  git add .github/CODEOWNERS && git commit -q -m "chore: set CODEOWNERS" || true
fi

if command -v gh >/dev/null 2>&1; then
  gh repo create "$REPO" --"$VISIBILITY" --source=. --remote=origin --push
  echo "Pushed via GitHub CLI."
else
  echo ""
  echo "GitHub CLI (gh) not found. Create an empty $VISIBILITY repo named '$REPO' at"
  echo "  https://github.com/new"
  echo "then run:"
  echo "  git remote add origin https://github.com/$USER_HANDLE/$REPO.git"
  echo "  git push -u origin main"
fi

echo ""
echo "Recommended next: enable branch protection on 'main'"
echo "  (Settings -> Branches -> Add rule -> require PR + review)."
echo "This operationalizes TRACE's human-approval gate."
