/* SAGE-PRO Frontend Application Logic */

// ── State ──────────────────────────────────────────────
const state = {
  user: null,
  sessions: [],
  activeSession: null,
  isProcessing: false,
};

// ── DOM References ─────────────────────────────────────
const $ = (id) => document.getElementById(id);
const loginPage = $("loginPage");
const appContainer = $("appContainer");
const loginForm = $("loginForm");
const loginError = $("loginError");
const chatArea = $("chatArea");
const welcomeScreen = $("welcomeScreen");
const messageInput = $("messageInput");
const sendBtn = $("sendBtn");
const historySection = $("historySection");
const chatTitle = $("chatTitle");

// ── Login ──────────────────────────────────────────────
loginForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const email = $("loginEmail").value.trim();
  const password = $("loginPassword").value;

  if (!email || !password) {
    showLoginError("Please fill in all fields.");
    return;
  }

  // Simulate auth (replace with real API call in production)
  state.user = {
    email: email,
    name: email.split("@")[0],
    initials: email[0].toUpperCase(),
  };

  localStorage.setItem("sage_user", JSON.stringify(state.user));
  loadSessions();
  enterApp();
});

function showLoginError(msg) {
  loginError.textContent = msg;
  loginError.style.display = "block";
  setTimeout(() => { loginError.style.display = "none"; }, 4000);
}

function enterApp() {
  loginPage.style.display = "none";
  appContainer.style.display = "block";
  $("userAvatar").textContent = state.user.initials;
  $("userName").textContent = state.user.name;
  messageInput.focus();
}

// ── Auto-login ─────────────────────────────────────────
(function checkAutoLogin() {
  const saved = localStorage.getItem("sage_user");
  if (saved) {
    state.user = JSON.parse(saved);
    loadSessions();
    enterApp();
  }
})();

// ── Logout ─────────────────────────────────────────────
$("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("sage_user");
  state.user = null;
  appContainer.style.display = "none";
  loginPage.style.display = "flex";
  $("loginEmail").value = "";
  $("loginPassword").value = "";
});

// ── Sessions / History ─────────────────────────────────
function loadSessions() {
  const saved = localStorage.getItem("sage_sessions");
  state.sessions = saved ? JSON.parse(saved) : [];
  renderHistory();
}

function saveSessions() {
  localStorage.setItem("sage_sessions", JSON.stringify(state.sessions));
}

function createSession(title) {
  const session = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    title: title.substring(0, 50),
    messages: [],
    createdAt: new Date().toISOString(),
  };
  state.sessions.unshift(session);
  state.activeSession = session;
  saveSessions();
  renderHistory();
  return session;
}

function renderHistory() {
  // Keep the label
  const label = historySection.querySelector(".history-label");
  historySection.innerHTML = "";
  if (label) historySection.appendChild(label);
  else {
    const lbl = document.createElement("div");
    lbl.className = "history-label";
    lbl.textContent = "Recent Sessions";
    historySection.appendChild(lbl);
  }

  state.sessions.forEach((s) => {
    const item = document.createElement("div");
    item.className = "history-item" + (state.activeSession && state.activeSession.id === s.id ? " active" : "");
    item.innerHTML = `
      <span class="history-item-icon">&#x1F4AC;</span>
      <span class="history-item-text">${escapeHtml(s.title)}</span>
    `;
    item.addEventListener("click", () => switchSession(s.id));
    historySection.appendChild(item);
  });
}

function switchSession(id) {
  const session = state.sessions.find((s) => s.id === id);
  if (!session) return;
  state.activeSession = session;
  chatTitle.textContent = session.title;
  renderHistory();
  renderMessages();
}

// ── New Chat ───────────────────────────────────────────
$("newChatBtn").addEventListener("click", () => {
  state.activeSession = null;
  chatTitle.textContent = "New Session";
  renderHistory();
  chatArea.innerHTML = "";
  chatArea.appendChild(welcomeScreen);
  welcomeScreen.style.display = "flex";
  messageInput.focus();
});

