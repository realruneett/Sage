#!/bin/bash
set -e

echo "Running full SAGE-CODE benchmark suite..."

python3 sage/benchmarks/humaneval_plus.py
python3 sage/benchmarks/swe_bench_lite.py
python3 sage/benchmarks/livecodebench.py
python3 sage/benchmarks/compare_single_vs_sage.py --quick

echo "Benchmarks complete. See docs/BENCHMARKS.md and docs/figures/benchmark_comparison.png"
