#!/usr/bin/env python3
"""
SAGE — Strategic Adversarial Generative Engine
Complexity router · Model tiers · Persistent memory · Debate mode
"""
from __future__ import annotations

import os
import re
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Tuple

import httpx
import gradio as gr

# ── Config ────────────────────────────────────────────────────────────────────

SAGE_API_URL   = os.environ.get("SAGE_API_URL",  "http://localhost:8000").rstrip("/")
HISTORY_FILE   = Path(os.environ.get("HISTORY_FILE", "/data/sage_history.json"))
HISTORY_WINDOW = 20   # how many past messages to send as context

# ── Model Registry ────────────────────────────────────────────────────────────

MODELS = {
    "fast":      "codellama:34b",         # 24 GB  — simple queries
    "capable":   "qwen2.5-coder:32b",     # 30 GB  — medium / implementer in debates
    "reasoning": "deepseek-r1:32b",       # 64 GB  — architect / debate lead
    "coder":     "deepseek-coder-v2:16b", # light  — fallback coder
}

# ── Complexity Tiers ──────────────────────────────────────────────────────────

TIERS: Dict[str, Dict] = {
    "simple": {
        "label":       "Single · Fast",
        "color":       "#22C55E",
        "primary":     "fast",
        "secondary":   None,
        "debate":      False,
        "description": "codellama:34b",
    },
    "medium": {
        "label":       "Single · Capable",
        "color":       "#FF8C42",
        "primary":     "capable",
        "secondary":   None,
        "debate":      False,
        "description": "qwen2.5-coder:32b",
    },
    "complex": {
        "label":       "Debate · Full Council",
        "color":       "#FF4444",
        "primary":     "reasoning",
        "secondary":   "capable",
        "debate":      True,
        "description": "deepseek-r1:32b ⟷ qwen2.5-coder:32b",
    },
}

# ── Complexity Router ─────────────────────────────────────────────────────────

_SIMPLE_RE = re.compile(
    r'\b(what is|what are|define|who is|when was|where is|'
    r'how do i|list|show me|tell me|explain briefly|'
    r'simple|quick|basic|example of|give me an? example)\b',
    re.I,
)
_COMPLEX_RE = re.compile(
    r'\b(architect|system design|scalab|distributed|microservice|'
    r'optimi[sz]e|refactor|deep.?dive|internals|under the hood|'
    r'implement.*from scratch|production.?ready|full.*implementation|'
    r'security|vulnerabilit|threat model|audit|'
    r'algorithm|data structure|big.?o|complexity analysis|'
    r'why does|how does.*work internally|'
    r'compare|trade.?off|benchmark|review my|what.s wrong with)\b',
    re.I,
)

def route_complexity(query: str) -> str:
    """Return 'simple', 'medium', or 'complex'."""
    q        = query.strip()
    words    = len(q.split())
    has_code = "```" in q or q.count("\n") > 3

    if words < 14 and _SIMPLE_RE.search(q) and not has_code:
        return "simple"

    complex_hits = len(_COMPLEX_RE.findall(q))
    if complex_hits >= 2:
        return "complex"
    if complex_hits == 1 and words > 35:
        return "complex"
    if words > 70:
        return "complex"
    if words > 22 or has_code:
        return "medium"
    if _SIMPLE_RE.search(q):
        return "simple"

    return "medium"

# ── Persistent History ────────────────────────────────────────────────────────

def load_history() -> list:
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text())
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

def save_history(history: list) -> None:
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        saveable = [h for h in history if h["role"] in ("user", "sage")]
        HISTORY_FILE.write_text(json.dumps(saveable, indent=2, ensure_ascii=False))
    except Exception:
        pass

def history_for_backend(history: list) -> list:
    msgs = []
    for h in history[-HISTORY_WINDOW:]:
        if h["role"] == "user":
            msgs.append({"role": "user",      "content": h["text"]})
        elif h["role"] == "sage":
            msgs.append({"role": "assistant", "content": h["text"]})
    return msgs

# ── Agent Styles ──────────────────────────────────────────────────────────────

