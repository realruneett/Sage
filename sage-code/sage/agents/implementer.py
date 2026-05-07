from sage.agents.base import VLLMAgent

class ImplementerAgent(VLLMAgent):
    """Implementer specialist utilizing DeepSeek-Coder-V2-Lite.

    Responsible for writing dense, idiomatic code bodies based on Architect specs.
    Approximate VRAM usage: 12 GB (AWQ-4bit).
    """
    def __init__(self) -> None:
        """Initializes the Implementer agent with specified MI300X VRAM allocation."""
        super().__init__(
            name="implementer",
            model_path="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
            quantization="awq",
            gpu_memory_utilization=0.07,
            vram_gb=12.0
        )
