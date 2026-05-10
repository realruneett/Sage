#!/usr/bin/env python3
"""
SAGE — Strategic Adversarial Generative Engine
Chat Interface with live agent deliberation
"""

from __future__ import annotations

import os
import json
import time
import asyncio
import hashlib
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

import httpx
import gradio as gr

# ── Config ──────────────────────────────────────────────────────────────────

SAGE_API_URL = os.environ.get("SAGE_API_URL", "http://localhost:8000").rstrip("/")

AGENT_STYLES = {
    "SYSTEM":      {"icon": "○",  "color": "#555555"},
    "Architect":   {"icon": "◈",  "color": "#FF6B1A"},
    "Implementer": {"icon": "◆",  "color": "#FF8C42"},
    "Red-Team":    {"icon": "◉",  "color": "#FF4444"},
    "Red-Team-Pre":{"icon": "◉",  "color": "#FF4444"},
    "Synthesizer": {"icon": "◇",  "color": "#FFA040"},
    "COUNCIL":     {"icon": "◎",  "color": "#22C55E"},
    "ERROR":       {"icon": "✕",  "color": "#FF4444"},
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:      #080808;
    --bg2:     #0D0D0D;
    --card:    #111111;
    --bd:      #1E1E1E;
    --bd2:     #2A2A2A;
    --tx:      #BBBBBB;
    --txd:     #444444;
    --txh:     #FFFFFF;
    --ora:     #FF6B1A;
    --ora2:    #FF8C42;
    --green:   #22C55E;
    --red:     #FF4444;
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
footer { display: none !important; }
.built-with { display: none !important; }

/* ── Navbar ── */
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

/* ── Chat container ── */
#chat-wrap {
    max-width: 860px;
    margin: 0 auto;
    padding: 24px 16px 140px;
}

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 12px 0;
}
.msg-user-bubble {
    background: var(--ora);
    color: #000;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 70%;
    font-size: 14px;
    line-height: 1.6;
    font-family: var(--F);
}
.msg-sage {
    display: flex;
    gap: 12px;
    margin: 12px 0;
    align-items: flex-start;
}
.msg-sage-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255,107,26,0.15);
    border: 1px solid rgba(255,107,26,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 4px;
}
.msg-sage-content {
    flex: 1;
    max-width: calc(100% - 44px);
}
.msg-sage-bubble {
    background: var(--card);
    border: 1px solid var(--bd);
    border-radius: 4px 18px 18px 18px;
    padding: 14px 18px;
    font-size: 14px;
    line-height: 1.7;
    color: var(--txh);
    font-family: var(--F);
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
    background: #0D0D0D;
    border: 1px solid var(--bd);
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: var(--M);
    font-size: 12px;
    line-height: 1.7;
    color: #E8A87C;
}

/* ── Agent deliberation (dim) ── */
.deliberation {
    margin-bottom: 8px;
    padding: 8px 12px;
    border-left: 2px solid var(--bd2);
    font-family: var(--M);
    font-size: 11px;
    color: var(--txd);
    line-height: 1.6;
}
.deliberation-line {
    display: flex;
    gap: 8px;
    align-items: baseline;
    margin: 2px 0;
}
.d-agent {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    min-width: 80px;
    flex-shrink: 0;
}
.d-msg { color: #333; }

/* ── Thinking indicator ── */
.thinking {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 8px 0;
}
.thinking-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--ora);
    animation: bounce 1.4s infinite ease-in-out;
}
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
}

/* ── Input bar ── */
#input-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(8,8,8,0.97);
    border-top: 1px solid var(--bd);
    padding: 16px 24px;
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
    height: 48px !important;
    width: 48px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
    padding: 0 !important;
    min-width: 48px !important;
}
#send-btn button:hover {
    background: var(--ora2) !important;
    transform: scale(1.05) !important;
}
#send-btn button:disabled {
    background: var(--bd2) !important;
    color: var(--txd) !important;
    transform: none !important;
}

/* ── Settings row ── */
#settings-row {
    max-width: 860px;
    margin: 0 auto 8px;
    display: flex;
    gap: 12px;
    align-items: center;
}
#settings-row select, #settings-row input {
    background: var(--card) !important;
    border: 1px solid var(--bd) !important;
    border-radius: 8px !important;
    color: var(--tx) !important;
    font-size: 12px !important;
    padding: 6px 10px !important;
    font-family: var(--F) !important;
}
label span {
    font-size: 10px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--txd) !important;
}
input[type=range] { accent-color: var(--ora) !important; }

/* ── Empty state ── */
#empty-state {
    text-align: center;
    padding: 80px 24px;
    color: var(--txd);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--bd2); border-radius: 4px; }

