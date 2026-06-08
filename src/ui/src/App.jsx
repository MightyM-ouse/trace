import { useEffect, useRef, useState, useCallback } from "react";
import { getState, getRoi, getEvidence, subscribe } from "./api.js";

/* ---------- small presentational helpers ---------- */

function Approx() {
  return (
    <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300">
      approx
    </span>
  );
}

function Real() {
  return (
    <span className="ml-2 rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
      real
    </span>
  );
}

function Card({ children, className = "" }) {
  return (
    <div className={`rounded-xl border border-edge bg-panel p-4 ${className}`}>
      {children}
    </div>
  );
}

function Stat({ label, value, sub, tag }) {
  return (
    <Card>
      <div className="flex items-center text-xs uppercase tracking-wide text-slate-400">
        {label}
        {tag}
      </div>
      <div className="mt-1 font-mono text-2xl text-slate-100">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </Card>
  );
}

/* ---------- context-rot gauge (from status line remaining_percentage) ---------- */

function ContextGauge({ ctx }) {
  const rem = typeof ctx?.remaining_percentage === "number" ? ctx.remaining_percentage : null;
  let color = "#34d399", state = "healthy";
  if (rem !== null) {
    if (rem <= 15) { color = "#f87171"; state = "context-rot risk"; }
    else if (rem <= 30) { color = "#fbbf24"; state = "context low"; }
  }
  return (
    <Card className="col-span-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center text-xs uppercase tracking-wide text-slate-400">
          Context window <Real />
        </div>
        <div className="font-mono text-xs text-slate-400">{ctx?.model || "—"}</div>
      </div>
      {rem === null ? (
        <div className="mt-4 text-sm text-slate-500">
          Awaiting status-line data… start a Claude Code session in this repo.
        </div>
      ) : (
        <>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-mono text-4xl" style={{ color }}>{rem.toFixed(0)}%</span>
            <span className="text-sm text-slate-400">free before autocompact</span>
          </div>
          <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-ink">
            <div className="h-full rounded-full transition-all duration-500"
                 style={{ width: `${Math.max(2, rem)}%`, background: color }} />
          </div>
          <div className="mt-2 flex justify-between text-xs">
            <span className="capitalize" style={{ color }}>{state}</span>
            {ctx?.exceeds_200k_tokens && <span className="text-red-300">200k+ tokens</span>}
          </div>
        </>
      )}
    </Card>
  );
}

/* ---------- live event timeline ---------- */

const EVENT_STYLES = {
  PreToolUse: "bg-sky-500/15 text-sky-300",
  PostToolUse: "bg-emerald-500/15 text-emerald-300",
  PostToolUseFailure: "bg-red-500/15 text-red-300",
  UserPromptSubmit: "bg-violet-500/15 text-violet-300",
  PreCompact: "bg-amber-500/15 text-amber-300",
  SessionStart: "bg-slate-500/15 text-slate-300",
  Stop: "bg-slate-500/15 text-slate-300",
};

function timeOf(ts) {
  if (!ts) return "";
  try { return new Date(ts).toLocaleTimeString(); } catch { return ts; }
}

