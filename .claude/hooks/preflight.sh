#!/usr/bin/env bash
# TRACE Check phase — preflight stop-gate.
# Verifies the environment is ready and the task is ratified before the agent
# burns tokens building. Exit 0 = proceed; non-zero = STOP (missing context).
set -uo pipefail
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
fail=0

echo "TRACE preflight:"
command -v python3 >/dev/null 2>&1 && echo "  [ok] python3" || { echo "  [STOP] python3 missing"; fail=1; }
command -v node    >/dev/null 2>&1 && echo "  [ok] node"    || echo "  [warn] node missing (frontend won't run)"
[ -f "$PROJECT_DIR/TECH_STACK.md" ] && echo "  [ok] TECH_STACK.md present" || { echo "  [STOP] TECH_STACK.md missing"; fail=1; }
[ -f "$PROJECT_DIR/PROJECT_STATUS_AND_NEXT_STEPS.md" ] && echo "  [ok] status file present" || { echo "  [STOP] status file missing"; fail=1; }

if grep -q "\[ \]" "$PROJECT_DIR/PROJECT_STATUS_AND_NEXT_STEPS.md" 2>/dev/null; then
  echo "  [ok] ratified task(s) found in queue"
else
  echo "  [warn] no open task in the queue — confirm the task is ratified before building"
fi

if [ "$fail" -ne 0 ]; then
  echo "PREFLIGHT FAILED — resolve the [STOP] items before executing."
  exit 1
fi
echo "PREFLIGHT PASSED."
exit 0