AGENT_STYLES = {
    "SYSTEM":       {"icon": "○",  "color": "#555555"},
    "Router":       {"icon": "⬡",  "color": "#818CF8"},
    "Architect":    {"icon": "◈",  "color": "#FF6B1A"},
    "Implementer":  {"icon": "◆",  "color": "#FF8C42"},
    "Red-Team":     {"icon": "◉",  "color": "#FF4444"},
    "Red-Team-Pre": {"icon": "◉",  "color": "#FF4444"},
    "Synthesizer":  {"icon": "◇",  "color": "#FFA040"},
    "COUNCIL":      {"icon": "◎",  "color": "#22C55E"},
    "ERROR":        {"icon": "✕",  "color": "#FF4444"},
}

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:    #080808;
    --bg2:   #0D0D0D;
    --card:  #111111;
    --bd:    #1E1E1E;
    --bd2:   #2A2A2A;
    --tx:    #BBBBBB;
    --txd:   #333333;
    --txh:   #FFFFFF;
    --ora:   #FF6B1A;
    --ora2:  #FF8C42;
    --green: #22C55E;
    --red:   #FF4444;
    --F: 'Inter', sans-serif;
    --M: 'JetBrains Mono', monospace;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body, .gradio-container {
    background: var(--bg) !important;
    font-family: var(--F) !important;
    color: var(--tx) !important;
}
.gradio-container { max-width: 100% !important; padding: 0 !important; }
footer, .built-with { display: none !important; }

#sage-navbar {
    background: rgba(8,8,8,0.97);
    border-bottom: 1px solid var(--bd);
    padding: 0 32px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    backdrop-filter: blur(12px);
}
#chat-wrap {
    max-width: 860px;
    margin: 0 auto;
    padding: 24px 16px 160px;
}
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 16px 0 4px;
}
.msg-user-bubble {
    background: var(--ora);
    color: #000;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 72%;
    font-size: 14px;
    line-height: 1.65;
    font-weight: 500;
}
.msg-sage {
    display: flex;
    gap: 12px;
    margin: 4px 0 16px;
    align-items: flex-start;
}
.msg-sage-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: rgba(255,107,26,0.12);
    border: 1px solid rgba(255,107,26,0.25);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; margin-top: 2px;
}
.msg-sage-content { flex: 1; max-width: calc(100% - 44px); }
.tier-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--M);
    font-size: 10px;
    letter-spacing: 0.06em;
    padding: 3px 10px;
    border-radius: 4px;
    border: 1px solid;
    margin-bottom: 6px;
    opacity: 0.75;
}
.deliberation {
    padding: 4px 0 6px 12px;
    border-left: 2px solid #181818;
    margin-bottom: 6px;
    font-family: var(--M);
    font-size: 11px;
    line-height: 1.65;
}
.deliberation-line {
    display: flex;
    gap: 8px;
    align-items: baseline;
    margin: 3px 0;
    opacity: 0.4;
    transition: opacity 0.15s;
}
.deliberation-line:hover { opacity: 0.75; }
.d-agent {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    min-width: 82px;
    flex-shrink: 0;
}
.d-msg { color: #555; }
.msg-sage-bubble {
    background: var(--card);
    border: 1px solid var(--bd);
    border-radius: 4px 18px 18px 18px;
    padding: 14px 18px;
    font-size: 14px;
    line-height: 1.75;
    color: var(--txh);
    white-space: pre-wrap;
    word-wrap: break-word;
}
.msg-sage-bubble code {
    font-family: var(--M);
    background: #0D0D0D;
    border: 1px solid var(--bd);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
    color: #FF8C42;
}
.msg-sage-bubble pre {
    background: #0A0A0A;
    border: 1px solid var(--bd);
    border-radius: 8px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: var(--M);
    font-size: 12px;
    line-height: 1.7;
    color: #E8A87C;
}
.thinking { display: flex; gap: 4px; align-items: center; padding: 10px 0; }
.thinking-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--ora);
    animation: bounce 1.4s infinite ease-in-out;
}
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.35; }
    40%           { transform: scale(1);   opacity: 1; }
}
#input-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(8,8,8,0.97);
    border-top: 1px solid var(--bd);
    padding: 14px 24px 18px;
    backdrop-filter: blur(12px);
    z-index: 998;
}
#input-inner {
    max-width: 860px;
    margin: 0 auto;
    display: flex;
    gap: 10px;
    align-items: flex-end;
}
#msg-input textarea {
    background: var(--card) !important;
    border: 1px solid var(--bd) !important;
    border-radius: 12px !important;
    color: var(--txh) !important;
    font-family: var(--F) !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    resize: none !important;
    min-height: 48px !important;
    max-height: 160px !important;
    transition: border-color 0.2s !important;
}
#msg-input textarea:focus {
    border-color: var(--ora) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(255,107,26,0.08) !important;
}
#send-btn button {
    background: var(--ora) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 12px !important;
    height: 48px !important; width: 48px !important;
    font-size: 18px !important; font-weight: 700 !important;
    padding: 0 !important; min-width: 48px !important;
    transition: all 0.2s !important;
}
#send-btn button:hover    { background: var(--ora2) !important; transform: scale(1.05) !important; }
#send-btn button:disabled { background: var(--bd2)  !important; color: var(--txd) !important; transform: none !important; }
#settings-row {
    max-width: 860px;
    margin: 0 auto 10px;
    display: flex; gap: 12px; align-items: center;
}
#settings-row select {
    background: var(--card) !important;
    border: 1px solid var(--bd) !important;
    border-radius: 8px !important;
    color: var(--tx) !important;
    font-size: 12px !important;
    padding: 6px 10px !important;
}
label span {
    font-size: 10px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--txd) !important;
}
input[type=range] { accent-color: var(--ora) !important; }
#empty-state { text-align: center; padding: 80px 24px; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--bd2); border-radius: 4px; }
.tabitem { background: transparent !important; border: none !important; }
#clear-btn button {
    background: transparent !important;
    border: 1px solid #2A2A2A !important;
    color: #444 !important;
    border-radius: 8px !important;
    font-size: 11px !important;
    padding: 4px 12px !important;
    font-family: var(--M) !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
