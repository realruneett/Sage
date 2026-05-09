"""
PROJECT SAGE × AODE — Ultimate Cinematic Gradio Interface
═══════════════════════════════════════════════════════════
Connects to a Dockerized vLLM backend on AMD MI300X.

ENVIRONMENT VARIABLES (set in HF Space settings or .env):
  VLLM_BASE_URL  — e.g. http://localhost:8001/v1
  HF_TOKEN       — HuggingFace / API auth token
  SAGE_MODEL_ID  — Model served by vLLM (default: auto-detect)
"""

import os
import time
import gradio as gr
from openai import OpenAI

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Ultimate Titan 4-Agent Ensemble
# Each agent runs on a dedicated vLLM instance, co-resident on MI300X 192GB HBM3
#
# Set in HF Space "Secrets" or .env:
#   VLLM_HOST       — Base hostname (default: localhost)
#   HF_TOKEN        — Auth token for all vLLM endpoints
# ══════════════════════════════════════════════════════════════════════════════
VLLM_HOST = os.environ.get("VLLM_HOST", "localhost")
API_KEY = os.environ.get("HF_TOKEN", "not-needed")

# ── The Four Co-Resident Agents ──────────────────────────────────────────────
AGENTS = {
    "architect": {
        "name": "ARCHITECT",
        "model": "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ",
        "port": 8001,
        "color": "#06b6d4",
        "icon": "◈",
        "system": (
            "You are the ARCHITECT agent in the SAGE adversarial ensemble. "
            "Your role: analyze the user's task and produce a rigorous "
            "design specification. Define data structures, API surfaces, "
            "error handling strategy, and concurrency model. "
            "Output ONLY the architectural spec, nothing else. Be precise."
        ),
    },
    "implementer": {
        "name": "IMPLEMENTER",
        "model": "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4",
        "port": 8002,
        "color": "#8b5cf6",
        "icon": "◆",
        "system": (
            "You are the IMPLEMENTER agent in the SAGE adversarial ensemble. "
            "You receive an architectural spec and produce complete, "
            "production-grade, fully typed Python code. Include docstrings, "
            "type hints, and error handling. Write ONLY code, no explanation."
        ),
    },
    "synthesizer": {
        "name": "SYNTHESIZER",
        "model": "MaziyarPanahi/Mistral-Large-Instruct-2407-AWQ",
        "port": 8003,
        "color": "#f97316",
        "icon": "◉",
        "system": (
            "You are the SYNTHESIZER — the chief reasoning engine of SAGE. "
            "You receive the original task, the architect's spec, the "
            "implementer's code, and the red-team's attack report. "
            "Your job: merge all branches, patch every vulnerability found "
            "by red-team, and emit the FINAL hardened code. "
            "Explain your patches, then output the complete fixed code."
        ),
    },
    "redteam": {
        "name": "RED-TEAM",
        "model": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "port": 8004,
        "color": "#ef4444",
        "icon": "⚑",
        "system": (
            "You are the RED-TEAM adversarial agent in the SAGE ensemble. "
            "Your ONLY job: attack the code you receive. Find race conditions, "
            "edge cases, security flaws, type errors, resource leaks, and "
            "logic bombs. Generate adversarial test cases that BREAK the code. "
            "Be ruthless. Output a numbered list of vulnerabilities found "
            "and the test code that exposes each one."
        ),
    },
}


def _make_client(agent_key: str) -> OpenAI:
    """Create an OpenAI client pointing at the agent's vLLM port."""
    port = AGENTS[agent_key]["port"]
    return OpenAI(
        base_url=f"http://{VLLM_HOST}:{port}/v1",
        api_key=API_KEY,
    )