.tabitem { background: transparent !important; border: none !important; }
"""

# ── Backend client ───────────────────────────────────────────────────────────

async def _stream_sage(query: str, max_cycles: int, priority: str) -> AsyncGenerator[Dict, None]:
    """Stream events from SAGE-PRO backend."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{SAGE_API_URL}/v1/sage/stream",
                json={"query": query, "max_cycles": max_cycles, "priority": priority},
            ) as resp:
                resp.raise_for_status()
                async for raw in resp.aiter_lines():
                    line = raw.strip()
                    if not line or line.startswith(":"): continue
                    if line.startswith("data: "): line = line[6:]
                    elif line.startswith("data:"): line = line[5:]
                    else: continue
                    try:
                        yield json.loads(line)
                    except:
                        continue
    except Exception as e:
        yield {"event": "error", "content": str(e), "agent": "ERROR", "meta": {}}


def _backend_available() -> bool:
    try:
        r = httpx.get(f"{SAGE_API_URL}/healthz", timeout=3.0)
        return r.status_code == 200
    except:
        return False


# ── HTML builders ────────────────────────────────────────────────────────────

def navbar_html() -> str:
    mode = "PRO" if SAGE_API_URL and _backend_available() else "DEMO"
    color = "#FF6B1A" if mode == "PRO" else "#6A4C93"
    return f"""
<div id="sage-navbar">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-family:'Inter',sans-serif;font-size:20px;font-weight:800;color:#fff;letter-spacing:-0.03em;">SAGE</span>
    <span style="width:6px;height:6px;border-radius:50%;background:#FF6B1A;"></span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#444;letter-spacing:0.1em;">STRATEGIC ADVERSARIAL GENERATIVE ENGINE</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;background:rgba(255,107,26,0.1);border:1px solid rgba(255,107,26,0.3);color:{color};padding:4px 10px;border-radius:4px;letter-spacing:0.08em;">{mode}</span>
    <span style="font-size:11px;color:#333;font-family:'Inter',sans-serif;">AMD MI300X · 192 GB HBM3</span>
  </div>
</div>"""


def user_bubble(text: str) -> str:
    return f"""
<div class="msg-user">
  <div class="msg-user-bubble">{text}</div>
</div>"""


def thinking_bubble() -> str:
    return """
<div class="msg-sage">
  <div class="msg-sage-avatar">◈</div>
  <div class="msg-sage-content">
    <div class="thinking">
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
    </div>
  </div>
</div>"""


def sage_bubble(deliberation_lines: List[Tuple[str, str]], final_answer: str) -> str:
    delib_html = ""
    if deliberation_lines:
        lines_html = ""
        for agent, msg in deliberation_lines:
            style = AGENT_STYLES.get(agent, {"icon": "○", "color": "#555"})
            lines_html += f"""
      <div class="deliberation-line">
        <span class="d-agent" style="color:{style['color']};">{style['icon']} {agent}</span>
        <span class="d-msg">{msg[:120]}</span>
      </div>"""
        delib_html = f'<div class="deliberation">{lines_html}</div>'

    # Format final answer - handle code blocks
    import re
    formatted = final_answer
    # Wrap code blocks
    formatted = re.sub(r'```(\w*)\n(.*?)```', lambda m: f'<pre><code>{m.group(2)}</code></pre>', formatted, flags=re.DOTALL)
    # Inline code
    formatted = re.sub(r'`([^`]+)`', r'<code>\1</code>', formatted)

    return f"""
<div class="msg-sage">
  <div class="msg-sage-avatar" style="color:#FF6B1A;">◎</div>
  <div class="msg-sage-content">
    {delib_html}
    <div class="msg-sage-bubble">{formatted}</div>
  </div>
</div>"""


def empty_state_html() -> str:
    return """
<div id="empty-state">
  <div style="font-size:48px;color:#1A1A1A;margin-bottom:20px;">◎</div>
  <div style="font-family:'Inter',sans-serif;font-size:22px;font-weight:700;color:#fff;margin-bottom:8px;">
    Ask SAGE anything
  </div>
  <div style="font-size:14px;color:#444;max-width:480px;margin:0 auto;line-height:1.7;">
    Code, analysis, creative writing, emotional support — the 4-agent council handles any query
    through adversarial deliberation and Nash equilibrium convergence.
  </div>
  <div style="display:flex;gap:12px;justify-content:center;margin-top:28px;flex-wrap:wrap;">
    <div style="background:#111;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#666;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='Build a Redis rate limiter';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      🔧 Build a Redis rate limiter
    </div>
    <div style="background:#111;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#666;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='I feel overwhelmed today';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      ❤️ I feel overwhelmed today
    </div>
    <div style="background:#111;border:1px solid #1E1E1E;border-radius:10px;padding:12px 18px;font-size:13px;color:#666;cursor:pointer;"
         onclick="document.querySelector('#msg-input textarea').value='Explain quantum entanglement simply';document.querySelector('#msg-input textarea').dispatchEvent(new Event('input'))">
      🧠 Explain quantum entanglement
    </div>
  </div>
</div>"""


