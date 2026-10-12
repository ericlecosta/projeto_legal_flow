from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import executions as repository
from app.schemas import ExecutionDetail, Execution, ExecutionFlow, ExecutionStatus, Page, PeriodFilter, RunRequest
from app.simulator.runner import ExecutionAlreadyRunning, simulation_manager

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/", response_model=Page[Execution])
def list_executions(
    period: PeriodFilter = "7d",
    status: ExecutionStatus | Literal["all"] = "all",
    flow: ExecutionFlow | Literal["all"] = "all",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[Execution]:
    """Histórico de execuções com filtros e paginação (formato `{count, results}`)."""
    return repository.list_executions(db, period, status, flow, page, page_size)


@router.post("/", response_model=ExecutionDetail, status_code=status.HTTP_201_CREATED)
def run_execution(request: RunRequest, db: Session = Depends(get_db)) -> ExecutionDetail:
    """Dispara uma execução manual (hoje, simulada). Responde 409 se já houver uma em andamento."""
    try:
        execution_id = simulation_manager.start(request.flow, "manual")
    except ExecutionAlreadyRunning as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return repository.get_execution(db, execution_id)


@router.get("/{execution_id}/", response_model=ExecutionDetail)
def get_execution(execution_id: int, db: Session = Depends(get_db)) -> ExecutionDetail:
    """Detalhe de uma execução, com etapas, logs e erro."""
    detail = repository.get_execution(db, execution_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Execução {execution_id} não encontrada")
    return detail


@router.post("/{execution_id}/stop/", status_code=status.HTTP_202_ACCEPTED)
def stop_execution(execution_id: int) -> dict[str, str]:
    """Pede a interrupção de uma execução em andamento."""
    if not simulation_manager.stop(execution_id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Execução {execution_id} não está em andamento")
    return {"status": "stopping"}
