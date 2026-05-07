#!/bin/bash
set -e

echo "Downloading specialist models for SAGE-CODE..."

models=(
  "Qwen/Qwen2.5-Coder-32B-Instruct"
  "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
  "Qwen/Qwen2.5-Coder-72B-Instruct"
  "BAAI/bge-large-en-v1.5"
)

mkdir -p models

for model in "${models[@]}"; do
  echo "Downloading $model..."
  huggingface-cli download "$model" --local-dir "models/$(basename $model)"
done
