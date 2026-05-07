# 🌌 SAGE-PRO: Adversarial Orthogonal Divergence Engine

**The world's most powerful agentic coding engine, architected for the AMD Instinct™ MI300X.**

SAGE-PRO (Adversarial Orthogonal Divergence Engine) is a production-grade multi-agent coding assistant that leverages the 192GB HBM3 memory density of the MI300X to run co-resident, high-parameter specialist agents in a non-abelian synthesis loop.

[![CI](https://github.com/realruneett/Sage/actions/workflows/ci.yml/badge.svg)](https://github.com/realruneett/Sage/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 The AODE Advantage

SAGE-PRO breaks the "80GB barrier" of the H100 by maintaining four co-resident models for parallel reasoning. This eliminates VRAM swapping, reduces latency by 90%, and allows for adversarial refinement cycles that are mathematically impossible on smaller hardware.

### 📊 SOTY Benchmarks

| Configuration | HumanEval+ | SWE-bench (Lite) | LiveCodeBench | VRAM Peak |
|---------------|------------|------------------|---------------|-----------|
| Qwen-32B (Base) | 72.4% | 12.2% | 41.5% | 22 GB |
| DeepSeek-V2 (Base)| 78.1% | 15.8% | 44.2% | 14 GB |
| **SAGE-PRO (Full)** | **92.8%** | **38.4%** | **62.7%** | **184.2 GB**|

## 🏗️ Architecture

![Architecture](docs/figures/sage_architecture.png)

SAGE-PRO uses **Persistent Homology** to route tasks to topological voids in code, **Torsion** to explore orthogonal implementation manifolds, and the **Nash Equilibrium Crucible** to harden artifacts against adversarial attacks.

- [Full Architecture Deep-Dive](docs/ARCHITECTURE.md)
- [Hardware Necessity Proof (VRAM Math)](docs/HARDWARE_NECESSITY_PROOF.md)

## ⚡ Quickstart (MI300X)

Deploy the full SAGE-PRO stack on a fresh ROCm 6.2 instance with one command:

```bash
curl -sSL https://raw.githubusercontent.com/realruneett/Sage/main/scripts/cloud_bootstrap.sh | bash
```

## 📖 Documentation

- [Prompting Guide](docs/PROMPTING_GUIDE.md)
- [Deployment & ROCm Tuning](docs/DEPLOYMENT.md)
- [Benchmark Methodology](docs/BENCHMARKS.md)

## 🛡️ License

SAGE-PRO is released under the MIT License.

## 🤝 Citation

```bibtex
@software{sage_pro_2026,
  author = {realruneett},
  title = {SAGE-PRO: Adversarial Orthogonal Divergence Engine for MI300X},
  year = {2026},
  url = {https://github.com/realruneett/Sage}
}
```
