from sage.agents.base import VLLMAgent

class RedTeamAgent(VLLMAgent):
    """Red-Team adversary ensemble.

    Responsible for attacking code to find bugs, security flaws, and edge cases.
    Approximate VRAM usage: 32 GB (FP16 ensemble).
    """
    def __init__(self) -> None:
        """Initializes the Red-Team agent with specified MI300X VRAM allocation."""
        # Using primary adversary model for the demo
        super().__init__(
            name="red_team",
            model_path="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
            quantization=None, # FP16 for adversarial precision
            gpu_memory_utilization=0.17,
            vram_gb=32.0
        )
