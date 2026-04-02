"""Operator-status routes and lightweight browser dashboard."""

from __future__ import annotations

import hashlib
import json

from control_plane.clock import utcnow
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.operator_status import OperatorStatusRequest, load_operator_status


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>RTLGen Control Plane</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f2efe8;
      --panel: #fffdf8;
      --ink: #1c1b19;
      --muted: #6f675e;
      --line: #d9cfbf;
      --accent: #0b6e4f;
      --warn: #b25a00;
      --danger: #a11c1c;
      --shadow: 0 18px 48px rgba(63, 41, 16, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: \"IBM Plex Sans\", \"Segoe UI\", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(11, 110, 79, 0.08), transparent 22rem),
        linear-gradient(180deg, #f7f2e8 0%, var(--bg) 100%);
      color: var(--ink);
    }
    .shell {
      width: 100%;
      max-width: 1500px;
      margin: 0 auto;
      padding: 24px;
      overflow-x: clip;
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
      gap: 16px;
      margin-bottom: 18px;
      min-width: 0;
    }
    .panel {
      background: rgba(255, 253, 248, 0.9);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 18px 20px;
      backdrop-filter: blur(8px);
      min-width: 0;
      overflow: hidden;
    }
    .headline {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }
    h1, h2, h3 {
      margin: 0;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    h1 { font-size: 1.9rem; }
    h2 { font-size: 1.05rem; margin-bottom: 12px; }
    .subtle, .meta, .empty { color: var(--muted); }
    .meta { font-size: 0.92rem; }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
      align-items: center;
    }
    .pill, button, select {
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 8px 12px;
      font: inherit;
    }
    button { cursor: pointer; }
    button.primary {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 0.92rem;
      border: 1px solid var(--line);
      background: #fff;
      max-width: 100%;
    }
    .badge.healthy { color: var(--accent); border-color: rgba(11, 110, 79, 0.25); }
    .badge.attention { color: var(--warn); border-color: rgba(178, 90, 0, 0.25); }
    .badge.failure { color: var(--danger); border-color: rgba(161, 28, 28, 0.25); }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }
    .summary-card {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.9);
    }
    .summary-card .label { color: var(--muted); font-size: 0.85rem; }
    .summary-card .value { font-size: 1.6rem; font-weight: 700; margin-top: 8px; }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.1fr) minmax(280px, 0.8fr);
      gap: 16px;
      min-width: 0;
      align-items: start;
    }
    .stack {
      display: grid;
      gap: 16px;
      min-width: 0;
    }
    .table-wrap {
      overflow-x: auto;
      min-width: 0;
      width: 100%;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
      table-layout: fixed;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid rgba(217, 207, 191, 0.7);
      vertical-align: top;
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    th { color: var(--muted); font-weight: 600; }
    .mono {
      font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      font-size: 0.86rem;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .event-log {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 10px;
    }
    .event-log li {
      border-left: 3px solid var(--line);
      padding-left: 10px;
    }
    .event-log .time { color: var(--muted); font-size: 0.82rem; display: block; }
    @media (max-width: 1080px) {
      .hero,
      .layout,
      .summary-grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
    }
    @media (max-width: 720px) {
      .hero, .layout, .summary-grid { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
    }
  </style>
</head>
<body>
  <div class=\"shell\">
    <section class=\"hero\">
      <div class=\"panel\">
        <div class=\"headline\">
          <div>
            <h1>RTLGen Control Plane</h1>
            <p class=\"subtle\">Live evaluator-side queue and run state with audible transition alerts.</p>
          </div>
          <div id=\"health-badge\" class=\"badge\">Loading</div>
        </div>
        <div class=\"summary-grid\" id=\"summary-grid\"></div>
      </div>
      <div class=\"panel\">
        <div class=\"headline\">
          <div>
            <h2>Monitor</h2>
            <p class=\"meta\" id=\"refresh-meta\">Connecting...</p>
          </div>
          <div class=\"controls\">
            <label class=\"pill\">Poll
              <select id=\"poll-select\">
                <option value=\"5000\">5s</option>
                <option value=\"10000\" selected>10s</option>
                <option value=\"30000\">30s</option>
              </select>
            </label>
            <button id=\"sound-toggle\" class=\"primary\">Sound On</button>
            <button id=\"refresh-button\">Refresh</button>
          </div>
        </div>
        <h3 style=\"margin-top: 16px; margin-bottom: 8px;\">Recent transitions</h3>
        <ul class=\"event-log\" id=\"event-log\">
          <li class=\"empty\">No transitions yet.</li>
        </ul>
      </div>
    </section>
    <section class="layout">
      <div class="stack">
        <div class="panel">
          <h2>Active Runs</h2>
          <div class="table-wrap"><table id="active-runs-table"></table></div>
        </div>
        <div class="panel">
          <h2>Recent Submissions</h2>
          <div class="table-wrap"><table id="submissions-table"></table></div>
        </div>
      </div>
      <div class="stack">
        <div class="panel">
          <h2>Recent Failures</h2>
          <div class="table-wrap"><table id="failures-table"></table></div>
        </div>
        <div class="panel">
          <h2>Stale Leases</h2>
          <div class="table-wrap"><table id="leases-table"></table></div>
        </div>
      </div>
      <div class="stack">
        <div class="panel">
          <h2>Operator Controls</h2>
          <div class="controls" style="justify-content:flex-start; margin-bottom: 10px;">
            <button id="dispatch-ready-button" class="primary">Dispatch Ready</button>
            <button id="process-completions-button">Process Completions</button>
            <button id="poll-github-button">Poll GitHub</button>
            <button id="backfill-review-button">Backfill Review States</button>
          </div>
          <p class="meta" id="control-status">No control actions yet.</p>
        </div>
        <div class="panel">
          <h2>Evaluators</h2>
          <div class="table-wrap"><table id="machines-table"></table></div>
        </div>
        <div class="panel">
          <h2>Pending Submission</h2>
          <div class="table-wrap"><table id="pending-submissions-table"></table></div>
        </div>
        <div class="panel">
          <h2>Dispatch Pending</h2>
          <div class="table-wrap"><table id="dispatch-pending-table"></table></div>
        </div>
        <div class="panel">
          <h2>State Counts</h2>
          <div class="table-wrap"><table id="states-table"></table></div>
        </div>
      </div>
    </section>
  </div>
  <script>
    const statusUrl = \"/api/v1/operator-status\";
    const summaryGrid = document.getElementById(\"summary-grid\");
    const refreshMeta = document.getElementById(\"refresh-meta\");
    const healthBadge = document.getElementById(\"health-badge\");
    const eventLog = document.getElementById(\"event-log\");
    const soundToggle = document.getElementById(\"sound-toggle\");
    const refreshButton = document.getElementById(\"refresh-button\");
    const pollSelect = document.getElementById(\"poll-select\");
    const dispatchReadyButton = document.getElementById(\"dispatch-ready-button\");
    const processCompletionsButton = document.getElementById(\"process-completions-button\");
    const pollGithubButton = document.getElementById(\"poll-github-button\");
    const backfillReviewButton = document.getElementById(\"backfill-review-button\");
    const controlStatus = document.getElementById(\"control-status\");
    const tables = {
      activeRuns: document.getElementById("active-runs-table"),
      submissions: document.getElementById("submissions-table"),
      failures: document.getElementById("failures-table"),
      leases: document.getElementById("leases-table"),
      machines: document.getElementById("machines-table"),
      pendingSubmissions: document.getElementById("pending-submissions-table"),
      dispatchPending: document.getElementById("dispatch-pending-table"),
      states: document.getElementById("states-table"),
    };

    let pollHandle = null;
    let previousAlertToken = null;
    let soundEnabled = true;
    let audioContext = null;
    const transitionHistory = [];

    function formatTime(iso) {
      if (!iso) return \"n/a\";
      return new Date(iso).toLocaleString();
    }

    function escapeHtml(value) {
      return String(value ?? \"\")
        .replace(/&/g, \"&amp;\")
        .replace(/</g, \"&lt;\")
        .replace(/>/g, \"&gt;\")
        .replace(/\"/g, \"&quot;\");
    }

    function renderTable(target, columns, rows) {
      if (!rows.length) {
        target.innerHTML = \"<tbody><tr><td class='empty'>None</td></tr></tbody>\";
        return;
      }
      const head = \"<thead><tr>\" + columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join(\"\") + \"</tr></thead>\";
      const body = \"<tbody>\" + rows.map((row) => {
        return \"<tr>\" + columns.map((column) => {
          const rendered = column.render ? column.render(row[column.key], row) : escapeHtml(row[column.key] ?? \"\");
          return `<td>${rendered}</td>`;
        }).join(\"\") + \"</tr>\";
      }).join(\"\") + \"</tbody>\";
      target.innerHTML = head + body;
    }

    async function postJson(url, payload = {}) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = data?.detail || `HTTP ${response.status}`;
        throw new Error(detail);
      }
      return data;
    }

    function setControlStatus(message) {
      controlStatus.textContent = message;
    }

    async function runControlAction(button, url, payload, successMessage) {
      const originalLabel = button.textContent;
      button.disabled = true;
      button.textContent = "Working...";
      try {
        const result = await postJson(url, payload);
        const message = typeof successMessage === "function" ? successMessage(result) : successMessage;
        setControlStatus(message);
        pushEvent(message);
        await refreshNow();
      } catch (error) {
        const message = `Control action failed: ${error}`;
        setControlStatus(message);
        pushEvent(message);
      } finally {
        button.disabled = false;
        button.textContent = originalLabel;
      }
    }

    function playTone(pattern) {
      if (!soundEnabled) return;
      if (!window.AudioContext && !window.webkitAudioContext) return;
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!audioContext) audioContext = new Ctx();
      const startAt = audioContext.currentTime + 0.02;
      pattern.forEach((tone, index) => {
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        oscillator.type = tone.type || \"sine\";
        oscillator.frequency.value = tone.frequency;
        gain.gain.setValueAtTime(0.0001, startAt + index * 0.18);
        gain.gain.exponentialRampToValueAtTime(tone.gain || 0.08, startAt + index * 0.18 + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, startAt + index * 0.18 + 0.15);
        oscillator.connect(gain);
        gain.connect(audioContext.destination);
        oscillator.start(startAt + index * 0.18);
        oscillator.stop(startAt + index * 0.18 + 0.16);
      });
    }

    function pushEvent(message) {
      transitionHistory.unshift({
        message,
        at: new Date().toISOString(),
      });
      while (transitionHistory.length > 8) transitionHistory.pop();
      eventLog.innerHTML = transitionHistory.map((event) => (
        `<li><span class="time">${escapeHtml(formatTime(event.at))}</span>${escapeHtml(event.message)}</li>`
      )).join("");
    }

    function buildAlertToken(payload) {
      const signature = {
        health: {
          status: payload.health_summary?.status || null,
          message: payload.health_summary?.message || null,
        },
        state_counts: payload.state_counts || {},
        active_runs: (payload.active_runs || []).map((row) => ({
          item_id: row.item_id || null,
          task_type: row.task_type || null,
          worker_host: row.worker_host || null,
        })),
        recent_submissions: (payload.recent_submissions || []).map((row) => ({
          item_id: row.item_id || null,
          pr_number: row.pr_number ?? null,
          state: row.state || null,
          finalization_status: row.finalization_status || null,
          finalized_proposal_id: row.finalized_proposal_id || null,
          finalization_commit: row.finalization_commit || null,
        })),
        recent_failures: (payload.recent_failures || []).map((row) => ({
          item_id: row.item_id || null,
          failure_category: row.failure_category || null,
          failure_issue_status: row.failure_issue_status || null,
          failure_issue_number: row.failure_issue_number ?? null,
          summary: row.summary || null,
        })),
        stale_leases: (payload.stale_leases || []).map((row) => ({
          item_id: row.item_id || null,
          hostname: row.hostname || null,
        })),
      };
      return JSON.stringify(signature);
    }

    function classifyTransition(payload, previousPayload) {
      if (!previousPayload) return null;
      const failures = payload.recent_failures?.length || 0;
      const previousFailures = previousPayload.recent_failures?.length || 0;
      const pendingSubmission = payload.state_counts?.artifact_sync || 0;
      const previousPendingSubmission = previousPayload.state_counts?.artifact_sync || 0;
      const awaitingReview = payload.state_counts?.awaiting_review || 0;
      const previousAwaitingReview = previousPayload.state_counts?.awaiting_review || 0;
      const mergedSubmissions = (payload.recent_submissions || []).filter((row) => row.state === "pr_merged").length;
      const previousMergedSubmissions = (previousPayload.recent_submissions || []).filter((row) => row.state === "pr_merged").length;
      const finalizedSubmissions = (payload.recent_submissions || []).filter((row) => row.finalization_status === "finalized" || row.finalization_status === "skipped").length;
      const previousFinalizedSubmissions = (previousPayload.recent_submissions || []).filter((row) => row.finalization_status === "finalized" || row.finalization_status === "skipped").length;
      const activeRuns = payload.active_runs?.length || 0;
      const previousActiveRuns = previousPayload.active_runs?.length || 0;

      if (failures > previousFailures) {
        return { message: `New failed job detected (${failures}).`, tone: "failure" };
      }
      if (pendingSubmission > previousPendingSubmission) {
        return { message: `New submission-ready item pending publication (${pendingSubmission}).`, tone: "review" };
      }
      if (awaitingReview > previousAwaitingReview) {
        return { message: `New PR awaiting review (${awaitingReview}).`, tone: "review" };
      }
      if (mergedSubmissions > previousMergedSubmissions) {
        return { message: `Merged review reconciled (${mergedSubmissions}).`, tone: "merge" };
      }
      if (finalizedSubmissions > previousFinalizedSubmissions) {
        return { message: `Proposal finalization updated (${finalizedSubmissions}).`, tone: "merge" };
      }
      if (activeRuns !== previousActiveRuns) {
        return { message: `Active run count changed (${previousActiveRuns} -> ${activeRuns}).`, tone: "activity" };
      }
      if (payload.health_summary?.message !== previousPayload.health_summary?.message) {
        return { message: payload.health_summary?.message || "Health summary changed.", tone: "activity" };
      }
      return null;
    }

    function tonePattern(name) {
      if (name === \"failure\") return [{frequency: 440, gain: 0.12, type: \"sawtooth\"}, {frequency: 330, gain: 0.1, type: \"square\"}];
      if (name === \"review\") return [{frequency: 660, gain: 0.08}, {frequency: 880, gain: 0.07}];
      if (name === \"merge\") return [{frequency: 523.25, gain: 0.06}, {frequency: 659.25, gain: 0.06}, {frequency: 783.99, gain: 0.05}];
      return [{frequency: 587.33, gain: 0.05}];
    }

    function renderSummary(payload) {
      const cards = [
        { label: \"Health\", value: payload.health_summary?.status || \"unknown\" },
        { label: \"Ready\", value: payload.state_counts?.ready || 0 },
        { label: \"Running\", value: payload.active_runs?.length || 0 },
        { label: \"Pending Submission\", value: payload.state_counts?.artifact_sync || 0 },
        { label: \"Recent Failures\", value: payload.recent_failures?.length || 0 },
      ];
      summaryGrid.innerHTML = cards.map((card) => `
        <div class=\"summary-card\">
          <div class=\"label\">${escapeHtml(card.label)}</div>
          <div class=\"value\">${escapeHtml(card.value)}</div>
        </div>
      `).join(\"\");
      const status = payload.health_summary?.status || \"attention\";
      healthBadge.className = `badge ${status === \"healthy\" ? \"healthy\" : \"attention\"}`;
      healthBadge.textContent = payload.health_summary?.message || \"unknown\";
    }

    function renderPayload(payload) {
      refreshMeta.textContent = `Last refresh: ${formatTime(payload.generated_utc)} | token ${payload.change_token.slice(0, 10)}`;
      renderSummary(payload);
      renderTable(tables.activeRuns, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "task_type", label: "Task" },
        { key: "worker_host", label: "Host" },
        { key: "started_at", label: "Started", render: (value) => escapeHtml(formatTime(value)) },
        { key: "last_heartbeat_at", label: "Heartbeat", render: (value) => escapeHtml(formatTime(value)) },
      ], payload.active_runs || []);
      renderTable(tables.submissions, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "pr_number", label: "PR" },
        { key: "state", label: "PR State" },
        { key: "finalization_status", label: "Finalize" },
        { key: "finalized_proposal_id", label: "Proposal", render: (value) => value ? `<span class='mono'>${escapeHtml(value)}</span>` : "" },
        { key: "finalization_commit", label: "Commit", render: (value, row) => value ? `<span class='mono' title='${escapeHtml(value)}'>${escapeHtml(value.slice(0, 10))}</span>` : (row.finalization_error ? `<span title='${escapeHtml(row.finalization_error)}'>failed</span>` : "") },
        { key: "updated_at", label: "Updated", render: (value) => escapeHtml(formatTime(value)) },
      ], payload.recent_submissions || []);
      renderTable(tables.failures, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "failure_category", label: "Category" },
        { key: "failure_issue_status", label: "Issue" },
        { key: "summary", label: "Summary" },
      ], payload.recent_failures || []);
      renderTable(tables.leases, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "hostname", label: "Host" },
        { key: "expires_at", label: "Expired", render: (value) => escapeHtml(formatTime(value)) },
      ], payload.stale_leases || []);
      renderTable(tables.machines, [
        { key: "machine_key", label: "Machine", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "role", label: "Role" },
        { key: "slot_capacity", label: "Slots" },
        { key: "active_slots", label: "Active" },
        { key: "assigned_ready", label: "Assigned Ready" },
        { key: "last_seen_at", label: "Last Seen", render: (value) => escapeHtml(formatTime(value)) },
      ], payload.evaluator_machines || []);
      renderTable(tables.pendingSubmissions, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "run_status", label: "Run" },
        { key: "reason", label: "Eligibility", render: (value, row) => row.eligible ? "eligible" : escapeHtml(value || "not eligible") },
        { key: "updated_at", label: "Updated", render: (value) => escapeHtml(formatTime(value)) },
        { key: "item_id", label: "Actions", render: (_value, row) => {
          const primaryAction = row.resume_requested ? "queued" : (row.eligible ? "submit" : (row.resumable ? "resume" : "blocked"));
          const primaryLabel = row.resume_requested ? "Queued" : (row.eligible ? "Submit" : (row.resumable ? "Resume" : "Blocked"));
          const primaryDisabled = (primaryAction === "blocked" || primaryAction === "queued") ? "disabled" : "";
          const primaryTitle = primaryAction === "blocked"
            ? `title="${escapeHtml(row.reason || "not eligible")}"`
            : primaryAction === "queued"
              ? 'title="Resume already requested"'
              : "";
          return `
            <button data-action="${primaryAction}" data-item-id="${escapeHtml(row.item_id)}" ${primaryDisabled} ${primaryTitle}>${primaryLabel}</button>
            <button data-action="supersede" data-item-id="${escapeHtml(row.item_id)}">Supersede</button>
          `;
        } },
      ], payload.pending_submission_items || []);
      renderTable(tables.dispatchPending, [
        { key: "item_id", label: "Item", render: (value) => `<span class='mono'>${escapeHtml(value)}</span>` },
        { key: "task_type", label: "Task" },
        { key: "assigned_machine_key", label: "Assigned", render: (value) => value ? `<span class='mono'>${escapeHtml(value)}</span>` : "" },
        { key: "updated_at", label: "Updated", render: (value) => escapeHtml(formatTime(value)) },
        { key: "item_id", label: "Actions", render: (_value, row) => `
            <button data-action="supersede" data-item-id="${escapeHtml(row.item_id)}">Supersede</button>
          ` },
      ], payload.dispatch_pending_items || []);
      const stateRows = Object.entries(payload.state_counts || {}).map(([name, count]) => ({ name, count }));
      renderTable(tables.states, [
        { key: "name", label: "State" },
        { key: "count", label: "Count" },
      ], stateRows);
    }

    async function loadStatus() {
      const response = await fetch(statusUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const previousPayload = window.__lastPayload || null;
      const alertToken = buildAlertToken(payload);
      if (previousAlertToken && previousAlertToken !== alertToken) {
        const transition = classifyTransition(payload, previousPayload);
        if (transition) {
          pushEvent(transition.message);
          playTone(tonePattern(transition.tone));
        }
      }
      previousAlertToken = alertToken;
      window.__lastPayload = payload;
      renderPayload(payload);
    }

    async function refreshNow() {
      try {
        await loadStatus();
      } catch (error) {
        refreshMeta.textContent = `Refresh failed: ${error}`;
      }
    }

    function restartPolling() {
      if (pollHandle) window.clearInterval(pollHandle);
      pollHandle = window.setInterval(refreshNow, Number(pollSelect.value));
    }

    dispatchReadyButton.addEventListener("click", () => runControlAction(
      dispatchReadyButton,
      "/api/v1/control/dispatch-ready",
      {},
      (result) => `Dispatched ${(result.results || []).length} items.`,
    ));
    processCompletionsButton.addEventListener("click", () => runControlAction(
      processCompletionsButton,
      "/api/v1/control/process-completions",
      { submit: true },
      (result) => `Processed completions (${(result.results || []).length}).`,
    ));
    pollGithubButton.addEventListener("click", () => runControlAction(
      pollGithubButton,
      "/api/v1/control/poll-github",
      {},
      (result) => `Polled GitHub (${result.checked_count || 0} links checked).`,
    ));
    backfillReviewButton.addEventListener("click", () => runControlAction(
      backfillReviewButton,
      "/api/v1/control/backfill-review-states",
      {},
      (result) => `Backfilled review states (${(result.results || []).length}).`,
    ));
    async function handleItemAction(event) {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const itemId = button.dataset.itemId;
      const action = button.dataset.action;
      if (!itemId || !action || action === "blocked" || action === "queued") return;
      if (action === "supersede" && !window.confirm(`Supersede ${itemId}?`)) return;
      const isSubmitLike = action === "submit" || action === "resume";
      const url = isSubmitLike
        ? `/api/v1/control/items/${encodeURIComponent(itemId)}/submit`
        : `/api/v1/control/items/${encodeURIComponent(itemId)}/supersede`;
      const payload = isSubmitLike ? {} : { reason: "dashboard_superseded" };
      const originalLabel = button.textContent;
      button.disabled = true;
      button.textContent = "Working...";
      try {
        await postJson(url, payload);
        const message = action === "submit"
          ? `Submission queued for ${itemId}.`
          : action === "resume"
            ? `Resume requested for ${itemId}.`
            : `Superseded ${itemId}.`;
        setControlStatus(message);
        pushEvent(message);
        await refreshNow();
      } catch (error) {
        const message = `Item action failed for ${itemId}: ${error}`;
        setControlStatus(message);
        pushEvent(message);
      } finally {
        button.disabled = false;
        button.textContent = originalLabel;
      }
    }

    tables.pendingSubmissions.addEventListener("click", handleItemAction);
    tables.dispatchPending.addEventListener("click", handleItemAction);
    soundToggle.addEventListener("click", () => {
      soundEnabled = !soundEnabled;
      soundToggle.textContent = soundEnabled ? "Sound On" : "Sound Off";
      if (soundEnabled) {
        try {
          playTone([{frequency: 659.25, gain: 0.04}, {frequency: 783.99, gain: 0.04}]);
        } catch (_error) {
        }
      }
    });
    refreshButton.addEventListener("click", refreshNow);
    pollSelect.addEventListener("change", restartPolling);

    refreshNow();
    restartPolling();
  </script>
</body>
</html>
"""


def _status_payload(database_url: str, recent_limit: int) -> dict[str, object]:
    engine = build_engine(database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        status = load_operator_status(session, OperatorStatusRequest(recent_limit=recent_limit))

    generated_utc = utcnow().isoformat()
    payload = {
        "generated_utc": generated_utc,
        "health_summary": status.health_summary,
        "state_counts": status.state_counts,
        "active_runs": status.active_runs,
        "stale_leases": status.stale_leases,
        "evaluator_machines": status.evaluator_machines,
        "pending_submission_items": status.pending_submission_items,
        "dispatch_pending_items": status.dispatch_pending_items,
        "recent_failures": status.recent_failures,
        "recent_submissions": status.recent_submissions,
    }
    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("generated_utc", None)
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")).hexdigest()
    payload["change_token"] = fingerprint
    return payload


def register_operator_status_routes(app) -> None:
    from control_plane.api.deps import get_settings

    settings = get_settings()

    def status_handler(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = json.dumps(_status_payload(settings.database_url, recent_limit=10), sort_keys=True).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, body

    def dashboard_handler(_method: str, _path: str, _params: dict[str, str], _body: bytes):
        body = _DASHBOARD_HTML.encode("utf-8")
        return 200, {"Content-Type": "text/html; charset=utf-8"}, body

    app.add_route("GET", "/", dashboard_handler)
    app.add_route("GET", "/dashboard", dashboard_handler)
    app.add_route("GET", "/api/v1/operator-status", status_handler)
    app.add_route("GET", "/api/v1/dashboard", status_handler)