# ── Main UI ──────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="SAGE — Strategic Adversarial Generative Engine") as demo:

        # State: list of (role, html_content) tuples
        # role = "user" | "sage"
        chat_history = gr.State([])  # list of {"role": str, "delib": list, "text": str, "query": str}

        # Navbar
        gr.HTML(navbar_html())

        # Chat display
        with gr.Column(elem_id="chat-wrap"):
            chat_display = gr.HTML(value=empty_state_html())

        # Fixed input bar
        with gr.Column(elem_id="input-bar"):
            # Settings row
            with gr.Row(elem_id="settings-row"):
                priority_dd = gr.Dropdown(
                    choices=["balanced", "performance", "security"],
                    value="balanced",
                    label="Priority",
                    scale=1,
                )
                cycles_sl = gr.Slider(
                    minimum=1, maximum=4, step=1, value=1,
                    label="Max Cycles",
                    scale=2,
                )

            # Input row
            with gr.Row(elem_id="input-inner"):
                msg_input = gr.Textbox(
                    placeholder="Ask anything — code, analysis, creative, emotional...",
                    lines=1,
                    max_lines=6,
                    show_label=False,
                    elem_id="msg-input",
                    scale=10,
                    submit_btn=True,
                )
                send_btn = gr.Button("↑", variant="primary", elem_id="send-btn", scale=1)

        # ── Helpers ──────────────────────────────────────────────────────────

        def render_chat(history: list) -> str:
            if not history:
                return empty_state_html()
            html = ""
            for msg in history:
                if msg["role"] == "user":
                    html += user_bubble(msg["text"])
                elif msg["role"] == "thinking":
                    html += thinking_bubble()
                elif msg["role"] == "sage":
                    html += sage_bubble(msg.get("delib", []), msg["text"])
            return html

        # ── Submit handler ────────────────────────────────────────────────────

        async def on_submit(query: str, history: list, priority: str, max_cycles: int):
            if not query.strip():
                yield gr.update(), gr.update(), history
                return

            # Add user message + thinking indicator
            history = history + [
                {"role": "user", "text": query},
                {"role": "thinking"},
            ]
            yield gr.update(value=""), gr.update(value=render_chat(history)), history

            # Stream from backend
            deliberation: List[Tuple[str, str]] = []
            final_answer = ""
            live = _backend_available()

            if live:
                async for evt in _stream_sage(query, max_cycles, priority):
                    event_type = evt.get("event", "")
                    agent = evt.get("agent", "SYSTEM")
                    content = evt.get("content", "")

                    if event_type == "error":
                        final_answer = f"Pipeline error: {content}"
                        break
                    elif event_type == "pipeline_done":
                        final_answer = content
                        break
                    elif event_type in ("agent_start", "agent_done", "agent_token"):
                        if content:
                            deliberation.append((agent, content))
                            # Update thinking display with live deliberation
                            live_history = history[:-1] + [{
                                "role": "sage",
                                "delib": deliberation,
                                "text": "⏳ Deliberating...",
                            }]
                            yield gr.update(), gr.update(value=render_chat(live_history)), history
            else:
                # Demo mode
                demo_steps = [
                    ("Architect", "Analysing task manifold and topology..."),
                    ("Red-Team", "Pre-attack scan for threat vectors..."),
                    ("Implementer", "Branch ABC: performance-first synthesis..."),
                    ("Implementer", "Branch ACB: security-first synthesis..."),
                    ("Synthesizer", "Nash equilibrium convergence cycle 1..."),
                    ("COUNCIL", "Artifact sealed ✓"),
                ]
                for agent, msg in demo_steps:
                    deliberation.append((agent, msg))
                    live_history = history[:-1] + [{
                        "role": "sage",
                        "delib": deliberation,
                        "text": "⏳ Deliberating...",
                    }]
                    yield gr.update(), gr.update(value=render_chat(live_history)), history
                    await asyncio.sleep(0.4)
                final_answer = f"[Demo mode — connect SAGE_API_URL for live inference]\n\nYou asked: {query}\n\nThis is a simulated response. Set SAGE_API_URL to your backend URL to get real adversarially-hardened answers."

            # Replace thinking with final sage bubble
            history = history[:-1] + [{
                "role": "sage",
                "delib": deliberation,
                "text": final_answer,
                "query": query,
            }]
            yield gr.update(), gr.update(value=render_chat(history)), history

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


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        favicon_path=None,
    )
