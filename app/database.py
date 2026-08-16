import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from app.config import POSTGRES_DB_URL

engine = create_async_engine(POSTGRES_DB_URL)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant")
    documents = relationship("Document", back_populates="knowledge_base")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True)
    file_path = Column(String(500))
    status = Column(String(50), default="processing")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant")
    user = relationship("User")
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    question = Column(Text)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await conn.execute(text(
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS kb_id INTEGER REFERENCES knowledge_bases(id)"
        ))


async def get_db():
    async with SessionLocal() as db:
        yield db
