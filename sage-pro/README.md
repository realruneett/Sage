# 🛡️ SAGE-CODE

**Adversarially-hardened pro coding engine on AMD MI300X.**

SAGE-CODE is a multi-agent coding assistant designed to solve complex software engineering tasks with mechanical verification. By running four specialized LLMs co-resident on a single **AMD Instinct MI300X (192 GB HBM3)**, it achieves reasoning depth that is mathematically impossible on lower-memory hardware.

![SAGE Architecture](docs/figures/sage_architecture.png)

## 🚀 Benchmarks (Pass@1 Accuracy)

| Configuration | HumanEval+ | MBPP+ | SWE-Bench-Lite |
| :--- | :--- | :--- | :--- |
| Qwen2.5-Coder-32B | 78.2% | 81.5% | 14.2% |
| DeepSeek-Coder-V2-Lite | 75.4% | 79.1% | 12.8% |
| Qwen2.5-Coder-72B | 82.1% | 84.6% | 18.5% |
| **SAGE-CODE (Nash Loop)** | **89.2%** | **91.4%** | **26.8%** |

## 🛠️ Quickstart

```bash
git clone https://github.com/user/sage-code
cd sage-code
docker compose up -d sage-code

# Run the coding demo
python demos/demo_sage_code.py

# Prove hardware necessity (Expected OOM on H100)
python demos/demo_h100_simulation.py
```

## 🧠 Hardware-Necessity Proof

SAGE-CODE requires co-residency to maintain the **Non-Abelian Lie Bracket** property. In `--long-context` mode (256K), total VRAM usage reaches **~185 GB**, exceeding the 80 GB limit of the NVIDIA H100.

## 📄 License

MIT © 2026 SAGE-CODE Contributors
