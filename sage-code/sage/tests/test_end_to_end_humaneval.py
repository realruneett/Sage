import pytest
import asyncio
from sage.core.graph import create_sage_code_graph

@pytest.mark.asyncio
async def test_end_to_end_humaneval():
    """Sanity check for the full graph execution on a stub problem."""
    class StubAgent:
        async def generate(self, prompt):
            from sage.core.aode import CodeProposal
            import numpy as np
            return CodeProposal(code="def solution(): return 42", tests="", vector=np.zeros(1024), cycle=0)

    agents = {
        "architect": StubAgent(),
        "implementer": StubAgent(),
        "synthesizer": StubAgent(),
        "red_team": StubAgent()
    }
    
    graph = create_sage_code_graph(agents)
    result = await graph.ainvoke({"task": "return 42"})
    
    assert "final_code" in result
    assert "solution" in result["final_code"]
