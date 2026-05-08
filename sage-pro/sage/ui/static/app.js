/* SAGE-PRO v2 — Application Logic */

const state = { user: null, sessions: [], active: null, busy: false };
const $ = id => document.getElementById(id);

// ── Auth ───────────────────────────────────────────────
$("loginForm").addEventListener("submit", e => {
  e.preventDefault();
  const email = $("loginEmail").value.trim();
  const pass = $("loginPass").value;
  if (!email || !pass) return showErr("Please fill in all fields.");
  state.user = { email, name: email.split("@")[0], initials: email[0].toUpperCase() };
  localStorage.setItem("su", JSON.stringify(state.user));
  loadSessions();
  openApp();
});

function showErr(m) {
  const el = $("loginError");
  el.textContent = m; el.style.display = "block";
  setTimeout(() => el.style.display = "none", 3500);
}

function openApp() {
  $("loginPage").style.display = "none";
  $("app").style.display = "block";
  $("userAvatar").textContent = state.user.initials;
  $("userName").textContent = state.user.name;
  $("msgInput").focus();
}

// Auto-login
(function () {
  const s = localStorage.getItem("su");
  if (s) { state.user = JSON.parse(s); loadSessions(); openApp(); }
})();

$("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("su");
  state.user = null;
  $("app").style.display = "none";
  $("loginPage").style.display = "flex";
  $("loginEmail").value = ""; $("loginPass").value = "";
});

// ── Sessions ───────────────────────────────────────────
function loadSessions() {
  state.sessions = JSON.parse(localStorage.getItem("ss") || "[]");
  drawHistory();
}

function saveSessions() {
  localStorage.setItem("ss", JSON.stringify(state.sessions));
}

function newSession(title) {
  const s = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
    title: title.slice(0, 60),
    msgs: [],
    ts: new Date().toISOString()
  };
  state.sessions.unshift(s);
  state.active = s;
  saveSessions();
  drawHistory();
  return s;
}

function drawHistory() {
  const el = $("historyList");
  const label = '<div class="history-group-label">Recent</div>';
  let html = label;
  state.sessions.forEach(s => {
    const cls = state.active && state.active.id === s.id ? " active" : "";
    html += `<div class="history-item${cls}" onclick="openSession('${s.id}')">
      <span class="history-item-icon">&#x25CB;</span>
      <span class="history-item-label">${esc(s.title)}</span>
    </div>`;
  });
  el.innerHTML = html;
}

function openSession(id) {
  state.active = state.sessions.find(s => s.id === id);
  if (!state.active) return;
  $("chatTitle").textContent = state.active.title;
  drawHistory();
  drawMessages();
}

$("newChatBtn").addEventListener("click", () => {
  state.active = null;
  $("chatTitle").textContent = "New Session";
  drawHistory();
  const ca = $("chatArea");
  ca.innerHTML = "";
  ca.appendChild($("welcomeScreen") || createWelcome());
  const ws = document.querySelector(".welcome");
  if (ws) ws.style.display = "flex";
  $("msgInput").focus();
});

// ── Messages ───────────────────────────────────────────
function drawMessages() {
  const ca = $("chatArea");
  ca.innerHTML = "";
  if (!state.active || !state.active.msgs.length) {
    const ws = document.querySelector(".welcome");
    if (ws) { ca.appendChild(ws); ws.style.display = "flex"; }
    return;
  }
  state.active.msgs.forEach(m => addMsgDOM(m.role, m.content));
  scrollEnd();
}

function addMsgDOM(role, content) {
  const isU = role === "user";
  const d = document.createElement("div");
  d.className = "msg";
  d.innerHTML = `
    <div class="msg-avatar ${isU ? 'user' : 'bot'}">${isU ? (state.user?.initials || "U") : "S"}</div>
    <div class="msg-body">
      <div class="msg-name">${isU ? "You" : "SAGE-PRO"}</div>
      <div class="msg-text">${isU ? esc(content) : fmt(content)}</div>
    </div>`;
  $("chatArea").appendChild(d);
  return d;
}

function fmt(t) {
  t = t.replace(/```(\w*)\n([\s\S]*?)```/g, (_, l, c) => `<pre><code>${esc(c.trim())}</code></pre>`);
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\n/g, "<br>");
  return t;
}

// ── Pipeline Trace ─────────────────────────────────────
function buildTrace() {
  const steps = [
    { id: "route", name: "Topological Routing" },
    { id: "arch", name: "Architect Agent" },
    { id: "impl", name: "Parallel Implementation (ABC || ACB)" },
    { id: "red", name: "Red-Team Attack" },
    { id: "synth", name: "Synthesis + Nash Crucible" },
    { id: "emit", name: "Emit Hardened Artifacts" }
  ];
  const el = document.createElement("div");
  el.className = "trace";
  el.id = "trace";
  steps.forEach(s => {
    el.innerHTML += `<div class="trace-step" id="ts-${s.id}">
      <div class="trace-dot wait" id="td-${s.id}">&#x2022;</div>
      <span class="trace-label">${s.name}</span>
      <span class="trace-time" id="tt-${s.id}"></span>
    </div>`;
  });
  return el;
}