// ── Messages ───────────────────────────────────────────
function renderMessages() {
  chatArea.innerHTML = "";
  if (!state.activeSession || state.activeSession.messages.length === 0) {
    chatArea.appendChild(welcomeScreen);
    welcomeScreen.style.display = "flex";
    return;
  }
  welcomeScreen.style.display = "none";
  state.activeSession.messages.forEach((m) => {
    appendMessageToDOM(m.role, m.content);
  });
  scrollToBottom();
}

function appendMessageToDOM(role, content) {
  const div = document.createElement("div");
  div.className = "message";
  const isUser = role === "user";
  div.innerHTML = `
    <div class="message-avatar ${isUser ? 'user' : 'assistant'}">
      ${isUser ? (state.user ? state.user.initials : "U") : "S"}
    </div>
    <div class="message-body">
      <div class="message-sender">${isUser ? "You" : "SAGE-PRO"}</div>
      <div class="message-content">${isUser ? escapeHtml(content) : formatResponse(content)}</div>
    </div>
  `;
  chatArea.appendChild(div);
  return div;
}

function formatResponse(text) {
  // Convert markdown-like code blocks
  text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
  });
  // Inline code
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bold
  text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Line breaks
  text = text.replace(/\n/g, "<br>");
  return text;
}

// ── Pipeline Trace ─────────────────────────────────────
function createPipelineTrace() {
  const steps = [
    { id: "route", label: "Topological Routing" },
    { id: "arch", label: "Architect Agent" },
    { id: "impl", label: "Parallel Implementation (ABC || ACB)" },
    { id: "red", label: "Red-Team Attack" },
    { id: "synth", label: "Synthesis + Nash Crucible" },
    { id: "emit", label: "Emit Hardened Artifacts" },
  ];

  const trace = document.createElement("div");
  trace.className = "pipeline-trace";
  trace.id = "pipelineTrace";

  steps.forEach((s) => {
    trace.innerHTML += `
      <div class="pipeline-step" id="step-${s.id}">
        <div class="step-indicator waiting" id="ind-${s.id}">&#x2022;</div>
        <span class="step-label">${s.label}</span>
        <span class="step-time" id="time-${s.id}"></span>
      </div>
    `;
  });

  return trace;
}

function updateStep(stepId, status, timeStr) {
  const ind = document.getElementById("ind-" + stepId);
  const label = document.querySelector("#step-" + stepId + " .step-label");
  const time = document.getElementById("time-" + stepId);
  if (!ind) return;

  ind.className = "step-indicator " + status;
  if (status === "running") { ind.innerHTML = "&#x25B6;"; label.classList.add("active"); }
  else if (status === "done") { ind.innerHTML = "&#x2713;"; label.classList.remove("active"); }
  else if (status === "error") { ind.innerHTML = "&#x2717;"; }
  if (timeStr && time) time.textContent = timeStr;
}

// ── Send Message ───────────────────────────────────────
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || state.isProcessing) return;

  state.isProcessing = true;
  sendBtn.disabled = true;

  // Create session if needed
  if (!state.activeSession) {
    createSession(text);
    chatTitle.textContent = state.activeSession.title;
    welcomeScreen.style.display = "none";
    chatArea.innerHTML = "";
  }

  // Add user message
  state.activeSession.messages.push({ role: "user", content: text });
  saveSessions();
  appendMessageToDOM("user", text);
  messageInput.value = "";
  autoResize();
  scrollToBottom();

  // Create assistant message container with pipeline trace
  const assistantDiv = document.createElement("div");
  assistantDiv.className = "message";
  assistantDiv.innerHTML = `
    <div class="message-avatar assistant">S</div>
    <div class="message-body">
      <div class="message-sender">SAGE-PRO</div>
      <div class="message-content" id="assistantContent">
        <div class="typing-indicator"><span></span><span></span><span></span></div>
      </div>
    </div>
  `;
  chatArea.appendChild(assistantDiv);
  scrollToBottom();

  // Insert pipeline trace
  const content = document.getElementById("assistantContent");
  const trace = createPipelineTrace();
  content.innerHTML = "";
  content.appendChild(trace);
  scrollToBottom();

  // Simulate the adversarial pipeline
  await runPipeline(text, content);

  state.isProcessing = false;
  sendBtn.disabled = false;
  messageInput.focus();
}

