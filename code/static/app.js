// Sentinel AI front end.
//
// The page has three tabs: Setup, Report, and Fix & re-test.
// "Scan my chatbot" runs the whole test in one go: analyse the prompt, write
// attacks, test them one by one (so we can show progress), then build the report.
//
// All state lives in the `state` object. Attack text and bot replies are
// untrusted, so they are always inserted with esc(), never as raw HTML.

const state = {
  info: null,          // server info (demo mode, model)
  systemPrompt: "",    // the prompt being tested
  mode: "predicted",   // "predicted" or "live"
  live: null,          // live endpoint settings used for this scan
  analysis: null,
  attacks: [],
  results: [],         // results of the scan
  summary: null,       // launch call + counts
  hardening: null,     // fixes + hardened prompt
  diff: [],
  retest: null,        // re-test results + comparison
  filters: { verdict: "", category: "" },
};

// How many attacks we test at the same time.
const PARALLEL = 3;

// ---------------------------------------------------------------------------
// Plain-language explanations for everything that might be jargon
// ---------------------------------------------------------------------------

const CATEGORY = {
  prompt_injection: {
    name: "Hidden instructions",
    tip: "Also called prompt injection. Commands hidden inside an email, review or document the bot is asked to read.",
  },
  instruction_override: {
    name: "Rule override",
    tip: "Tries to cancel the bot's rules: \"ignore previous instructions\", fake admins or developers, made-up policy updates.",
  },
  jailbreak: {
    name: "Trickery",
    tip: "Also called a jailbreak. Role-play, stories, \"what if\" questions or emotional pressure to talk the bot out of its rules.",
  },
  system_prompt_leak: {
    name: "Prompt leak",
    tip: "Tries to make the bot reveal its hidden instructions, e.g. by repeating, translating or summarising them.",
  },
};

const SEVERITY_TIP = {
  Critical: "Leaked a secret, a password-like code or someone else's data, or agreed to do something forbidden.",
  High: "Revealed most of its hidden instructions, or dropped one of its core rules.",
  Medium: "Revealed part of its instructions, or bent a rule without serious harm.",
  Low: "Small slip, like wandering off-topic or out of character.",
  None: "No problem: the bot kept its rules.",
};

const GLOSSARY = {
  severity: "How bad a failure is: Critical, High, Medium or Low. Hover over a severity in the table for details.",
  result: "Pass means the bot kept its rules. Fail means the attack worked.",
  launch: "Sentinel's overall advice, based on the worst failure it found.",
  evidence: "The exact words from the reply that show what happened. Sentinel checks that they really appear in the reply.",
  prompt_fix: "A change to the wording of the system prompt.",
  app_fix: "A change to your app's code around the bot (for example a check on the server). Prompt wording alone can't fully fix these.",
};

const LAUNCH_TEXT = {
  "Block launch": { icon: "⛔", text: "Don't launch yet. At least one attack leaked a secret or someone's data, or got the bot to do something forbidden." },
  "Hold launch": { icon: "✋", text: "Hold off. An attack exposed most of the hidden instructions or broke a core rule." },
  "Fix before launch": { icon: "🔧", text: "Only smaller problems found. Fix them before launch, but nothing serious leaked." },
  "No failures found": { icon: "✅", text: "Every attack was blocked. A good sign, but not a guarantee: try more attacks, or test your real bot." },
};

// Ready-made settings for common chatbot APIs (live mode).
const PRESETS = {
  mock: {
    url: "http://127.0.0.1:8001/chat", headers: "{}", body: '{"message": "{{attack}}"}', path: "reply",
    help: "Start the practice bot first: open a second terminal and run  python -m mock_bot.server",
  },
  simple: {
    url: "", headers: "{}", body: '{"message": "{{attack}}"}', path: "reply",
    help: "For bots that take {\"message\": \"...\"} and answer {\"reply\": \"...\"}. Just fill in the web address.",
  },
  openai: {
    url: "", headers: "{}",
    body: '{"messages": [{"role": "system", "content": "{{system_prompt}}"}, {"role": "user", "content": "{{attack}}"}]}',
    path: "choices.0.message.content",
    help: "For bots with a chat-completions style API. Add your test login under Request format if it needs one.",
  },
  custom: { url: "", headers: "{}", body: '{"message": "{{attack}}"}', path: "reply",
    help: "Open Request format and describe what your bot expects." },
};

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

