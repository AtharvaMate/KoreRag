<div align="center">

# 🧠 Nexus RAG

### Enterprise-Grade Multi-Tenant Retrieval-Augmented Generation Platform

A production-ready API for document ingestion, hybrid semantic search, and context-aware LLM chat — with complete data isolation, agentic query routing, and intelligent caching.

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-FE005D?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-4B0082?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-key-features) •
[Architecture](#-system-architecture) •
[Tech Stack](#%EF%B8%8F-tech-stack) •
[Getting Started](#-getting-started) •
[API Reference](#-api-endpoints) •
[Evaluation](#-evaluation) •
[Contributing](#-contributing)

</div>

---

## 📖 Overview

**Nexus RAG** is a production-oriented Retrieval-Augmented Generation platform built for **multi-tenant SaaS** environments. It goes beyond basic RAG by combining:

- 🔬 **Hypothetical Document Embeddings (HyDE)** for superior query understanding
- 🔀 **Hybrid retrieval** fusing dense vectors with BM25 sparse search
- 🎯 **Cross-encoder reranking** for precision context selection
- 🤖 **LangGraph agentic routing** to dynamically switch between RAG and live web search
- ⚡ **Content-addressed Redis caching** with tenant-level invalidation
- 🔐 **Complete tenant isolation** across every data path

Every tenant's documents, embeddings, chat history, and cache entries are fully segregated — guaranteeing zero data leakage in shared infrastructure.

---

## ⚡ System Architecture

<div align="center">
  <img src="./assets/architecture.svg" alt="Nexus RAG System Architecture" width="850" />
</div>

<br/>

### 🔬 Query Lifecycle — End-to-End Flow

The diagram below traces a single query through the system: from cache lookup, through the LangGraph agent's routing decision, hybrid retrieval with HyDE, cross-encoder reranking, and finally LLM generation with source citations.

<div align="center">
  <img src="./assets/query-lifecycle.svg" alt="Query Lifecycle — End-to-End RAG Flow" width="750" />
</div>

<details>
<summary><b>📋 Detailed Pipeline Walkthrough</b></summary>
<br>

| Stage | Component | Description |
|:---:|---|---|
| **1** | **Cache Check** | Incoming query is SHA-256 hashed with the tenant context. On a cache hit, the response is returned in <1ms. |
| **2** | **LangGraph Router** | A `StateGraph` evaluates the user-selected mode and conditionally routes to either the RAG pipeline or Tavily web search. |
| **3a** | **HyDE Retrieval** | The LLM generates a hypothetical answer passage, which is embedded and used for dense similarity search — dramatically improving recall for short or ambiguous queries. |
| **3b** | **Tavily Search** | For `online` mode, the query is sent to Tavily for real-time web results with source URLs. |
| **4** | **Ensemble Fusion** | Dense results (HyDE, weight 0.6) are fused with sparse BM25 results (weight 0.4) via `EnsembleRetriever`. |
| **5** | **Cross-Encoder Rerank** | `BAAI/bge-reranker-base` re-scores all candidate chunks, keeping only the top 5 most relevant. |
| **6** | **LLM Generation** | Top-ranked context is assembled into a structured prompt and sent to Groq (`gpt-oss-120b`) for a cited, grounded answer. |
| **7** | **Cache Write** | The response is stored in Redis with a configurable TTL for subsequent identical queries. |

</details>

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">

### 🔐 True Multi-Tenancy
Complete data isolation across documents, embeddings, chat history, and cache entries. Users in Tenant A can never access Tenant B's data.

### 🔍 Hybrid Search Engine
Fuses keyword-based BM25 sparse retrieval with dense semantic vectors via `EnsembleRetriever`, with configurable fusion weights.

### 🧠 Hypothetical Document Embeddings
Custom `HyDERetriever` generates a hypothetical answer passage before embedding, producing vectors that sit closer to relevant chunks in embedding space.

  </td>
  <td width="50%">

### 🤖 LangGraph Agentic Routing
`StateGraph`-based agent dynamically routes queries to either the internal RAG pipeline or Tavily web search based on user-selected mode.

### ⚡ Intelligent Redis Caching
Content-addressed SHA-256 cache keys with tenant-scoped invalidation. Graceful degradation when Redis is unavailable.

### 🎯 Cross-Encoder Reranking
`BAAI/bge-reranker-base` re-scores retrieved chunks for precision, surfacing only the most relevant context for the LLM.

  </td>
  </tr>
  <tr>
    <td>

### 🧩 Semantic Chunking Pipeline
Three-stage document processing: Markdown header splitting → semantic chunking → table linearization. No naive character-based splitting.

  </td>
  <td>

### 📊 RAGAS-Evaluated Quality
Retrieval and generation quality continuously measured across faithfulness, answer relevancy, context precision, and context recall.

  </td>
  </tr>
</table>

---

## 🛠️ Tech Stack

| Category | Technologies |
|:---|:---|
| **Framework** | FastAPI, Pydantic, Uvicorn |
| **Databases** | PostgreSQL (`asyncpg`), Qdrant (vector DB), Redis |
| **ORM** | SQLAlchemy 2.0 (`AsyncSession`) |
| **AI / LLM** | LangChain, LangGraph, Groq (`gpt-oss-120b`), HuggingFace |
| **Embeddings** | `BAAI/bge-large-en-v1.5` (1024-dim, normalized) |
| **Reranking** | `BAAI/bge-reranker-base` (cross-encoder) |
| **Retrieval** | HyDE, BM25, EnsembleRetriever, ContextualCompressionRetriever |
| **Web Search** | Tavily (real-time search integration) |
| **Caching** | Redis (SHA-256 content-addressed, TTL-based, tenant-scoped) |
| **Evaluation** | RAGAS (faithfulness, relevancy, precision, recall) |
| **Auth & Security** | JWT (HS256), bcrypt, role-based access control |
| **Infrastructure** | Docker, Docker Compose |

---

## 📁 Project Structure

```
NexusRag/
├── app/
│   ├── main.py              # FastAPI app, lifespan hooks, seeding
│   ├── config.py             # Environment variable loader
│   ├── database.py           # SQLAlchemy models & async engine
│   ├── auth.py               # JWT creation, verification, RBAC
│   ├── rag_engine.py         # HyDE, hybrid retrieval, reranking, indexing
│   ├── agent.py              # LangGraph StateGraph (RAG vs. online routing)
│   ├── cache.py              # Redis cache with tenant invalidation
│   ├── routes/
│   │   ├── auth_routes.py    # /api/auth — register, login, me
│   │   ├── chat_routes.py    # /api/chat — query, history, cache stats
│   │   ├── document_routes.py# /api/documents — upload, list, delete
│   │   └── admin_routes.py   # /api/admin — tenants, KBs, bulk upload
│   └── static/               # Frontend (Web UI + Admin Panel)
├── assets/                   # Architecture & query lifecycle SVGs
├── sample_kb/                # Sample markdown knowledge bases
├── docker-compose.yml        # PostgreSQL + Redis + App
├── Dockerfile                # Production container image
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Project metadata (uv/pip)
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|:---|:---|
| Python | 3.12+ |
| PostgreSQL | 14+ |
| Redis | 7+ |
| Groq API Key | [Get one →](https://console.groq.com) |
| Qdrant Cloud | [Get one →](https://cloud.qdrant.io) |

### Option 1 — Local Development

```bash
# Clone and setup
git clone https://github.com/AtharvaMate/NexusRag.git
cd NexusRag
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see below)

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Option 2 — Docker Compose (Recommended)

```bash
git clone https://github.com/AtharvaMate/NexusRag.git
cd NexusRag
cp .env.example .env
# Edit .env with your Groq + Qdrant credentials

docker-compose up --build
```

> 🚀 The API will be available at `http://localhost:8000`
> 📘 Interactive Swagger docs at `http://localhost:8000/docs`
> 🔧 Admin panel at `http://localhost:8000/admin`

### Environment Variables

```env
# Required
POSTGRES_DB_URL="postgresql+asyncpg://user:password@localhost:5432/rag_db"
QDRANT_URL="https://your-cluster.cloud.qdrant.io"
QDRANT_API_KEY="your-qdrant-api-key"
GROQ_API_KEY="your-groq-api-key"

# Optional
JWT_SECRET_KEY="super-secret-key-change-in-production"
REDIS_URL="redis://localhost:6379/0"
REDIS_CACHE_TTL="3600"
TAVILY_API_KEY="your-tavily-api-key"
```

---

## 📚 API Endpoints

For full interactive documentation, visit `http://localhost:8000/docs` while the server is running.

### 🔐 Authentication — `/api/auth`

| Method | Endpoint | Description |
|:---:|:---|:---|
| `POST` | `/register` | Register a new user under a specific tenant |
| `POST` | `/login` | Authenticate and receive a JWT |
| `GET` | `/me` | Get current user details and tenant context |
| `GET` | `/tenants` | List all available tenants |

### 📄 Documents — `/api/documents`

| Method | Endpoint | Description |
|:---:|:---|:---|
| `POST` | `/upload` | Ingest a `.md` document → chunk → embed → index |
| `GET` | `/` | List all documents for the authenticated user's tenant |
| `DELETE` | `/{doc_id}` | Remove a document and its vectors |

### 💬 Chat — `/api/chat`

| Method | Endpoint | Description |
|:---:|:---|:---|
| `POST` | `/` | Send a query (supports `rag` and `online` modes) |
| `GET` | `/history` | Fetch previous chat logs |
| `GET` | `/cache-stats` | View Redis cache hit/miss statistics |

### 🔧 Admin — `/api/admin`

| Method | Endpoint | Description |
|:---:|:---|:---|
| `GET` | `/tenants` | List all tenants |
| `POST` | `/tenants` | Create a new tenant |
| `DELETE` | `/tenants/{id}` | Delete a tenant (with cascade cleanup) |
| `GET` | `/knowledge-bases` | List knowledge bases (filterable by tenant) |
| `POST` | `/knowledge-bases` | Create a new knowledge base |
| `DELETE` | `/knowledge-bases/{id}` | Delete a knowledge base and its documents |
| `POST` | `/knowledge-bases/{id}/upload` | Upload a single `.md` file to a KB |
| `POST` | `/knowledge-bases/{id}/bulk-upload` | Bulk upload multiple `.md` files |
| `GET` | `/knowledge-bases/{id}/documents` | List documents in a KB |

---

## 📊 Evaluation

Retrieval and generation quality is tracked with [RAGAS](https://github.com/explodinggradients/ragas) across four standardized metrics:

| Metric | What It Measures |
|:---|:---|
| **Faithfulness** | Are generated claims grounded in the retrieved context? |
| **Answer Relevancy** | Does the answer directly address the user's question? |
| **Context Precision** | Are the top-ranked retrieved chunks actually relevant? |
| **Context Recall** | Does the retrieved context cover all parts of the ground truth? |

Results are written to `ragas_eval_results.csv` after each evaluation run.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/AtharvaMate/NexusRag/issues).

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request

