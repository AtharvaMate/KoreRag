import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.database import get_db, Tenant, KnowledgeBase, Document, User
from app.auth import get_admin_user
from app.rag_engine import process_uploaded_document
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Pydantic models ──────────────────────────────────────────────

class CreateKBRequest(BaseModel):
    name: str
    tenant_slug: str


class CreateTenantRequest(BaseModel):
    name: str
    slug: str


# ── Tenant management ────────────────────────────────────────────

@router.get("/tenants")
async def list_tenants(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).order_by(Tenant.name))
    tenants = result.scalars().all()
    return [{"id": t.id, "name": t.name, "slug": t.slug, "created_at": t.created_at.isoformat()} for t in tenants]


@router.post("/tenants")
async def create_tenant(
    req: CreateTenantRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    # Check for duplicate slug
    result = await db.execute(select(Tenant).where(Tenant.slug == req.slug))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Tenant slug already exists")

    tenant = Tenant(name=req.name, slug=req.slug)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Cascade-delete all dependent records
    from app.database import ChatMessage
    for model in [ChatMessage, Document, KnowledgeBase, User]:
        rows = await db.execute(select(model).where(model.tenant_id == tenant_id))
        for row in rows.scalars().all():
            await db.delete(row)

    await db.delete(tenant)
    await db.commit()
    return {"ok": True}


# ── Knowledge Base management ────────────────────────────────────

@router.get("/knowledge-bases")
async def list_knowledge_bases(
    tenant_slug: str = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeBase).options(selectinload(KnowledgeBase.tenant))
    if tenant_slug:
        query = query.join(Tenant).where(Tenant.slug == tenant_slug)
    query = query.order_by(KnowledgeBase.created_at.desc())
    result = await db.execute(query)
    kbs = result.scalars().all()

    items = []
    for kb in kbs:
        # Get actual document count
        doc_count_result = await db.execute(
            select(func.count(Document.id)).where(Document.kb_id == kb.id)
        )
        doc_count = doc_count_result.scalar() or 0
        items.append({
            "id": kb.id,
            "name": kb.name,
            "tenant_slug": kb.tenant.slug,
            "tenant_name": kb.tenant.name,
            "document_count": doc_count,
            "created_at": kb.created_at.isoformat(),
        })
    return items


@router.post("/knowledge-bases")
async def create_knowledge_base(
    req: CreateKBRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    # Find tenant
    result = await db.execute(select(Tenant).where(Tenant.slug == req.tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(400, "Invalid tenant slug")

    # Check unique name per tenant
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.name == req.name,
            KnowledgeBase.tenant_id == tenant.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Knowledge base with this name already exists for this tenant")

    kb = KnowledgeBase(name=req.name, tenant_id=tenant.id)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return {"id": kb.id, "name": kb.name, "tenant_slug": req.tenant_slug}


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBase).options(selectinload(KnowledgeBase.tenant)).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(404, "Knowledge base not found")

    # Delete associated documents and files
    doc_result = await db.execute(select(Document).where(Document.kb_id == kb_id))
    docs = doc_result.scalars().all()
    for doc in docs:
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await db.delete(doc)

    await db.delete(kb)
    await db.commit()
    return {"ok": True}


# ── File upload ──────────────────────────────────────────────────

def _validate_md_file(filename: str):
    """Strictly validate that the file has a .md extension."""
    if not filename or not filename.lower().endswith(".md"):
        raise HTTPException(400, f"Only .md files are allowed. Got: '{filename}'")


@router.post("/knowledge-bases/{kb_id}/upload")
async def upload_to_kb(
    kb_id: int,
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a single .md file to a specific knowledge base."""
    _validate_md_file(file.filename)

    # Fetch KB with tenant
    result = await db.execute(
        select(KnowledgeBase).options(selectinload(KnowledgeBase.tenant)).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(404, "Knowledge base not found")

    tenant_slug = kb.tenant.slug
    tenant_dir = os.path.join(UPLOAD_DIR, tenant_slug)
    os.makedirs(tenant_dir, exist_ok=True)
    file_path = os.path.join(tenant_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    doc = Document(
        filename=file.filename,
        tenant_id=kb.tenant_id,
        uploaded_by=admin.id,
        kb_id=kb.id,
        file_path=file_path,
        status="processing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        num_chunks = await process_uploaded_document(file_path, tenant_slug)
        doc.status = "ready"
        await db.commit()
        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": "ready",
            "chunks": num_chunks,
            "kb_id": kb.id,
        }
    except Exception as e:
        doc.status = "error"
        await db.commit()
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.post("/knowledge-bases/{kb_id}/bulk-upload")
async def bulk_upload_to_kb(
    kb_id: int,
    files: List[UploadFile] = File(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple .md files to a specific knowledge base."""
    if not files:
        raise HTTPException(400, "No files provided")

    # Validate all files first before processing any
    for f in files:
        _validate_md_file(f.filename)

    # Fetch KB with tenant
    result = await db.execute(
        select(KnowledgeBase).options(selectinload(KnowledgeBase.tenant)).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(404, "Knowledge base not found")

    tenant_slug = kb.tenant.slug
    tenant_dir = os.path.join(UPLOAD_DIR, tenant_slug)
    os.makedirs(tenant_dir, exist_ok=True)

    results = []
    for file in files:
        file_path = os.path.join(tenant_dir, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        doc = Document(
            filename=file.filename,
            tenant_id=kb.tenant_id,
            uploaded_by=admin.id,
            kb_id=kb.id,
            file_path=file_path,
            status="processing",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        try:
            num_chunks = await process_uploaded_document(file_path, tenant_slug)
            doc.status = "ready"
            await db.commit()
            results.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": "ready",
                "chunks": num_chunks,
            })
        except Exception as e:
            doc.status = "error"
            await db.commit()
            results.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": "error",
                "error": str(e),
            })

    success_count = sum(1 for r in results if r["status"] == "ready")
    return {
        "kb_id": kb.id,
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "files": results,
    }


# ── KB documents listing ─────────────────────────────────────────

@router.get("/knowledge-bases/{kb_id}/documents")
async def list_kb_documents(
    kb_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(404, "Knowledge base not found")

    doc_result = await db.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.uploaded_at.desc())
    )
    docs = doc_result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in docs
    ]
