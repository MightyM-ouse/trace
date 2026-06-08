# TRACE — AI Architecture Review

*Review mode only. No implementation, no scaffolding. Reviewed against the three config files (`CLAUDE.md`, `PROJECT_ARCHITECTURE.md`, `.claude/settings.json`), the 21-page Architecture Blueprint, and the official Claude Code hooks / monitoring / statusline specifications. Date: 2026-06-08.*

---

## Verdict

The **conceptual model is strong**. TRACE's instincts — repository as source of truth, role-bounded agents, preflight gates, evidence packages, human approval — are well-aligned with how reliable agent systems are actually built, and several specific choices (HTTP hooks to a local server, per-role context indexes, ADRs) are sound.

The **telemetry and enforcement layer is where the architecture is currently fragile**. Three things matter most:

1. **As written, none of the hooks fire** — the `settings.json` uses the wrong structure (Blocker #1).
2. **Token telemetry only exists if your agents are real Claude Code subagents.** If Planner/Builder/Validator are just prompt personas in one session, the dashboard will show *zero* token data. This is the single biggest architectural fork.
3. **The most accurate token/cost/time data does not come from hooks at all** — it comes from OpenTelemetry. Hooks give you a live *intent timeline*; OTel gives you the *accurate ledger*. You want both, used for different jobs.

Everything below is organized by your four review questions, then cross-cutting findings, then a prioritized fix list and the decisions I need from you.

---

## 1. Telemetry & Hooks

### What's right
- **HTTP hooks are real and a good fit.** `type: "http"` is a valid handler; Claude Code POSTs the event JSON to your URL with `Content-Type: application/json`. Crucially, **non-2xx responses, connection failures, and timeouts are non-blocking** — if your FastAPI server is down, the agent keeps working. That's the correct resilience property for an observability sidecar.
- **Subagent completions genuinely carry ROI data.** On a completed `Agent` tool call, `PostToolUse.tool_response` includes `totalTokens`, `totalDurationMs`, `totalToolUseCount`, and a `usage` breakdown (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`). Your plan to parse these is viable.

### Critical issues

**1.1 — `settings.json` is structurally invalid (Blocker).**
Claude Code requires a two-level structure: each event maps to an array of **matcher groups**, and each matcher group contains an inner **`hooks`** array of handlers. Your file flattens this — it places `{ "type": ..., "command": ..., "matcher": ... }` directly in the event array with no inner `hooks` wrapper. The parser will not recognize these, so **today none of your hooks run**. Correct shape:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          { "type": "http", "url": "http://localhost:8000/api/telemetry/hook" }
        ]
      }
    ]
  }
}
```
Note the `matcher: "Agent"` — for ROI you specifically want to fire on subagent completions (see 1.2). Your `SessionStart` entry has the same flattening problem, and its `"command": "bash", "args": [...]` form is otherwise valid but must live inside an inner `hooks` array.

**1.2 — Token telemetry depends entirely on the agent model.**
`totalTokens`/`totalDurationMs` appear **only** on `Agent`-tool (subagent) completions. They do **not** appear for standard tools, and they do **not** capture the main/orchestrator thread's own token consumption. Consequences:
- If Planner/Builder/Validator are implemented as **real subagents** (spawned via the Agent tool, or `.claude/agents/*.md`), you get per-role token + duration data. Good.
- If they are **prompt personas in a single session**, `PostToolUse` will never surface a token count, and the dashboard's "token burn" panel stays empty.
- Even in the subagent case, the **orchestrator's own tokens are invisible** to PostToolUse, so "exact token burn / exact ROI" is an overstatement. Treat hook-derived tokens as *per-subagent*, not *whole-session*.

**1.3 — Standard tools give duration, not tokens.**
Standard tools (Bash/Edit/Write) expose a per-tool `duration_ms` (execution time, excluding time paused on human permission) — consistent with the `claude_code.tool.execution` span. Good for a per-tool timing/timeline, but it carries **no token data**. Background subagents (`run_in_background: true`) return `status: "async_launched"` with no usage fields at all — your dashboard must handle that case or it will mis-count.

**1.4 — You asked about a `PreToolUse` security gate — yes, add it, with caveats.**
`PreToolUse` can inspect intent and block (exit 2 / `permissionDecision: "deny"`). It also supports an `if` permission-rule filter (e.g. `Bash(git push *)`, `Edit(*.ts)`). **But hook `if`-matching is best-effort and "fails open"** on unparseable commands. For *hard* boundaries (the whole point of "Assign"), use Claude Code's **permission system** (allow/deny rules), and use `PreToolUse` hooks for the *observability* side (telling the UI "agent is about to run X"). Don't rely on a hook alone as a security control.

**1.5 — "Effort saved / human iterations" is modeled, not measured.**
No hook emits "effort saved." The honest proxy is counting `UserPromptSubmit` events (human iterations) and pairing that with token/time deltas vs. a baseline. Label this clearly in the UI as an *estimate*, or it will erode trust in the otherwise-real numbers.

### Biggest missed opportunity: OpenTelemetry
Claude Code has **native OTel export** (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, OTLP/Prometheus exporters). It emits exactly the metrics TRACE wants ROI from, with no parsing and full session coverage:
- `claude_code.token.usage` (tokens), `claude_code.cost.usage` (USD), `claude_code.active_time.total` (seconds)
- `claude_code.session.count`, `claude_code.lines_of_code.count`, `claude_code.commit.count`, `claude_code.pull_request.count`
- Events: `claude_code.tool_result`, `claude_code.api_request`; Traces: `claude_code.tool.execution` (per-tool duration, split from permission wait).

**Recommended split:** HTTP hooks → the **live intent/timeline feed** (what's happening right now) and per-subagent ROI; OTel → the **authoritative token/cost/time ledger** (the numbers you actually report). This removes your reliance on reconstructing session totals from partial PostToolUse payloads.

---

## 2. Context Routing & Folder Structure (Route & Assign)

### What's right
- `AGENT_CONTEXT_INDEX.json` with `role` / `allowed_files` / `forbidden_files` is a good context-filter concept and directly attacks token waste.
- Clean separation of `agent-context/`, `agent-logs/`, `review-packages/` maps neatly onto Route / Evidence.

### Gaps

**2.1 — The index is advisory, not enforced.** Folders and a JSON index don't *bound* anything; nothing stops an agent from reading `forbidden_files`. To actually enforce "Route" and "Assign," the `allowed_files`/`forbidden_files` must become **Claude Code permission rules** (deny/allow), optionally backed by a `PreToolUse` hook that checks the target path against the active role profile. Right now "Assign" is documentation, not a control.

**2.2 — There's no mechanism that loads the *right* context per role.** `CLAUDE.md` is global (always in context). The native way to give a role its own narrowed context + tool set is a **subagent definition** (`.claude/agents/planner.md`, `builder.md`, `validator.md`) with its own `tools` and `permissions`. That also solves 1.2 (token telemetry) and 2.3 (attribution) at the same time — strong reason to adopt the subagent model.

**2.3 — No notion of "active role."** A telemetry or security hook has no way to know whether the current actor is Planner vs Builder unless roles are real subagents. With subagents you can use the `subagent_type` matcher and `SubagentStart`/`SubagentStop` to attribute both *actions* and *telemetry* per role — which is exactly what the dashboard's "Active Agents" panel needs.

**2.4 — The Role Matrix is excellent but currently unmappable.** The Planner/Builder/Validator "Forbidden" columns (e.g., "Forbidden: Altering TECH_STACK.md", "Forbidden: self-approving commits") are precisely what should be expressed as deny rules. As-is they live only in a slide and a JSON the agent is *asked* to respect.

---

## 3. Observability UI Transport (FastAPI / React)

### What's right
- FastAPI ingest + React on localhost is a reasonable, low-friction choice for a single-developer tool. Polling is fine to start.

### Improvements

**3.1 — The server should be a projection, not the source of truth.** HTTP hooks are fire-and-forget; because they're non-blocking, a downed server means **silently dropped telemetry**. Have hooks *also* append JSONL to `agent-logs/` (you already have the folder), and let FastAPI tail/ingest that log. The log is durable across restarts, replayable, and matches your own "Evidence" principle. This is a one-line change in philosophy with big resilience payoff.

**3.2 — Prefer SSE over WebSockets.** The data flow is one-way (server → UI). Server-Sent Events are simpler, auto-reconnect, and sufficient. WebSockets is over-engineering here. Plain polling of the JSONL is an acceptable v1.

**3.3 — Don't reconstruct token totals from PostToolUse.** Feed the ROI panels from OTel (Prometheus exporter scrape, or OTLP → your server) or from the JSONL rollup. Use PostToolUse only for the live timeline and per-subagent cards.

**3.4 — The context-rot gauge cannot be sourced from PostToolUse.** It must come from **`statusLine`**, which is a *separate continuous mechanism*, not a lifecycle hook. Its stdin JSON exposes exactly what you need:
- `context_window.remaining_percentage` and `context_window.used_percentage` (pre-calculated)
- `context_window.total_input_tokens`, `context_window.total_output_tokens`, `context_window.context_window_size`
- `cost.total_cost_usd`, `cost.total_duration_ms`, `cost.total_lines_added`, `exceeds_200k_tokens`

As you noted, `remaining_percentage` already accounts for the autocompact buffer (~33K tokens), so it represents true free space before forced compaction — ideal for threshold warnings and proactive state backups. Wire a `statusLine` script that writes/POSTs these numbers to the gauge. Then use the **`PreCompact`** hook (a real, blocking-capable hook) as the "about to lose memory" alarm *and* the trigger to snapshot state before compaction.

---

## 4. Onboarding — `setup.sh` via `SessionStart`

### Critical issue: this won't work as designed.
A `SessionStart` hook **cannot run an interactive wizard**:
- The hook's **stdin is the event JSON payload, not a TTY**. A `read`-based Q&A will receive that JSON (or EOF) instead of keyboard input — it hangs or auto-fills garbage.
- The hook's **stdout is injected into the model's context**, not shown to the human as a prompt. The user never sees the questions.
- `SessionStart` fires on **every** session start, including `resume` and `compact` (it carries a `source` field). So the wizard would re-run constantly, not just on first clone.
- On a fresh clone, MCP servers typically haven't connected yet at `SessionStart`, so anything depending on them fails on first run.

### Recommendation
- Keep onboarding an **explicit human-run command** — exactly the `npm run init` / `make init` your blueprint already mentions. Don't bind it to `SessionStart`.
- If you want it to be *interactive and agent-native*, drive it through **Plan Mode + the AskUserQuestion** flow rather than a shell `read` loop — that's the supported interactive-prompt path.
- If you keep a shell script, make it **non-interactive when run as a hook** (read answers from args/env/a config file) and **idempotent** via a sentinel (e.g., skip if `.trace-initialized` exists).
- Reserve `SessionStart` for what it's *good* at: **non-interactive context injection** — e.g., echo the current `PROJECT_STATUS_AND_NEXT_STEPS.md` and active role into context on resume. That directly serves your anti-context-rot goal.

---

## 5. Cross-Cutting: Context Engineering, `/compact`, and Security

**5.1 — Close the `/compact` loop (your flagged gap — highest-value addition).**
Add a `PreCompact` hook that (a) snapshots current state into `PROJECT_STATUS_AND_NEXT_STEPS.md` *before* compaction, and (b) alerts the UI. Pair it with `SessionStart` (`source: resume`/`compact`) re-injecting that status file. Combined with the `statusLine` gauge from 3.4, this is a complete context-rot defense: *warn early (statusLine) → persist before loss (PreCompact) → rehydrate after (SessionStart)*. This is the strongest missed opportunity in the whole design and directly answers "I know I missed /compact to memory."

**5.2 — Security / trust model (important for an OSS clone-and-run template).**
- A repo's `.claude/settings.json` **executes hooks on open** — `SessionStart` commands and any `PreToolUse`/`PostToolUse` handlers. Shipping this in a public template means *anyone who clones and opens it runs your hook commands*. Document the trust model explicitly and keep every hook command in-repo and reviewable.
- Your `PostToolUse` HTTP endpoint (`localhost:8000`) is **unauthenticated** — any local process can POST fabricated telemetry. Bind to localhost only, and consider a shared-secret header (`headers` + `allowedEnvVars`) so the dashboard only accepts its own session's events.
- A forked/malicious version could repoint an HTTP hook at an exfiltration URL or run arbitrary `SessionStart` commands. Note this in the README and treat hook config as security-sensitive.

**5.3 — Reconcile a contradiction in `CLAUDE.md`.**
"Do not bypass hooks… all tool uses must be allowed to complete" is (a) unenforceable from inside `CLAUDE.md`, and (b) in tension with safety — you *want* `PreToolUse` to be able to block dangerous calls. Reframe as "telemetry hooks are non-blocking by design; safety gates may block," so the instruction doesn't undercut your own Check phase.

---

## Prioritized Fix List

1. **Fix `settings.json` nesting** (Blocker — nothing fires today).
2. **Decide the agent model** — are Planner/Builder/Validator real Claude Code subagents, separate sessions, or prompt personas? This determines whether token telemetry exists at all and whether Route/Assign can be enforced or attributed.
3. **Adopt OTel** for the accurate token/cost/time ledger; keep HTTP hooks for the live intent timeline + per-subagent ROI cards.
4. **Move onboarding off `SessionStart`** to an explicit `init` command (or Plan Mode + AskUserQuestion).
5. **Add `PreCompact` + `statusLine`** for the context-rot gauge and pre-compaction state snapshots; rehydrate on `SessionStart(resume)`.
6. **Turn role profiles into enforced permission rules** (deny/allow), not advisory JSON; back with a `PreToolUse` observability hook.
7. **Make `agent-logs/` JSONL the durable sink**; FastAPI becomes a projection; use SSE (or polling) to the UI.
8. **Harden the trust model** — localhost bind, shared-secret header, documented hook execution risk.

---

## Decisions I Need From You (approval gate)

1. **Agent model:** are the three roles implemented as real subagents (Agent tool / `.claude/agents/*.md`), as separate Claude Code sessions, or as prompt personas in one session? *(Biggest fork — drives items 2, 3, 6.)*
2. **Telemetry strategy:** OK to adopt OTel alongside hooks (recommended), or do you want hooks-only and accept partial token coverage?
3. **Scope:** single-user local dashboard only, or eventual multi-user/team telemetry? *(Affects transport, auth, and storage choices.)*

No implementation will start until you've weighed in on these.

---

## Decisions & v1 Scope (locked 2026-06-08)

1. **Agent model → prompt personas in v1; real subagents in v2.0.** Roles (Planner/Builder/Validator) are a *discipline + labeling* convention in v1, enforced by `CLAUDE.md` instructions and permission rules — not by the subagent runtime.
2. **Telemetry → OTel alongside hooks.** Approximate token/cost figures are acceptable for v1; accuracy of *change/evidence* records is not negotiable.
3. **Scope → single-user local in v1; team telemetry in v2.0.**
   - Other recommendations: accepted.

### Consequence to accept consciously (from Decision 1)
With prompt personas in a single session, `PostToolUse` will **not** emit per-agent `totalTokens`. So in v1:

- **Token / cost ROI = whole-session and approximate**, sourced from OTel (`claude_code.token.usage`, `cost.usage`, `active_time.total`). No per-role token breakdown until v2 subagents. *(You've accepted this.)*
- **Per-role attribution** in the "Active Agents" panel comes from the active-phase label TRACE writes (which persona is running), not from runtime isolation.

### The v1 telemetry contract (the honest split)
- **REAL / deterministic** (must be accurate): what changed and what was implemented — git diffs, `review-packages/` (`git_diff.patch`, `test_logs.txt`, `validation_report.json`), `PROJECT_STATUS_AND_NEXT_STEPS.md` updates, and the per-tool intent timeline from hooks (`tool_name`, command/intent, `duration_ms`, success/failure). Context gauge from `statusLine` is also real.
- **APPROXIMATE / modeled** (clearly labeled as such in the UI): session token totals, cost, and any "effort/iterations saved" figure.

This split is clean: the *evidence* layer is provably real; only the *ROI rollup* is estimated.