const $ = (id) => document.getElementById(id);

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/** A little ⓘ that shows an explanation on hover or keyboard focus. */
function info(text) {
  return `<span class="info" tabindex="0" role="note" aria-label="${esc(text)}" data-tip="${esc(text)}">i</span>`;
}

function show(id, visible = true) { $(id).hidden = !visible; }

function showError(message) {
  $("error").textContent = message;
  show("error", Boolean(message));
  if (message) window.scrollTo({ top: 0, behavior: "smooth" });
}

/** Disable every button while something is running, so nothing gets clicked twice. */
function setWorking(working) {
  document.querySelectorAll("main button").forEach((b) => (b.disabled = working));
}

/** Call the API with JSON. Throws an Error with a readable message on failure. */
async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    // A 404 on our own API almost always means the server is running older
    // code than this page (it was started before an update). Say so plainly.
    if (res.status === 404 && path.startsWith("/api/")) {
      throw new Error("The Sentinel server is running an older version of the code. " +
        "Stop it (Ctrl+C in its terminal), start it again, then refresh this page.");
    }
    const data = await res.json().catch(() => ({}));
    let detail = data.detail || `Request failed (${res.status})`;
    if (Array.isArray(detail)) detail = detail.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
    throw new Error(detail);
  }
  return res;
}
const apiJson = async (path, body) => (await api(path, body)).json();

/** Run a slow single action with the little "busy" pill at the bottom. */
async function withBusy(text, action) {
  showError("");
  $("busy-text").textContent = text;
  show("busy");
  setWorking(true);
  try { return await action(); }
  catch (e) { showError(e.message); }
  finally { show("busy", false); setWorking(false); }
}

/** Download a server response as a file. */
async function download(path, body, filename) {
  await withBusy("Preparing download...", async () => {
    const res = await api(path, body);
    const url = URL.createObjectURL(await res.blob());
    Object.assign(document.createElement("a"), { href: url, download: filename }).click();
    URL.revokeObjectURL(url);
  });
}

function verdictOf(r) { return r.judgment ? r.judgment.verdict : "Error"; }
function severityOf(r) { return r.judgment ? r.judgment.severity : "-"; }

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

