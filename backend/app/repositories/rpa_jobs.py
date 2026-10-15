"""
Fila de pedidos de execução do modo real: o painel pede, o worker do robô reivindica e executa.

Só uma execução roda por vez (o robô usa uma única credencial e um único navegador), valha ela
pedida pelo painel ou disparada fora dele (docker compose run --rm rpa).
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Execution, ExecutionLog, RpaJob
from app.repositories import rpa_ingest
from app.schemas import RpaExecutionFinish

WAITING_MESSAGE = "Execução solicitada pelo painel. Aguardando o robô assumir..."


class ExecutionAlreadyRunning(Exception):
    def __init__(self, execution_id: int):
        super().__init__(f"Execução {execution_id} ainda está em andamento")
        self.execution_id = execution_id


def _now() -> datetime:
    return datetime.now().astimezone()


def _fail(db: Session, execution: Execution, title: str, message: str) -> None:
    execution.logs.append(ExecutionLog(timestamp=_now(), level="warning", message=message))
    rpa_ingest.finish_execution(
        db, execution.id, RpaExecutionFinish(status="failed", error_title=title, error_message=message)
    )


def expire_unclaimed(db: Session) -> int:
    """Falha os pedidos que nenhum worker assumiu dentro do prazo (worker parado ou sem acesso à API)."""
    timeout = get_settings().rpa_claim_timeout_seconds
    limit = _now() - timedelta(seconds=timeout)
    stale = db.scalars(
        select(RpaJob)
        .join(Execution)
        .where(RpaJob.claimed_at.is_(None), RpaJob.requested_at < limit, Execution.status == "running")
    ).all()
    for job in stale:
        _fail(
            db,
            job.execution,
            "Robô indisponível",
            f"Nenhum worker do robô assumiu a execução em {timeout} s. "
            "Verifique se o serviço rpa-worker está no ar (docker compose up -d rpa-worker).",
        )
    return len(stale)


def request_run(db: Session) -> int:
    """Abre a execução (status running, sem etapas até o robô assumir) e enfileira o pedido."""
    expire_unclaimed(db)
    running = db.scalar(select(Execution.id).where(Execution.status == "running").limit(1))
    if running is not None:
        raise ExecutionAlreadyRunning(running)

    now = _now()
    execution = Execution(flow="contract_extraction", status="running", trigger="manual", started_at=now)
    execution.logs.append(ExecutionLog(timestamp=now, level="info", message=WAITING_MESSAGE))
    db.add(execution)
    db.flush()
    db.add(RpaJob(execution_id=execution.id, requested_at=now))
    db.commit()
    return execution.id


def claim_next(db: Session) -> int | None:
    """O worker pega o pedido mais antigo ainda não assumido. Devolve o ID da execução ou None."""
    expire_unclaimed(db)
    job = db.scalar(
        select(RpaJob)
        .join(Execution)
        .where(RpaJob.claimed_at.is_(None), Execution.status == "running")
        .order_by(RpaJob.requested_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        return None
    job.claimed_at = _now()
    db.commit()
    return job.execution_id


def request_stop(db: Session, execution_id: int) -> bool:
    """
    Pede a interrupção. Um pedido ainda na fila é cancelado na hora; um em andamento fica marcado
    para o worker encerrar o robô. False se a execução não está em andamento ou não veio do painel.
    """
    job = db.scalar(select(RpaJob).where(RpaJob.execution_id == execution_id))
    if job is None or job.execution.status != "running":
        return False
    if job.claimed_at is None:
        _fail(db, job.execution, "Execução interrompida", "Execução cancelada antes de o robô começar.")
        return True
    job.stop_requested = True
    db.commit()
    return True


def stop_requested(db: Session, execution_id: int) -> bool | None:
    """Se o painel pediu para parar. None se a execução não tem pedido do painel."""
    job = db.scalar(select(RpaJob).where(RpaJob.execution_id == execution_id))
    return None if job is None else job.stop_requested
