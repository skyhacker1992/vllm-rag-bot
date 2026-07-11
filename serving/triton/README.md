# NVIDIA Triton Inference Server

Reference layout for embedding + LLM ensemble on GKE:

```
model_repository/
  embedding/          # ONNX or TensorRT embedding model
  llm_gateway/        # Business logic ensemble (preprocess → vLLM sidecar → postprocess)
```

Production pattern: Triton fronts embedding batching; vLLM handles generation via KServe multi-model inference graph.

See `k8s/kserve/inferenceservice-vllm.yaml` for the KServe-native vLLM path used in this repo's primary deployment.