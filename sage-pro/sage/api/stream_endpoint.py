"""
SAGE-PRO Streaming SSE Endpoint
════════════════════════════════
Emits structured Server-Sent Events as each agent in the AODE pipeline
completes its phase.  The Gradio frontend consumes these events to drive
the live XAI trace, telemetry panel, and final artifact display.

Event schema (one JSON object per SSE `data:` line):
    {
      "event":   "agent_start" | "agent_token" | "agent_done" | "pipeline_done" | "error",
      "agent":   "Architect" | "Implementer" | "Red-Team" | "Synthesizer",
      "content": "<text>",
      "meta": {
        "vram_gb":    float,
        "nash_cycle": int,
        "divergence": float,
        "status":     str,
      }
    }
"""

import json
import asyncio
import structlog
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


# ── Request model ──────────────────────────────────────────────────────────
class StreamRequest(BaseModel):
    """Request body for the streaming SAGE pipeline."""
    query: str = Field(..., description="Natural language coding task")
    max_cycles: int = Field(default=5, ge=1, le=12)
    priority: str = Field(default="performance")


# ── SSE event helper ───────────────────────────────────────────────────────
def _sse_event(event: str, agent: str = "", content: str = "", **meta) -> str:
    """Encode a single SSE data payload."""
    return json.dumps({
        "event": event,
        "agent": agent,
        "content": content,
        "meta": meta,
    })


# ── Pipeline runner (streams real agent outputs via the live graph) ────────
async def _run_pipeline(query: str, max_cycles: int, priority: str) -> AsyncGenerator[str, None]:
    """
    Drives the full AODE 4-agent pipeline and yields SSE events.

    Uses the same lazy-bootstrapped agents from server.py.
    """
    try:
        # Import the lazy bootstrap from server
        from sage.api.server import _get_graph
        from sage.core.types import SageRequest
    except ImportError as e:
        yield _sse_event("error", content=f"Pipeline import failed: {e}")
        return

    sage_req = SageRequest(
        task=query,
        context_files=[],
        max_cycles=max_cycles,
        priority=priority,
    )

    try:
        graph = _get_graph()

        # Emit boot
        yield _sse_event("agent_start", agent="SYSTEM", content="Initialising SAGE-PRO AODE council …",
                         vram_gb=0, nash_cycle=0, divergence=1.0, status="BOOTING")

        # Run the full graph
        result = await graph.ainvoke({"request": sage_req, "repo_files": []})

        # Extract structured data from result
        final_code = result.get("final_code", "")
        nash_cycles = len(result.get("cycle_history", []))
        divergence = result.get("divergence_index", 0.0)
        vram_peak = result.get("vram_peak_gb", 0.0)
        xai_trace = result.get("xai_trace", [])

        # Emit per-agent traces from the XAI log
        for trace_entry in xai_trace:
            agent_name = getattr(trace_entry, "step_name", "SYSTEM")
            action = getattr(trace_entry, "action_taken", "")
            div_signal = getattr(trace_entry, "divergence_signal", divergence)
            yield _sse_event(
                "agent_done",
                agent=agent_name,
                content=action,
                vram_gb=vram_peak,
                nash_cycle=nash_cycles,
                divergence=div_signal,
                status="RUNNING",
            )

        # Final event
        yield _sse_event(
            "pipeline_done",
            agent="COUNCIL",
            content=final_code,
            vram_gb=vram_peak,
            nash_cycle=nash_cycles,
            divergence=divergence,
            status="CONVERGED",
        )

    except Exception as e:
        logger.error("stream_pipeline_failed", error=str(e))
        yield _sse_event("error", content=f"Pipeline error: {e}")


# ── SSE endpoint ───────────────────────────────────────────────────────────
@router.post("/v1/sage/stream")
async def stream_sage_pipeline(req: StreamRequest):
    """
    Streams the full AODE adversarial pipeline as Server-Sent Events.
    Consumed by the Gradio frontend's `run_sage_engine()` generator.
    """
    return EventSourceResponse(_run_pipeline(req.query, req.max_cycles, req.priority))


@router.get("/v1/sage/health")
async def sage_pipeline_health():
    """Quick check that the pipeline modules can be imported."""
    try:
        from sage.core.graph import build_graph  # noqa: F401
        return {"status": "pipeline_ready"}
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Pipeline not ready: {e}")
