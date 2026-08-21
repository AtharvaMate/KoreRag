from __future__ import annotations

import logging
from typing import TypedDict, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    question: str
    tenant: str
    mode: str
    context: str
    sources: list
    answer: str


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

ONLINE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant that answers using web search results.\n"
     "Rules:\n"
     "1. Use ONLY the search results provided below to answer.\n"
     "2. Cite sources inline like [1], [2] matching the numbering given.\n"
     "3. If the results don't contain relevant info, say so explicitly.\n"
     "4. Be concise and accurate.\n\n"
     "Search Results:\n{context}"),
    ("human", "{question}"),
])


def retrieve_rag(state: AgentState) -> dict:
    from app.rag_engine import get_retriever, format_docs

    question = state["question"]
    tenant = state["tenant"]

    retriever = get_retriever(tenant)
    docs = retriever.invoke(question)
    context = format_docs(docs)

    sources = [
        {
            "type": "rag",
            "source": doc.metadata.get("source", ""),
            "tenant": doc.metadata.get("tenant", ""),
        }
        for doc in docs
    ]
    return {"context": context, "sources": sources}


def retrieve_online(state: AgentState) -> dict:
    question = state["question"]

    tavily = TavilySearch(max_results=5, topic="general")
    results = tavily.invoke(question)

    if isinstance(results, list):
        context_parts = []
        sources = []
        for i, r in enumerate(results):
            title = r.get("title", "Web Result")
            url = r.get("url", "")
            content = r.get("content", str(r))
            context_parts.append(f"[{i+1}] {title}\n{content}\nSource: {url}")
            sources.append({"type": "online", "title": title, "url": url})
        context = "\n\n".join(context_parts)
    else:
        context = f"[1] {results}"
        sources = [{"type": "online", "title": "Web Search", "url": ""}]
    return {"context": context, "sources": sources}


async def generate(state: AgentState) -> dict:
    from app.rag_engine import llm_model

    mode = state["mode"]
    prompt = ONLINE_PROMPT if mode == "online" else RAG_PROMPT

    prompt_value = prompt.invoke({
        "context": state["context"],
        "question": state["question"],
    })
    response = await llm_model.ainvoke(prompt_value)

    logger.info("Generated %d-char answer [mode=%s]", len(response.content), mode)
    return {"answer": response.content}


def route_query(state: AgentState) -> Literal["retrieve_rag", "retrieve_online"]:
    mode = state.get("mode", "rag")
    if mode == "online":
        return "retrieve_online"
    return "retrieve_rag"


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_rag", retrieve_rag)
    graph.add_node("retrieve_online", retrieve_online)
    graph.add_node("generate", generate)

    graph.add_conditional_edges(
        START,
        route_query,
        {
            "retrieve_rag": "retrieve_rag",
            "retrieve_online": "retrieve_online",
        },
    )

    graph.add_edge("retrieve_rag", "generate")
    graph.add_edge("retrieve_online", "generate")

    graph.add_edge("generate", END)

    return graph.compile()


agent = build_agent_graph()
