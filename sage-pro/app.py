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
import gradio as gr
from openai import OpenAI

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Set these in your Hugging Face Space "Secrets" panel
# ══════════════════════════════════════════════════════════════════════════════
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8001/v1")
API_KEY = os.environ.get("HF_TOKEN", "not-needed")
SAGE_MODEL = os.environ.get("SAGE_MODEL_ID", "TechxGenus/Mistral-Large-Instruct-2407-AWQ")

SYSTEM_PROMPT = (
    "You are SAGE, the Adversarial Orthogonal Divergence Engine — "
    "a sovereign reasoning system running on AMD Instinct MI300X. "
    "You write hardened, production-grade code. Every response passes "
    "through a Nash Equilibrium crucible of adversarial verification. "
    "Be precise, authoritative, and technically flawless."
)

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