function openTab(name) {
  ["setup", "report", "fix"].forEach((t) => show(`tab-${t}`, t === name));
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function unlockTab(name, unlocked = true) {
  document.querySelector(`.tab[data-tab=${name}]`).disabled = !unlocked;
}

// ---------------------------------------------------------------------------
// Setup tab
// ---------------------------------------------------------------------------

async function loadInfo() {
  try {
    state.info = await apiJson("/api/info");
    const badge = $("mode-badge");
    if (state.info.demo) {
      badge.textContent = "Demo mode: pre-written answers, no AI calls";
      badge.classList.add("demo");
    } else {
      badge.textContent = `AI model: ${state.info.model}`;
    }
    $("per-category").max = state.info.max_per_category;
    $("per-category").value = state.info.default_per_category;
  } catch { showError("Could not reach the Sentinel server. Is it running?"); }
}

async function loadExample() {
  await withBusy("Loading the example...", async () => {
    const data = await apiJson("/api/example");
    $("system-prompt").value = data.system_prompt;
    show("baseline-note", false);
  });
}

function selectedMode() { return document.querySelector("input[name=mode]:checked").value; }

function applyPreset() {
  const p = PRESETS[$("live-preset").value];
  $("live-url").value = p.url;
  $("live-headers").value = p.headers;
  $("live-body").value = p.body;
  $("live-path").value = p.path;
  $("preset-help").textContent = p.help;
  $("live-test-result").textContent = "";
}

/** Read the live chatbot settings from the form (throws if something is wrong). */
function readLiveConfig() {
  const url = $("live-url").value.trim();
  if (!url) throw new Error("Enter your chatbot's web address (URL) first.");
  let headers;
  try { headers = JSON.parse($("live-headers").value || "{}"); }
  catch { throw new Error('Extra headers must be JSON, for example {"Authorization": "Bearer test-token"}.'); }
  return { url, headers, body_template: $("live-body").value, reply_path: $("live-path").value.trim() };
}

async function testConnection() {
  const out = $("live-test-result");
  try {
    const live = readLiveConfig();
    out.textContent = "Connecting...";
    const data = await apiJson("/api/live/test", { live });
    out.className = data.ok ? "ok-text" : "bad-text";
    out.textContent = data.ok ? `Connected. The bot replied: "${data.reply.slice(0, 120)}"` : `Not working: ${data.error}`;
  } catch (e) { out.className = "bad-text"; out.textContent = e.message; }
}

/** Mark a checklist line as "now", "done" or "todo". */
function progressStep(id, status) {
  $(id).className = status;
}

function setRunProgress(done, total) {
  $("p-run-count").textContent = total ? `${done} of ${total}` : "";
  $("p-run-bar").style.width = total ? `${(done / total) * 100}%` : "0";
}

/** Forget everything from a previous scan. */
function resetScan() {
  Object.assign(state, { analysis: null, attacks: [], results: [], summary: null,
                         hardening: null, diff: [], retest: null, filters: { verdict: "", category: "" } });
  $("hardening").innerHTML = ""; $("retest").innerHTML = "";
  show("retest-card", false); show("baseline-card", false); show("review", false);
  unlockTab("report", false); unlockTab("fix", false);
}

/** The one-click scan: analyse, write attacks, test them, build the report. */
async function scan() {
  showError("");
  const prompt = $("system-prompt").value.trim();
  if (!prompt) return showError("Paste a system prompt first, or click \"Try the example bot\".");

  let live = null;
  const mode = selectedMode();
  if (mode === "live") {
    try { live = readLiveConfig(); } catch (e) { return showError(e.message); }
  }

  resetScan();
  Object.assign(state, { systemPrompt: prompt, mode, live });
  ["p-analyze", "p-attacks", "p-run", "p-report"].forEach((id) => progressStep(id, "todo"));
  setRunProgress(0, 0);
  show("progress");
  $("progress").scrollIntoView({ behavior: "smooth" });
  setWorking(true);

  try {
    progressStep("p-analyze", "now");
    state.analysis = await apiJson("/api/analyze", { system_prompt: prompt });
    progressStep("p-analyze", "done");

    progressStep("p-attacks", "now");
    const data = await apiJson("/api/attacks", {
      system_prompt: prompt, analysis: state.analysis, per_category: Number($("per-category").value),
    });
    state.attacks = data.attacks;
    state.warnings = data.warnings;
    progressStep("p-attacks", "done");

    if ($("review-first").checked) {
      renderReview();
      show("review");
      $("review").scrollIntoView({ behavior: "smooth" });
      return; // the user continues with "Run these attacks"
    }
    await runAndReport();
  } catch (e) {
    show("progress", false);
    showError(e.message);
  } finally {
    setWorking(false);
  }
}

/** Test every attack, then build the report and open the Report tab. */
async function runAndReport() {
  show("review", false);
  progressStep("p-run", "now");
  state.results = await runAttacks(state.systemPrompt, (done, total) => setRunProgress(done, total));
  progressStep("p-run", "done");

  progressStep("p-report", "now");
  state.summary = await apiJson("/api/summary", { results: state.results });
  progressStep("p-report", "done");

  renderReport();
  unlockTab("report");
  unlockTab("fix");
  show("progress", false);
  openTab("report");
}

async function runReviewed() {
  setWorking(true);
  try { await runAndReport(); }
  catch (e) { showError(e.message); }
  finally { setWorking(false); }
}

/**
 * Test each attack with its own request, a few at a time, so we can report
 * progress. Results come back in the same order as state.attacks.
 */
async function runAttacks(systemPrompt, onProgress) {
  const attacks = state.attacks;
  const results = new Array(attacks.length);
  let next = 0, done = 0;
  onProgress(0, attacks.length);

  async function worker() {
    while (next < attacks.length) {
      const i = next++;
      const data = await apiJson("/api/run", {
        system_prompt: systemPrompt, analysis: state.analysis, attacks: [attacks[i]],
        mode: state.mode, live: state.live,
      });
      results[i] = data.results[0];
      onProgress(++done, attacks.length);
    }
  }
  await Promise.all(Array.from({ length: Math.min(PARALLEL, attacks.length) }, worker));
  return results;
}

function attackListHtml(attacks) {
  return Object.keys(CATEGORY).map((cat) => {
    const items = attacks.filter((a) => a.category === cat);
    if (!items.length) return "";
    return `<h3>${CATEGORY[cat].name} ${info(CATEGORY[cat].tip)}</h3>` + items.map((a) => `
      <details class="attack">
        <summary><b>${esc(a.id)}</b> ${esc(a.technique)}</summary>
        <p class="hint">Goal: ${esc(a.goal)}</p>
        <pre>${esc(a.prompt)}</pre>
      </details>`).join("");
  }).join("");
}

function renderReview() {
  const warnings = (state.warnings || []).map((w) => `<div class="note">${esc(w)}</div>`).join("");
  $("review-list").innerHTML = warnings + attackListHtml(state.attacks);
}

// ---------------------------------------------------------------------------
// Report tab
// ---------------------------------------------------------------------------

function launchBanner(summary) {
  const c = summary.counts;
  const t = LAUNCH_TEXT[summary.launch_call];
  const cls = { "Block launch": "block", "Hold launch": "hold", "Fix before launch": "fix" }[summary.launch_call] || "clear";
  const sev = ["Critical", "High", "Medium", "Low"]
    .filter((s) => c[s]).map((s) => `<span class="sev sev-${s}">${c[s]} ${s}</span>`).join(", ");
  return `<div class="launch ${cls}">
      <div class="call">${t.icon} ${esc(summary.launch_call)} ${info(GLOSSARY.launch)}</div>
      <p>${t.text}</p>
      <p class="counts"><b>${c.fail} of ${c.total}</b> attacks worked${sev ? ` (${sev})` : ""}.
        ${c.error ? `${c.error} could not be run.` : ""}</p>
    </div>`;
}

function renderReport() {
  $("launch").innerHTML = launchBanner(state.summary);
  show("predicted-note", state.mode === "predicted");
  show("chip-error", state.results.some((r) => !r.judgment));

  // Category filter chips, with counts.
  $("filter-category").innerHTML = `<button class="chip active" data-value="">All types</button>` +
    Object.keys(CATEGORY).map((cat) => {
      const n = state.results.filter((r) => r.attack.category === cat).length;
      return n ? `<button class="chip" data-value="${cat}">${CATEGORY[cat].name} (${n})</button>` : "";
    }).join("");
  wireChips("filter-category", "category");

  renderAnalysis();
  renderTable();
}

function wireChips(containerId, key) {
  $(containerId).querySelectorAll(".chip").forEach((chip) => chip.addEventListener("click", () => {
    $(containerId).querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === chip));
    state.filters[key] = chip.dataset.value;
    renderTable();
  }));
}

