import asyncio
from loguru import logger
from sage.core.graph import create_sage_code_graph

class MockMI300XCodeAgent:
    def __init__(self, name):
        self.name = name
    async def generate(self, prompt):
        from sage.core.aode import CodeProposal
        import numpy as np
        logger.info(f"[{self.name.upper()}] Loading... ✓")
        return CodeProposal(
            code=f"# SAGE-CODE Solution\nclass Cache:\n    async def evict(self): pass",
            tests="def test_evict(): pass",
            vector=np.random.randn(1024),
            cycle=0
        )

async def main():
    logger.info("Starting SAGE-CODE Demo on AMD MI300X...")
    
    agents = {
        "architect": MockMI300XCodeAgent("architect"),
        "implementer": MockMI300XCodeAgent("implementer"),
        "synthesizer": MockMI300XCodeAgent("synthesizer"),
        "red_team": MockMI300XCodeAgent("red_team")
    }
    
    graph = create_sage_code_graph(agents)
    task = "Build a thread-safe LRU cache with TTL and async eviction"
    
    result = await graph.ainvoke({"task": task})
    
    print("\n--- SAGE-CODE EXECUTION TRACE ---")
    print(f"[VRAM] {result['vram_peak_gb']} / 192.0 GB")
    print(f"[DIVERGENCE] {result['divergence_index']:.4f}")
    for cycle in result["cycle_history"]:
        print(f"[CYCLE {cycle['cycle']}] Damage: {cycle['damage']:.2f}")
    
    print("\nFINAL CODE PREVIEW:")
    print(result["final_code"][:100] + "...")

if __name__ == "__main__":
    asyncio.run(main())
