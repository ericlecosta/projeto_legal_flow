"""
Configuração comum dos testes: SQLite em arquivo temporário, sem seed, sem agenda fictícia
e com um token fixo para as rotas do robô. As variáveis precisam existir antes de importar o app.
"""

import os
import tempfile
from pathlib import Path

_DB_FILE = Path(tempfile.mkdtemp(prefix="lms-api-tests-")) / "test.db"
os.environ.update(
    DATABASE_URL=f"sqlite+pysqlite:///{_DB_FILE}",
    SEED_ON_STARTUP="false",
    SIMULATOR_SCHEDULER_ENABLED="false",
    RPA_MODE="real",
    RPA_API_TOKEN="token-de-teste",  # mesmo valor de tests/constants.py
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def banco_limpo():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def settings():
    """Settings em cache; mudanças feitas pelo teste são desfeitas no final."""
    current = get_settings()
    original = current.model_dump()
    yield current
    for name, value in original.items():
        setattr(current, name, value)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