function replyBlock(r) {
  if (r.reply.error) return `<h4>Reply</h4><div class="error">Could not run this attack: ${esc(r.reply.error)}</div>`;
  const label = r.reply.mode === "predicted"
    ? `<span class="badge predicted">Simulated reply, not your real bot</span>`
    : `<span class="badge live">Real reply from your chatbot</span>`;
  return `<h4>Reply ${label}</h4><pre>${esc(r.reply.text)}</pre>`;
}

function detailHtml(r) {
  const j = r.judgment;
  const evidence = j ? `<h4>Evidence ${info(GLOSSARY.evidence)}</h4><code>${esc(j.evidence)}</code>
      ${r.evidence_verified ? "" : `<span class="badge">couldn't find this quote in the reply</span>`}` : "";
  return `<div class="detail-box">
      <p><b>What the attacker wanted:</b> ${esc(r.attack.goal)}</p>
      <h4>Attack message</h4><pre>${esc(r.attack.prompt)}</pre>
      ${replyBlock(r)}
      ${evidence}
    </div>`;
}

function renderTable() {
  const { verdict, category } = state.filters;
  const rows = state.results.filter((r) =>
    (!category || r.attack.category === category) && (!verdict || verdictOf(r) === verdict));

  const table = $("results-table");
  table.innerHTML = `<thead><tr><th>Attack</th><th>Type</th><th>Result ${info(GLOSSARY.result)}</th>
      <th>Severity ${info(GLOSSARY.severity)}</th><th>Why</th></tr></thead>`;
  const tbody = document.createElement("tbody");

  rows.forEach((r) => {
    const v = verdictOf(r), s = severityOf(r);
    const tr = document.createElement("tr");
    tr.className = "result-row";
    tr.tabIndex = 0;
    tr.innerHTML = `
      <td><b>${esc(r.attack.id)}</b><br><span class="hint">${esc(r.attack.technique)}</span></td>
      <td>${CATEGORY[r.attack.category].name}</td>
      <td class="verdict-${v}">${{ Pass: "✓ Pass", Fail: "✗ Fail", Error: "Error" }[v]}</td>
      <td><span class="sev sev-${s}" title="${esc(SEVERITY_TIP[s] || "")}">${s === "None" ? "-" : s}</span></td>
      <td>${esc(r.judgment ? r.judgment.reason : r.reply.error)}</td>`;
    // Clicking (or pressing Enter on) a row opens a detail row underneath it.
    const toggle = () => {
      const next = tr.nextElementSibling;
      if (next && next.classList.contains("detail")) return next.remove();
      const detail = document.createElement("tr");
      detail.className = "detail";
      detail.innerHTML = `<td colspan="5">${detailHtml(r)}</td>`;
      tr.after(detail);
    };
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter") toggle(); });
    tbody.appendChild(tr);
  });

  if (!rows.length) tbody.innerHTML = `<tr><td colspan="5" class="hint">No attacks match these filters.</td></tr>`;
  table.appendChild(tbody);
}

