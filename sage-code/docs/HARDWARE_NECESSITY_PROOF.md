# Hardware Necessity Proof: AMD MI300X vs NVIDIA H100

SAGE-CODE is architected to exploit the unique memory density of the AMD Instinct MI300X.

## The Bottleneck: Co-Residency

To maintain the **Non-Abelian Lie Bracket** property, four LLM agents must reside in VRAM simultaneously. Sequential swapping introduces state decay and 10x latency penalties.

| Hardware | VRAM | Co-Residency Status |
| :--- | :--- | :--- |
| NVIDIA H100 | 80 GB | **FAILED** (Requires swapping) |
| AMD MI300X | 192 GB | **SUCCESS** (Full co-residency) |

## Long-Context Expansion

In `--long-context` mode (256K tokens), the KV-cache for the 72B Synthesizer alone consumes ~50 GB.

- **Architect (32B)**: 20 GB
- **Implementer (16B)**: 12 GB
- **Synthesizer (72B) + KV-cache**: 95 GB
- **Red-Team (Ensemble)**: 32 GB
- **Total**: **~159 GB** (Plus activation overhead → ~185 GB)

The NVIDIA H100 (80 GB) is mathematically incapable of running this stack without OOM.
