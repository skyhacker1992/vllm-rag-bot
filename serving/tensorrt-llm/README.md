# TensorRT-LLM (reference)

TensorRT-LLM is used on NVIDIA datacenter GPUs (L4, L40S, H100) for maximum throughput.

## Build flow (GKE / Azure NC-series)
1. Export HF checkpoint → TensorRT-LLM checkpoint
2. Build engine with FP8/INT4 AWQ weights
3. Serve via Triton `tensorrt_llm` backend or TRT-LLM standalone server
4. Wire KServe `InferenceService` predictor to Triton gRPC port 8001

This repo documents the path; local dev uses vLLM AWQ on RTX 3060 for fast iteration.