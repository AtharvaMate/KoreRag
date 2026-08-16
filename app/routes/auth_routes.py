from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.database import get_db, User, Tenant
from app.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    tenant: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Username taken")

    result = await db.execute(select(Tenant).where(Tenant.slug == req.tenant))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(400, "Invalid tenant")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        tenant_id=tenant.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_token(user.id, user.username, tenant.slug, user.is_admin)
    return {"token": token, "username": user.username, "tenant": tenant.slug, "is_admin": user.is_admin}


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(selectinload(User.tenant)).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(user.id, user.username, user.tenant.slug, user.is_admin)
    return {"token": token, "username": user.username, "tenant": user.tenant.slug, "is_admin": user.is_admin}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "tenant": user.tenant.slug, "is_admin": user.is_admin}


@router.get("/tenants")
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant))
    tenants = result.scalars().all()
    return [{"id": t.id, "name": t.name, "slug": t.slug} for t in tenants]
