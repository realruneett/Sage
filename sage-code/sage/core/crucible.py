from typing import Tuple, List, Dict, Any
from sage.core.aode import CodeProposal, nash_refine
from sage.tools.grounding import evaluate_code
from loguru import logger

class CrucibleLoop:
    """The Nash Equilibrium refinement loop for code.

    This module coordinates the adversarial refinement of code by leveraging 
    the Red-Team (attacks) and the Synthesizer (fixes), grounded by tool feedback.
    """
    def __init__(self, red_team_agent: Any, synth_agent: Any) -> None:
        """Initializes the Crucible with the specialized agents.
        
        Args:
            red_team_agent: The agent responsible for finding flaws.
            synth_agent: The agent responsible for fixing flaws.
        """
        self.red_team = red_team_agent
        self.synth = synth_agent

    async def refine(self, proposal: CodeProposal) -> Tuple[CodeProposal, List[Dict[str, Any]]]:
        """Runs the grounded Nash loop until convergence or max cycles.

        Args:
            proposal: The initial code proposal to refine.

        Returns:
            Tuple containing the converged CodeProposal and the refinement history.
        """
        async def red_fn(code: str) -> Any:
            return await self.red_team.generate(f"Perform adversarial attack on this code:\n{code}")
            
        async def synth_fn(prop: CodeProposal, tool_report: Dict[str, Any]) -> Any:
            return await self.synth.generate(
                f"Fix the following code based on the tool findings:\n"
                f"Code: {prop.code}\nFindings: {tool_report}"
            )

        async def tool_fn(code: str, tests: str) -> Dict[str, Any]:
            return await evaluate_code(code, tests)

        # delegate to the core AODE nash_refine implementation
        return await nash_refine(
            proposal,
            red_fn,
            synth_fn,
            tool_fn
        )
