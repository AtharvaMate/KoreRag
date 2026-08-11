<div align="center">

# 🧠 Nexus RAG
**Enterprise-Grade Multi-Tenant Retrieval-Augmented Generation API**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-FE005D?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)

An advanced API for document ingestion, semantic search, and context-aware LLM chatting with built-in data isolation for multiple tenants. 

</div>

---

## ⚡ Architecture

This project is designed for scalability and accurate semantic retrieval. It uses a **Hybrid Search Pipeline** combining BM25 (sparse) and Dense Vector retrieval, followed by a **Cross-Encoder Reranker** for optimal context fetching.

<div align="center">
  <img src="./assets/architecture.svg" alt="Nexus RAG Architecture" width="800" />
</div>

## ✨ Key Features

- 🔐 **True Multi-Tenancy**: Complete data isolation. Users belonging to `Tenant A` cannot retrieve or chat with documents from `Tenant B`.
- 🔍 **Hybrid Search Engine**: Fuses keyword-based BM25 sparse retrieval with dense semantic vectors via `EnsembleRetriever`.
- 🎯 **Advanced Reranking**: Uses `BAAI/bge-reranker-base` Cross-Encoder to re-rank chunks before sending them to the LLM for highest precision.
- ⚡ **Asynchronous Core**: Fully async database interactions (using `asyncpg` and SQLAlchemy 2.0) and non-blocking endpoint design.
- 🧩 **Intelligent Semantic Chunking**: Replaces naive character-splitting with LLM-aware semantic text splitting for better context boundaries.
- 🛡️ **JWT Authentication**: Secure endpoints with role/tenant-based context injection.

---

## 🛠️ Tech Stack

| Category         | Technologies Used |
|-----------------|-------------------|
| **Framework**   | FastAPI, Pydantic |
| **Databases**   | PostgreSQL (asyncpg), Qdrant (Vector DB) |
| **ORM**         | SQLAlchemy 2.0 (AsyncSession) |
| **AI / LLM**    | LangChain, Groq (`gpt-oss-120b`), HuggingFace |
| **Embeddings**  | `BAAI/bge-large-en-v1.5` |
| **Security**    | JWT, bcrypt |

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have the following installed:
- **Python 3.10+**
- **PostgreSQL** running locally or via Docker
- **Qdrant** cluster URL and API key

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/yourusername/nexus-rag.git
cd nexus-rag
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and populate it:

```env
POSTGRES_DB_URL="postgresql+asyncpg://user:password@localhost:5432/rag_db"
QDRANT_URL="https://your-cluster-url.aws.cloud.qdrant.io"
QDRANT_API_KEY="your-qdrant-api-key"
GROQ_API_KEY="your-groq-api-key"
JWT_SECRET_KEY="super-secret-key-change-in-production"
```

### 4. Run the Server
The application uses Uvicorn to run the ASGI server.

```bash
uvicorn app.main:app --reload --port 8000
```
> The API will be available at `http://localhost:8000`

---

## 📚 API Endpoints Overview

For the full interactive documentation, navigate to `http://localhost:8000/docs` while the server is running.

### 🔐 Authentication (`/api/auth`)
- `POST /register`: Register a new user under a specific tenant.
- `POST /login`: Authenticate and receive a JWT.
- `GET /me`: Get current user details.

### 📄 Documents (`/api/documents`)
- `POST /upload`: Ingest a `.md` document, split it, generate embeddings, and index into Qdrant.
- `GET /`: List all documents belonging to the authenticated user's tenant.
- `DELETE /{doc_id}`: Remove a document and its vectors.

### 💬 Chat (`/api/chat`)
- `POST /`: Send a question. The system retrieves the most relevant chunks from the user's tenant, reranks them, and generates an answer.
- `GET /history`: Fetch previous chat logs.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check [issues page](https://github.com/yourusername/nexus-rag/issues).

<div align="center">
  <sub>Built with ❤️ for modern GenAI applications.</sub>
</div>
