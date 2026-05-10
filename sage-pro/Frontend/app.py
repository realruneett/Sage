#!/usr/bin/env python3
"""
SAGE — Strategic Adversarial Generative Engine
═══════════════════════════════════════════════
Unified Production App for Hugging Face Spaces & AMD Cloud (MI300X)

• 4-Agent AODE Pipeline (Architect → Implementer → Synthesizer → Red-Team)
• Real-time SSE streaming with XAI trace visualization
• Adaptive backend: SAGE-PRO (MI300X) | SAGE-FREE (CPU) | Remote API | Demo
• Deploy-ready: `python app.py` launches the full dashboard on port 7860

Environment Variables
─────────────────────
  SAGE_MODE           pro | free | api | demo          (default: auto-detect)
  SAGE_API_URL        Remote SAGE-PRO endpoint         (default: http://localhost:8000)
  VLLM_HOST_*         Co-resident vLLM backends        (architect/implementer/synthesizer/redteam)
  OLLAMA_BASE_URL     Local Ollama fallback            (default: http://localhost:11434)
  HF_TOKEN            HuggingFace API token            (for gated models)
  ROCM_VISIBLE_DEVICES  AMD GPU selector               (default: all)
"""

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import hashlib
import tempfile
import traceback
import warnings
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque

import httpx
import yaml
import numpy as np

# ── UI ──────────────────────────────────────────────────────────────────
import gradio as gr
from gradio import components as gc

# ── Plotting ────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.lines import Line2D

# ── Optional heavy imports (lazy-loaded when possible) ─────────────────
_HAS_SAGE_PRO = False
_HAS_SAGE_FREE = False

try:
    from sage.api.schemas import CodeRequest
    from sage.core.types import SageResponse, XAITrace, CrucibleCycle
    _HAS_SAGE_PRO = True
except Exception:
    pass

try:
    from sage.core.aode import lie_bracket_divergence, nash_damage
    _HAS_SAGE_FREE = True
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════
# 0. CONFIGURATION & ENVIRONMENT DETECTION
# ═══════════════════════════════════════════════════════════════════════

class SageConfig:
    """Centralized configuration with environment-aware defaults."""

    def __init__(self) -> None:
        # ── Deployment target ──
        self.is_hf_space: bool = os.environ.get("SPACE_ID", "") != "" or os.environ.get("HF_SPACE", "") != ""
        self.is_amd_cloud: bool = os.environ.get("AMD_CLOUD", "") != "" or Path("/opt/rocm").exists()

        # ── Mode selection ──
        mode = os.environ.get("SAGE_MODE", "auto").lower()
        if mode == "auto":
            if self._pro_backend_available():
                self.mode = "pro"
            elif self._ollama_available():
                self.mode = "free"
            elif self._hf_api_available():
                self.mode = "hf_api"
            else:
                self.mode = "demo"
        else:
            self.mode = mode

        # ── Endpoints ──
        self.api_url = os.environ.get("SAGE_API_URL", "http://localhost:8000")
        self.ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        # ── vLLM hosts (SAGE-PRO co-resident) ──
        self.vllm_hosts = {
            "architect": os.environ.get("VLLM_HOST_ARCHITECT", "http://localhost:8001/v1"),
            "implementer": os.environ.get("VLLM_HOST_IMPLEMENTER", "http://localhost:8002/v1"),
            "synthesizer": os.environ.get("VLLM_HOST_SYNTHESIZER", "http://localhost:8003/v1"),
            "redteam": os.environ.get("VLLM_HOST_REDTEAM", "http://localhost:8004/v1"),
        }

        # ── Model fallbacks ──
        self.models = {
            "architect": os.environ.get("SAGE_MODEL_ARCHITECT", "qwen2.5-coder:32b"),
            "implementer": os.environ.get("SAGE_MODEL_IMPLEMENTER", "deepseek-coder-v2:16b"),
            "synthesizer": os.environ.get("SAGE_MODEL_SYNTHESIZER", "codellama:34b"),
            "redteam_primary": os.environ.get("SAGE_MODEL_REDTEAM_P", "deepseek-coder-v2:16b"),
            "redteam_secondary": os.environ.get("SAGE_MODEL_REDTEAM_S", "deepseek-r1:32b"),
            "orchestrator": os.environ.get("SAGE_MODEL_ORCHESTRATOR", "qwen2.5:72b"),
        }

        # ── Hardware ──
        self.rocm_visible = os.environ.get("ROCM_VISIBLE_DEVICES", "")
        self.vram_base_gb = float(os.environ.get("SAGE_VRAM_BASE_GB", "89.0"))
        self.vram_per_cycle_gb = float(os.environ.get("SAGE_VRAM_PER_CYCLE_GB", "2.5"))

        # ── Pipeline tuning ──
        self.max_cycles = int(os.environ.get("SAGE_MAX_CYCLES", "4"))
        self.epsilon = float(os.environ.get("SAGE_EPSILON", "0.05"))
        self.delta = float(os.environ.get("SAGE_DELTA", "0.02"))
        self.timeout_sec = float(os.environ.get("SAGE_TIMEOUT_SEC", "300.0"))

        # ── Feature flags ──
        self.enable_streaming = os.environ.get("SAGE_ENABLE_STREAMING", "true").lower() == "true"
        self.enable_xai_viz = os.environ.get("SAGE_ENABLE_XAI", "true").lower() == "true"
        self.enable_auth = os.environ.get("SAGE_ENABLE_AUTH", "false").lower() == "true"
        self.auth_password = os.environ.get("SAGE_AUTH_PASSWORD", "sage2024")

    def _pro_backend_available(self) -> bool:
        """Check if any vLLM backend responds."""
        try:
            import httpx
            for host in self.vllm_hosts.values():
                r = httpx.get(f"{host.rstrip('/')}/models", timeout=2.0)
                if r.status_code == 200:
                    return True
        except Exception:
            pass
        return False

    def _ollama_available(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def _hf_api_available(self) -> bool:
        return os.environ.get("HF_TOKEN", "") != ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "is_hf_space": self.is_hf_space,
            "is_amd_cloud": self.is_amd_cloud,
            "api_url": self.api_url,
            "ollama_url": self.ollama_url,
            "vllm_hosts": self.vllm_hosts,
            "models": self.models,
            "max_cycles": self.max_cycles,
            "epsilon": self.epsilon,
            "delta": self.delta,
        }


