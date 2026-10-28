from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import contracts as repository
from app.schemas import Contract, ContractSummary, Page
from app.services import contract_export

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


@router.get(
    "/export/",
    response_class=Response,
    responses={200: {"content": {media: {} for media in contract_export.MEDIA_TYPES.values()}}},
)
def export_contracts(
    format: contract_export.ExportFormat = "xlsx",
    search: str | None = Query(None, max_length=100),
    progress_state: str | None = None,
    department: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    """
    Baixa a Base Ideal com a mesma busca e filtros da tela (todos os contratos, sem paginação),
    com as colunas e os valores da planilha. Formatos: csv, xlsx, xls e pdf.
    """
    rows = repository.base_ideal_rows(db, search, progress_state, department)
    now = datetime.now().astimezone()
    filters = " · ".join(
        f"{name} = {value}"
        for name, value in (("busca", search), ("Progress State", progress_state), ("departamento", department))
        if value
    )
    content = contract_export.export(rows, format, now, filters)
    return Response(
        content,
        media_type=contract_export.MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{contract_export.filename(format, now)}"'},
    )
