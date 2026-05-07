import structlog
from sage.agents.base import VLLMAgent

logger = structlog.get_logger(__name__)

class Synthesizer(VLLMAgent):
    \"\"\"The Synthesizer specialist agent.

    Responsible for merging divergent code branches (ABC/ACB) into a unified, 
    hardened solution. Uses Qwen2.5-Coder-72B for high-parameter reasoning.
    \"\"\"

    def __init__(
        self, 
        base_url: str, 
        model_name: str = "Qwen2.5-Coder-72B-Instruct-AWQ",
        prompt_path: str = "sage/prompts/synthesizer.md"
    ) -> None:
        \"\"\"Initializes the Synthesizer with specialized parameters for MI300X.\"\"\"
        super().__init__(
            name="Synthesizer",
            base_url=base_url,
            model_name=model_name,
            temperature=0.0, # Greedy for stable synthesis
            system_prompt_path=prompt_path
        )

    async def merge(
        self, 
        spec: str, 
        code_abc: str, 
        code_acb: str, 
        red_team_prior: str = ""
    ) -> str:
        \"\"\"Resolves divergence between synthesis branches using the Lie bracket commutator.

        Args:
            spec: The original architectural specification.
            code_abc: Code from the Design-first branch.
            code_acb: Code from the Threat-first branch.
            red_team_prior: Optional prior findings from the Red-Team.

        Returns:
            The final synthesized and hardened Python code.
        \"\"\"
        user_msg = (
            f"Architectural Spec:\\n{spec}\\n\\n"
            f"Branch ABC (Design-First):\\n{code_abc}\\n\\n"
            f"Branch ACB (Threat-First):\\n{code_acb}\\n\\n"
            f"Red-Team Findings:\\n{red_team_prior}\\n\\n"
            f"Synthesize the final hardened solution. Resolve all semantic conflicts."
        )
        
        response = await self.complete(user_msg)
        return response.content
