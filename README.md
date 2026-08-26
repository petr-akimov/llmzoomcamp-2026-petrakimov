# High-Speed RAG Assistant (LLM Zoomcamp 2026 Project)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![LanceDB](https://img.shields.io/badge/LanceDB-VectorDB-black)](https://lancedb.com)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Yandex_Cloud-326CE5)](https://kubernetes.io/)

An end-to-end, high-speed Retrieval-Augmented Generation (RAG) service optimized for CPU inference. The system indexes document knowledge bases, stores vector embeddings in Yandex Cloud S3 via LanceDB, performs hybrid search, and streams answers using local LLM runtimes (Ollama with Qwen2.5-1.5B) inside Yandex Managed Service for Kubernetes.

Built as a capstone project for the **[DataTalks.Club LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp)**.

---

## Problem Description

Navigating large technical documentations, manuals, and internal knowledge bases can be slow and inefficient. Standard general-purpose LLMs often suffer from hallucinations when answering domain-specific questions or lack access to up-to-date private documents.

**The Solution:**
This project provides an automated, low-latency, end-to-end RAG architecture deployed in Yandex Cloud that:
1. Ingests domain PDF/text documents into a structured vector database.
2. Uses **Hybrid Search** (combining dense vector search with sparse text search) to achieve high recall and precision.
3. Serves low-latency streaming answers (Server-Sent Events / SSE) over a high-performance **FastAPI** backend using an **Ollama (`qwen2.5:1.5b`)** engine deployed inside Kubernetes.
4. Leverages **Yandex Cloud S3 Object Storage** as a persistent storage layer for LanceDB vector indexes.

---
## System Architecture

```mermaid

flowchart TD
    User["User"]

    subgraph YandexCloud["Yandex Cloud"]
        RAG["RAG / Embedding"]
        Ollama["Ollama / Qwen"]
        S3[("S3 / LanceDB")]
    end

    User -->|"1. Question"| RAG
    RAG -->|"2. Hybrid Search"| S3
    S3 -->|"3. Retrieved Context"| RAG
    RAG -->|"4. Prompt + Context"| Ollama
    Ollama -->|"5. Generated Answer"| RAG
    RAG -->|"6. Answer / Stream"| User

```


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
- terraform

1. Clone the repository:

git clone https://github.com/petr-akimov/llmzoomcamp-2026-petrakimov.git

2. Create infrastructure (k8s managed cluster and s3 bucket)

```
cd infra
terraform init
terraform validate
terraform plan
terraform apply
```

variables.json will be created in infra directory.

3. Configure Environment Variables:

Copy env.example to .env and update it

```
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
TABLE_NAME=pdf_vectors

S3_BUCKET_NAME=akimovp-bucket-...
S3_ACCESS_KEY=YC...
S3_SECRET_KEY=YC...
S3_ENDPOINT_URL=https://storage.yandexcloud.net
AWS_REGION=ru-central1

KSERVE_URL=http://apps.akimovp.ru/v1/completions
LLM_MODEL_NAME=qwen-1-5b
```

Files k8s/secret-rag.yaml, k8s/configmap-rag.yaml should be populated accordingly.

4. Install Dependencies:

uv sync

5. Run the Ingestion Script:

uv run python scripts/ingest.py

6. Build and push the image

docker build -t petrakimovdocker/rag-service:latest .
docker push petrakimovdocker/rag-service:latest

7. Deploy RAG and LLM in k8s cluster:

kubectl apply -f k8s

8. Add monitoring:

docker-compose up -f monitoring.yaml

