from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CodeRequest(BaseModel):
    task: str
    context_files: Optional[List[str]] = []
    mode: str = "deep" # fast | deep | long-context

class CodeResponse(BaseModel):
    code: str
    tests: str
    tool_report: Dict[str, Any]
    divergence_index: float
    nash_cycles: int
    damage_trajectory: List[float]
    vram_peak_gb: float
    xai_trace: List[str]
