"""
Rotas que o robô (ideal_raw_RPA) usa para registrar as execuções e gravar a base Ideal Raw.
Todas exigem o cabeçalho X-RPA-Token.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_rpa_token
from app.db import get_db
from app.repositories import contracts as contracts_repository
from app.repositories import rpa_ingest
from app.schemas import (
    ContractsUpload,
    ContractsUploadResult,
    RpaExecutionCreated,
    RpaExecutionFinish,
    RpaExecutionStart,
    RpaLogsIn,
    RpaStepUpdate,
)

router = APIRouter(prefix="/rpa", tags=["rpa"], dependencies=[Depends(require_rpa_token)])


def _not_found(execution_id: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Execução {execution_id} não encontrada")


def _closed(execution_id: int) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail=f"Execução {execution_id} já foi finalizada")


@router.post("/executions/", response_model=RpaExecutionCreated, status_code=status.HTTP_201_CREATED)
def start_execution(data: RpaExecutionStart, db: Session = Depends(get_db)) -> RpaExecutionCreated:
    """Abre uma execução real (status running) com as etapas que o robô vai percorrer."""
    return RpaExecutionCreated(id=rpa_ingest.start_execution(db, data).id)


@router.patch("/executions/{execution_id}/steps/{key}/")
def update_step(execution_id: int, key: str, data: RpaStepUpdate, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        step = rpa_ingest.update_step(db, execution_id, key, data)
    except rpa_ingest.ExecutionNotFound:
        raise _not_found(execution_id)
    except rpa_ingest.ExecutionClosed:
        raise _closed(execution_id)
    if step is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Etapa '{key}' não existe na execução {execution_id}")
    return {"status": step.status}


@router.post("/executions/{execution_id}/logs/", status_code=status.HTTP_201_CREATED)
def add_logs(execution_id: int, data: RpaLogsIn, db: Session = Depends(get_db)) -> dict[str, int]:
    try:
        return {"received": rpa_ingest.add_logs(db, execution_id, data.logs)}
    except rpa_ingest.ExecutionNotFound:
        raise _not_found(execution_id)
    except rpa_ingest.ExecutionClosed:
        raise _closed(execution_id)


@router.post("/executions/{execution_id}/finish/")
def finish_execution(execution_id: int, data: RpaExecutionFinish, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        execution = rpa_ingest.finish_execution(db, execution_id, data)
    except rpa_ingest.ExecutionNotFound:
        raise _not_found(execution_id)
    except rpa_ingest.ExecutionClosed:
        raise _closed(execution_id)
    return {"status": execution.status}


@router.put("/contracts/", response_model=ContractsUploadResult)
def upload_contracts(data: ContractsUpload, db: Session = Depends(get_db)) -> ContractsUploadResult:
    """Grava a base Ideal Raw consolidada: cria contratos novos e atualiza os existentes."""
    return contracts_repository.upsert_contracts(db, data.contracts, data.execution_id)
