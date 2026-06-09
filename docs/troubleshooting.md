# Troubleshooting

## Requirements
- **Python 3.11+** (the backend uses 3.11 syntax). Check: `python3 --version`.
- **Node 20+** (Vite 5 / Rollup 4). Check: `node --version`.

## `python3 -m pytest` says "No module named pytest"
Install the backend dev dependencies (pytest is included):
```bash
pip install -r src/server/requirements.txt
# or, isolated:
python3 -m venv .venv && source .venv/bin/activate && pip install -r src/server/requirements.txt
```
Then run from the repo root: `python3 -m pytest -q`.

## `npm run build` fails with a Rollup native module error (e.g. `@rollup/rollup-darwin-arm64`)
This is a known npm bug with optional platform dependencies (npm/cli#4828): a
`package-lock.json` generated on one OS can omit the native Rollup binary for yours.
TRACE intentionally does **not** commit a platform-specific lockfile. Fix with a clean install:
```bash
cd src/ui
rm -rf node_modules package-lock.json
npm install
npm run build
```

## `npx eslint src` complains about a missing plugin
Install dependencies first — `eslint-plugin-react` and `eslint-plugin-react-hooks`
are declared in `src/ui/package.json`:
```bash
cd src/ui && npm install && npm run lint
```

## Server logs `disk I/O error` from SQLite
SQLite WAL mode isn't supported on some network/overlay filesystems. The server falls
back to rollback-journal mode automatically; if it still fails, put the repo on a local disk.

## Ports already in use
The server uses `127.0.0.1:8000` and the dashboard `localhost:5173`. Override with
`uvicorn ... --port <n>` and Vite's `--port <n>` (update the proxy target in `vite.config.js`).

## Dashboard shows "Telemetry server not reachable on :8000"
Start the server (`make server`) — the dashboard polls `/api/state`. The two run together with `make dev`.
