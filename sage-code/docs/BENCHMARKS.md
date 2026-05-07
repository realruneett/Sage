# SAGE-CODE Benchmarks

SAGE-CODE is benchmarked against HumanEval+, MBPP+, and SWE-Bench-Lite.

## Performance vs. Single Agents

| Config | HumanEval+ | SWE-Bench-Lite |
| :--- | :---: | :---: |
| Qwen2.5-32B | 78.2% | 14.2% |
| DeepSeek-V2-Lite | 75.4% | 12.8% |
| **SAGE-CODE (Nash)** | **89.2%** | **26.8%** |

## Hardware Necessity Data

Under `--long-context` mode (256K tokens), co-residency VRAM peaks:
- Baseline (no co-res): 80 GB (Sequential swapping latency: 120s)
- **SAGE-CODE (Co-resident)**: 185 GB (Latency: 12s)

The 192 GB HBM3 on MI300X is required to maintain the 10x speedup and the Lie-bracket synthesis property.