#clear-btn button:hover { border-color: var(--red) !important; color: var(--red) !important; }
"""

# ── Backend client ────────────────────────────────────────────────────────────

async def _stream_sage(
    query: str,
    history: list,
    max_cycles: int,
    priority: str,
    tier: str,
) -> AsyncGenerator[Dict, None]:
    tier_cfg = TIERS[tier]
    payload  = {
        "query":      query,
        "history":    history,
        "max_cycles": max_cycles,
        "priority":   priority,
        "tier":       tier,
        "model":      MODELS[tier_cfg["primary"]],
        "model2":     MODELS[tier_cfg["secondary"]] if tier_cfg["secondary"] else None,
        "debate":     tier_cfg["debate"],
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{SAGE_API_URL}/v1/sage/stream",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for raw in resp.aiter_lines():
                    line = raw.strip()
                    if not line or line.startswith(":"): continue
                    if line.startswith("data: "):  line = line[6:]
                    elif line.startswith("data:"): line = line[5:]
                    else: continue
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
    except Exception as e:
        yield {"event": "error", "content": str(e), "agent": "ERROR", "meta": {}}


def _backend_available() -> bool:
    try:
        r = httpx.get(f"{SAGE_API_URL}/healthz", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False

# ── HTML builders ─────────────────────────────────────────────────────────────

def navbar_html() -> str:
    live  = _backend_available()
    mode  = "LIVE" if live else "DEMO"
    color = "#22C55E" if live else "#818CF8"
    return f"""
<div id="sage-navbar">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:20px;font-weight:800;color:#fff;letter-spacing:-0.03em;">SAGE</span>
    <span style="width:6px;height:6px;border-radius:50%;background:#FF6B1A;"></span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#3A3A3A;letter-spacing:0.1em;">STRATEGIC ADVERSARIAL GENERATIVE ENGINE</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;background:rgba(255,107,26,0.08);border:1px solid rgba(255,107,26,0.2);color:{color};padding:4px 10px;border-radius:4px;letter-spacing:0.08em;">{mode}</span>
    <span style="font-size:11px;color:#2A2A2A;">AMD MI300X · 192 GB HBM3</span>
  </div>
</div>"""


def user_bubble(text: str) -> str:
    return f'<div class="msg-user"><div class="msg-user-bubble">{text}</div></div>'


def thinking_bubble(tier: str = "medium") -> str:
    cfg   = TIERS.get(tier, TIERS["medium"])
    color = cfg["color"]
    return f"""
<div class="msg-sage">
  <div class="msg-sage-avatar">◈</div>
  <div class="msg-sage-content">
    <div class="tier-badge" style="color:{color};border-color:{color}30;background:{color}0D;">
      ⬡ {cfg['label']} &nbsp;·&nbsp; {cfg['description']}
    </div>
    <div class="thinking">
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
    </div>
  </div>
