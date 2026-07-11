# NAOFPA LLM Platform

Naturally Artificial of Pennsylvania operates GPU-backed LLM inference for internal RAG assistants.

## Serving stack
- vLLM with AWQ quantization and prefix caching
- Optional SGLang backend for comparison benchmarks
- Triton and TensorRT-LLM reference configs for production GKE paths

## Operations
- Prometheus metrics on gateway :7862/metrics
- Grafana dashboards on :3000
- KServe InferenceService manifests for GKE deployment
- Terraform modules for GPU node pools and landing-zone networking