async function runPipeline(task, contentEl) {
  const steps = ["route", "arch", "impl", "red", "synth", "emit"];
  const durations = [1200, 3500, 5000, 4000, 3000, 800];
  const outputs = [
    `**[ROUTE]** Topological void analysis complete.\nPersistent Homology: B1=2, B2=0.\nRouted to void: "Core data structures".`,

    `**[ARCH]** Design specification generated.\n\n**Data Structures:** OrderedDict + threading.Lock + heapq for TTL tracking.\n**API Surface:** get(), set(), delete(), clear(), stats().\n**Error Strategy:** Graceful degradation with structured logging.\n**Concurrency:** ReentrantLock with condition variables for async eviction.`,

    `**[IMPL]** Parallel branch synthesis complete.\n\n**Branch ABC (Design-first):** Clean architecture with type hints and docstrings. 127 lines.\n**Branch ACB (Threat-first):** Defensive coding with input validation and overflow protection. 156 lines.\n**Lie Bracket Divergence:** 0.142`,

    `**[RED]** Adversarial attack phase complete.\n\n**Tests generated:** 24 adversarial test cases.\n**Vulnerabilities found:** 3\n- Race condition in TTL eviction thread (CRITICAL)\n- Integer overflow in cache size calculation (MEDIUM)\n- Missing validation on negative TTL values (LOW)\n\nAll vulnerabilities will be patched during synthesis.`,

    `**[SYNTH]** Nash Crucible convergence achieved.\n\n**Cycle 1:** Damage = 0.089 (epsilon = 0.05)\n**Cycle 2:** Damage = 0.031 -- **CONVERGED**\n\nAll 3 Red-Team vulnerabilities resolved. Final code: 168 lines, 100% type-safe.`,

    `**[EMIT]** Hardened artifacts ready.\n\n\`\`\`python
import threading
import time
from collections import OrderedDict
from typing import Any, Optional

class ThreadSafeLRUCache:
    """Thread-safe LRU cache with TTL and async eviction."""

    def __init__(self, capacity: int = 128, default_ttl: float = 300.0) -> None:
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._capacity = capacity
        self._default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._ttls: dict[str, float] = {}
        self._lock = threading.RLock()
        self._eviction_thread = threading.Thread(
            target=self._eviction_loop, daemon=True
        )
        self._eviction_thread.start()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            if self._is_expired(key):
                self._remove(key)
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            if ttl is not None and ttl < 0:
                raise ValueError("TTL must be non-negative")
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            self._ttls[key] = time.monotonic() + (ttl or self._default_ttl)
            if len(self._cache) > self._capacity:
                self._cache.popitem(last=False)
\`\`\`\n\n**Nash Equilibrium verified.** Code is adversarially hardened.`,
  ];

  for (let i = 0; i < steps.length; i++) {
    updateStep(steps[i], "running");
    await sleep(durations[i]);
    updateStep(steps[i], "done", (durations[i] / 1000).toFixed(1) + "s");
  }

  // Append the full response after pipeline
  const responseDiv = document.createElement("div");
  responseDiv.style.marginTop = "16px";
  responseDiv.innerHTML = formatResponse(outputs.join("\n\n---\n\n"));
  contentEl.appendChild(responseDiv);

  // Save to session
  const fullResponse = outputs.join("\n\n");
  state.activeSession.messages.push({ role: "assistant", content: fullResponse });
  saveSessions();
  scrollToBottom();
}

// ── Quick Actions ──────────────────────────────────────
function setPrompt(text) {
  messageInput.value = text;
  messageInput.focus();
  autoResize();
}

// ── Input Handling ─────────────────────────────────────
function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

messageInput.addEventListener("input", autoResize);

function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
}

// ── Utilities ──────────────────────────────────────────
function scrollToBottom() {
  requestAnimationFrame(() => {
    chatArea.scrollTop = chatArea.scrollHeight;
  });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
