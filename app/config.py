import os

SECRET_KEY = os.getenv("REPORTS_SECRET_KEY") or os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").lower()
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
SGLANG_BASE_URL = os.getenv("SGLANG_BASE_URL", "http://127.0.0.1:30000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct-AWQ")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
QUANTIZATION = os.getenv("QUANTIZATION", "awq")
TENSOR_PARALLEL_SIZE = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))

CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8100"))
RAG_DOCS_PATH = os.getenv("RAG_DOCS_PATH", "./data/docs")

def inference_base_url() -> str:
    return SGLANG_BASE_URL if INFERENCE_BACKEND == "sglang" else VLLM_BASE_URL