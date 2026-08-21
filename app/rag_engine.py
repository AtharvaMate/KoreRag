from __future__ import annotations

import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List

from cachetools import TTLCache
from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.indexes import SQLRecordManager, index
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from langchain_qdrant import QdrantVectorStore
from app.config import QDRANT_URL, QDRANT_API_KEY, POSTGRES_SYNC_DB_URL
from app.cache import cache

logger = logging.getLogger(__name__)

embeddings = None
cache_embeddings = None
vector_store = None
llm_model = None
reranker_model = None
all_chunks = []
retriever_cache = TTLCache(maxsize=50, ttl=3600)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise assistant that answers ONLY using the provided context.\n"
     "Rules:\n"
     "1. If the context does not contain the answer, say so explicitly — never guess.\n"
     "2. Every factual claim must be traceable to a numbered source below.\n"
     "3. Cite sources inline like [1], [2] matching the numbering given.\n"
     "4. Be concise. Do not repeat the question.\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])

HYDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an internal knowledge-base author.  Given a question, write a "
     "detailed, factual passage (150-250 words) that directly answers it.  "
     "Write as if this passage already exists in the organization's documentation.  "
     "Do NOT mention the question itself, do NOT use phrases like "
     "'this document explains…'.  Just write the content."),
    ("human", "{question}"),
])


class HyDERetriever(BaseRetriever):
    """Hypothetical Document Embeddings retriever.

    1. Sends the user question to the LLM → gets a hypothetical answer passage.
    2. Embeds that passage (not the question).
    3. Uses the resulting vector for dense similarity search in Qdrant.

    This produces embeddings that sit closer to real relevant chunks in vector
    space, dramatically improving recall for short / ambiguous queries.
    """

    vector_store: QdrantVectorStore
    llm: object
    embeddings: object 
    tenant: str = ""
    k: int = 15

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        hyde_chain = HYDE_PROMPT | self.llm | StrOutputParser()
        hypothetical_doc = hyde_chain.invoke({"question": query})
        logger.info(
            "HyDE generated %d-char hypothetical doc for: %s…",
            len(hypothetical_doc), query[:80],
        )

        hyde_embedding = self.embeddings.embed_query(hypothetical_doc)

        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.tenant",
                    match=MatchAny(any=[self.tenant]),
                )
            ]
        )
        results = self.vector_store.similarity_search_by_vector(
            embedding=hyde_embedding,
            k=self.k,
            filter=qdrant_filter,
        )
        return results


def init_models():
    global embeddings, cache_embeddings, vector_store, llm_model, reranker_model, all_chunks

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        encode_kwargs={"normalize_embeddings": True},
    )

    store = LocalFileStore("./embedding_cache/")
    cache_embeddings = CacheBackedEmbeddings.from_bytes_store(
        embeddings, store, namespace="BAAI/bge-large-en-v1.5"
    )

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="knowledge_base",
        embedding=embeddings,
        vector_name="vectors",
    )

    llm_model = init_chat_model(model="openai/gpt-oss-120b", model_provider="groq")
    reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")

    all_chunks = load_and_process_documents()
    index_documents(all_chunks)


def load_and_process_documents(base_dir="sample_kb/kb"):
    loader = DirectoryLoader(base_dir, glob="**/*.md", loader_cls=TextLoader, recursive=True)
    docs = loader.load()

    for doc in docs:
        path = Path(doc.metadata["source"])
        updated = datetime.fromtimestamp(path.stat().st_mtime)
        parts = path.parts
        tenant = parts[2]
        doc.metadata["updated_at"] = updated.isoformat()
        doc.metadata["tenant"] = tenant

    header_to_split = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    md_splitter = MarkdownHeaderTextSplitter(header_to_split)

    header_chunks = []
    for doc in docs:
        chunks = md_splitter.split_text(doc.page_content)
        for chunk in chunks:
            chunk.metadata.update(doc.metadata)
        header_chunks.extend(chunks)

    semantic_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    semantic_chunks = []
    for chunk in header_chunks:
        split_docs = semantic_splitter.create_documents(
            [chunk.page_content], metadatas=[chunk.metadata]
        )
        total = len(split_docs)
        for i, doc in enumerate(split_docs):
            doc.metadata["chunk_index"] = i
            doc.metadata["total_chunks"] = total
        semantic_chunks.extend(split_docs)

    for chunk in semantic_chunks:
        if "|" in chunk.page_content and "---" in chunk.page_content:
            lines = chunk.page_content.strip().split("\n")
            table_lines = [l for l in lines if l.strip().startswith("|")]
            if len(table_lines) >= 3:
                headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
                rows = []
                for row in table_lines[2:]:
                    cells = [c.strip() for c in row.split("|") if c.strip()]
                    if len(cells) == len(headers):
                        rows.append(". ".join(f"{headers[j]}: {cells[j]}" for j in range(len(headers))) + ".")
                non_table = [l for l in lines if not l.strip().startswith("|")]
                chunk.page_content = "\n".join(rows) + ("\n\n" + "\n".join(non_table) if non_table else "")

    return semantic_chunks


