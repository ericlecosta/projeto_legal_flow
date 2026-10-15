"""
Popula o banco com um histórico fictício de execuções do RPA.

Uso (a partir da pasta backend/ ou dentro do contêiner da API):
    python -m app.simulator.seed                 # só popula se o banco estiver vazio
    python -m app.simulator.seed --reset         # apaga tudo e recria
    python -m app.simulator.seed --days 60 --seed 7
"""

import argparse
import logging
import random
from datetime import datetime, time, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Execution, ExecutionLog, ExecutionStep
from app.simulator.plan import RunPlan, build_plan
from app.simulator.schedule import scheduled_slots

logger = logging.getLogger("lms_api.seed")


def materialize(plan: RunPlan, started_at: datetime, trigger: str) -> Execution:
    """Converte um roteiro em uma execução já concluída, com etapas e logs."""
    execution = Execution(flow=plan.flow, status=plan.status, trigger=trigger, started_at=started_at)

    cursor = started_at
    ran = {step.key: step for step in plan.steps}
    for position, (key, label) in enumerate(plan.all_steps):
        step = ran.get(key)
        if step is None:
            execution.steps.append(
                ExecutionStep(position=position, key=key, label=label, status="skipped", duration_seconds=None)
            )
            continue
        execution.steps.append(
            ExecutionStep(
                position=position,
                key=key,
                label=label,
                status="failed" if step.failed else "success",
                duration_seconds=step.duration,
            )
        )
        for log in step.logs:
            execution.logs.append(
                ExecutionLog(timestamp=cursor + timedelta(seconds=log.offset), level=log.level, message=log.message)
            )
        cursor += timedelta(seconds=step.duration)

    execution.finished_at = cursor
    execution.duration_seconds = round((cursor - started_at).total_seconds(), 1)
    execution.records = plan.records
    if plan.error:
        execution.error_title, execution.error_message, _ = plan.error
    return execution


def build_history(days: int, rng: random.Random, failure_rate: float) -> list[Execution]:
    now = datetime.now().astimezone()
    executions: list[Execution] = []

    for days_ago in range(days, -1, -1):
        day = (now - timedelta(days=days_ago)).date()

        starts: list[tuple[datetime, str, str]] = []
        for slot in scheduled_slots(day):
            jitter = timedelta(seconds=rng.randint(0, 25))
            starts.append((slot + jitter, "scheduled", "login_capture"))
        # Execuções manuais esporádicas (testes do time, reprocessamentos)
        if rng.random() < 0.35:
            start = datetime.combine(day, time(rng.randint(9, 17), rng.randint(0, 59))).astimezone()
            flow = "otp_only" if rng.random() < 0.3 else "login_capture"
            starts.append((start, "manual", flow))

        for start, trigger, flow in sorted(starts):
            plan = build_plan(rng, flow=flow, failure_rate=failure_rate)
            total = sum(step.duration for step in plan.steps)
            if start + timedelta(seconds=total) > now:
                continue  # ainda não teria terminado: fica para o agendador/simulador
            executions.append(materialize(plan, start, trigger))

    return executions


def seed(
    session: Session, days: int = 30, random_seed: int = 42, failure_rate: float = 0.12, reset: bool = False
) -> int:
    if reset:
        session.execute(delete(ExecutionLog))
        session.execute(delete(ExecutionStep))
        session.execute(delete(Execution))
    elif session.scalar(select(func.count()).select_from(Execution)):
        logger.info("Banco já possui execuções; seed ignorado (use --reset para recriar).")
        return 0

    executions = build_history(days, random.Random(random_seed), failure_rate)
    session.add_all(executions)
    session.commit()
    logger.info("Seed concluído: %d execuções fictícias nos últimos %d dias.", len(executions), days)
    return len(executions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o banco com execuções fictícias do RPA.")
    parser.add_argument("--days", type=int, default=30, help="dias de histórico (padrão: 30)")
    parser.add_argument("--seed", type=int, default=42, help="semente do gerador aleatório (padrão: 42)")
    parser.add_argument("--failure-rate", type=float, default=0.12, help="taxa de falhas (padrão: 0.12)")
    parser.add_argument("--reset", action="store_true", help="apaga as execuções existentes antes")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed(session, days=args.days, random_seed=args.seed, failure_rate=args.failure_rate, reset=args.reset)


if __name__ == "__main__":
    main()
