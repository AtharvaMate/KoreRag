import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db, Document, User
from app.auth import get_current_user
from app.rag_engine import process_uploaded_document
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("")
async def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.tenant_id == user.tenant_id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in docs
    ]


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".md"):
        raise HTTPException(400, "Only .md files allowed")

    tenant_dir = os.path.join(UPLOAD_DIR, user.tenant.slug)
    os.makedirs(tenant_dir, exist_ok=True)
    file_path = os.path.join(tenant_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    doc = Document(
        filename=file.filename,
        tenant_id=user.tenant_id,
        uploaded_by=user.id,
        file_path=file_path,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        num_chunks = process_uploaded_document(file_path, user.tenant.slug)
        doc.status = "ready"
        db.commit()
        return {"id": doc.id, "filename": doc.filename, "status": "ready", "chunks": num_chunks}
    except Exception as e:
        doc.status = "error"
        db.commit()
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == user.tenant_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"ok": True}