def index_documents(chunks):
    record_manager = SQLRecordManager(
        namespace="qdrant/knowledge_base",
        db_url=POSTGRES_SYNC_DB_URL,
    )
    record_manager.create_schema()
    return index(
        docs_source=chunks,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup="incremental",
        source_id_key="source",
    )


def get_retriever(tenant: str):
    if tenant in retriever_cache:
        return retriever_cache[tenant]

    tenant_chunks = [doc for doc in all_chunks if doc.metadata.get("tenant") == tenant]
    if not tenant_chunks:
        tenant_chunks = all_chunks
    sparse_retriever = BM25Retriever.from_documents(tenant_chunks)
    sparse_retriever.k = 5

    hyde_retriever = HyDERetriever(
        vector_store=vector_store,
        llm=llm_model,
        embeddings=embeddings,
        tenant=tenant,
        k=15,
    )

    hybrid_retriever = EnsembleRetriever(
        retrievers=[hyde_retriever, sparse_retriever],
        weights=[0.6, 0.4],
    )

    compressor = CrossEncoderReranker(model=reranker_model, top_n=5)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=hybrid_retriever
    )

    retriever_cache[tenant] = compression_retriever
    return compression_retriever


def format_docs(docs):
    return "\n\n".join(f"[{i+1}] {d.page_content}" for i, d in enumerate(docs))


async def query_rag(question: str, tenant: str, mode: str = "rag") -> dict:
    from app.agent import agent

    t0 = time.perf_counter()

    cache_key = f"{mode}::{question}"

    cached_answer = await cache.get(cache_key, tenant)
    if cached_answer is not None:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "answer": cached_answer,
            "cache_hit": True,
            "response_time_ms": elapsed,
            "mode": mode,
        }

    result = await agent.ainvoke({
        "question": question,
        "tenant": tenant,
        "mode": mode,
    })
    answer = result["answer"]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    await cache.set(cache_key, tenant, answer)

    return {
        "answer": answer,
        "cache_hit": False,
        "response_time_ms": elapsed,
        "mode": mode,
    }


async def process_uploaded_document(file_path: str, tenant: str):
    loader = TextLoader(file_path)
    docs = loader.load()

    path = Path(file_path)
    for doc in docs:
        doc.metadata["updated_at"] = datetime.now().isoformat()
        doc.metadata["tenant"] = tenant
        doc.metadata["source"] = str(path)

    header_to_split = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    md_splitter = MarkdownHeaderTextSplitter(header_to_split)

    header_chunks = []
    for doc in docs:
        chunks = md_splitter.split_text(doc.page_content)
        for chunk in chunks:
            chunk.metadata.update(doc.metadata)
        header_chunks.extend(chunks)

    semantic_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    new_chunks = []
    for chunk in header_chunks:
        split_docs = semantic_splitter.create_documents(
            [chunk.page_content], metadatas=[chunk.metadata]
        )
        total = len(split_docs)
        for i, doc in enumerate(split_docs):
            doc.metadata["chunk_index"] = i
            doc.metadata["total_chunks"] = total
        new_chunks.extend(split_docs)

    for chunk in new_chunks:
        if "|" in chunk.page_content and "---" in chunk.page_content:
            lines = chunk.page_content.strip().split("\n")
            table_lines = [l for l in lines if l.strip().startswith("|")]
            if len(table_lines) >= 3:
                headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
                rows = []
                for row in table_lines[2:]:
                    cells = [c.strip() for c in row.split("|") if c.strip()]
                    if len(cells) == len(headers):
                        rows.append(". ".join(f"{headers[j]}: {cells[j]}" for j in range(len(headers))) + ".")
                non_table = [l for l in lines if not l.strip().startswith("|")]
                chunk.page_content = "\n".join(rows) + ("\n\n" + "\n".join(non_table) if non_table else "")

    all_chunks.extend(new_chunks)
    index_documents(new_chunks)

    if tenant in retriever_cache:
        del retriever_cache[tenant]


    return len(new_chunks)
