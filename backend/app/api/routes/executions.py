from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.repositories import executions as repository
from app.repositories import rpa_jobs
from app.schemas import ExecutionDetail, Execution, ExecutionFlow, ExecutionStatus, Page, PeriodFilter, RunRequest
from app.simulator.runner import ExecutionAlreadyRunning, simulation_manager

router = APIRouter(prefix="/executions", tags=["executions"])


def _expire_unclaimed(db: Session) -> None:
    """No modo real, pedidos que o worker não assumiu a tempo viram falha antes de qualquer leitura."""
    if not get_settings().simulated:
        rpa_jobs.expire_unclaimed(db)


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
    _expire_unclaimed(db)
    return repository.list_executions(db, period, status, flow, page, page_size)


@router.post("/", response_model=ExecutionDetail, status_code=status.HTTP_201_CREATED)
def run_execution(request: RunRequest, db: Session = Depends(get_db)) -> ExecutionDetail:
    """
    Dispara uma execução manual. No modo simulado roda o simulador; no modo real enfileira o pedido
    para o worker do robô (o fluxo é sempre o de extração de contratos). 409 se já houver uma em andamento.
    """
    settings = get_settings()
    try:
        if settings.simulated:
            execution_id = simulation_manager.start(request.flow, "manual")
        else:
            if not settings.rpa_api_token:
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Integração com o robô desativada: defina RPA_API_TOKEN na API e no robô.",
                )
            execution_id = rpa_jobs.request_run(db)
    except (ExecutionAlreadyRunning, rpa_jobs.ExecutionAlreadyRunning) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return repository.get_execution(db, execution_id)


@router.get("/{execution_id}/", response_model=ExecutionDetail)
def get_execution(execution_id: int, db: Session = Depends(get_db)) -> ExecutionDetail:
    """Detalhe de uma execução, com etapas, logs e erro."""
    _expire_unclaimed(db)
    detail = repository.get_execution(db, execution_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Execução {execution_id} não encontrada")
    return detail


@router.post("/{execution_id}/stop/", status_code=status.HTTP_202_ACCEPTED)
def stop_execution(execution_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Pede a interrupção de uma execução em andamento. No modo real só vale para execuções pedidas
    pelo painel: o worker encerra o robô e a execução fecha como falha.
    """
    if get_settings().simulated:
        stopped = simulation_manager.stop(execution_id)
    else:
        stopped = rpa_jobs.request_stop(db, execution_id)
    if not stopped:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Execução {execution_id} não está em andamento ou não foi iniciada pelo painel",
        )
    return {"status": "stopping"}
