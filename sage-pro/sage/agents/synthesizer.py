from sage.agents.base import VLLMAgent

class SynthesizerAgent(VLLMAgent):
    """Synthesizer specialist utilizing Qwen2.5-Coder-72B.

    Responsible for merging architectural designs and implementations via Lie-bracket synthesis.
    Approximate VRAM usage: 45 GB (AWQ-4bit).
    """
    def __init__(self) -> None:
        """Initializes the Synthesizer agent with specified MI300X VRAM allocation."""
        super().__init__(
            name="synthesizer",
            model_path="Qwen/Qwen2.5-Coder-72B-Instruct",
            quantization="awq",
            gpu_memory_utilization=0.24,
            vram_gb=45.0
        )
