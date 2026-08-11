from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username taken")
    tenant = db.query(Tenant).filter(Tenant.slug == req.tenant).first()
    if not tenant:
        raise HTTPException(400, "Invalid tenant")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.username, tenant.slug)
    return {"token": token, "username": user.username, "tenant": tenant.slug}


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    token = create_token(user.id, user.username, tenant.slug)
    return {"token": token, "username": user.username, "tenant": tenant.slug}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "tenant": user.tenant.slug}


@router.get("/tenants")
async def list_tenants(db: Session = Depends(get_db)):
    tenants = db.query(Tenant).all()
    return [{"id": t.id, "name": t.name, "slug": t.slug} for t in tenants]