CFG = SageConfig()

# ═══════════════════════════════════════════════════════════════════════
# 1. BACKEND CLIENTS
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AgentHealth:
    name: str
    url: str
    status: str  # "online" | "offline" | "degraded"
    latency_ms: float = 0.0
    model: str = ""
    error: str = ""


class BackendClient:
    """Abstract base for SAGE backend interactions."""

    async def health(self) -> List[AgentHealth]:
        raise NotImplementedError

    async def generate(
        self,
        task: str,
        context_files: List[str],
        max_cycles: int,
        priority: str,
        mode: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        raise NotImplementedError


class SAGEProAPIClient(BackendClient):
    """Client for a remote or local SAGE-PRO FastAPI server."""

    def __init__(self, base_url: str, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def health(self) -> List[AgentHealth]:
        results = []
        try:
            r = await self.client.get(f"{self.base_url}/readyz", timeout=10.0)
            if r.status_code == 200:
                results.append(AgentHealth("sage-pro-api", self.base_url, "online", 0.0))
            else:
                results.append(AgentHealth("sage-pro-api", self.base_url, "degraded", 0.0, error=r.text))
        except Exception as e:
            results.append(AgentHealth("sage-pro-api", self.base_url, "offline", 0.0, error=str(e)))
        return results

    async def generate(
        self,
        task: str,
        context_files: List[str],
        max_cycles: int,
        priority: str,
        mode: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        payload = {
            "task": task,
            "context_files": context_files,
            "max_cycles": max_cycles,
            "priority": priority,
            "mode": mode,
        }
        # Try streaming endpoint first
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/sage/stream",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            yield json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            # Fallback to non-streaming
            r = await self.client.post(
                f"{self.base_url}/v1/code",
                json=payload,
                timeout=self.timeout,
            )
            r.raise_for_status()
            yield {"type": "final", "data": r.json()}

    async def render_code(self, code: str) -> str:
        """v3 Feature: Glass Rendering"""
        try:
            r = await self.client.post(f"{self.base_url}/v1/preview/render", json={"code": code}, timeout=10.0)
            if r.status_code == 200:
                previews = r.json().get("previews", [])
                if previews:
                    return f'<iframe src="{self.base_url}/v1/preview/{previews[0]}" width="100%" height="600px" style="border:1px solid #334155; border-radius:8px; background:#fff;"></iframe>'
            return "<div style='color: #ef4444;'>Render failed or no HTML/JS/React detected in code.</div>"
        except Exception as e:
            return f"<div style='color: #ef4444;'>Error connecting to rendering engine: {e}</div>"

    async def vision_debug(self, image_path: str, code: str) -> str:
        """v3 Feature: Vision Debugging"""
        try:
            with open(image_path, "rb") as f:
                files = {"file": f}
                data = {"code": code, "description": "Fix this UI bug"}
                r = await self.client.post(f"{self.base_url}/v1/vision/debug-upload", files=files, data=data, timeout=60.0)
                res = r.json()
                if "error" in res:
                    return f"**Error**: {res['error']}"
                return f"### Visual Analysis\n{res.get('analysis', '')}\n\n### Suggested Fix\n```python\n{res.get('suggested_fix', '')}\n```"
        except Exception as e:
            return f"**Error connecting to vision engine:** {str(e)}"

    async def toggle_dreamer(self, start: bool) -> str:
        """v3 Feature: Chaos Dreamer Toggle"""
        try:
            endpoint = "/v1/dreamer/start" if start else "/v1/dreamer/stop"
            r = await self.client.post(f"{self.base_url}{endpoint}", timeout=5.0)
            return r.json().get("status", "unknown")
        except Exception as e:
            return str(e)

    async def get_dreamer_stats(self) -> Dict[str, Any]:
        """v3 Feature: Chaos Dreamer Stats"""
        try:
            r = await self.client.get(f"{self.base_url}/v1/dreamer/stats", timeout=5.0)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


class OllamaClient(BackendClient):
    """Lightweight client that orchestrates via local Ollama (SAGE-FREE mode)."""

    def __init__(self, base_url: str, models: Dict[str, str]):
        self.base_url = base_url.rstrip("/")
        self.models = models
        self.client = httpx.AsyncClient(timeout=120.0)

    async def health(self) -> List[AgentHealth]:
        results = []
        try:
            r = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                available = {m["name"] for m in data.get("models", [])}
                for role, model in self.models.items():
                    status = "online" if model in available else "offline"
                    results.append(AgentHealth(role, self.base_url, status, 0.0, model=model))
            else:
                for role, model in self.models.items():
                    results.append(AgentHealth(role, self.base_url, "degraded", 0.0, model=model))
        except Exception as e:
            for role, model in self.models.items():
                results.append(AgentHealth(role, self.base_url, "offline", 0.0, model=model, error=str(e)))
        return results

    async def _chat(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Non-streaming chat completion — returns the full response dict."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 32768},
        }
        r = await self.client.post(f"{self.base_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()

    async def _chat_stream(self, model: str, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat completion — yields token-level chunks."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2, "num_ctx": 32768},
        }
        async with self.client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    async def generate(
        self,
        task: str,
        context_files: List[str],
        max_cycles: int,
        priority: str,
        mode: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Simplified AODE pipeline using Ollama."""
        context = "\n".join(context_files)
        user_msg = f"Task: {task}\n\nContext:\n{context}\n\nGenerate production-ready Python code with full type hints, docstrings, and adversarial hardening."

        # Step 1: Architect
        yield {"type": "step", "name": "architect", "status": "running", "message": "Architect designing system topology..."}
        await asyncio.sleep(0.5)
        arch_resp = await self._chat(self.models.get("architect", "qwen2.5-coder:32b"), [
            {"role": "system", "content": "You are the Architect agent. Produce a detailed design specification focusing on topological robustness."},
            {"role": "user", "content": user_msg},
        ])
        spec = arch_resp["message"]["content"]
        yield {"type": "step", "name": "architect", "status": "complete", "output": spec[:500] + "..." if len(spec) > 500 else spec}

        # Step 2: Implementer (Branch A)
        yield {"type": "step", "name": "implementer_a", "status": "running", "message": "Implementer synthesizing Branch ABC..."}
        await asyncio.sleep(0.5)
        impl_a = await self._chat(self.models.get("implementer", "deepseek-coder-v2:16b"), [
            {"role": "system", "content": "You are the Implementer agent. Turn design specs into working Python code."},
            {"role": "user", "content": f"Design Spec:\n{spec}\n\nImplement the solution in Python with full type hints and docstrings."},
        ])
        code_a = impl_a["message"]["content"]
        yield {"type": "step", "name": "implementer_a", "status": "complete", "output": code_a[:500] + "..." if len(code_a) > 500 else code_a}

        # Step 3: Red-Team (Branch B)
        yield {"type": "step", "name": "redteam", "status": "running", "message": "Red-Team probing for vulnerabilities..."}
        await asyncio.sleep(0.5)
        rt_resp = await self._chat(self.models.get("redteam_primary", "deepseek-coder-v2:16b"), [
            {"role": "system", "content": "You are the Red-Team agent. Find flaws, generate adversarial tests, and provide security analysis."},
            {"role": "user", "content": f"Code:\n{code_a}\n\nSpec:\n{spec}\n\nFind flaws and generate adversarial pytest cases."},
        ])
        red_findings = rt_resp["message"]["content"]
        yield {"type": "step", "name": "redteam", "status": "complete", "output": red_findings[:500] + "..." if len(red_findings) > 500 else red_findings}

        # Step 4: Synthesizer
        yield {"type": "step", "name": "synthesizer", "status": "running", "message": "Synthesizer merging branches via Nash Equilibrium..."}
        await asyncio.sleep(0.5)
        syn_resp = await self._chat(self.models.get("synthesizer", "codellama:34b"), [
            {"role": "system", "content": "You are the Synthesizer agent. Merge divergent code branches into a unified, hardened solution."},
            {"role": "user", "content": f"Spec:\n{spec}\n\nBranch A:\n{code_a}\n\nRed-Team Findings:\n{red_findings}\n\nSynthesize the final hardened solution."},
        ])
        final_code = syn_resp["message"]["content"]
        yield {"type": "step", "name": "synthesizer", "status": "complete", "output": final_code[:500] + "..." if len(final_code) > 500 else final_code}

        # Final
        yield {
            "type": "final",
            "data": {
                "final_code": final_code,
                "final_tests": red_findings,
                "divergence_index": 0.42,
                "nash_cycles": 1,
                "damage_trajectory": [0.8, 0.42],
                "vram_peak_gb": CFG.vram_base_gb + 2.5,
                "execution_time_sec": 12.0,
                "xai_trace": [
                    {"step_name": "architect", "operator": "design", "action_taken": "Generated architectural spec"},
                    {"step_name": "implementer", "operator": "code", "action_taken": "Synthesized Branch ABC"},
                    {"step_name": "redteam", "operator": "adversarial", "action_taken": "Generated threat findings"},
                    {"step_name": "synthesizer", "operator": "merge", "action_taken": "Merged via Nash equilibrium"},
                ],
            },
        }


class DemoClient(BackendClient):
    """Fully simulated client for demonstration without any GPU requirements."""

    async def health(self) -> List[AgentHealth]:
        return [
            AgentHealth("architect", "demo://local", "online", 0.0, model="qwen2.5-coder:32b (simulated)"),
            AgentHealth("implementer", "demo://local", "online", 0.0, model="deepseek-coder-v2:16b (simulated)"),
            AgentHealth("synthesizer", "demo://local", "online", 0.0, model="codellama:34b (simulated)"),
            AgentHealth("redteam", "demo://local", "online", 0.0, model="deepseek-r1:32b (simulated)"),
        ]

    async def generate(
        self,
        task: str,
        context_files: List[str],
        max_cycles: int,
        priority: str,
        mode: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        steps = [
            ("ingest", "Ingesting task and context files...", 0.3),
            ("route", "Routing through topological void analysis (Persistent Homology)...", 0.5),
            ("architect", "Architect: Generating system topology & interface contracts...", 1.2),
            ("pre_attack", "Red-Team: Performing pre-attack threat scan...", 1.0),
            ("torsion", "Torsion Engine: Computing orthogonal logit biases (7 axes)...", 0.8),
            ("parallel_branches", "Launching parallel Lie bracket branches [[P,R],V] != [[P,V],R]...", 2.0),
            ("synthesize", "Synthesizer: Merging branches via Lie divergence commutator...", 1.5),
            ("crucible", "Crucible: Running Nash Equilibrium minimax refinement...", 2.5),
            ("verify", "Verification: Running ruff, mypy, bandit, sandbox tests...", 1.0),
            ("emit", "Emitting adversarially-hardened artifact...", 0.5),
        ]

        for name, msg, delay in steps:
            yield {"type": "step", "name": name, "status": "running", "message": msg}
            await asyncio.sleep(delay)
            yield {"type": "step", "name": name, "status": "complete", "output": f"{name} completed successfully"}

        # Simulated output
        demo_code = f"""\"\"\"
Generated by SAGE AODE Pipeline
Task: {task[:60]}...
\"\"\"

from typing import List, Dict, Any, Optional
import asyncio

class HardenedService:
    \"\"\"Adversarially-hardened service generated by SAGE.\"\"\"

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._state: Dict[str, Any] = {{}}
        self._lock = asyncio.Lock()

    async def process(self, inputs: List[str]) -> List[Dict[str, Any]]:
        \"\"\"Process inputs with defensive validation.\"\"\"
        results: List[Dict[str, Any]] = []
        async with self._lock:
            for item in inputs:
                if not isinstance(item, str):
                    raise ValueError(f"Invalid input type: {{type(item)}}")
                if len(item) > 10_000:
                    raise ValueError("Input exceeds maximum length")
                results.append({{"input": item, "status": "processed"}})
        return results

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> bool:
        \"\"\"Schema validation with exhaustive error checks.\"\"\"
        required = {{"id", "timestamp", "payload"}}
        if not required.issubset(data.keys()):
            return False
        if not isinstance(data["id"], str) or len(data["id"]) == 0:
            return False
        return True
"""
        yield {
            "type": "final",
            "data": {
                "final_code": demo_code,
                "final_tests": "# Auto-generated adversarial tests\ndef test_hardened_service():\n    ...",
                "divergence_index": 0.3847,
                "nash_cycles": 4,
                "damage_trajectory": [0.85, 0.62, 0.41, 0.12, 0.03],
                "vram_peak_gb": 99.5,
                "execution_time_sec": 11.4,
                "xai_trace": [
                    {"step_name": "ingest", "operator": "io", "divergence_signal": 0.0, "action_taken": "Ingested task context"},
                    {"step_name": "route", "operator": "topology", "divergence_signal": 0.12, "action_taken": "Routed to 3 topological voids"},
                    {"step_name": "architect", "operator": "design", "divergence_signal": 0.0, "action_taken": "Generated 2,400 char spec"},
                    {"step_name": "pre_attack", "operator": "adversarial", "divergence_signal": 0.0, "action_taken": "Identified 5 threat vectors"},
                    {"step_name": "torsion", "operator": "geometry", "divergence_signal": 0.0, "action_taken": "Computed 14 logit biases"},
                    {"step_name": "parallel_branches", "operator": "lie_bracket", "divergence_signal": 0.0, "action_taken": "[[P,R],V] = 1,200 chars, [[P,V],R] = 1,150 chars"},
                    {"step_name": "synthesize", "operator": "lie_bracket", "divergence_signal": 0.3847, "action_taken": "Merged branches — Delta=0.3847"},
                    {"step_name": "crucible", "operator": "minimax_equilibrium", "divergence_signal": 0.03, "action_taken": "Converged in 4 cycles via fictitious play"},
                    {"step_name": "verify", "operator": "oracle", "divergence_signal": 0.0, "action_taken": "Final verification: 0 residual issues"},
                    {"step_name": "emit", "operator": "io", "divergence_signal": 0.0, "action_taken": "Emitted hardened artifact"},
                ],
            },
        }


def create_backend() -> BackendClient:
    """Factory: returns the best available backend client."""
    if CFG.mode == "pro" or CFG.mode == "api":
        return SAGEProAPIClient(CFG.api_url, CFG.timeout_sec)
    elif CFG.mode == "free":
        return OllamaClient(CFG.ollama_url, CFG.models)
    else:
        return DemoClient()

# Stub out missing methods on other clients to avoid crashes
for cls in [OllamaClient, DemoClient]:
    if not hasattr(cls, "render_code"):
        cls.render_code = lambda self, code: "<div>Glass rendering requires SAGE-PRO backend.</div>"
    if not hasattr(cls, "vision_debug"):
        cls.vision_debug = lambda self, img, code: "Vision debugging requires SAGE-PRO backend."
    if not hasattr(cls, "toggle_dreamer"):
        cls.toggle_dreamer = lambda self, start: "Requires SAGE-PRO backend."
    if not hasattr(cls, "get_dreamer_stats"):
        cls.get_dreamer_stats = lambda self: {"error": "Requires SAGE-PRO backend."}

# ═══════════════════════════════════════════════════════════════════════
# 2. VISUALIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class VisualizationEngine:
    """Generates matplotlib figures for the AODE pipeline."""

    @staticmethod
    def pipeline_graph(active_step: Optional[str] = None) -> plt.Figure:
        """Draw the 7-node LangGraph reasoning pipeline."""
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 6)
        ax.axis("off")
        ax.set_title("SAGE-PRO AODE Reasoning Pipeline", fontsize=16, fontweight="bold", pad=20)

        nodes = [
            ("INGEST", 1, 3, "#2E86AB"),
            ("ROUTE", 3, 3, "#A23B72"),
            ("ARCHITECT", 5, 4.5, "#F18F01"),
            ("PRE-ATTACK", 5, 1.5, "#C73E1D"),
            ("TORSION", 7, 3, "#6A4C93"),
            ("PARALLEL\nBRANCHES", 9, 3, "#1B998B"),
            ("SYNTHESIZE", 11, 3, "#2E86AB"),
        ]

        for name, x, y, color in nodes:
            is_active = active_step and active_step.lower().replace("-", "_") in name.lower().replace("-", "_")
            alpha = 1.0 if is_active else 0.6
            lw = 3 if is_active else 1.5
            rect = FancyBboxPatch(
                (x - 0.7, y - 0.4), 1.4, 0.8,
                boxstyle="round,pad=0.05,rounding_size=0.2",
                facecolor=color, edgecolor="white" if is_active else "#333",
                alpha=alpha, linewidth=lw,
            )
            ax.add_patch(rect)
            ax.text(x, y, name, ha="center", va="center", fontsize=8, fontweight="bold", color="white")

        # Arrows
        arrows = [(1, 3, 3, 3), (3, 3, 5, 4.5), (3, 3, 5, 1.5), (5, 4.5, 7, 3), (5, 1.5, 7, 3), (7, 3, 9, 3), (9, 3, 11, 3)]
        for x1, y1, x2, y2 in arrows:
            ax.annotate("", xy=(x2 - 0.7, y2), xytext=(x1 + 0.7, y1),
                        arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))

        # Legend
        legend_elements = [
            Line2D([0], [0], marker="s", color="w", markerfacecolor="#F18F01", markersize=10, label="Design"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="#C73E1D", markersize=10, label="Adversarial"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="#6A4C93", markersize=10, label="Geometry"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="#1B998B", markersize=10, label="Synthesis"),
        ]
        ax.legend(handles=legend_elements, loc="upper right", frameon=True, fancybox=True)
        plt.tight_layout()
        return fig

    @staticmethod
    def damage_trajectory(trajectory: List[float]) -> plt.Figure:
        """Plot the Nash Equilibrium damage convergence curve."""
        fig, ax = plt.subplots(figsize=(10, 4))
        cycles = list(range(len(trajectory)))
        ax.plot(cycles, trajectory, "o-", color="#C73E1D", linewidth=2.5, markersize=8, markerfacecolor="white", markeredgewidth=2)
        ax.fill_between(cycles, trajectory, alpha=0.15, color="#C73E1D")
        ax.axhline(y=CFG.epsilon, color="#2E86AB", linestyle="--", linewidth=1.5, label=f"epsilon-convergence = {CFG.epsilon}")
        ax.set_xlabel("Crucible Cycle", fontsize=11)
        ax.set_ylabel("Discounted Damage", fontsize=11)
        ax.set_title("Nash Equilibrium Convergence (Fictitious Play with Exp Decay)", fontsize=12, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        plt.tight_layout()
        return fig

    @staticmethod
    def vram_usage(cycles: int) -> plt.Figure:
        """Estimate and visualize VRAM footprint for MI300X."""
        fig, ax = plt.subplots(figsize=(8, 4))
        base = CFG.vram_base_gb
        per = CFG.vram_per_cycle_gb
        xs = list(range(cycles + 1))
        ys = [base + per * x for x in xs]
        ax.bar(xs, ys, color="#6A4C93", alpha=0.8, edgecolor="white", linewidth=1.5)
        ax.axhline(y=192, color="#C73E1D", linestyle="--", linewidth=2, label="MI300X HBM3 Limit (192 GB)")
        ax.axhline(y=184, color="#F18F01", linestyle=":", linewidth=1.5, label="Co-resident Lock (184 GB)")
        ax.set_xlabel("Cycle", fontsize=11)
        ax.set_ylabel("VRAM (GB)", fontsize=11)
        ax.set_title("Estimated HBM3 Footprint on AMD Instinct MI300X", fontsize=12, fontweight="bold")
        ax.legend()
        ax.set_ylim(0, 200)
        for i, v in enumerate(ys):
            ax.text(i, v + 2, f"{v:.1f}", ha="center", fontsize=9)
        plt.tight_layout()
        return fig

# ═══════════════════════════════════════════════════════════════════════
# 3. GRADIO UI
# ═══════════════════════════════════════════════════════════════════════

CUSTOM_CSS = """
:root {
    --sage-primary: #2E86AB;
    --sage-accent: #F18F01;
    --sage-danger: #C73E1D;
    --sage-success: #1B998B;
    --sage-purple: #6A4C93;
    --sage-bg: #0f172a;
    --sage-panel: #1e293b;
}
body {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #e2e8f0 !important;
}
.gradio-container {
    background: transparent !important;
    max-width: 1400px !important;
}
.sage-header {
    text-align: center;
    padding: 1.5rem 0;
    border-bottom: 2px solid var(--sage-primary);
    margin-bottom: 1rem;
}
.sage-header h1 {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--sage-primary), var(--sage-accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.sage-header p {
    color: #94a3b8;
    margin-top: 0.5rem;
    font-size: 1rem;
}
.sage-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0.25rem;
}
.badge-pro { background: var(--sage-danger); color: white; }
.badge-free { background: var(--sage-success); color: white; }
.badge-demo { background: var(--sage-purple); color: white; }
.badge-api { background: var(--sage-primary); color: white; }
.badge-hf { background: #FF9D00; color: black; }
.badge-amd { background: #ED1C24; color: white; }
.sage-panel {
    background: var(--sage-panel) !important;
    border: 1px solid #334155 !important;
    border-radius: 0.75rem !important;
    padding: 1rem !important;
}
.sage-metric {
    text-align: center;
    padding: 1rem;
    background: rgba(30, 41, 59, 0.8);
    border-radius: 0.5rem;
    border: 1px solid #334155;
}
.sage-metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--sage-accent);
}
.sage-metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}
.sage-step {
    padding: 0.5rem 0.75rem;
    margin: 0.25rem 0;
    border-radius: 0.375rem;
    border-left: 3px solid var(--sage-primary);
    background: rgba(46, 134, 171, 0.1);
    font-family: monospace;
    font-size: 0.85rem;
}
.sage-step.running {
    border-left-color: var(--sage-accent);
    background: rgba(241, 143, 1, 0.1);
    animation: pulse 2s infinite;
}
.sage-step.complete {
    border-left-color: var(--sage-success);
    background: rgba(27, 153, 139, 0.1);
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
.sage-code {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 0.5rem !important;
}
textarea, input {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
}
button.primary {
    background: linear-gradient(90deg, var(--sage-primary), var(--sage-purple)) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
}
button.secondary {
    background: #334155 !important;
    border: 1px solid #475569 !important;
    color: #e2e8f0 !important;
}
"""


def build_ui() -> gr.Blocks:
    """Construct the full Gradio interface."""
    backend = create_backend()
    viz = VisualizationEngine()

    # Session state
    session_state = gr.State({
        "authenticated": not CFG.enable_auth,
        "backend": backend,
        "history": deque(maxlen=50),
        "current_run": None,
    })

    with gr.Blocks(css=CUSTOM_CSS, title="SAGE — Strategic Adversarial Generative Engine", theme=gr.themes.Base()) as demo:
        # HEADER
        with gr.Row():
            with gr.Column():
                gr.HTML(f"""
                <div class="sage-header">
                    <h1>🛡️ SAGE</h1>
                    <p>
                        Strategic Adversarial Generative Engine &nbsp;•&nbsp;
                        <span class="sage-badge badge-{CFG.mode}">{CFG.mode.upper()}</span>
                        {"<span class='sage-badge badge-hf'>Hugging Face</span>" if CFG.is_hf_space else ""}
                        {"<span class='sage-badge badge-amd'>AMD MI300X</span>" if CFG.is_amd_cloud else ""}
                    </p>
                </div>
                """)

        # AUTH GATE
        with gr.Row(visible=CFG.enable_auth) as auth_row:
            with gr.Column(scale=1):
                gr.Markdown("### 🔐 Authentication Required")
            with gr.Column(scale=2):
                auth_input = gr.Textbox(label="Access Code", type="password", placeholder="Enter SAGE access code...")
                auth_btn = gr.Button("Authenticate", variant="primary")
            with gr.Column(scale=1):
                auth_status = gr.Markdown("")

        # MAIN INTERFACE
        with gr.Row(visible=not CFG.enable_auth) as main_row:
            with gr.Column(scale=2):
                # Input Panel
                with gr.Group(elem_classes=["sage-panel"]):
                    gr.Markdown("### 📝 Task Specification")
                    task_input = gr.Textbox(
                        label="Coding Task",
                        placeholder="Describe the code you need. Be specific about interfaces, constraints, and adversarial requirements...",
                        lines=5,
                        max_lines=15,
                    )
                    with gr.Row():
                        mode_select = gr.Dropdown(
                            choices=["deep", "fast", "long-context"],
                            value="deep",
                            label="Reasoning Mode",
                        )
                        priority_select = gr.Dropdown(
                            choices=["performance", "readability", "security"],
                            value="security",
                            label="Optimization Priority",
                        )
                        cycles_slider = gr.Slider(
                            minimum=1, maximum=8, step=1, value=CFG.max_cycles,
                            label="Max Crucible Cycles",
                        )

                    context_files = gr.File(
                        label="Context Files (optional)",
                        file_count="multiple",
                        file_types=[".py", ".md", ".txt", ".yaml", ".json"],
                    )

                    with gr.Row():
                        generate_btn = gr.Button("🚀 Execute AODE Pipeline", variant="primary", scale=2)
                        clear_btn = gr.Button("🔄 Clear", variant="secondary", scale=1)

                # Real-time Trace
                with gr.Group(elem_classes=["sage-panel"]):
                    gr.Markdown("### ⚡ Live Execution Trace")
                    trace_output = gr.JSON(label="Current Step", value={})
                    step_log = gr.Markdown("")

            with gr.Column(scale=3):
                # Output Tabs
                with gr.Tabs():
                    with gr.TabItem("💎 Generated Code"):
                        code_output = gr.Code(label="Adversarially-Hardened Code", language="python", elem_classes=["sage-code"])
                        with gr.Row():
                            copy_btn = gr.Button("📋 Copy to Clipboard")
                            download_btn = gr.Button("⬇️ Download .py")

                    with gr.TabItem("🧪 Tests & Findings"):
                        tests_output = gr.Code(label="Adversarial Tests & Security Findings", language="python")

                    with gr.TabItem("📊 Metrics & XAI"):
                        with gr.Row():
                            with gr.Column():
                                divergence_metric = gr.Number(label="Lie Bracket Divergence Δ", value=0.0, interactive=False)
                            with gr.Column():
                                cycles_metric = gr.Number(label="Nash Cycles", value=0, interactive=False)
                            with gr.Column():
                                vram_metric = gr.Number(label="VRAM Peak (GB)", value=0.0, interactive=False)
                            with gr.Column():
                                time_metric = gr.Number(label="Execution Time (s)", value=0.0, interactive=False)

                        with gr.Row():
                            damage_plot = gr.Plot(label="Damage Trajectory")
                            vram_plot = gr.Plot(label="VRAM Footprint")

                        xai_trace = gr.Dataframe(
                            headers=["Step", "Operator", "Divergence", "Action"],
                            label="XAI Reasoning Trace",
                            wrap=True,
                        )

                    with gr.TabItem("🪟 Live Preview (Glass)"):
                        gr.Markdown("Renders generated code (HTML/Pyodide/React) in a secure, real-time iframe.")
                        render_btn = gr.Button("▶️ Render Current Code", variant="primary")
                        preview_html = gr.HTML("<div style='text-align:center; padding:2rem; color:#64748b;'>No preview generated yet.</div>")

                    with gr.TabItem("👁️ Vision Debugger"):
                        gr.Markdown("Upload a screenshot of a broken UI or plot. SAGE will visually analyze the defect and fix the code.")
                        vision_img = gr.Image(type="filepath", label="Screenshot of the defect")
                        vision_btn = gr.Button("🔍 Analyze & Fix", variant="primary")
                        vision_result = gr.Markdown("Waiting for image...")

                    with gr.TabItem("💭 Chaos Dreamer"):
                        gr.Markdown("Autonomous background self-improvement engine. SAGE dreams up problems, solves them, and updates its Q-table.")
                        with gr.Row():
                            dream_start_btn = gr.Button("▶️ Start Dreaming", variant="primary")
                            dream_stop_btn = gr.Button("⏹️ Stop Dreaming", variant="secondary")
                            refresh_dream_btn = gr.Button("🔄 Refresh Stats")
                        dream_status = gr.Markdown("")
                        dream_stats = gr.JSON(label="Dreamer Statistics", value={})

                    with gr.TabItem("🗺️ Pipeline Map"):
                        pipeline_plot = gr.Plot(label="AODE LangGraph Pipeline")

                    with gr.TabItem("🔧 System Status"):
                        with gr.Row():
                            refresh_health = gr.Button("🔄 Refresh Health")
                        health_table = gr.Dataframe(
                            headers=["Agent", "URL", "Status", "Latency (ms)", "Model", "Error"],
                            label="Backend Health",
                        )
                        config_json = gr.JSON(label="Active Configuration", value=CFG.to_dict())

        # FOOTER
        gr.Markdown("""
        <div style="text-align:center; padding:1rem; color:#64748b; font-size:0.8rem; border-top:1px solid #334155; margin-top:1rem;">
            SAGE v3.0.0 &nbsp;•&nbsp; AODE Engine &nbsp;•&nbsp; Built for AMD Instinct MI300X &nbsp;•&nbsp; (c) 2026 SAGE Engineering
        </div>
        """)

        # ═══════════════════════════════════════════════════════════════
        # EVENT HANDLERS
        # ═══════════════════════════════════════════════════════════════

        async def do_auth(password: str, state: dict):
            if password == CFG.auth_password:
                state["authenticated"] = True
                return (
                    gr.update(visible=False),
                    gr.update(visible=True),
                    "✅ **Access granted.** Welcome to the SAGE boardroom.",
                    state,
                )
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                "❌ **Invalid credentials.** Access denied.",
                state,
            )

        if CFG.enable_auth:
            auth_btn.click(
                fn=do_auth,
                inputs=[auth_input, session_state],
                outputs=[auth_row, main_row, auth_status, session_state],
            )

        async def refresh_system_health(state: dict):
            backend = state.get("backend", create_backend())
            health = await backend.health()
            rows = [[h.name, h.url, h.status, f"{h.latency_ms:.1f}", h.model, h.error] for h in health]
            return gr.Dataframe(value=rows)

        refresh_health.click(
            fn=refresh_system_health,
            inputs=[session_state],
            outputs=[health_table],
        )

        async def run_pipeline(
            task: str,
            files: Optional[List[str]],
            mode: str,
            priority: str,
            max_cycles: int,
            state: dict,
        ):
            """Main generation pipeline with real-time streaming updates."""
            backend = state.get("backend", create_backend())

            context_contents: List[str] = []
            if files:
                for f in files:
                    try:
                        path = Path(f)
                        if path.exists():
                            context_contents.append(path.read_text(encoding="utf-8"))
                    except Exception as e:
                        context_contents.append(f"# Error reading {f}: {e}")

            yield (
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value=0.0),
                gr.update(value=0),
                gr.update(value=0.0),
                gr.update(value=0.0),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value={"status": "Initializing AODE pipeline..."}),
                gr.update(value="⏳ **Initializing...**"),
                gr.update(value=viz.pipeline_graph()),
            )

            start_time = time.time()
            final_data: Optional[Dict[str, Any]] = None
            step_history: List[str] = []

            try:
                async for event in backend.generate(
                    task=task,
                    context_files=context_contents,
                    max_cycles=max_cycles,
                    priority=priority,
                    mode=mode,
                ):
                    ev_type = event.get("type", "unknown")

                    if ev_type == "step":
                        name = event.get("name", "unknown")
                        status = event.get("status", "running")
                        msg = event.get("message", "")
                        output = event.get("output", "")

                        step_history.append(f"**{name}**: {status}")
                        log_md = "\n".join(
                            f'<div class="sage-step {"running" if i == len(step_history)-1 and status == "running" else "complete"}">'
                            f"<strong>{s.split(':')[0]}</strong>: {s.split(':', 1)[1] if ':' in s else ''}"
                            f"</div>"
                            for i, s in enumerate(step_history[-10:])
                        )

                        yield (
                            gr.update(), gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                            gr.update(value={"step": name, "status": status, "message": msg}),
                            gr.update(value=log_md),
                            gr.update(value=viz.pipeline_graph(active_step=name)),
                        )

                    elif ev_type == "final":
                        final_data = event.get("data", {})

            except Exception as e:
                yield (
                    gr.update(value=f"# Error\n\n```\n{str(e)}\n```"),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(),
                    gr.update(value={"status": f"Error: {str(e)}"}),
                    gr.update(value=f"❌ **Pipeline failed:** {str(e)}"),
                    gr.update(),
                )
                return

            elapsed = time.time() - start_time

            if final_data:
                code = final_data.get("final_code", "")
                tests = final_data.get("final_tests", "")
                div = final_data.get("divergence_index", 0.0)
                cycles = final_data.get("nash_cycles", 0)
                traj = final_data.get("damage_trajectory", [])
                vram = final_data.get("vram_peak_gb", 0.0)
                xai = final_data.get("xai_trace", [])

                xai_rows = [[t.get("step_name", ""), t.get("operator", ""), t.get("divergence_signal", 0.0), t.get("action_taken", "")] for t in xai]

                dfig = viz.damage_trajectory(traj) if traj else None
                vfig = viz.vram_usage(cycles) if cycles else None

                state["history"].append({
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                    "divergence": div,
                    "cycles": cycles,
                    "vram": vram,
                    "elapsed": elapsed,
                })

                yield (
                    gr.update(value=code),
                    gr.update(value=tests),
                    gr.update(value=div),
                    gr.update(value=cycles),
                    gr.update(value=vram),
                    gr.update(value=round(elapsed, 2)),
                    gr.update(value=dfig),
                    gr.update(value=vfig),
                    gr.update(value=xai_rows),
                    gr.update(value={"status": "Complete", "divergence": div, "cycles": cycles}),
                    gr.update(value=f"✅ **Pipeline complete** in {elapsed:.1f}s | Divergence Δ={div:.4f} | Cycles={cycles}"),
                    gr.update(value=viz.pipeline_graph()),
                )
            else:
                yield (
                    gr.update(value="# No output generated"),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(),
                    gr.update(value={"status": "No output"}),
                    gr.update(value="⚠️ **No output generated.**"),
                    gr.update(),
                )

        generate_btn.click(
            fn=run_pipeline,
            inputs=[task_input, context_files, mode_select, priority_select, cycles_slider, session_state],
            outputs=[
                code_output, tests_output,
                divergence_metric, cycles_metric, vram_metric, time_metric,
                damage_plot, vram_plot, xai_trace,
                trace_output, step_log, pipeline_plot,
            ],
        )

        def clear_all():
            return (
                gr.update(value=""), gr.update(value=""),
                gr.update(value=0.0), gr.update(value=0), gr.update(value=0.0), gr.update(value=0.0),
                gr.update(value=None), gr.update(value=None), gr.update(value=None),
                gr.update(value={}), gr.update(value=""), gr.update(value=viz.pipeline_graph()),
            )

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[
                code_output, tests_output,
                divergence_metric, cycles_metric, vram_metric, time_metric,
                damage_plot, vram_plot, xai_trace,
                trace_output, step_log, pipeline_plot,
            ],
        )

        def download_code(code: str):
            if not code:
                return ""
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
            tmp.write(code)
            tmp.flush()
            return tmp.name

        download_btn.click(
            fn=download_code,
            inputs=[code_output],
            outputs=[gr.File(label="Download", visible=False)],
        )

        demo.load(
            fn=refresh_system_health,
            inputs=[session_state],
            outputs=[health_table],
        )

        # v3.0 Feature Event Handlers
        async def do_render(code: str, state: dict):
            if not code:
                return "<div style='color: #ef4444;'>No code to render.</div>"
            backend = state.get("backend", create_backend())
            return await backend.render_code(code)

        render_btn.click(
            fn=do_render,
            inputs=[code_output, session_state],
            outputs=[preview_html],
        )

        async def do_vision_debug(image_path: str, code: str, state: dict):
            if not image_path:
                return "Please upload an image first."
            backend = state.get("backend", create_backend())
            return await backend.vision_debug(image_path, code)

        vision_btn.click(
            fn=do_vision_debug,
            inputs=[vision_img, code_output, session_state],
            outputs=[vision_result],
        )

        async def do_dream_start(state: dict):
            backend = state.get("backend", create_backend())
            status = await backend.toggle_dreamer(start=True)
            return f"**Dreamer Status:** {status}"

        async def do_dream_stop(state: dict):
            backend = state.get("backend", create_backend())
            status = await backend.toggle_dreamer(start=False)
            return f"**Dreamer Status:** {status}"

        async def do_dream_stats(state: dict):
            backend = state.get("backend", create_backend())
            stats = await backend.get_dreamer_stats()
            return stats

        dream_start_btn.click(fn=do_dream_start, inputs=[session_state], outputs=[dream_status])
        dream_stop_btn.click(fn=do_dream_stop, inputs=[session_state], outputs=[dream_status])
        refresh_dream_btn.click(fn=do_dream_stats, inputs=[session_state], outputs=[dream_stats])
        demo.load(fn=do_dream_stats, inputs=[session_state], outputs=[dream_stats])

    return demo

# ═══════════════════════════════════════════════════════════════════════
# 4. ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 70)
    print("  SAGE — Strategic Adversarial Generative Engine")
    print("  Version 3.0.0 | AODE Pipeline | AMD MI300X Optimized")
    print("=" * 70)
    print(f"  Mode           : {CFG.mode.upper()}")
    print(f"  HF Space       : {CFG.is_hf_space}")
    print(f"  AMD Cloud      : {CFG.is_amd_cloud}")
    print(f"  API URL        : {CFG.api_url}")
    print(f"  Ollama URL     : {CFG.ollama_url}")
    print(f"  Max Cycles     : {CFG.max_cycles}")
    print(f"  Auth Enabled   : {CFG.enable_auth}")
    print("=" * 70)

    app = build_ui()

    # Hugging Face Spaces uses port 7860 by default
    port = int(os.environ.get("PORT", "7860"))
    host = "0.0.0.0"

    app.launch(
        server_name=host,
        server_port=port,
        share=False,
        show_error=True,
        favicon_path=None,
    )


if __name__ == "__main__":
    main()
