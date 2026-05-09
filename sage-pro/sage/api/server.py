"""
SAGE-PRO FastAPI Server
═══════════════════════
Headless API for the Axiomatic Orthogonal Divergence Engine.
Bootstraps all agents, tools, and the LangGraph pipeline on startup.
"""

import os
import uvicorn
import yaml
import structlog
import uuid
import time
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sage.api.schemas import CodeRequest, ReviewRequest, RefactorRequest, SolveIssueRequest, APIResponse
from sage.api.streaming import create_streaming_response
from sage.api.stream_endpoint import router as stream_router
from sage.core.graph import build_graph
from sage.core.types import SageRequest

# Agent imports
from sage.agents.architect import Architect
from sage.agents.implementer import Implementer
from sage.agents.red_team import RedTeam
from sage.agents.synthesizer import Synthesizer
from sage.core.routing import CodeTopologyRouter

# Tool imports
from sage.tools.sandbox import run_in_sandbox, run_command_in_sandbox
from sage.tools.linter import run_ruff
from sage.tools.security import run_bandit, run_semgrep

logger = structlog.get_logger(__name__)

app = FastAPI(title="SAGE-PRO Engine API", version="2.0.0")

# Register the streaming SSE endpoint for the Gradio frontend
app.include_router(stream_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────
#  Bootstrap agents & tools at module level
# ─────────────────────────────────────────────────────────────────────

def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _build_agents(hyperparams: dict) -> dict:
    """Instantiate all 4 agents + router from environment config."""
    vllm_hosts = hyperparams.get("vllm_hosts", {})
    agent_configs = hyperparams.get("agents", {})
    
    arch_cfg = agent_configs.get("architect", {})
    impl_cfg = agent_configs.get("implementer", {})
    syn_cfg = agent_configs.get("synthesizer", {})
    rt_cfg = agent_configs.get("redteam", {})

    return {
        "architect": Architect(
            base_url=_env("VLLM_HOST_ARCHITECT", vllm_hosts.get("architect", "http://localhost:8001/v1")),
            model_name=arch_cfg.get("model_name", "qwen2.5:72b"),
            prompt_path=arch_cfg.get("prompt_path", "sage/prompts/architect.md"),
            temperature=arch_cfg.get("temperature", 0.3),
        ),
        "implementer": Implementer(
            base_url=_env("VLLM_HOST_IMPLEMENTER", vllm_hosts.get("implementer", "http://localhost:8002/v1")),
            model_name=impl_cfg.get("model_name", "qwen2.5-coder:32b"),
            prompt_path=impl_cfg.get("prompt_path", "sage/prompts/implementer.md"),
            temperature=impl_cfg.get("temperature", 0.1),
        ),
        "synthesizer": Synthesizer(
            base_url=_env("VLLM_HOST_SYNTHESIZER", vllm_hosts.get("synthesizer", "http://localhost:8003/v1")),
            model_name=syn_cfg.get("model_name", "deepseek-coder-v2:16b"),
            prompt_path=syn_cfg.get("prompt_path", "sage/prompts/synthesizer.md"),
            temperature=syn_cfg.get("temperature", 0.0),
        ),
        "red_team": RedTeam(
            base_url=_env("VLLM_HOST_REDTEAM", vllm_hosts.get("redteam", "http://localhost:8004/v1")),
            primary_model=rt_cfg.get("primary_model", "starcoder2:15b"),
            secondary_model=rt_cfg.get("secondary_model", "starcoder2:15b"),
            primary_temperature=rt_cfg.get("primary_temperature", 0.7),
            secondary_temperature=rt_cfg.get("secondary_temperature", 0.5),
            prompt_path=rt_cfg.get("prompt_path", "sage/prompts/red_team.md"),
        ),
        "router": CodeTopologyRouter(
            model_name=hyperparams.get("embedding_model", "BAAI/bge-small-en-v1.5"),
            index_dims=hyperparams.get("index_dims", 384),
            max_neighbors=hyperparams.get("routing_max_neighbors", 5),
            search_cap=hyperparams.get("routing_search_cap", 500),
        ),
    }


def _build_tools() -> dict:
    """Build tool callables compatible with the Crucible loop."""
    import tempfile
    from pathlib import Path

    async def ruff_tool(code: str):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            f.flush()
            return await run_ruff(f.name)

    async def mypy_tool(code: str):
        """Run mypy via sandbox — returns findings list."""
        import json as _json
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            f.flush()
            ret, stdout, stderr = await run_command_in_sandbox(
                ["python3", "-m", "mypy", "--no-error-summary", "--output", "json", f.name]
            )
            try:
                return _json.loads(stdout) if stdout else []
            except Exception:
                return []

    async def bandit_tool(code: str):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            f.flush()
            return await run_bandit(f.name)

    async def sandbox_tool(code: str, tests: str):
        return await run_in_sandbox(code, tests)

    return {
        "ruff": ruff_tool,
        "mypy": mypy_tool,
        "bandit": bandit_tool,
        "sandbox": sandbox_tool,
    }


def _load_hyperparams() -> dict:
    """Load AODE hyperparameters from YAML config."""
    config_path = "configs/aode_hyperparams.yaml"
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("hyperparams_not_found", path=config_path)
        return {
            "epsilon": 0.05,
            "delta": 0.02,
            "max_cycles": 4,
            "damage_weights": {
                "ruff": 0.1, "mypy": 0.2, "bandit": 0.5,
                "semgrep": 0.4, "tests": 1.0, "complexity": 0.05,
            },
        }


def _load_torsion_penalties() -> dict:
    """Load torsion token penalty map from YAML config."""
    config_path = "configs/torsion_penalties.yaml"
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("torsion_penalties_not_found", path=config_path)
        return {}


# Lazy-initialized globals — created on first request
_agents = None
_tools = None
_hyperparams = None
_torsion_penalties = None


def _get_graph():
    """Returns a compiled graph with live agents and tools."""
    global _agents, _tools, _hyperparams, _torsion_penalties
    if _agents is None:
        _hyperparams = _load_hyperparams()
        _agents = _build_agents(_hyperparams)
        _tools = _build_tools()
        _torsion_penalties = _load_torsion_penalties()
        logger.info("sage_pipeline_bootstrapped",
                     agents=list(_agents.keys()),
                     tools=list(_tools.keys()))
    return build_graph(_agents, _tools, _hyperparams, _torsion_penalties)


# ─────────────────────────────────────────────────────────────────────
#  HTTP middleware
# ─────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """SAGE-PRO API root — headless engine, no frontend."""
    return {
        "service": "SAGE-PRO Engine",
        "version": "2.0.0",
        "aode": True,
        "endpoints": ["/v1/code", "/v1/sage/stream", "/v1/review", "/healthz", "/readyz"],
    }


@app.post("/v1/code", response_model=APIResponse)
async def generate_code(req: CodeRequest):
    """Generates adversarially-hardened code for a given task."""
    graph = _get_graph()
    sage_req = SageRequest(
        task=req.task,
        context_files=req.context_files,
        max_cycles=req.max_cycles,
        priority=req.priority,
    )

    try:
        result = await graph.ainvoke({"request": sage_req, "repo_files": []})
        return APIResponse(
            request_id=str(uuid.uuid4()),
            **result,
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
    global _hyperparams
    if _hyperparams is None:
        _hyperparams = _load_hyperparams()
        
    vllm_hosts = _hyperparams.get("vllm_hosts", {})
    hosts = list(vllm_hosts.values())
    
    if not hosts:
        hosts = [
            "http://localhost:8001/v1",
            "http://localhost:8002/v1",
            "http://localhost:8003/v1",
            "http://localhost:8004/v1"
        ]
        
    async with httpx.AsyncClient() as client:
        for host in hosts:
            # We want to ping the base URL's /models endpoint
            url = f"{host.rstrip('/')}/models"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise HTTPException(status_code=503, detail=f"vLLM host {host} not ready")
            except Exception:
                raise HTTPException(status_code=503, detail=f"vLLM host {host} unreachable")
    return {"status": "all_systems_ready"}


if __name__ == "__main__":
    hyperparams = _load_hyperparams()
    host = hyperparams.get("server_host", "0.0.0.0")
    port = hyperparams.get("server_port", 8000)
    uvicorn.run(app, host=host, port=port)
