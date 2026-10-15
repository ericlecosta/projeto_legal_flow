"""
Ponto de entrada da API do LMS RPA Monitor.

Execução local:  uvicorn app.main:app --reload   (a partir da pasta backend/)
Documentação:    http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401  (registra os modelos no Base.metadata)
from app.api.routes import executions, health, overview
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.simulator.runner import recover_orphans, scheduled_runner
from app.simulator.seed import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("lms_api")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Enquanto não houver migrações (Alembic), cria as tabelas na subida.
    # Se o banco estiver fora do ar, a API sobe mesmo assim e só o /api/health/ responde normalmente.
    try:
        Base.metadata.create_all(bind=engine)
        orphans = recover_orphans()
        if orphans:
            logger.warning("%d execução(ões) em andamento marcadas como interrompidas.", orphans)
        if settings.seed_on_startup:
            with SessionLocal() as db:
                seed(db, days=settings.seed_days, failure_rate=settings.simulator_failure_rate)
    except SQLAlchemyError as exc:
        logger.warning("Banco de dados indisponível, tabelas não criadas: %s", exc)

    if settings.simulator_scheduler_enabled:
        scheduled_runner.start()
    yield
    scheduled_runner.shutdown()


app = FastAPI(
    title=settings.project_name,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health.router)
api_router.include_router(overview.router)
api_router.include_router(executions.router)
app.include_router(api_router)