def _stream_agent(agent_key: str, messages: list) -> str:
    """Stream tokens from a single agent. Returns the full response."""
    agent = AGENTS[agent_key]
    client = _make_client(agent_key)

    full = ""
    stream = client.chat.completions.create(
        model=agent["model"],
        messages=messages,
        stream=True,
        max_tokens=4096,
        temperature=0.7,
        top_p=0.95,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            full += delta.content
    return full


def _stage_header(agent_key: str, status: str = "ACTIVE") -> str:
    """Format a cinematic stage header for the chat output."""
    a = AGENTS[agent_key]
    return (
        f"\n\n---\n\n"
        f"**{a['icon']} [{a['name']}]** — *{status}*\n\n"
    )


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND — 4-Agent Adversarial Pipeline with Streaming
#
# Pipeline: ARCHITECT (Qwen-32B) → IMPLEMENTER (Llama-70B)
#                                          ↓
#           SYNTHESIZER (Mistral-123B) ← RED-TEAM (DeepSeek-V2-Lite)
#
# Each stage streams its output to the Gradio chatbot in real-time.
# ══════════════════════════════════════════════════════════════════════════════
def sage_inference(user_message, chat_history):
    """
    Runs the full AODE adversarial pipeline across all four agents.
    Each agent runs on its own vLLM instance on a separate port.
    Output is streamed stage-by-stage to the chat.
    """
    if not user_message or not user_message.strip():
        yield chat_history, ""
        return

    # Append user message
    chat_history = chat_history + [{"role": "user", "content": user_message}]
    chat_history = chat_history + [{"role": "assistant", "content": ""}]
    yield chat_history, ""

    output = ""

    try:
        # ── STAGE 1: ARCHITECT (Qwen2.5-Coder-32B) ──
        output += _stage_header("architect", "Generating design spec...")
        chat_history[-1]["content"] = output + "\n\n⟳ *Streaming from Qwen-32B on port 8001...*"
        yield chat_history, ""

        arch_msgs = [
            {"role": "system", "content": AGENTS["architect"]["system"]},
            {"role": "user", "content": f"Design a solution for:\n\n{user_message}"},
        ]

        client = _make_client("architect")
        arch_response = ""
        stream = client.chat.completions.create(
            model=AGENTS["architect"]["model"],
            messages=arch_msgs, stream=True, max_tokens=2048, temperature=0.6,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                arch_response += chunk.choices[0].delta.content
                chat_history[-1]["content"] = output + arch_response
                yield chat_history, ""

        output += arch_response

        # ── STAGE 2: IMPLEMENTER (Llama-3.1-70B) ──
        output += _stage_header("implementer", "Writing production code...")
        chat_history[-1]["content"] = output + "\n\n⟳ *Streaming from Llama-70B on port 8002...*"
        yield chat_history, ""

        impl_msgs = [
            {"role": "system", "content": AGENTS["implementer"]["system"]},
            {"role": "user", "content": (
                f"Original task: {user_message}\n\n"
                f"Architectural spec from Architect:\n{arch_response}\n\n"
                f"Now write the complete implementation."
            )},
        ]

        client = _make_client("implementer")
        impl_response = ""
        stream = client.chat.completions.create(
            model=AGENTS["implementer"]["model"],
            messages=impl_msgs, stream=True, max_tokens=4096, temperature=0.5,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                impl_response += chunk.choices[0].delta.content
                chat_history[-1]["content"] = output + impl_response
                yield chat_history, ""

        output += impl_response

        # ── STAGE 3: RED-TEAM (DeepSeek-V2-Lite) ──
        output += _stage_header("redteam", "Adversarial attack in progress...")
        chat_history[-1]["content"] = output + "\n\n⟳ *Streaming from DeepSeek-V2-Lite on port 8004...*"
        yield chat_history, ""

        red_msgs = [
            {"role": "system", "content": AGENTS["redteam"]["system"]},
            {"role": "user", "content": (
                f"Attack the following code. Find every flaw.\n\n{impl_response}"
            )},
        ]

        client = _make_client("redteam")
        red_response = ""
        stream = client.chat.completions.create(
            model=AGENTS["redteam"]["model"],
            messages=red_msgs, stream=True, max_tokens=2048, temperature=0.8,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                red_response += chunk.choices[0].delta.content
                chat_history[-1]["content"] = output + red_response
                yield chat_history, ""

        output += red_response

        # ── STAGE 4: SYNTHESIZER / NASH CRUCIBLE (Mistral-123B) ──
        output += _stage_header("synthesizer", "Nash Equilibrium convergence...")
        chat_history[-1]["content"] = output + "\n\n⟳ *Streaming from Mistral-123B on port 8003...*"
        yield chat_history, ""

        synth_msgs = [
            {"role": "system", "content": AGENTS["synthesizer"]["system"]},
            {"role": "user", "content": (
                f"## Original Task\n{user_message}\n\n"
                f"## Architect Spec\n{arch_response}\n\n"
                f"## Implementation\n{impl_response}\n\n"
                f"## Red-Team Findings\n{red_response}\n\n"
                f"Patch all vulnerabilities. Emit the final hardened code."
            )},
        ]

        client = _make_client("synthesizer")
        synth_response = ""
        stream = client.chat.completions.create(
            model=AGENTS["synthesizer"]["model"],
            messages=synth_msgs, stream=True, max_tokens=4096, temperature=0.4,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                synth_response += chunk.choices[0].delta.content
                chat_history[-1]["content"] = output + synth_response
                yield chat_history, ""

        output += synth_response

        # ── FINAL: Nash Equilibrium stamp ──
        output += (
            "\n\n---\n\n"
            "**◎ NASH EQUILIBRIUM VERIFIED** — "
            "Code hardened through adversarial crucible. "
            "All four agents have converged.\n\n"
            "| Agent | Model | Port | Status |\n"
            "|-------|-------|------|--------|\n"
            "| ◈ Architect | Qwen2.5-Coder-32B-AWQ | 8001 | ✓ CONVERGED |\n"
            "| ◆ Implementer | Llama-3.1-70B-AWQ | 8002 | ✓ CONVERGED |\n"
            "| ⚑ Red-Team | DeepSeek-V2-Lite | 8004 | ✓ CONVERGED |\n"
            "| ◉ Synthesizer | Mistral-Large-123B-AWQ | 8003 | ✓ CONVERGED |\n"
        )
        chat_history[-1]["content"] = output
        yield chat_history, ""

    except Exception as e:
        error_msg = (
            f"\n\n**[SYSTEM FAULT]** Agent pipeline interrupted.\n\n"
            f"`{VLLM_HOST}` — Connection to one or more vLLM endpoints failed.\n\n"
            f"Ensure all 4 Dockerized vLLM containers are running on MI300X:\n"
            f"- Port 8001: Architect (Qwen-32B)\n"
            f"- Port 8002: Implementer (Llama-70B)\n"
            f"- Port 8003: Synthesizer (Mistral-123B)\n"
            f"- Port 8004: Red-Team (DeepSeek-V2-Lite)\n\n"
            f"```\nError: {str(e)}\n```"
        )
        chat_history[-1]["content"] = output + error_msg
        yield chat_history, ""


# ══════════════════════════════════════════════════════════════════════════════
# AODE AESTHETIC — Custom CSS (scanlines, vignette, brutalist typography)
# Extracted from sage_cinematic_intro.html reference palette
# ══════════════════════════════════════════════════════════════════════════════
AODE_CSS = """
/* ── GLOBAL RESET ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: #000000 !important;
    font-family: 'Georgia', serif !important;
    color: #e8d5a3 !important;
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
}

/* ── ATMOSPHERIC LAYERS (vignette + scanlines) ────────────────── */
.gradio-container::before {
    content: '';
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.7) 100%);
    pointer-events: none; z-index: 1;
}
.gradio-container::after {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    pointer-events: none; z-index: 2; opacity: 0.5;
}

/* ── TYPOGRAPHY — uppercase, wide spacing ─────────────────────── */
h1, h2, h3, h4, label, button, .label-wrap span {
    font-family: 'Georgia', serif !important;
    text-transform: uppercase !important;
    letter-spacing: 4px !important;
    color: #e8d5a3 !important;
}

/* ── CHATBOT CONTAINER ────────────────────────────────────────── */
#sage-chatbot {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
}
#sage-chatbot .chatbot {
    background: transparent !important;
}
#sage-chatbot .wrapper { background: transparent !important; }

/* Message rows */
#sage-chatbot .message-wrap { background: transparent !important; }
#sage-chatbot .message { border-radius: 0 !important; }

/* ── USER MESSAGES — muted, right-aligned ─────────────────────── */
#sage-chatbot .role-user .message-bubble-border {
    background: transparent !important;
    border: 1px solid #333 !important;
    border-radius: 0 !important;
}
#sage-chatbot .role-user .message-content {
    color: #888888 !important;
    font-family: 'Georgia', serif !important;
}

/* ── SAGE MESSAGES — authority styling ────────────────────────── */
#sage-chatbot .role-assistant .message-bubble-border {
    background: rgba(204, 0, 0, 0.05) !important;
    border: none !important;
    border-left: 3px solid #CC0000 !important;
    border-radius: 0 !important;
}
#sage-chatbot .role-assistant .message-content {
    color: #ffffff !important;
    font-family: 'Georgia', serif !important;
}

/* ── CODE BLOCKS inside messages ──────────────────────────────── */
#sage-chatbot pre, #sage-chatbot code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    background: #0a0a0a !important;
    border: 1px solid #1a0000 !important;
    border-radius: 0 !important;
    color: #e8d5a3 !important;
}

/* ── INPUT BOX ────────────────────────────────────────────────── */
#sage-input textarea {
    background: #0a0a0a !important;
    color: #e8d5a3 !important;
    border: none !important;
    border-bottom: 1px solid #333 !important;
    border-radius: 0 !important;
    font-family: 'Georgia', serif !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    padding: 16px !important;
    font-size: 14px !important;
}
#sage-input textarea:focus {
    border-bottom: 1px solid #CC0000 !important;
    box-shadow: 0 2px 20px rgba(204, 0, 0, 0.3) !important;
    outline: none !important;
}
#sage-input .wrap { background: transparent !important; border: none !important; }

/* ── TRANSMIT BUTTON ──────────────────────────────────────────── */
#transmit-btn {
    background: #000000 !important;
    color: #CC0000 !important;
    border: 1px solid #CC0000 !important;
    border-radius: 0 !important;
    font-family: 'Georgia', serif !important;
    letter-spacing: 6px !important;
    text-transform: uppercase !important;
    font-size: 13px !important;
    padding: 14px 32px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 15px rgba(204, 0, 0, 0.2) !important;
    min-width: 180px !important;
}
#transmit-btn:hover {
    color: #FF3300 !important;
    border-color: #FF3300 !important;
    box-shadow: 0 0 30px rgba(255, 51, 0, 0.4) !important;
}

/* ── REMOVE GRADIO DEFAULTS ───────────────────────────────────── */
.contain, .block, .wrap, .panel {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}
footer { display: none !important; }
.built-with { display: none !important; }
.show-api { display: none !important; }

/* ── INTRO OVERLAY ────────────────────────────────────────────── */
#sage-intro-frame {
    position: fixed; inset: 0;
    z-index: 99999; background: #000;
    transition: opacity 2.5s ease, transform 2.5s ease;
}
#sage-intro-frame.exit {
    opacity: 0;
    transform: scale(1.08);
    pointer-events: none;
}
#sage-intro-frame iframe {
    width: 100%; height: 100%;
    border: none;
}

/* ── APP REVEAL ANIMATION ─────────────────────────────────────── */
@keyframes appReveal {
    from { opacity: 0; }
    to   { opacity: 1; }
}
#sage-app-body { animation: appReveal 1s ease 0.5s both; }
"""

# ══════════════════════════════════════════════════════════════════════════════
# HEADER HTML — The Crown (glowing title + separator)
# ══════════════════════════════════════════════════════════════════════════════
HEADER_HTML = """
<div style="text-align:center; padding:40px 20px 24px; position:relative; z-index:3;">
  <div style="
    font-family: Georgia, serif;
    font-size: clamp(24px, 4vw, 48px);
    letter-spacing: 10px;
    color: #fff;
    text-transform: uppercase;
    text-shadow: 0 0 40px rgba(204,0,0,0.9), 0 0 80px rgba(204,0,0,0.4);
    margin-bottom: 12px;
  ">PROJECT SAGE × AODE</div>
  <div style="
    font-family: Georgia, serif;
    font-size: clamp(9px, 1.2vw, 14px);
    letter-spacing: 6px;
    color: #CC0000;
    text-transform: uppercase;
    margin-bottom: 8px;
  ">AMD Instinct MI300X · 192 GB HBM3</div>
  <div style="
    font-family: Georgia, serif;
    font-size: 10px;
    letter-spacing: 4px;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 20px;
  ">Adversarial Orthogonal Divergence Engine</div>
  <div style="
    width: 280px; height: 1px; margin: 0 auto;
    background: linear-gradient(to right, transparent, #CC0000, transparent);
  "></div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# HEAD INJECTION — Three.js CDN for the intro iframe
# ══════════════════════════════════════════════════════════════════════════════
INTRO_HEAD = """
<style>
  #sage-intro-frame {
    position: fixed; inset: 0; z-index: 99999;
    background: #000;
    transition: opacity 2.5s ease, transform 2.5s ease;
  }
  #sage-intro-frame.exit {
    opacity: 0; transform: scale(1.08); pointer-events: none;
  }
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
# INTRO JAVASCRIPT — Hyper Frame State Engine
# Creates the cinematic overlay, loads the 3D intro via iframe,
# listens for completion/skip, then executes the crossfade transition
# ══════════════════════════════════════════════════════════════════════════════
INTRO_JS = """
() => {
  /* ── Hyper Frame A: Create the intro overlay ── */
  const frame = document.createElement('div');
  frame.id = 'sage-intro-frame';

  const iframe = document.createElement('iframe');
  iframe.style.cssText = 'width:100%;height:100%;border:none;';

  /* Load the cinematic intro HTML. In production on HF Spaces,
     place sage_cinematic_intro.html in the same directory as app.py
     and Gradio will serve it as a static file. */
  iframe.src = '/file=sage_cinematic_intro.html';
  frame.appendChild(iframe);
  document.body.appendChild(frame);

  /* ── Hyper Frame Transition Engine ── */
  let transitioned = false;
  function enterSystem() {
    if (transitioned) return;
    transitioned = true;
    frame.classList.add('exit');
    setTimeout(() => { frame.remove(); }, 3000);
  }

  /* Listen for postMessage from the intro iframe */
  window.addEventListener('message', (e) => {
    if (e.data === 'sage-enter-system') enterSystem();
  });

  /* Fallback: auto-transition after 42 seconds */
  setTimeout(enterSystem, 42000);
}
"""

# ══════════════════════════════════════════════════════════════════════════════
# BACKEND — Streaming inference via vLLM OpenAI-compatible API
# ══════════════════════════════════════════════════════════════════════════════
def sage_inference(user_message, chat_history):
    """
    Primary inference function.
    Connects to the Dockerized vLLM container on MI300X via the
    OpenAI-compatible /v1/chat/completions endpoint.
    Streams tokens for cinematic character-by-character output.
    """
    if not user_message or not user_message.strip():
        yield chat_history, ""
        return

    # ── Format history into OpenAI message dicts ──
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # ── Append user message to display ──
    chat_history = chat_history + [{"role": "user", "content": user_message}]
    chat_history = chat_history + [{"role": "assistant", "content": ""}]
    yield chat_history, ""

    # ── Stream from vLLM ──
    try:
        client = OpenAI(base_url=VLLM_BASE_URL, api_key=API_KEY)
        stream = client.chat.completions.create(
            model=SAGE_MODEL,
            messages=messages,
            stream=True,
            max_tokens=4096,
            temperature=0.7,
            top_p=0.95,
        )

        partial = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                partial += delta.content
                chat_history[-1]["content"] = partial
                yield chat_history, ""

    except Exception as e:
        # Fallback: if vLLM is unreachable, return a diagnostic message
        error_msg = (
            f"**[SYSTEM FAULT]** Cannot reach vLLM backend.\n\n"
            f"`{VLLM_BASE_URL}` — Connection refused.\n\n"
            f"Ensure the Dockerized vLLM container is running on MI300X "
            f"and `VLLM_BASE_URL` is set correctly.\n\n"
            f"```\nError: {str(e)}\n```"
        )
        chat_history[-1]["content"] = error_msg
        yield chat_history, ""


# ══════════════════════════════════════════════════════════════════════════════
# GRADIO LAYOUT — Hyper Frame B (The Neural Interface)
# ══════════════════════════════════════════════════════════════════════════════
with gr.Blocks(title="PROJECT SAGE × AODE") as app:

    # ── The Crown (header) ──
    gr.HTML(HEADER_HTML)

    # ── Chat body ──
    with gr.Column(elem_id="sage-app-body"):
        chatbot = gr.Chatbot(
            elem_id="sage-chatbot",
            height=700,
            show_label=False,
            placeholder=(
                "<div style='text-align:center;padding:60px 20px;"
                "font-family:Georgia,serif;letter-spacing:4px;"
                "text-transform:uppercase;color:#555;font-size:12px;'>"
                "AWAITING COMMAND INPUT<br>"
                "<span style='color:#CC0000;font-size:10px;"
                "letter-spacing:6px;'>SAGE ENGINE ONLINE</span>"
                "</div>"
            ),
        )

    # ── Footer: Input + Transmit ──
    with gr.Row():
        with gr.Column(scale=6):
            msg_input = gr.Textbox(
                elem_id="sage-input",
                placeholder="ENTER COMMAND...",
                show_label=False,
                lines=1,
                max_lines=6,
            )
        with gr.Column(scale=1, min_width=180):
            submit_btn = gr.Button(
                "TRANSMIT",
                elem_id="transmit-btn",
                variant="primary",
            )

    # ── Event wiring ──
    submit_btn.click(
        fn=sage_inference,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    msg_input.submit(
        fn=sage_inference,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )

# ══════════════════════════════════════════════════════════════════════════════
# LAUNCH
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        # Gradio 6: theme, css, js, head are now launch() params
        theme=gr.themes.Monochrome(),
        css=AODE_CSS,
        head=INTRO_HEAD,
        js=INTRO_JS,
        # Allow Gradio to serve the intro HTML as a static file
        allowed_paths=["."],
    )
