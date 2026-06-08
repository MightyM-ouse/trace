"""Incremental ingestion of the JSONL write-ahead log into SQLite.

The hook appends every event to agent-logs/events.jsonl (durable, even when the
server is offline). This module replays only the *new* bytes since last time,
using a byte offset stored in the `meta` table — so the projection is exactly
once and survives restarts.
"""
import json

from paths import jsonl_path
import db


def ingest_new() -> list[dict]:
    """Read unprocessed lines from the JSONL log, insert them, advance offset.

    Returns the list of newly ingested records (for SSE broadcast).
    """
    path = jsonl_path()
    if not path.exists():
        return []

    new_records: list[dict] = []
    with db.connect() as c:
        offset = int(db.get_meta(c, "jsonl_offset", "0"))
        size = path.stat().st_size
        if size < offset:  # log was truncated/rotated — restart from 0
            offset = 0
        with open(path, "r", encoding="utf-8") as fh:
            fh.seek(offset)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                db.insert_event(c, rec)
                new_records.append(rec)
            new_offset = fh.tell()
        set_offset = max(new_offset, offset)
        db.set_meta(c, "jsonl_offset", str(set_offset))
    return new_records
