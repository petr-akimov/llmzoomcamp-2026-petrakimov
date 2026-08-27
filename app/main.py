import json
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastembed import TextEmbedding
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
import httpx
import lancedb
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

load_dotenv()

LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "qwen2.5:1.5b")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
TABLE_NAME: str = os.getenv("TABLE_NAME", "pdf_vectors")

S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "https://storage.yandexcloud.net")
AWS_REGION: str = os.getenv("AWS_REGION", "ru-central1")

OLLAMA_URL: str = os.getenv(
    "OLLAMA_URL",
    "http://ollama-qwen-service.default.svc.cluster.local:11434/api/generate",
)

state: dict[str, Any] = {}


def generate_embedding(embedder: TextEmbedding, text: str) -> list[float]:
    embeddings_gen = embedder.embed([text])
    return next(embeddings_gen).tolist()


def build_prompt(context_str: str, question: str) -> str:
    return (
        "Answer the question directly and concisely based ONLY on the following context.\n"
        "Do not generalize or guess. If context lacks information, state so.\n\n"
        f"Context:\n{context_str}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["embedder"] = TextEmbedding(model_name=EMBEDDING_MODEL)

    s3_uri = f"s3://{S3_BUCKET_NAME}/lancedb"
    storage_options = {
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_KEY,
        "aws_region": AWS_REGION,
        "aws_endpoint": S3_ENDPOINT_URL,
        "allow_http": "true" if S3_ENDPOINT_URL.startswith("http://") else "false",
    }

    state["db"] = lancedb.connect(s3_uri, storage_options=storage_options)
    state["table"] = state["db"].open_table(TABLE_NAME)
    state["http_client"] = httpx.AsyncClient(timeout=60.0)

    yield

    await state["http_client"].aclose()


app = FastAPI(
    title="High-Speed RAG Service (Ollama Engine)",
    description="CPU Based RAG-service",
    version="2.1.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    question: str = Field(..., description="User question")
    k: int = Field(default=3, ge=1, le=10, description="Number of context chunks (default 3)")


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]


@app.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz():
    return {"status": "ok"}


async def fetch_context(embedder: TextEmbedding, table, question: str, k: int):
    query_vector = await run_in_threadpool(generate_embedding, embedder, question)

    try:
        search_results = (
            table.search(query_vector, query_type="hybrid")
            .text(question)
            .select(["text", "metadata"])
            .limit(k)
            .to_list()
        )
    except Exception:
        search_results = table.search(query_vector).select(["text", "metadata"]).limit(k).to_list()

    if not search_results:
        return "", []

    context_blocks = []
    sources = []
    for item in search_results:
        text = item.get("text", "").strip()
        metadata = item.get("metadata", "")
        if text:
            context_blocks.append(text)
        if metadata and metadata not in sources:
            sources.append(metadata)

    return "\n\n---\n\n".join(context_blocks), sources


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    embedder: TextEmbedding = state["embedder"]
    table = state["table"]
    http_client: httpx.AsyncClient = state["http_client"]

    context_str, sources = await fetch_context(embedder, table, request.question, request.k)

    if not context_str:
        return QueryResponse(
            question=request.question,
            answer="No passing info in the knowledge base.",
            sources=[],
        )

    prompt = build_prompt(context_str, request.question)

    payload = {
        "model": LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 120,  
            "num_thread": 4,    
        },
    }

    try:
        response = await http_client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        llm_data = response.json()
        answer = llm_data.get("response", "").strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama Error: {str(e)}",
        )

    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=sources,
    )


@app.post("/api/v1/query/stream")
async def query_rag_stream(request: QueryRequest):
    embedder: TextEmbedding = state["embedder"]
    table = state["table"]
    http_client: httpx.AsyncClient = state["http_client"]

    context_str, sources = await fetch_context(embedder, table, request.question, request.k)

    if not context_str:
        async def empty_gen():
            yield "No passing info in the knowledge base."
        return StreamingResponse(empty_gen(), media_type="text/plain")

    prompt = build_prompt(context_str, request.question)

    payload = {
        "model": LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.0,
            "num_predict": 120,
            "num_thread": 4,
        },
    }

    async def stream_generator():
        try:
            async with http_client.stream("POST", OLLAMA_URL, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        text_chunk = chunk.get("response", "")
                        if text_chunk:
                            yield text_chunk
        except Exception as e:
            yield f"\n[Generation error: {str(e)}]"

    return StreamingResponse(stream_generator(), media_type="text/plain")