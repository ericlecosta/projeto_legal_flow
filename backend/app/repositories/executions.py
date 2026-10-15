"""
Consultas de execuções no banco e conversão para os schemas da API.
"""

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import Execution, ExecutionStep
from app.schemas import (
    Execution as ExecutionSchema,
    ExecutionDetail,
    ExecutionError,
    ExecutionStep as ExecutionStepSchema,
    LogEntry,
    OperationalStatus,
    Overview,
    Page,
    PeriodFilter,
    StepFailureShare,
    UpcomingRun,
)
from app.simulator.schedule import slot_name, upcoming_slots

PERIOD_LABELS: dict[str, str] = {
    "7d": "Últimos 7 dias",
    "30d": "Últimos 30 dias",
    "all": "Todo o período",
}

STATUS_MESSAGES: dict[OperationalStatus, str] = {
    "green": "O RPA está rodando conforme o esperado.",
    "yellow": "Comportamento atípico: running rate abaixo da meta. Verifique o motivo das falhas.",
    "red": "RPA fora de operação. Intervenção imediata necessária.",
}


def _midnight(days_ago: int) -> datetime:
    now = datetime.now().astimezone()
    return (now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)


def _period_start(period: PeriodFilter) -> datetime | None:
    if period == "all":
        return None
    return _midnight(6 if period == "7d" else 29)


def _to_schema(execution: Execution) -> ExecutionSchema:
    return ExecutionSchema(
        id=execution.id,
        flow=execution.flow,
        status=execution.status,
        trigger=execution.trigger,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        duration_seconds=execution.duration_seconds,
        records=execution.records,
    )


def list_executions(
    db: Session, period: PeriodFilter, status: str, flow: str, page: int, page_size: int
) -> Page[ExecutionSchema]:
    query = select(Execution)
    since = _period_start(period)
    if since is not None:
        query = query.where(Execution.started_at >= since)
    if status != "all":
        query = query.where(Execution.status == status)
    if flow != "all":
        query = query.where(Execution.flow == flow)

    count = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Execution.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return Page[ExecutionSchema](count=count, results=[_to_schema(row) for row in rows])


def get_execution(db: Session, execution_id: int) -> ExecutionDetail | None:
    execution = db.scalar(
        select(Execution)
        .where(Execution.id == execution_id)
        .options(selectinload(Execution.steps), selectinload(Execution.logs))
    )
    if execution is None:
        return None

    error = None
    if execution.error_title:
        error = ExecutionError(
            title=execution.error_title,
            message=execution.error_message or "",
            screenshot_url=execution.error_screenshot_url,
        )
    return ExecutionDetail(
        **_to_schema(execution).model_dump(),
        steps=[
            ExecutionStepSchema(
                key=step.key, label=step.label, status=step.status, duration_seconds=step.duration_seconds
            )
            for step in execution.steps
        ],
        logs=[LogEntry(timestamp=log.timestamp, level=log.level, message=log.message) for log in execution.logs],
        error=error,
    )


def get_overview(db: Session) -> Overview:
    target = get_settings().running_rate_target
    since = _period_start("7d")
    finished = db.scalars(
        select(Execution).where(Execution.started_at >= since, Execution.status != "running")
    ).all()

    failed = [e for e in finished if e.status == "failed"]
    succeeded = len(finished) - len(failed)
    running_rate = succeeded / len(finished) * 100 if finished else 0.0

    failed_labels = Counter(
        db.scalars(
            select(ExecutionStep.label)
            .join(Execution)
            .where(Execution.started_at >= since, Execution.status == "failed", ExecutionStep.status == "failed")
        ).all()
    )
    total_failures = sum(failed_labels.values())

    trend = []
    for days_ago in range(6, -1, -1):
        day = _midnight(days_ago).date()
        trend.append(sum(e.records or 0 for e in finished if e.started_at.astimezone().date() == day))

    if not finished:
        status: OperationalStatus = "yellow"
    elif running_rate >= target:
        status = "green"
    elif running_rate >= 70:
        status = "yellow"
    else:
        status = "red"

    return Overview(
        operational_status=status,
        status_message=STATUS_MESSAGES[status] if finished else "Nenhuma execução concluída nos últimos 7 dias.",
        updated_at=datetime.now().astimezone(),
        period_label=PERIOD_LABELS["7d"],
        running_rate=round(running_rate, 1),
        running_rate_target=target,
        total_executions=len(finished),
        succeeded=succeeded,
        failed=len(failed),
        avg_duration_seconds=round(sum(e.duration_seconds or 0 for e in finished) / max(1, len(finished))),
        captured_records=sum(e.records or 0 for e in finished),
        captured_trend=trend,
        failures_by_step=[
            StepFailureShare(label=label, percent=round(count / total_failures * 100))
            for label, count in failed_labels.most_common()
        ],
        upcoming_runs=[
            UpcomingRun(name=slot_name(slot), scheduled_at=slot, source="cron")
            for slot in upcoming_slots(datetime.now().astimezone())
        ],
    )
