from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import executions as repository
from app.schemas import Overview

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("/", response_model=Overview)
def get_overview(db: Session = Depends(get_db)) -> Overview:
    """Indicadores dos últimos 7 dias, calculados a partir das execuções no banco."""
    return repository.get_overview(db)