function Timeline({ events }) {
  return (
    <Card className="flex h-full flex-col">
      <div className="mb-3 flex items-center text-xs uppercase tracking-wide text-slate-400">
        Live tool timeline <Real />
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto pr-1" style={{ maxHeight: 460 }}>
        {events.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-500">
            No events yet. The hooks emit here as the agent works.
          </div>
        )}
        {events.map((e, i) => (
          <div key={i} className="flex items-center gap-3 rounded-lg border border-edge/60 bg-ink/40 px-3 py-2">
            <span className="w-16 shrink-0 font-mono text-[11px] text-slate-500">{timeOf(e.ts)}</span>
            <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${EVENT_STYLES[e.event] || "bg-slate-500/15 text-slate-300"}`}>
              {e.event}
            </span>
            <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-300" title={e.tool_intent || ""}>
              {e.tool_intent || e.tool_name || "—"}
            </span>
            {typeof e.total_tokens === "number" && (
              <span className="shrink-0 font-mono text-[11px] text-amber-300">{e.total_tokens.toLocaleString()} tok</span>
            )}
            {typeof e.duration_ms === "number" && (
              <span className="shrink-0 font-mono text-[11px] text-slate-400">{Math.round(e.duration_ms)} ms</span>
            )}
            <span className={`shrink-0 text-xs ${e.success === false ? "text-red-400" : "text-emerald-400"}`}>
              {e.success === false ? "✕" : "✓"}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ---------- ROI + evidence side column ---------- */

function fmtMs(ms) {
  if (typeof ms !== "number") return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)} s`;
  return `${(ms / 60000).toFixed(1)} min`;
}

function RoiPanel({ roi }) {
  if (!roi) return null;
  return (
    <Card>
      <div className="flex items-center text-xs uppercase tracking-wide text-slate-400">
        ROI <Approx />
      </div>
      <div className="mt-3 space-y-2 text-sm">
        <Row k="Subagent tokens" v={roi.subagent_tokens?.toLocaleString() ?? "—"} approx />
        <Row k="Session cost" v={roi.session_cost_usd != null ? `$${roi.session_cost_usd}` : "—"} approx />
        <Row k="Session duration" v={fmtMs(roi.session_duration_ms)} approx />
        <Row k="Human iterations" v={roi.human_iterations} />
        <Row k="Tool calls" v={roi.tool_calls} />
        <Row k="Tool time" v={fmtMs(roi.total_tool_duration_ms)} />
      </div>
      <p className="mt-3 text-[11px] leading-snug text-slate-500">{roi.note}</p>
    </Card>
  );
}

function Row({ k, v, approx }) {
  return (
    <div className="flex items-center justify-between border-b border-edge/40 pb-1">
      <span className="text-slate-400">
        {k}{approx && <span className="ml-1 text-amber-400/70">~</span>}
      </span>
      <span className="font-mono text-slate-200">{v}</span>
    </div>
  );
}

function EvidencePanel({ evidence }) {
  const items = evidence?.review_packages || [];
  return (
    <Card>
      <div className="flex items-center text-xs uppercase tracking-wide text-slate-400">
        Evidence <Real />
      </div>
      {items.length === 0 ? (
        <div className="mt-3 text-sm text-slate-500">
          No review-packages yet. The Validator role writes portable proof here.
        </div>
      ) : (
        <ul className="mt-3 space-y-1">
          {items.map((it) => (
            <li key={it.name} className="flex items-center justify-between font-mono text-xs text-slate-300">
              <span className="truncate">{it.is_dir ? "📁" : "📦"} {it.name}</span>
              {it.size_bytes != null && <span className="text-slate-500">{(it.size_bytes / 1024).toFixed(1)} kb</span>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/* ---------- app shell ---------- */

const STATUS_LABEL = {
  live: "live", reconnecting: "reconnecting…", error: "offline", idle: "connecting…",
};
const STATUS_COLOR = {
  live: "bg-emerald-400", reconnecting: "bg-amber-400", error: "bg-red-400", idle: "bg-slate-500",
};

export default function App() {
  const [state, setState] = useState(null);
  const [roi, setRoi] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const debounce = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const [s, r, e] = await Promise.all([getState(), getRoi(), getEvidence()]);
      setState(s); setRoi(r); setEvidence(e); setError(null);
    } catch (err) {
      setError("Telemetry server not reachable on :8000 — run `make server`.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const poll = setInterval(refresh, 5000);
    const unsub = subscribe(
      () => {
        if (debounce.current) clearTimeout(debounce.current);
        debounce.current = setTimeout(refresh, 350);
      },
      (st) => setStatus(st)
    );
    return () => { clearInterval(poll); unsub(); };
  }, [refresh]);

  const c = state?.counters || {};
  const events = state?.recent_events ? [...state.recent_events].reverse() : [];

  return (
    <div className="min-h-screen bg-ink px-6 py-5">
      <header className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="font-mono text-xl font-bold tracking-widest text-slate-100">
            TRACE<span className="text-emerald-400">.</span>
          </h1>
          <p className="text-xs text-slate-500">Template · Route · Assign · Check · Evidence — live observability</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-xs text-slate-500">
            <div>session</div>
            <div className="font-mono text-slate-300">{c.active_session ? c.active_session.slice(0, 8) : "—"}</div>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-edge bg-panel px-3 py-1.5">
            <span className={`h-2 w-2 rounded-full ${STATUS_COLOR[status]} ${status === "live" ? "animate-pulse" : ""}`} />
            <span className="text-xs text-slate-300">{STATUS_LABEL[status]}</span>
          </div>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* top row: gauge + key stats */}
      <div className="mb-4 grid grid-cols-2 gap-4 md:grid-cols-6">
        <ContextGauge ctx={state?.context} />
        <Stat label="Iterations" tag={<Real />} value={c.human_iterations ?? "—"} sub="human prompts" />
        <Stat label="Tool calls" tag={<Real />} value={c.tool_calls ?? "—"} sub={`${c.failures ?? 0} failed`} />
        <Stat label="Subagent tokens" tag={<Approx />} value={(c.subagent_tokens ?? 0).toLocaleString()} sub="from Agent runs" />
        <Stat label="Tool time" tag={<Real />} value={fmtMs(c.total_tool_duration_ms)} sub="execution only" />
      </div>

      {/* main grid: timeline + side column */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Timeline events={events} />
        </div>
        <div className="space-y-4">
          <RoiPanel roi={roi} />
          <EvidencePanel evidence={evidence} />
        </div>
      </div>

      <footer className="mt-5 text-center text-[11px] text-slate-600">
        <Real /> = measured & committed to git · <Approx /> = estimated (enable OpenTelemetry for accurate token/cost)
      </footer>
    </div>
  );
}
