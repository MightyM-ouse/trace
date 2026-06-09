"""Incremental ingestion of the JSONL write-ahead log into SQLite.

The hook appends every event to agent-logs/events.jsonl (durable, even when the
server is offline). This module replays only the *new, complete* lines since last
time, using a byte offset stored in the `meta` table — so the projection is
exactly-once and survives restarts.

Partial trailing lines (a line still being written, with no terminating newline)
are intentionally left unconsumed: the offset only advances past the last
newline, so an in-flight event is picked up once it's fully written.
"""
import json

import db
from paths import jsonl_path


def ingest_new() -> list[dict]:
    """Read unprocessed, newline-terminated lines from the JSONL log, insert
    them, and advance the offset. Returns the newly ingested records."""
    path = jsonl_path()
    if not path.exists():
        return []

    new_records: list[dict] = []
    with db.connect() as c:
        offset = int(db.get_meta(c, "jsonl_offset", "0"))
        size = path.stat().st_size
        if size < offset:  # log was truncated/rotated — restart from 0
            offset = 0

        with open(path, "rb") as fh:
            fh.seek(offset)
            chunk = fh.read()  # bytes from offset to current EOF

        # Only process up to the last newline; keep any partial tail for next time.
        last_nl = chunk.rfind(b"\n")
        if last_nl == -1:
            return []  # no complete line yet
        complete = chunk[: last_nl + 1]

        for raw in complete.split(b"\n"):
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            db.insert_event(c, rec)
            new_records.append(rec)

        db.set_meta(c, "jsonl_offset", str(offset + len(complete)))
    return new_records
