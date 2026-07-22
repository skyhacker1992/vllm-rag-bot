import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.auth import get_username_from_token
from app.backends import backend_status, chat_completion, stream_chat
from app.config import INFERENCE_BACKEND, LLM_MODEL, QUANTIZATION
from app.rag import initialize_rag, ingest_text, retrieve_context

# Prometheus metrics (SRE / observability)
REQ_COUNTER = Counter("naofpa_gateway_requests_total", "Gateway requests", ["endpoint", "backend"])
LATENCY = Histogram("naofpa_gateway_latency_seconds", "Gateway latency", ["endpoint"])
BACKEND_GAUGE = Gauge("naofpa_inference_backend_up", "Backend selected", ["backend"])

app = FastAPI(title="NAOFPA LLM Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True


class IngestRequest(BaseModel):
    text: str
    source: str = "api"


@app.on_event("startup")
async def startup():
    initialize_rag()
    BACKEND_GAUGE.labels(backend=INFERENCE_BACKEND).set(1)


def _require_user(request: Request) -> str:
    # Temporary bypass for dev / testing
    if os.getenv("DISABLE_AUTH", "false").lower() in ("true", "1", "yes"):
        return "dev-user"

    token = request.query_params.get("token") or request.headers.get("X-Auth-Token", "")
    user = get_username_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user


@app.get("/")
async def ui(request: Request):
    _require_user(request)
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "backend": backend_status(),
        "model": LLM_MODEL,
        "quantization": QUANTIZATION,
    }


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/chat")
async def chat(body: ChatRequest, request: Request):
    user = _require_user(request)
    REQ_COUNTER.labels(endpoint="chat", backend=INFERENCE_BACKEND).inc()
    with LATENCY.labels(endpoint="chat").time():
        context = retrieve_context(body.message) if body.use_rag else ""
        system = (
            "You are S.A.R.A, a helpful AI assistant for Naturally Artificial of Pennsylvania. "
            "Answer clearly and concisely. Use provided context when relevant."
        )
        if context:
            system += f"\n\nContext:\n{context}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": body.message},
        ]
        reply = await chat_completion(messages)
    return {"user": user, "reply": reply, "rag_used": bool(context)}


@app.post("/v1/chat/stream")
async def chat_stream(body: ChatRequest, request: Request):
    _require_user(request)
    REQ_COUNTER.labels(endpoint="chat_stream", backend=INFERENCE_BACKEND).inc()
    context = retrieve_context(body.message) if body.use_rag else ""
    system = "You are S.A.R.A, a helpful AI assistant."
    if context:
        system += f"\n\nContext:\n{context}"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": body.message}]

    async def gen():
        async for chunk in stream_chat(messages):
            yield chunk

    return StreamingResponse(gen(), media_type="text/plain")


@app.post("/v1/ingest")
async def ingest(body: IngestRequest, request: Request):
    _require_user(request)
    count = ingest_text(body.text, body.source)
    return {"chunks_indexed": count}