</div>"""


def sage_bubble(tier: str, deliberation_lines: List[Tuple[str, str]], final_answer: str) -> str:
    cfg   = TIERS.get(tier, TIERS["medium"])
    color = cfg["color"]

    badge = (
        f'<div class="tier-badge" style="color:{color};border-color:{color}30;background:{color}0D;">'
        f'⬡ {cfg["label"]} &nbsp;·&nbsp; {cfg["description"]}</div>'
    )

    delib_html = ""
    if deliberation_lines:
        lines_html = ""
        for agent, msg in deliberation_lines:
            st = AGENT_STYLES.get(agent, {"icon": "○", "color": "#555"})
            lines_html += (
                f'<div class="deliberation-line">'
                f'<span class="d-agent" style="color:{st["color"]};">{st["icon"]} {agent}</span>'
                f'<span class="d-msg">{msg[:140]}</span></div>'
            )
        delib_html = f'<div class="deliberation">{lines_html}</div>'

    formatted = re.sub(
        r'```(\w*)\n(.*?)```',
        lambda m: f'<pre><code>{m.group(2)}</code></pre>',
        final_answer, flags=re.DOTALL,
    )
    formatted = re.sub(r'`([^`]+)`', r'<code>\1</code>', formatted)

    return (
        f'<div class="msg-sage">'
        f'<div class="msg-sage-avatar" style="color:#FF6B1A;">◎</div>'
        f'<div class="msg-sage-content">{badge}{delib_html}'
        f'<div class="msg-sage-bubble">{formatted}</div></div></div>'
    )


def empty_state_html() -> str:
    return """
<div id="empty-state">
  <div style="font-size:48px;color:#181818;margin-bottom:20px;">◎</div>
  <div style="font-size:22px;font-weight:700;color:#fff;margin-bottom:8px;">Ask SAGE anything</div>
  <div style="font-size:13px;color:#333;max-width:480px;margin:0 auto;line-height:1.8;">
    Simple queries load one fast model. Complex problems trigger the full council —
    Architect debates Implementer until the best answer emerges.
  </div>
  <div style="display:flex;gap:10px;justify-content:center;margin-top:28px;flex-wrap:wrap;">
    <div style="background:#0E0E0E;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#555;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='Build a Redis rate limiter in Python';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      🔧 Build a Redis rate limiter
    </div>
    <div style="background:#0E0E0E;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#555;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='Design a distributed task queue system from scratch with fault tolerance';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      🏗 Design a distributed task queue
    </div>
    <div style="background:#0E0E0E;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#555;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='What is a context manager in Python?';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      🧠 What is a context manager?
    </div>
  </div>
