#!/usr/bin/env bash
set -euo pipefail
MODEL="${LLM_MODEL:-Qwen/Qwen2.5-3B-Instruct-AWQ}"
echo "=== vLLM benchmark ==="
python3 benchmarks/bench_openai.py --base-url http://127.0.0.1:8000/v1 --model "$MODEL"
echo "=== SGLang benchmark (if running) ==="
python3 benchmarks/bench_openai.py --base-url http://127.0.0.1:30000/v1 --model "$MODEL" || echo "SGLang not up"