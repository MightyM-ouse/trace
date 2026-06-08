// Thin client for the TRACE telemetry server. All calls go through /api,
// proxied to the FastAPI server in dev (see vite.config.js).

export async function getState() {
  const r = await fetch("/api/state");
  if (!r.ok) throw new Error(`state ${r.status}`);
  return r.json();
}

export async function getRoi() {
  const r = await fetch("/api/roi");
  if (!r.ok) throw new Error(`roi ${r.status}`);
  return r.json();
}

export async function getEvidence() {
  const r = await fetch("/api/evidence");
  if (!r.ok) throw new Error(`evidence ${r.status}`);
  return r.json();
}

// Subscribe to the live SSE feed. Returns an unsubscribe function.
export function subscribe(onEvent, onStatus) {
  let es;
  try {
    es = new EventSource("/api/stream");
  } catch {
    onStatus?.("error");
    return () => {};
  }
  es.onopen = () => onStatus?.("live");
  es.onmessage = (e) => {
    if (!e.data) return;
    try {
      const rec = JSON.parse(e.data);
      if (rec && Object.keys(rec).length) onEvent(rec);
    } catch {
      /* ignore keep-alives */
    }
  };
  es.onerror = () => onStatus?.("reconnecting");
  return () => es.close();
}