</div>"""

# ── Main UI ───────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    initial_history = load_history()

    with gr.Blocks(css=CSS, title="SAGE — Strategic Adversarial Generative Engine") as demo:

        chat_history = gr.State(initial_history)

        gr.HTML(navbar_html())

        with gr.Column(elem_id="chat-wrap"):
            init_html = _render_chat(initial_history) if initial_history else empty_state_html()
            chat_display = gr.HTML(value=init_html)

        with gr.Column(elem_id="input-bar"):
            with gr.Row(elem_id="settings-row"):
                priority_dd = gr.Dropdown(
                    choices=["balanced", "performance", "security"],
                    value="balanced",
                    label="Priority",
                    scale=1,
                )
                cycles_sl = gr.Slider(
                    minimum=1, maximum=4, step=1, value=2,
                    label="Max Cycles",
                    scale=2,
                )
                clear_btn = gr.Button("✕ Clear history", elem_id="clear-btn", scale=1)

            with gr.Row(elem_id="input-inner"):
                msg_input = gr.Textbox(
                    placeholder="Ask anything — SAGE routes to the right model automatically...",
                    lines=1,
                    max_lines=6,
                    show_label=False,
                    elem_id="msg-input",
                    scale=10,
                    submit_btn=True,
                )
                send_btn = gr.Button("↑", variant="primary", elem_id="send-btn", scale=1)

        # ── Helpers ───────────────────────────────────────────────────────────

        def _render_chat(history: list) -> str:
            if not history:
                return empty_state_html()
            html = ""
            for msg in history:
                role = msg.get("role")
                if role == "user":
                    html += user_bubble(msg["text"])
                elif role == "thinking":
                    html += thinking_bubble(msg.get("tier", "medium"))
                elif role == "sage":
                    html += sage_bubble(
                        msg.get("tier", "medium"),
                        msg.get("delib", []),
                        msg["text"],
                    )
            return html

        def on_clear(history: list):
            save_history([])
            return [], empty_state_html()

        clear_btn.click(fn=on_clear, inputs=[chat_history], outputs=[chat_history, chat_display])

        # ── Submit ────────────────────────────────────────────────────────────

        async def on_submit(query: str, history: list, priority: str, max_cycles: int):
            if not query.strip():
                yield gr.update(), gr.update(), history
                return

            tier = route_complexity(query)

            history = history + [
                {"role": "user",     "text": query},
                {"role": "thinking", "tier": tier},
            ]
            yield gr.update(value=""), gr.update(value=_render_chat(history)), history

            deliberation: List[Tuple[str, str]] = []
            final_answer = ""
            live = _backend_available()

            if live:
                backend_history = history_for_backend(history[:-2])
                async for evt in _stream_sage(query, backend_history, max_cycles, priority, tier):
                    event_type = evt.get("event", "")
                    agent      = evt.get("agent", "SYSTEM")
                    content    = evt.get("content", "")

                    if event_type == "error":
                        final_answer = f"Pipeline error: {content}"
                        break
                    elif event_type == "pipeline_done":
                        final_answer = content
                        break
                    elif event_type in ("agent_start", "agent_done", "agent_token"):
                        if content:
                            deliberation.append((agent, content))
                            live_history = history[:-1] + [{
                                "role":  "sage",
                                "tier":  tier,
                                "delib": deliberation,
                                "text":  "⏳ Deliberating...",
                            }]
                            yield gr.update(), gr.update(value=_render_chat(live_history)), history
            else:
                # Demo mode
                if tier == "simple":
                    demo_steps = [
                        ("Router",    f"Simple query → loading {MODELS['fast']}"),
                        ("Architect", "Analysing request..."),
                        ("COUNCIL",   "Answer ready ✓"),
                    ]
                elif tier == "medium":
                    demo_steps = [
                        ("Router",      f"Medium query → loading {MODELS['capable']}"),
                        ("Architect",   "Scoping task complexity..."),
                        ("Implementer", "Drafting solution..."),
                        ("COUNCIL",     "Answer ready ✓"),
                    ]
                else:
                    demo_steps = [
                        ("Router",      f"Complex query → {MODELS['reasoning']} + {MODELS['capable']}"),
                        ("Architect",   "Analysing task manifold and topology..."),
                        ("Red-Team",    "Pre-attack scan for threat vectors..."),
                        ("Implementer", "Branch ABC: performance-first synthesis..."),
                        ("Implementer", "Branch ACB: security-first synthesis..."),
                        ("Synthesizer", "Nash equilibrium convergence cycle 1..."),
                        ("COUNCIL",     "Artifact sealed ✓"),
                    ]

                for agent, msg in demo_steps:
                    deliberation.append((agent, msg))
                    live_history = history[:-1] + [{
                        "role":  "sage",
                        "tier":  tier,
                        "delib": deliberation,
                        "text":  "⏳ Deliberating...",
                    }]
                    yield gr.update(), gr.update(value=_render_chat(live_history)), history
                    await asyncio.sleep(0.35)

                final_answer = (
                    f"[Demo mode — set SAGE_API_URL to enable live inference]\n\n"
                    f"Tier: {TIERS[tier]['label']}  |  Models: {TIERS[tier]['description']}\n\n"
                    f"You asked: {query}"
                )

            history = history[:-1] + [{
                "role":  "sage",
                "tier":  tier,
                "delib": deliberation,
                "text":  final_answer,
                "query": query,
            }]
            save_history(history)
            yield gr.update(), gr.update(value=_render_chat(history)), history

        send_btn.click(
            fn=on_submit,
            inputs=[msg_input, chat_history, priority_dd, cycles_sl],
            outputs=[msg_input, chat_display, chat_history],
        )
        msg_input.submit(
            fn=on_submit,
            inputs=[msg_input, chat_history, priority_dd, cycles_sl],
            outputs=[msg_input, chat_display, chat_history],
        )

    return demo


def _render_chat(history: list) -> str:
    if not history:
        return empty_state_html()
    html = ""
    for msg in history:
        role = msg.get("role")
        if role == "user":
            html += user_bubble(msg["text"])
        elif role == "thinking":
            html += thinking_bubble(msg.get("tier", "medium"))
        elif role == "sage":
            html += sage_bubble(
                msg.get("tier", "medium"),
                msg.get("delib", []),
                msg["text"],
            )
    return html

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    app  = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        favicon_path=None,
    )
