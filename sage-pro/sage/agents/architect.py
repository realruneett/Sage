from sage.agents.base import VLLMAgent

class ArchitectAgent(VLLMAgent):
    """Architect specialist utilizing Qwen2.5-Coder-32B.

    Responsible for high-level design, file layout, and API contracts.
    Approximate VRAM usage: 20 GB (AWQ-4bit).
    """
    def __init__(self) -> None:
        """Initializes the Architect agent with specified MI300X VRAM allocation."""
        super().__init__(
            name="architect",
            model_path="Qwen/Qwen2.5-Coder-32B-Instruct",
            quantization="awq",
            gpu_memory_utilization=0.11,
            vram_gb=20.0
        )
