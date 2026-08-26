# High-Speed RAG Assistant (LLM Zoomcamp 2026 Project)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![LanceDB](https://img.shields.io/badge/LanceDB-VectorDB-black)](https://lancedb.com)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K8s-326CE5)](https://kubernetes.io/)

An end-to-end, high-speed Retrieval-Augmented Generation (RAG) service optimized for CPU inference. The system indexes document knowledge bases, stores vector embeddings in Yandex Cloud S3 via LanceDB, performs hybrid search, and streams answers using local LLM runtimes (Ollama with Qwen2.5-1.5B).

Built as a capstone project for the **[DataTalks.Club LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp)**.

---

## 📋 Problem Description

Navigating large technical documentations, manuals, and internal knowledge bases can be slow and inefficient. Standard general-purpose LLMs often suffer from hallucinations when answering domain-specific questions or lack access to up-to-date private documents.

**The Solution:**
This project provides an automated, low-latency, end-to-end RAG architecture that:
1. Ingests domain PDF/text documents into a structured vector database.
2. Uses **Hybrid Search** (combining dense vector search with sparse text search) to achieve high recall and precision.
3. Serves low-latency streaming answers (Server-Sent Events / SSE) over a high-performance **FastAPI** backend using local Ollama (`qwen2.5:1.5b`) optimized for CPU runtimes.
4. Leverages **S3 object storage (Yandex Cloud)** as a persistent serverless storage layer for LanceDB vector indexes.

---

## 🏗 System Architecture

```mermaid
flowchart TD
    User["Client / User"]
    API["FastAPI App (app/main.py)"]
    Embedder["FastEmbed (BAAI/bge-small-en-v1.5)"]
    LanceDB[("LanceDB Index on Yandex Cloud S3")]
    Ollama["Ollama Engine (Qwen2.5:1.5b)"]
    K8s["Kubernetes / Docker Stack"]

    User -->|"POST /query /stream"| API
    API -->|"Generate Embedding"| Embedder
    API -->|"Hybrid Search (Vector + Text)"| LanceDB
    LanceDB -->|"Retrieved Context (Top-K)"| API
    API -->|"Concise Prompt + Context"| Ollama
    Ollama -->|"Streaming Response (SSE) / JSON"| API
    API -->|"Streamed Answer"| User

    subgraph Infrastructure
        LanceDB
        Ollama
        K8s
    end


## Tech Stack & Tools

- LLM Runtime: Ollama running qwen2.5:1.5b (local CPU inference, lightweight & fast).
- Embedding Model: BAAI/bge-small-en-v1.5 via fastembed (ONNX-accelerated CPU embeddings).
- Vector Database: LanceDB connected to Yandex Cloud S3 (s3://...).
- Backend / API Framework: FastAPI + httpx (Asynchronous HTTP client) + uvicorn.
- Package & Dependency Management: uv (pyproject.toml).
- Containerization & Deployment: Docker, docker-compose, and Kubernetes (k8s/ manifests).

## Repository Structure

```
.
├── app/
│   └── main.py              # Main FastAPI service (Healthz, /query, /stream endpoints)
├── data/                    # Raw input documents 
├── infra/                   # Infrastructure configuration (Terraform)
├── k8s/                     # Kubernetes deployment manifests (Services, Deployments)
├── scripts/                 # Data ingestion scripts, embedding generators, and evaluation
├── .dockerignore
├── .env                     # Local environment variables
├── Dockerfile               # Production container image build recipe
├── pyproject.toml           # Project dependencies 
└── requirements.txt         # Requirements used in Dockerfile
```

## Evaluation & Metrics

### 1. Retrieval Evaluation

### 2. LLM Output Evaluation (LLM-as-a-Judge)

## Quickstart & Setup Guide

Prerequisites
- OS Linux
- Python 3.12
- Docker, Docker Compose Kubernetes cluster)
- uv for Python environment management

1. Clone the repository:

git clone https://github.com/petr-akimov/llmzoomcamp-2026-petrakimov.git

2. Configure Environment Variables:

Copy env.example to .env and update it

```
LLM_MODEL_NAME=qwen2.5:1.5b
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
TABLE_NAME=pdf_vectors
S3_BUCKET_NAME=your-s3-bucket
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT_URL=[https://storage.yandexcloud.net](https://storage.yandexcloud.net)
AWS_REGION=ru-central1
OLLAMA_URL=http://localhost:11434/api/generate
```

3. 
1. Install Dependencies:

uv sync

2. Run the Ingestion Script:


