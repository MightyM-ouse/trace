#!/usr/bin/env bash
# TRACE interactive setup wizard.
#
# Run by a HUMAN in a terminal:  npm run init   (or  make init)
# NOT wired to the SessionStart hook — a hook's stdin is the event JSON, not a
# keyboard, so it cannot run an interactive prompt. This script is the supported
# onboarding path.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SENTINEL="$ROOT/.trace-initialized"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   TRACE · project initialization     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

if [ -f "$SENTINEL" ]; then
  read -r -p "TRACE is already initialized. Re-run the wizard? [y/N] " again
  case "${again:-N}" in
    y|Y) : ;;
    *) echo "Nothing to do."; exit 0 ;;
  esac
fi

ask() {  # ask <prompt> <default> -> echoes answer
  local prompt="$1" def="$2" ans
  read -r -p "$prompt [$def]: " ans
  echo "${ans:-$def}"
}

NAME=$(ask "Project name" "trace-app")
DESC=$(ask "Short description" "An AI-assisted application built with the TRACE methodology")
ROLES=$(ask "Agent roles (comma-separated)" "Planner,Builder,Validator")
BACKEND=$(ask "Backend stack" "FastAPI (Python 3.11+)")
FRONTEND=$(ask "Frontend stack" "React + Vite + Tailwind")
DATABASE=$(ask "Telemetry store" "SQLite (local) + GitHub for evidence")

mkdir -p "$ROOT/agent-context"

# Build the JSON in Python so quotes, backslashes, or odd input can't corrupt it,
# and validate it before we declare success.
if ! TRACE_NAME="$NAME" TRACE_DESC="$DESC" TRACE_ROLES="$ROLES" \
     TRACE_BACKEND="$BACKEND" TRACE_FRONTEND="$FRONTEND" TRACE_DB="$DATABASE" \
     python3 - "$ROOT/agent-context/project.json" <<'PY'
import datetime, json, os, sys

roles = [r.strip() for r in os.environ.get("TRACE_ROLES", "").split(",") if r.strip()]
data = {
    "name": os.environ.get("TRACE_NAME", ""),
    "description": os.environ.get("TRACE_DESC", ""),
    "roles": roles,
    "tech_stack": {
        "backend": os.environ.get("TRACE_BACKEND", ""),
        "frontend": os.environ.get("TRACE_FRONTEND", ""),
        "telemetry_store": os.environ.get("TRACE_DB", ""),
    },
    "initialized_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
out = sys.argv[1]
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
with open(out, encoding="utf-8") as f:
    json.load(f)  # validate round-trip
PY
then
  echo "  ✗ Failed to write a valid project.json — aborting." >&2
  exit 1
fi

touch "$SENTINEL"

echo ""
echo "  ✓ Wrote and validated agent-context/project.json"
echo "  ✓ Marked project initialized (.trace-initialized)"
echo ""
echo "  Next steps:"
echo "    make install   # backend + frontend deps"
echo "    make dev       # FastAPI :8000 + dashboard :5173"
echo ""
echo "  Then open http://localhost:5173 and start a Claude Code session in this repo."
echo ""
