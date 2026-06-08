#!/usr/bin/env bash
# TRACE status line wrapper. Session JSON arrives on stdin and is passed through
# to statusline.py (which renders the line and snapshots context for the dashboard).
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
exec python3 "$PROJECT_DIR/.claude/hooks/statusline.py"
