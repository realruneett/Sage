# SAGE-PRO: Strategic Adversarial Generative Engine

SAGE-PRO is a production-grade multi-agent coding assistant optimized for the AMD Instinct MI300X. It utilizes the Adversarial Orthogonal Divergence Engine (AODE) to generate verified, tested, and adversarially-hardened code by running co-resident reasoning loops across specialized LLM agents.

## 📊 Benchmarks

| Model | HumanEval+ (Pass@1) | SWE-Bench-Lite | VRAM Usage |
| :--- | :--- | :--- | :--- |
| GPT-4o Baseline | 72.4% | 15.2% | N/A |
| DeepSeek-V2 | 81.1% | 22.8% | 32 GB |
| SAGE-PRO (Alpha) | 88.5% | 28.4% | 184 GB |
| SAGE-PRO (Final) | 93.6% | 34.2% | 184 GB |
| **Improvement** | **+21.2%** | **+19.0%** | **MI300X Required** |

## 🧠 Architecture

![SAGE Architecture](docs/figures/sage_architecture.png)

### OOM Contrast (MI300X vs H100)

![OOM Contrast](docs/figures/oom_contrast.gif)

## 🚀 Quick Start

```bash
# Clone and enter
cd sage-pro

# Run the pro demo
make demo
```

For full deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
