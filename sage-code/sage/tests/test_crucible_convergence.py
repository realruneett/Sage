import pytest
import asyncio
from sage.core.aode import CodeProposal, nash_refine

@pytest.mark.asyncio
async def test_crucible_convergence():
    """Verifies that the Nash loop converges as damage decreases."""
    async def mock_red(code):
        from unittest.mock import MagicMock
        m = MagicMock()
        m.tests = "assert True"
        return m
        
    async def mock_synth(prop, report):
        return CodeProposal(code=prop.code, tests="", vector=prop.vector, cycle=prop.cycle + 1)
        
    async def mock_tool(code, tests):
        # Decrease damage over cycles
        cycle = int(code.split()[-1]) if code.split() else 0
        return {"total_damage": max(0, 0.8 - 0.3 * cycle)}

    initial = CodeProposal(code="Initial 0", tests="", vector=[0], cycle=0)
    final, history = await nash_refine(initial, mock_red, mock_synth, mock_tool, eps=0.1)
    
    assert len(history) <= 4
    assert history[-1]["damage"] < 0.8