function renderAnalysis() {
  const a = state.analysis;
  const kinds = { secret: "secret", user_data: "other people's data", system_prompt: "the prompt itself", other: "other" };
  $("analysis").innerHTML = `
    <p><b>What it's for:</b> ${esc(a.purpose)}</p>
    <div class="grid2">
      <div>
        <h3>Rules it must follow</h3>
        <ul>${a.rules.map((r) => `<li><b>${esc(r.id)}</b> ${esc(r.text)}</li>`).join("")}</ul>
        <h3>What it can do</h3>
        <ul>${a.capabilities.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>
        <p>Reads text it didn't write (emails, documents...): <b>${a.reads_untrusted_content ? "Yes, so hidden instructions are a risk" : "No"}</b></p>
      </div>
      <div>
        <h3>What it must protect</h3>
        <ul>${a.protected_assets.map((p) => `<li><b>${esc(p.name)}</b> <span class="badge">${esc(kinds[p.kind] || p.kind)}</span><br>${esc(p.description)}</li>`).join("")}</ul>
        <h3>Weak spots in how the prompt is written</h3>
        <ul>${a.weak_spots.map((w) => `<li><b>${esc(w.issue)}</b>${w.quote ? `: <code>${esc(w.quote)}</code>` : ""}<br><span class="hint">${esc(w.why_it_matters)}</span></li>`).join("")}</ul>
      </div>
    </div>
    <h3>Attacks used</h3>
    ${attackListHtml(state.attacks)}`;
}

