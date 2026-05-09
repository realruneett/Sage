---
title: SAGE-PRO Crucible
emoji: ⚡
colorFrom: blue
colorTo: cyan
sdk: gradio
sdk_version: 4.29.0
app_file: app.py
pinned: true
license: mit
short_description: 4-Agent AI Coding Engine on AMD Instinct MI300X (192 GB HBM3)
---

# ⚡ SAGE-PRO — Strategic Adversarial Generative Engine

> **4-Agent Co-Resident Ensemble · AMD Instinct MI300X · 192 GB HBM3 · AMD Developer Hackathon 2024**

SAGE-PRO is an enterprise-grade AI coding engine that breaks the single-model paradigm by running four specialised agents simultaneously in a unified HBM3 memory pool — enabling context windows and model co-residency impossible on conventional hardware.

---

## Architecture

| Agent | Role | Signal Colour |
|-------|------|---------------|
| **Architect** | System topology, interface contracts, distributed-system constraints | `#4a90ff` |
| **Implementer** | Torsion-aware code synthesis, optimal primitive selection | `#3dffa0` |
| **Red-Team** | Adversarial probing, boundary fuzzing, CVE-pattern vulnerability discovery | `#ffb347` |
| **Synthesizer** | Nash Equilibrium Crucible — multi-agent conflict resolution & artifact sealing | `#c084fc` |

---

## Hardware Target

| Specification | Value |
|---------------|-------|
| GPU | AMD Instinct MI300X |
| VRAM | 192 GB HBM3 |
| Memory Bandwidth | 5.3 TB/s |
| Co-Resident Agents | 4 |
| Unified Context Pool | 512 K tokens |
| Avg. Nash Cycles | 4 · Δ = 0.02 |

---

## Features

- 🔐 **Secure Auth Gate** — full-screen split-panel login, clearance-required access
- ⚡ **Real-time Streaming** — async generator driving live XAI trace logs per agent
- 📡 **Live Telemetry** — VRAM peak, Nash cycles, divergence index, council status
- 🏺 **Final Artifact** — Nash-hardened, Red-Team-verified Python output
- 📋 **Session History** — all runs persisted and browsable within the session
- ⚙️ **Settings** — engine configuration panel (backend URL, Nash depth, VRAM soft-cap)
- ℹ️ **About** — hardware specs and full agent capability descriptions

---

## Access

Access credentials are managed by the project administrator.
Contact the repository owner at [github.com/realruneett/Sage](https://github.com/realruneett/Sage) for authorised access.

---

## Wiring to the FastAPI Backend

Set `SAGE_BACKEND_URL` in your HF Space **Secrets** (Settings → Variables and secrets), then replace the `run_sage_engine` generator body with a real streaming call:

```python
import os, httpx

async def run_sage_engine(query: str, sessions: list[dict]):
    url = os.environ["SAGE_BACKEND_URL"] + "/v1/sage/generate"
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, json={"query": query}) as resp:
            async for chunk in resp.aiter_text():
                # parse chunk, update UI state, yield outputs
                yield ...
```

---

## Repository

**GitHub:** [github.com/realruneett/Sage](https://github.com/realruneett/Sage)

---

*SAGE-PRO · Built for the AMD Instinct MI300X Developer Hackathon 2024*
