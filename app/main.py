import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal, Tenant, User
from sqlalchemy.future import select
from app.rag_engine import init_models
from app.cache import cache
from app.auth import hash_password
from app.routes import auth_routes, chat_routes, document_routes
from app.routes import admin_routes


TENANTS = ["changelog", "compliance", "engineering", "eval", "policies", "pricing", "product", "support"]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


async def seed_tenants():
    async with SessionLocal() as db:
        result = await db.execute(select(Tenant))
        if len(result.scalars().all()) == 0:
            for t in TENANTS:
                db.add(Tenant(name=t.title(), slug=t))
            await db.commit()


async def seed_admin():
    """Create the hardcoded admin user if it doesn't exist."""
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.username == ADMIN_USERNAME))
        if result.scalar_one_or_none() is None:
            # Assign to first tenant
            tenant_result = await db.execute(select(Tenant).limit(1))
            tenant = tenant_result.scalar_one_or_none()
            if tenant:
                admin = User(
                    username=ADMIN_USERNAME,
                    password_hash=hash_password(ADMIN_PASSWORD),
                    tenant_id=tenant.id,
                    is_admin=True,
                )
                db.add(admin)
                await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_tenants()
    await seed_admin()
    await cache.connect()
    init_models()
    yield
    await cache.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(document_routes.router)
app.include_router(admin_routes.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/admin")
def admin_panel():
    return FileResponse(os.path.join(static_dir, "admin.html"))
