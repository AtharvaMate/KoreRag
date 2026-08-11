import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal, Tenant
from sqlalchemy.future import select
from app.rag_engine import init_models
from app.routes import auth_routes, chat_routes, document_routes


TENANTS = ["changelog", "compliance", "engineering", "eval", "policies", "pricing", "product", "support"]


async def seed_tenants():
    async with SessionLocal() as db:
        result = await db.execute(select(Tenant))
        if len(result.scalars().all()) == 0:
            for t in TENANTS:
                db.add(Tenant(name=t.title(), slug=t))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_tenants()
    init_models()
    yield


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

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))