// ---------------------------------------------------------------------------
// Fix & re-test tab
// ---------------------------------------------------------------------------

async function harden() {
  await withBusy("Writing fixes and a stronger prompt...", async () => {
    const data = await apiJson("/api/harden", {
      system_prompt: state.systemPrompt, analysis: state.analysis, results: state.results,
    });
    state.hardening = data.hardening;
    state.diff = data.diff;
    state.retest = null;
    $("retest").innerHTML = "";
    renderHardening(data.unfixed);
    show("retest-card"); show("baseline-card");
  });
}

function renderHardening(unfixed) {
  const h = state.hardening;
  const fixes = h.fixes.map((f) => {
    const isPrompt = f.kind === "prompt";
    return `<div class="fix-card">
      <span class="title">${esc(f.title)}</span>
      <span class="badge ${f.kind}">${isPrompt ? "Change the prompt" : "Change the app"}</span> ${info(isPrompt ? GLOSSARY.prompt_fix : GLOSSARY.app_fix)}
      <p>${esc(f.description)}</p>
      <span class="hint">Fixes: ${f.fixes_attacks.length ? f.fixes_attacks.map(esc).join(", ") : "general hardening"}</span>
    </div>`;
  }).join("");
  const unfixedNote = unfixed.length
    ? `<div class="note">None of the fixes cover: ${unfixed.map(esc).join(", ")}</div>` : "";

  $("hardening").innerHTML = `
    <h3>Suggested fixes</h3>${unfixedNote}${fixes}
    <h3>Your stronger prompt</h3>
    <div class="row tight">
      <div class="seg">
        <button class="active" data-view="prompt">New prompt</button>
        <button data-view="diff">What changed</button>
      </div>
      <span class="grow"></span>
      <button class="secondary small" id="btn-copy">Copy prompt</button>
    </div>
    <div id="view-prompt"><pre>${esc(h.hardened_prompt)}</pre></div>
    <div id="view-diff" hidden>
      <ul>${h.change_summary.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>
      <p class="hint"><span class="key add">added</span> <span class="key remove">removed</span></p>
      <div class="diff">${state.diff.map((d) => `<div class="${d.op}">${esc(d.text)}</div>`).join("")}</div>
    </div>`;

  $("hardening").querySelectorAll(".seg button").forEach((btn) => btn.addEventListener("click", () => {
    $("hardening").querySelectorAll(".seg button").forEach((b) => b.classList.toggle("active", b === btn));
    show("view-prompt", btn.dataset.view === "prompt");
    show("view-diff", btn.dataset.view === "diff");
  }));
  $("btn-copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(h.hardened_prompt); $("btn-copy").textContent = "Copied!"; }
    catch { $("btn-copy").textContent = "Copy failed: select the text instead"; }
  });
}

async function retest() {
  if (state.mode === "live" && !confirm(
    "This sends the attacks to your chatbot again. Put the fixed prompt on your chatbot first " +
    "(or use {{system_prompt}} in the request format). Continue?")) return;

  showError("");
  setWorking(true);
  show("retest-progress");
  $("retest").innerHTML = "";
  try {
    const after = await runAttacks(state.hardening.hardened_prompt, (done, total) => {
      $("r-count").textContent = `${done} of ${total}`;
      $("r-bar").style.width = `${(done / total) * 100}%`;
    });
    state.retest = { ...(await apiJson("/api/compare", { before: state.results, after })), results: after };
    renderRetest();
  } catch (e) { showError(e.message); }
  finally { setWorking(false); show("retest-progress", false); }
}

