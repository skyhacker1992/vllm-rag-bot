#!/usr/bin/env python3
"""Benchmark vLLM or SGLang via OpenAI-compatible /v1/chat/completions."""

import argparse
import json
import statistics
import time
import urllib.request

PROMPTS = [
    "Summarize continuous batching in vLLM.",
    "Explain AWQ vs GPTQ vs FP8 quantization tradeoffs.",
    "What is prefix caching for LLM inference?",
    "Describe KServe InferenceService patterns on GKE.",
]


def one_request(base_url: str, model: str, prompt: str) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128,
        "temperature": 0.2,
        "stream": False,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer bench"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read())
    elapsed = time.perf_counter() - t0
    usage = body.get("usage", {})
    completion_tokens = usage.get("completion_tokens", 0)
    return {
        "latency_s": elapsed,
        "completion_tokens": completion_tokens,
        "tok_per_s": completion_tokens / elapsed if elapsed > 0 else 0,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    p.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct-AWQ")
    p.add_argument("--rounds", type=int, default=3)
    args = p.parse_args()

    results = []
    for r in range(args.rounds):
        for prompt in PROMPTS:
            try:
                results.append(one_request(args.base_url, args.model, prompt))
                print(f"ok latency={results[-1]['latency_s']:.2f}s tok/s={results[-1]['tok_per_s']:.1f}")
            except Exception as e:
                print(f"error: {e}")

    if not results:
        print("No successful requests")
        return

    latencies = [x["latency_s"] for x in results]
    tps = [x["tok_per_s"] for x in results if x["tok_per_s"] > 0]
    summary = {
        "requests": len(results),
        "latency_p50": statistics.median(latencies),
        "latency_p95": sorted(latencies)[int(len(latencies) * 0.95) - 1],
        "tok_per_s_avg": statistics.mean(tps) if tps else 0,
    }
    print(json.dumps(summary, indent=2))
    out = f"benchmarks/results/{int(time.time())}.json"
    import os
    os.makedirs("benchmarks/results", exist_ok=True)
    with open(out, "w") as f:
        json.dump({"summary": summary, "samples": results}, f, indent=2)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()