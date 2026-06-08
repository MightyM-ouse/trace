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
cat > "$ROOT/agent-context/project.json" <<JSON
{
  "name": "$NAME",
  "description": "$DESC",
  "roles": [$(echo "$ROLES" | awk -F, '{for(i=1;i<=NF;i++){gsub(/^ +| +$/,"",$i);printf "%s\"%s\"",(i>1?", ":""),$i}}')],
  "tech_stack": {
    "backend": "$BACKEND",
    "frontend": "$FRONTEND",
    "telemetry_store": "$DATABASE"
  },
  "initialized_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON

touch "$SENTINEL"

echo ""
echo "  ✓ Wrote agent-context/project.json"
echo "  ✓ Marked project initialized (.trace-initialized)"
echo ""
echo "  Next steps:"
echo "    make install   # backend + frontend deps"
echo "    make dev       # FastAPI :8000 + dashboard :5173"
echo ""
echo "  Then open http://localhost:5173 and start a Claude Code session in this repo."
echo ""
