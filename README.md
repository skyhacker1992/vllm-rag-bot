# NAOFPA LLM Inference Platform

Production-style **S.A.R.A.-like** GenAI platform demonstrating LLM serving, RAG, observability, and cloud-native deployment patterns aligned with enterprise ML platform engineering roles.

Built for **Naturally Artificial of Pennsylvania** — runnable locally on **RTX 3060 12GB**, deployable to **GKE + KServe**.

## What this demonstrates

| Job requirement | Implementation in this repo |
|-----------------|----------------------------|
| **vLLM** | Primary inference server (`docker-compose.yml`, AWQ + prefix caching) |
| **SGLang** | Optional profile `docker compose --profile sglang up` |
| **Triton / TensorRT-LLM** | Reference docs + production path notes (`serving/triton`, `serving/tensorrt-llm`) |
| **Quantization AWQ/GPTQ/FP8** | AWQ default; tuning notes in `serving/vllm/README.md` |
| **Tensor parallelism** | `TENSOR_PARALLEL_SIZE` env; KServe manifest uses 2 GPUs |
| **Benchmarking** | `benchmarks/bench_openai.py`, `compare_backends.sh` |
| **RAG / GenAI** | FastAPI gateway + Chroma + HuggingFace embeddings |
| **Kubernetes / KServe** | `k8s/kserve/inferenceservice-vllm.yaml` |
| **Helm** | `helm/naofpa-llm-platform/` |
| **Terraform / GKE** | `terraform/gke/main.tf` (GPU node pool, VPC, workload identity) |
| **Vault secrets** | `k8s/vault/agent-inject.yaml` |
| **Prometheus / Grafana** | `observability/` + `/metrics` on gateway |
| **JWT auth (Reports Hub)** | Same `REPORTS_SECRET_KEY` pattern as S.A.R.A. |

## Architecture

```
User (Reports Hub JWT) → Gateway :7862 → vLLM :8000 (OpenAI API)
                              ↓
                         Chroma RAG :8100
                              ↓
                    Prometheus :9090 → Grafana :3002
```

## Quick start (local, RTX 3060)

```bash
cd ~/workingDIR/naofpa-vllmproj
cp .env.example .env
# Edit .env — set REPORTS_SECRET_KEY to match Reports Hub
chmod +x deploy.sh benchmarks/compare_backends.sh
./deploy.sh
```

First vLLM start downloads `Qwen/Qwen2.5-3B-Instruct-AWQ` (~2GB). Allow several minutes.

Open from Reports Hub with token:
`http://127.0.0.1:7862/?token=YOUR_JWT`

## Benchmark

```bash
./benchmarks/compare_backends.sh
```

## Switch to SGLang backend

```bash
# In .env: INFERENCE_BACKEND=sglang
docker compose --profile sglang -p naofpa-vllmproj up -d sglang
docker compose -p naofpa-vllmproj up -d --force-recreate gateway
```

## Kubernetes / GKE

```bash
# Terraform GPU cluster
cd terraform/gke && terraform init && terraform apply -var=project_id=YOUR_GCP_PROJECT

# KServe InferenceService
kubectl apply -f k8s/kserve/inferenceservice-vllm.yaml

# Helm
helm install naofpa helm/naofpa-llm-platform -n naofpa-llm --create-namespace
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /?token=` | Chat UI |
| `POST /v1/chat?token=` | RAG chat JSON `{message, use_rag}` |
| `POST /v1/ingest?token=` | Add text to RAG index |
| `GET /health` | Backend + model status |
| `GET /metrics` | Prometheus metrics |

## Ports

| Service | Port |
|---------|------|
| Gateway | 7862 |
| vLLM | 8000 |
| SGLang | 30000 |
| Chroma | 8100 |
| Prometheus | 9090 |
| Grafana | 3002 |

## Interview talking points

- **Continuous batching**: vLLM PagedAttention + dynamic batching vs static batching
- **Prefix caching**: RAG system prompts share KV blocks across requests
- **Quantization tradeoffs**: AWQ on 12GB consumer GPU; FP8 on datacenter TensorRT-LLM
- **SRE**: gateway exposes request counters, latency histograms, error rates
- **Multi-cloud**: Terraform GKE module; patterns portable to Azure AKS + GPU SKUs