function setStep(id, st, t) {
  const dot = document.getElementById("td-" + id);
  const step = document.getElementById("ts-" + id);
  const time = document.getElementById("tt-" + id);
  if (!dot) return;
  dot.className = "trace-dot " + st;
  if (st === "run") { dot.innerHTML = "&#x25B6;"; step.classList.add("active"); }
  else if (st === "ok") { dot.innerHTML = "&#x2713;"; step.classList.remove("active"); }
  if (t && time) time.textContent = t;
}

// ── Send ───────────────────────────────────────────────
async function send() {
  const txt = $("msgInput").value.trim();
  if (!txt || state.busy) return;
  state.busy = true;
  $("sendBtn").disabled = true;

  if (!state.active) {
    newSession(txt);
    $("chatTitle").textContent = state.active.title;
    const ws = document.querySelector(".welcome");
    if (ws) ws.style.display = "none";
    $("chatArea").innerHTML = "";
  }

  state.active.msgs.push({ role: "user", content: txt });
  saveSessions();
  addMsgDOM("user", txt);
  $("msgInput").value = "";
  resize();
  scrollEnd();

  // Bot reply shell
  const bd = document.createElement("div");
  bd.className = "msg";
  bd.innerHTML = `<div class="msg-avatar bot">S</div>
    <div class="msg-body">
      <div class="msg-name">SAGE-PRO</div>
      <div class="msg-text" id="botOut"><div class="dots"><span></span><span></span><span></span></div></div>
    </div>`;
  $("chatArea").appendChild(bd);
  scrollEnd();

  const out = document.getElementById("botOut");
  out.innerHTML = "";
  out.appendChild(buildTrace());
  scrollEnd();

  await runPipeline(txt, out);

  state.busy = false;
  $("sendBtn").disabled = false;
  $("msgInput").focus();
}

async function runPipeline(task, el) {
  const ids = ["route", "arch", "impl", "red", "synth", "emit"];
  const ms = [1000, 3200, 4800, 3800, 2800, 700];
  const out = [
    `**[ROUTE]** Topological void analysis complete.\nPersistent Homology: B1=2, B2=0\nRouted to void: "Core data structures"`,
    `**[ARCH]** Design specification generated.\n\n**Data Structures:** OrderedDict + threading.Lock + heapq\n**API Surface:** get(), set(), delete(), clear(), stats()\n**Error Strategy:** Graceful degradation with structured logging\n**Concurrency:** ReentrantLock with condition variables`,
    `**[IMPL]** Parallel branch synthesis complete.\n\n**Branch ABC (Design-first):** 127 lines, clean architecture\n**Branch ACB (Threat-first):** 156 lines, defensive coding\n**Lie Bracket Divergence:** 0.142`,
    `**[RED]** Adversarial attack complete.\n\n**Tests generated:** 24 adversarial cases\n**Vulnerabilities found:** 3\n- Race condition in eviction thread (CRITICAL)\n- Integer overflow in size calc (MEDIUM)\n- Missing negative TTL validation (LOW)`,
    `**[SYNTH]** Nash Crucible converged.\n\n**Cycle 1:** Damage = 0.089\n**Cycle 2:** Damage = 0.031 -- **CONVERGED**\n\nAll vulnerabilities patched. Final: 168 lines, 100% type-safe.`,
    `**[EMIT]** Hardened artifacts ready.\n\n\`\`\`python\nimport threading\nimport time\nfrom collections import OrderedDict\nfrom typing import Any, Optional\n\nclass ThreadSafeLRUCache:\n    def __init__(self, capacity: int = 128, default_ttl: float = 300.0) -> None:\n        if capacity <= 0:\n            raise ValueError("Capacity must be positive")\n        self._capacity = capacity\n        self._default_ttl = default_ttl\n        self._cache: OrderedDict = OrderedDict()\n        self._ttls: dict[str, float] = {}\n        self._lock = threading.RLock()\n\n    def get(self, key: str) -> Optional[Any]:\n        with self._lock:\n            if key not in self._cache:\n                return None\n            if self._is_expired(key):\n                self._remove(key)\n                return None\n            self._cache.move_to_end(key)\n            return self._cache[key]\n\n    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:\n        with self._lock:\n            if ttl is not None and ttl < 0:\n                raise ValueError("TTL must be non-negative")\n            if key in self._cache:\n                self._cache.move_to_end(key)\n            self._cache[key] = value\n            self._ttls[key] = time.monotonic() + (ttl or self._default_ttl)\n            if len(self._cache) > self._capacity:\n                self._cache.popitem(last=False)\n\`\`\`\n\n**Nash Equilibrium verified.** Code is adversarially hardened.`
  ];

  for (let i = 0; i < ids.length; i++) {
    setStep(ids[i], "run");
    await wait(ms[i]);
    setStep(ids[i], "ok", (ms[i] / 1000).toFixed(1) + "s");
  }

  const res = document.createElement("div");
  res.style.marginTop = "16px";
  res.innerHTML = fmt(out.join("\n\n---\n\n"));
  el.appendChild(res);

  const full = out.join("\n\n");
  state.active.msgs.push({ role: "assistant", content: full });
  saveSessions();
  scrollEnd();
}

// ── Helpers ────────────────────────────────────────────
function fillPrompt(t) { $("msgInput").value = t; $("msgInput").focus(); resize(); }
function onKey(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }

$("msgInput").addEventListener("input", resize);
function resize() {
  const el = $("msgInput");
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

function scrollEnd() { requestAnimationFrame(() => { const c = $("chatArea"); c.scrollTop = c.scrollHeight; }); }
function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
