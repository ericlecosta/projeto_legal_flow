from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import contracts as repository
from app.schemas import Contract, ContractSummary, Page

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/", response_model=Page[Contract])
def list_contracts(
    search: str | None = Query(None, max_length=100),
    progress_state: str | None = None,
    department: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[Contract]:
    """Contratos da base Ideal Raw, com busca por número, contraparte, nome ou revisor."""
    return repository.list_contracts(db, search, progress_state, department, page, page_size)


@router.get("/summary/", response_model=ContractSummary)
def get_summary(db: Session = Depends(get_db)) -> ContractSummary:
    """Total de contratos por status do LMS e quando a base foi atualizada pela última vez."""
    return repository.get_summary(db)
