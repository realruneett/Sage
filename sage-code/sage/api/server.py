from fastapi import FastAPI, HTTPException
from loguru import logger
import uvicorn
import os

from sage.api.schemas import CodeRequest, CodeResponse
from sage.core.graph import create_sage_code_graph

# Mock agents for initialization
class MockAgent:
    async def generate(self, prompt: str):
        from sage.core.aode import CodeProposal
        import numpy as np
        return CodeProposal(code=f"# Generated code for: {prompt[:20]}\ndef main(): pass", tests="assert True", vector=np.random.randn(1024), cycle=0)

agents = {
    "architect": MockAgent(),
    "implementer": MockAgent(),
    "synthesizer": MockAgent(),
    "red_team": MockAgent()
}

app = FastAPI(title="SAGE-CODE API", version="0.1.0")
graph = create_sage_code_graph(agents)

@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Health check endpoint for the SAGE-CODE engine.
    
    Returns:
        Dict indicating the system status and target hardware.
    """
    return {"status": "ok", "engine": "SAGE-CODE", "hardware": "AMD MI300X"}

@app.post("/v1/code", response_model=CodeResponse)
async def code_endpoint(request: CodeRequest) -> CodeResponse:
    """Primary endpoint for adversarially-hardened code generation.
    
    Triggers the full SAGE-CODE LangGraph workflow: Ingest -> Route -> Debate -> 
    Synth -> Crucible -> Verify -> Emit.

    Args:
        request: The CodeRequest containing the task and context.

    Returns:
        CodeResponse containing the final verified solution and reasoning trace.
    """
    logger.info(f"Received coding task: {request.task}")
    try:
        inputs = {"task": request.task, "context_files": request.context_files}
        # Execute the reasoning graph
        result = await graph.ainvoke(inputs)
        
        return CodeResponse(
            code=result["final_code"],
            tests=result["final_tests"],
            tool_report={}, 
            divergence_index=result["divergence_index"],
            nash_cycles=len(result["cycle_history"]),
            damage_trajectory=[c["damage"] for c in result["cycle_history"]],
            vram_peak_gb=result["vram_peak_gb"],
            xai_trace=result["xai_trace"]
        )
    except Exception as e:
        logger.error(f"SAGE-CODE Engine Failure: {e}")
        raise HTTPException(status_code=500, detail=f"Engine failure: {str(e)}")

if __name__ == "__main__":
    from typing import Dict
    uvicorn.run(app, host="0.0.0.0", port=8000)
