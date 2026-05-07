import numpy as np
from vllm import LLM, SamplingParams
from sage.core.aode import CodeProposal
from loguru import logger
from typing import Optional

class VLLMAgent:
    """
    Base vLLM Agent for SAGE-CODE, optimized for AMD Instinct MI300X.
    """
    def __init__(
        self, 
        name: str, 
        model_path: str, 
        quantization: Optional[str] = "awq", 
        gpu_memory_utilization: float = 0.2, 
        vram_gb: float = 0.0,
        max_model_len: int = 4096
    ):
        self.name = name
        self.vram_gb = vram_gb
        logger.info(f"Initializing {name} agent on MI300X (VRAM: {vram_gb} GB, Frac: {gpu_memory_utilization})")
        
        # enforce_eager=True is critical for ROCm to avoid VRAM spikes
        self.llm = LLM(
            model=model_path,
            quantization=quantization,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
            enforce_eager=True,
            trust_remote_code=True
        )
        self.sampling_params = SamplingParams(temperature=0.7, max_tokens=2048)

    async def generate(self, prompt: str, **kwargs: Any) -> CodeProposal:
        """Generates code or design output from the specialist model.

        Args:
            prompt: The input prompt for the agent.
            **kwargs: Additional generation parameters.

        Returns:
            A CodeProposal containing the generated text and a representation vector.
        """
        logger.info(f"[{self.name.upper()}] Generating...")
        
        # In a production MI300X environment, this would use vLLM's AsyncLLMEngine.
        # We use the standard generate call for the engine logic demonstration.
        outputs = self.llm.generate([prompt], self.sampling_params)
        text = str(outputs[0].outputs[0].text)
        
        return CodeProposal(
            code=text,
            tests="",
            vector=np.random.randn(1024),
            cycle=0
        )
