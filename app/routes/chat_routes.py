from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, ChatMessage, User
from app.auth import get_current_user
from app.rag_engine import query_rag

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("")
async def chat(req: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    answer = query_rag(req.question, user.tenant.slug)
    msg = ChatMessage(
        user_id=user.id,
        tenant_id=user.tenant_id,
        question=req.question,
        answer=answer,
    )
    db.add(msg)
    db.commit()
    return {"answer": answer}


@router.get("/history")
async def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": m.id,
            "question": m.question,
            "answer": m.answer,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