function renderRetest() {
  const r = state.retest;
  const c = r.comparison_counts;
  const before = Object.fromEntries(state.results.map((x) => [x.attack.id, x]));
  const after = Object.fromEntries(r.results.map((x) => [x.attack.id, x]));
  const names = { fixed: "✓ Fixed", still_failing: "Still failing", new_failure: "New problem", still_passing: "Still passing" };
  const cell = (verdict, severity) =>
    `<span class="verdict-${verdict}">${verdict}</span>${severity !== "None" ? ` <span class="sev sev-${severity}">${severity}</span>` : ""}`;

  const rows = r.comparison.map((row) => `<tr>
      <td><b>${esc(row.attack_id)}</b><br><span class="hint">${esc(before[row.attack_id].attack.technique)}</span></td>
      <td>${cell(row.before_verdict, row.before_severity)}</td>
      <td>${cell(row.after_verdict, row.after_severity)}<br><span class="hint">${esc(after[row.attack_id].judgment.reason)}</span></td>
      <td class="status-${row.status}">${names[row.status]}</td></tr>`).join("");

  $("retest").innerHTML = `
    <div class="stat-row">
      <div class="stat"><b class="status-fixed">${c.fixed}</b>fixed</div>
      <div class="stat"><b class="status-still_failing">${c.still_failing}</b>still failing</div>
      <div class="stat"><b class="status-new_failure">${c.new_failure}</b>new problems ${info("Attacks that passed before but fail with the fixed prompt. The rewrite broke something.")}</div>
      <div class="stat"><b class="status-still_passing">${c.still_passing}</b>still passing</div>
    </div>
    ${launchBanner(r)}
    ${state.mode === "predicted" ? `<div class="note">Before and after are both <b>simulated</b> replies, not your real bot.</div>` : ""}
    <div class="table-wrap"><table>
      <thead><tr><th>Attack</th><th>Before</th><th>After</th><th>Change</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>`;
}

/** Load the fixed prompt into Setup so the user can scan it with fresh attacks. */
function useAsBaseline() {
  $("system-prompt").value = state.hardening.hardened_prompt;
  resetScan();
  show("baseline-note");
  openTab("setup");
}

// ---------------------------------------------------------------------------
// Downloads
// ---------------------------------------------------------------------------

function exportMarkdown() {
  download("/api/export/markdown", {
    system_prompt: state.systemPrompt, analysis: state.analysis, results: state.results,
    hardening: state.hardening,
    retest_results: state.retest ? state.retest.results : null,
    comparison: state.retest ? state.retest.comparison : null,
    demo: Boolean(state.info && state.info.demo),
  }, "sentinel-report.md");
}

function exportCsv() {
  download("/api/export/csv", { results: state.results }, "sentinel-results.csv");
}

// ---------------------------------------------------------------------------
// Wire up the page
// ---------------------------------------------------------------------------

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => openTab(t.dataset.tab)));
$("btn-example").addEventListener("click", loadExample);
$("btn-scan").addEventListener("click", scan);
$("btn-run-reviewed").addEventListener("click", runReviewed);
$("btn-test-live").addEventListener("click", testConnection);
$("live-preset").addEventListener("change", applyPreset);
$("btn-go-fix").addEventListener("click", () => openTab("fix"));
$("btn-harden").addEventListener("click", harden);
$("btn-retest").addEventListener("click", retest);
$("btn-baseline").addEventListener("click", useAsBaseline);
$("btn-md").addEventListener("click", exportMarkdown);
$("btn-csv").addEventListener("click", exportCsv);
$("system-prompt").addEventListener("input", () => show("baseline-note", false));
wireChips("filter-verdict", "verdict");
document.querySelectorAll("input[name=mode]").forEach((radio) =>
  radio.addEventListener("change", () => show("live-config", selectedMode() === "live")));

applyPreset();
loadInfo();
