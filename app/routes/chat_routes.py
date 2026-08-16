import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, ChatMessage, User
from app.auth import get_current_user
from app.rag_engine import query_rag
from app.cache import cache

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    mode: str = "rag"


@router.post("")
async def chat(req: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mode = req.mode if req.mode in ("rag", "online") else "rag"
    result = await query_rag(req.question, user.tenant.slug, mode=mode)

    msg = ChatMessage(
        user_id=user.id,
        tenant_id=user.tenant_id,
        question=req.question,
        answer=result["answer"],
    )
    db.add(msg)
    await db.commit()

    return {
        "answer": result["answer"],
        "cache_hit": result["cache_hit"],
        "response_time_ms": result["response_time_ms"],
        "mode": result["mode"],
    }


@router.get("/history")
async def history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "question": m.question,
            "answer": m.answer,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.get("/cache-stats")
async def cache_stats(user: User = Depends(get_current_user)):
    """Return Redis cache hit/miss statistics for observability."""
    stats = await cache.get_stats()
    return stats
