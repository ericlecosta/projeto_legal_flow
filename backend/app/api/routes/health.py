from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Usado pelo healthcheck do Docker. A API responde mesmo com o banco fora do ar."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "unavailable"
    return {"status": "ok", "database": database}
