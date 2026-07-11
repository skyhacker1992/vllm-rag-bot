"""OpenAI-compatible clients for vLLM and SGLang inference servers."""

import time
from typing import AsyncIterator

import httpx

from app.config import INFERENCE_BACKEND, LLM_MODEL, QUANTIZATION, TENSOR_PARALLEL_SIZE, inference_base_url

METRICS = {
    "requests_total": 0,
    "tokens_generated_total": 0,
    "latency_seconds_sum": 0.0,
    "errors_total": 0,
}


async def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 512) -> str:
    base = inference_base_url().rstrip("/")
    url = f"{base}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {"Authorization": "Bearer naofpa-local"}
    t0 = time.perf_counter()
    METRICS["requests_total"] += 1
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            METRICS["tokens_generated_total"] += usage.get("completion_tokens", len(text.split()))
            METRICS["latency_seconds_sum"] += time.perf_counter() - t0
            return text.strip()
    except Exception:
        METRICS["errors_total"] += 1
        METRICS["latency_seconds_sum"] += time.perf_counter() - t0
        raise


async def stream_chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 512) -> AsyncIterator[str]:
    base = inference_base_url().rstrip("/")
    url = f"{base}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    headers = {"Authorization": "Bearer naofpa-local"}
    METRICS["requests_total"] += 1
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:].strip()
                    if chunk == "[DONE]":
                        break
                    import json
                    data = json.loads(chunk)
                    delta = data["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        METRICS["tokens_generated_total"] += 1
                        yield delta
        METRICS["latency_seconds_sum"] += time.perf_counter() - t0
    except Exception:
        METRICS["errors_total"] += 1
        METRICS["latency_seconds_sum"] += time.perf_counter() - t0
        raise


def backend_status() -> dict:
    return {
        "backend": INFERENCE_BACKEND,
        "base_url": inference_base_url(),
        "model": LLM_MODEL,
        "quantization": QUANTIZATION,
        "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
        "metrics": METRICS.copy(),
    }