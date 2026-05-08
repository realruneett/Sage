import uvicorn
import structlog
import uuid
import time
import httpx
import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sage.api.schemas import CodeRequest, ReviewRequest, RefactorRequest, SolveIssueRequest, APIResponse
from sage.api.streaming import create_streaming_response
from sage.core.graph import build_graph
from sage.core.types import SageRequest

logger = structlog.get_logger(__name__)

app = FastAPI(title="SAGE-PRO Engine API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
STATIC_DIR = Path(__file__).resolve().parent.parent / "ui" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    """Serves the SAGE-PRO Dark Nebula Dashboard."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info("http_request", path=request.url.path, duration=duration, status_code=response.status_code)
    response.headers["X-Request-ID"] = request_id
    return response


@app.post("/v1/code", response_model=APIResponse)
async def generate_code(req: CodeRequest):
    """Generates adversarially-hardened code for a given task."""
    graph = build_graph()
    sage_req = SageRequest(
        task=req.task,
        context_files=req.context_files,
        max_cycles=req.max_cycles,
        priority=req.priority
    )

    try:
        result = await graph.ainvoke({"request": sage_req, "repo_files": []})
        return APIResponse(
            request_id=str(uuid.uuid4()),
            **result
        )
    except Exception as e:
        logger.error("graph_invocation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/review")
async def review_code(req: ReviewRequest):
    """Performs a Red-Team review of existing code."""
    return {"status": "under_construction"}


@app.get("/healthz")
async def health_check():
    """Checks if the SAGE-PRO server is alive."""
    return {"status": "healthy"}


@app.get("/readyz")
async def readiness_check():
    """Checks if all co-resident vLLM backends are reachable."""
    ports = [8001, 8002, 8003, 8004]
    async with httpx.AsyncClient() as client:
        for port in ports:
            try:
                resp = await client.get(f"http://localhost:{port}/v1/models")
                if resp.status_code != 200:
                    raise HTTPException(status_code=503, detail=f"vLLM port {port} not ready")
            except Exception:
                raise HTTPException(status_code=503, detail=f"vLLM port {port} unreachable")
    return {"status": "all_systems_ready"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
