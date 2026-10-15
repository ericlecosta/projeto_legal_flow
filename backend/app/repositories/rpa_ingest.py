"""
Gravação do andamento de uma execução real do robô, recebido pelas rotas /api/rpa/.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Execution, ExecutionLog, ExecutionStep
from app.schemas import LogEntry, RpaExecutionFinish, RpaExecutionStart, RpaStepUpdate


class ExecutionNotFound(Exception):
    pass


class ExecutionClosed(Exception):
    """A execução já foi finalizada e não aceita mais alterações."""


def _now() -> datetime:
    return datetime.now().astimezone()


def _open_execution(db: Session, execution_id: int) -> Execution:
    execution = db.get(Execution, execution_id)
    if execution is None:
        raise ExecutionNotFound(execution_id)
    if execution.status != "running":
        raise ExecutionClosed(execution_id)
    return execution


def start_execution(db: Session, data: RpaExecutionStart) -> Execution:
    execution = Execution(flow=data.flow, status="running", trigger=data.trigger, started_at=_now())
    for position, step in enumerate(data.steps):
        execution.steps.append(ExecutionStep(position=position, key=step.key, label=step.label, status="pending"))
    db.add(execution)
    db.commit()
    return execution


def attach_execution(db: Session, execution_id: int, data: RpaExecutionStart) -> Execution:
    """
    O robô assume uma execução já aberta pelo painel (pedido do worker): grava as etapas que vai
    percorrer e marca o início real, para a duração não contar o tempo na fila.
    """
    execution = _open_execution(db, execution_id)
    execution.flow = data.flow
    execution.started_at = _now()
    execution.steps.clear()
    db.flush()
    for position, step in enumerate(data.steps):
        execution.steps.append(ExecutionStep(position=position, key=step.key, label=step.label, status="pending"))
    db.commit()
    return execution


def update_step(db: Session, execution_id: int, key: str, data: RpaStepUpdate) -> ExecutionStep | None:
    _open_execution(db, execution_id)
    step = db.scalar(select(ExecutionStep).where(ExecutionStep.execution_id == execution_id, ExecutionStep.key == key))
    if step is None:
        return None
    step.status = data.status
    if data.duration_seconds is not None:
        step.duration_seconds = data.duration_seconds
    db.commit()
    return step


def add_logs(db: Session, execution_id: int, logs: list[LogEntry]) -> int:
    execution = _open_execution(db, execution_id)
    for log in logs:
        execution.logs.append(ExecutionLog(timestamp=log.timestamp, level=log.level, message=log.message))
    db.commit()
    return len(logs)


def finish_execution(db: Session, execution_id: int, data: RpaExecutionFinish) -> Execution:
    """Fecha a execução: etapas que não rodaram viram 'skipped' e a duração é calculada pela API."""
    execution = _open_execution(db, execution_id)
    now = _now()
    for step in execution.steps:
        if step.status == "pending":
            step.status = "skipped"
        elif step.status == "running":
            step.status = "failed" if data.status == "failed" else "success"
    execution.status = data.status
    execution.records = data.records
    execution.finished_at = now
    started_at = execution.started_at if execution.started_at.tzinfo else execution.started_at.astimezone()
    execution.duration_seconds = round((now - started_at).total_seconds(), 1)
    execution.error_title = data.error_title
    execution.error_message = data.error_message
    db.commit()
    return execution
