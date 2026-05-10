# SAGE Frontend — Gradio Dashboard

Production-ready frontend for the SAGE-PRO AODE Engine.

## Features (v3.0.0)
- 🚀 **Full AODE Pipeline UI** — Task input → Live execution trace → Hardened code output
- 🪟 **Glass Renderer** — Sandboxed live preview of agent-generated code (HTML/CSS/JS, Pyodide, React)
- 👁️ **Vision Debugger** — Upload screenshots of broken UIs; SAGE auto-fixes the code via VLM
- 💭 **Chaos Dreamer** — Start/stop autonomous self-improvement; view dream statistics live
- 📊 **XAI Metrics** — Damage trajectory, VRAM footprint, divergence index, reasoning trace
- 🗺️ **Pipeline Map** — Animated visualization of the 10-node LangGraph execution
- 🔧 **System Health** — Real-time backend agent status with model info

## Modes
| Mode | Description |
|------|-------------|
| `pro` | Full SAGE-PRO backend (MI300X vLLM) |
| `free` | Local Ollama models |
| `api` | Remote SAGE-PRO API |
| `demo` | Fully simulated (no GPU) |

## Deploy on Hugging Face Spaces
```bash
# Set SAGE_MODE=demo for zero-GPU demo
python app.py
```

## Environment Variables
- `SAGE_MODE` — `pro | free | api | demo` (default: auto-detect)
- `SAGE_API_URL` — SAGE-PRO backend URL
- `VLLM_HOST_*` — Co-resident vLLM endpoints
- `OLLAMA_BASE_URL` — Local Ollama fallback
