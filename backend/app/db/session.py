"""
Configuração base do SQLAlchemy. Em produção, PostgreSQL; nos testes, SQLite em arquivo temporário.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_database_url = get_settings().database_url
# O SQLite só aceita a conexão na thread que a criou; o TestClient e o simulador usam outras threads.
_connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}
engine = create_engine(_database_url, pool_pre_ping=True, connect_args=_connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e a fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
