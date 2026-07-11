# NAOFPA LLM Inference Platform

A production-style GenAI platform for enterprise LLM serving, retrieval-augmented generation, observability, and cloud-native deployment.

Built for local validation on RTX 3060 and deployable to GKE + KServe with reusable infrastructure and security patterns.

## Why it matters

- Demonstrates a complete end-to-end GenAI platform stack in one repo.
- Validates 12GB consumer GPU inference with AWQ and modern model routing.
- Shows secure gateway architecture with JWT auth, RAG, metrics, and cloud deploy.
- Provides reusable reference patterns for ML platform engineering teams.

## What this repo includes

- **LLM inference**: vLLM as the primary OpenAI-compatible backend
- **RAG**: Chroma vector store with HuggingFace embeddings
- **Observability**: Prometheus metrics, Grafana dashboards, latency, and error tracking
- **Deployment**: Docker Compose, Helm chart, KServe manifest, Terraform GKE module
- **Security**: JWT auth flow and Vault agent secret injection
- **Benchmarks**: backend comparison and performance testing scripts
- **Production notes**: Triton, TensorRT-LLM, AWQ/FP8 quantization guidance

## Architecture

User → Gateway (:7862) → Inference backend (vLLM / SGLang) + Chroma RAG → Metrics

- Gateway proxies chat requests to vLLM on `:8000`
- RAG uses Chroma on `:8100`
- Prometheus scrapes `/metrics` and exposes dashboards via Grafana

## Quick start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and set `REPORTS_SECRET_KEY`.
3. Make scripts executable:
   ```bash
   chmod +x deploy.sh benchmarks/compare_backends.sh
   ```
4. Start locally:
   ```bash
   ./deploy.sh
   ```
5. Open the gateway UI:
   ```text
   http://127.0.0.1:7862/?token=YOUR_JWT
   ```

> First startup downloads `Qwen/Qwen2.5-3B-Instruct-AWQ` (~2GB), so allow a few minutes.

## Core commands

- Run benchmark comparison:
  ```bash
  ./benchmarks/compare_backends.sh
  ```
- Switch to SGLang backend:
  ```bash
  # set INFERENCE_BACKEND=sglang in .env
  docker compose --profile sglang -p naofpa-vllmproj up -d sglang
  docker compose -p naofpa-vllmproj up -d --force-recreate gateway
  ```

## Kubernetes / GKE deploy

```bash
cd terraform/gke
terraform init
terraform apply -var=project_id=YOUR_GCP_PROJECT
kubectl apply -f k8s/kserve/inferenceservice-vllm.yaml
helm install naofpa helm/naofpa-llm-platform -n naofpa-llm --create-namespace
```

## API endpoints

- `GET /?token=` — chat UI
- `POST /v1/chat?token=` — chat request JSON `{message, use_rag}`
- `POST /v1/ingest?token=` — add text to RAG index
- `GET /health` — status check
- `GET /metrics` — Prometheus metrics

## Ports

- Gateway: `7862`
- vLLM: `8000`
- Chroma: `8100`
- Prometheus: `9090`
- Grafana: `3002`
- SGLang: `30000`

## Impact summary

- Enables rapid prototyping of secure, observable GenAI services on constrained GPU hardware.
- Reduces deployment friction by unifying local compose, Kubernetes, Helm, and Terraform workflows.
- Provides a reusable reference for teams adopting RAG, inference routing, and production observability.
- Helps teams understand performance, quantization, caching, and deployment tradeoffs.

## Notes

- `serving/vllm/README.md` contains tuning and quantization details.
- `k8s/kserve/inferenceservice-vllm.yaml` demonstrates scalable GPU inference with KServe.
- `helm/naofpa-llm-platform/` contains the platform chart for production-style deployment.
