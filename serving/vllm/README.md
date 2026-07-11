# vLLM serving profile

Local RTX 3060 (12GB) settings in `docker-compose.yml`:

| Knob | Value | Why |
|------|-------|-----|
| `--quantization awq` | AWQ 4-bit | Fits 3B model in 12GB VRAM |
| `--enable-prefix-caching` | on | RAG system prompts reuse KV |
| `--tensor-parallel-size 1` | single GPU | 3060 has one device |
| `--gpu-memory-utilization 0.90` | 90% | Headroom for CUDA context |

## FP8 / GPTQ notes

- **FP8**: Best on H100/L40S; on consumer GPUs use AWQ/GPTQ instead.
- **GPTQ**: Swap `--quantization awq` → `gptq` and use a `*-GPTQ` model id.
- **Tensor parallelism**: Set `TENSOR_PARALLEL_SIZE=2` when running 2+ GPUs (GKE node pool).