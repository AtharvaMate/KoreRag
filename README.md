<div align="center">

# 🧠 Nexus RAG

### Enterprise-Grade Multi-Tenant Retrieval-Augmented Generation API

An advanced API for document ingestion, semantic search, and context-aware LLM chat — with built-in data isolation for multiple tenants.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-FE005D?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-key-features) •
[Architecture](#-architecture) •
[Tech Stack](#%EF%B8%8F-tech-stack) •
[Getting Started](#-getting-started) •
[API Reference](#-api-endpoints-overview) •
[Contributing](#-contributing)

</div>

---

## 📖 Overview

Nexus RAG is a production-oriented Retrieval-Augmented Generation service built for multi-tenant SaaS use cases. It combines **hybrid search** (dense + sparse retrieval), **cross-encoder reranking**, and **semantic chunking** to deliver precise, source-grounded answers — while keeping every tenant's data fully isolated.

## ⚡ Architecture

The system is designed for scalability and accurate semantic retrieval. It uses a **hybrid search pipeline** combining BM25 (sparse) and dense vector retrieval, followed by a **cross-encoder reranker** for optimal context selection before generation.

<div align="center">
  <img src="./assets/architecture.svg" alt="Nexus RAG Architecture" width="800" />
</div>

### 🔬 Inside a Single Query

The diagram below traces one request end to end: hybrid retrieval fans out to the candidate chunks, the highest-scoring ones survive reranking, and only those feed the LLM.

<div align="center">
  <img src="./assets/query-lifecycle.svg" alt="Nexus RAG Single Query Working" width="700" />
</div>

<details>
<summary><b>How a query flows through the system</b></summary>
<br>

1. **Ingest** — Markdown documents are loaded, split by header structure, then semantically chunked and embedded with `BAAI/bge-large-en-v1.5`.
2. **Index** — Chunks are incrementally indexed into Qdrant via a Postgres-backed record manager (add/update/delete without a full reindex).
3. **Retrieve** — An incoming query is run against an `EnsembleRetriever` that fuses dense (Qdrant) and sparse (BM25) results.
4. **Rerank** — Candidate chunks are re-scored by a `BAAI/bge-reranker-base` cross-encoder to surface the most relevant context.
5. **Generate** — The top-ranked context is assembled into a prompt and sent to Groq (`gpt-oss-120b`) for a cited, grounded answer.

</details>

## ✨ Key Features

| | |
|---|---|
| 🔐 **True Multi-Tenancy** | Complete data isolation — users in `Tenant A` cannot retrieve or chat with documents from `Tenant B`. |
| 🔍 **Hybrid Search Engine** | Fuses keyword-based BM25 sparse retrieval with dense semantic vectors via `EnsembleRetriever`. |
| 🎯 **Advanced Reranking** | Uses `BAAI/bge-reranker-base` cross-encoder to re-rank chunks before sending them to the LLM for highest precision. |
| 🧩 **Intelligent Semantic Chunking** | Replaces naive character-splitting with LLM-aware semantic text splitting for better context boundaries. |
| ⚡ **Asynchronous Core** | Fully async database interactions (`asyncpg`, SQLAlchemy 2.0) with non-blocking endpoint design. |
| 🛡️ **JWT Authentication** | Secure endpoints with role- and tenant-based context injection. |
| 📊 **RAGAS-Evaluated** | Retrieval quality is continuously measured with faithfulness, answer relevancy, context precision, and context recall metrics. |

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Framework** | FastAPI, Pydantic |
| **Databases** | PostgreSQL (`asyncpg`), Qdrant (vector DB) |
| **ORM** | SQLAlchemy 2.0 (`AsyncSession`) |
| **AI / LLM** | LangChain, Groq (`gpt-oss-120b`), HuggingFace |
| **Embeddings** | `BAAI/bge-large-en-v1.5` |
| **Reranking** | `BAAI/bge-reranker-base` |
| **Evaluation** | RAGAS |
| **Security** | JWT, bcrypt |

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.10+**
- **PostgreSQL** running locally or via Docker
- **Qdrant** cluster URL and API key
- **Groq** API key

### 2. Installation

```bash
git clone https://github.com/AtharvaMate/NexusRag.git
cd NexusRag
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Environment Variables

Populate the `.env` file created above:

```env
POSTGRES_DB_URL="postgresql+asyncpg://user:password@localhost:5432/rag_db"
QDRANT_URL="https://your-cluster-url.aws.cloud.qdrant.io"
QDRANT_API_KEY="your-qdrant-api-key"
GROQ_API_KEY="your-groq-api-key"
JWT_SECRET_KEY="super-secret-key-change-in-production"
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

> The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### 5. Run with Docker

```bash
docker-compose up --build
```

---

## 📚 API Endpoints Overview

For full interactive documentation, navigate to `http://localhost:8000/docs` while the server is running.

### 🔐 Authentication — `/api/auth`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Register a new user under a specific tenant. |
| `POST` | `/login` | Authenticate and receive a JWT. |
| `GET` | `/me` | Get current user details. |

### 📄 Documents — `/api/documents`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Ingest a `.md` document, split it, generate embeddings, and index into Qdrant. |
| `GET` | `/` | List all documents belonging to the authenticated user's tenant. |
| `DELETE` | `/{doc_id}` | Remove a document and its vectors. |

### 💬 Chat — `/api/chat`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/` | Send a question. The system retrieves the most relevant chunks from the user's tenant, reranks them, and generates an answer. |
| `GET` | `/history` | Fetch previous chat logs. |

---

## 📊 Evaluation

Retrieval quality is tracked with [RAGAS](https://github.com/explodinggradients/ragas) across four metrics — faithfulness, answer relevancy, context precision, and context recall — against a hand-built evaluation set. Results are written to `ragas_eval_results.csv` after each run.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/AtharvaMate/NexusRag/issues).

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Built with ❤️ for modern GenAI applications.</sub>
</div>
