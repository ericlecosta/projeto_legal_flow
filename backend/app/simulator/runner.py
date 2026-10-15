"""
Simulador ao vivo do RPA: executa um roteiro em tempo real numa thread, gravando no banco
o avanço das etapas e os logs, exatamente como o robô real fará.

Só uma execução roda por vez (o RPA usa uma única credencial e um único navegador).
"""

import logging
import random
import threading
import time
from datetime import datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db import SessionLocal
from app.models import Execution, ExecutionLog, ExecutionStep
from app.schemas import ExecutionFlow, ExecutionTrigger
from app.simulator.plan import RunPlan, build_plan
from app.simulator.schedule import scheduled_slots

logger = logging.getLogger("lms_api.simulator")


class ExecutionAlreadyRunning(Exception):
    def __init__(self, execution_id: int):
        super().__init__(f"Execução {execution_id} ainda está em andamento")
        self.execution_id = execution_id


class _Stopped(Exception):
    pass


class SimulationManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current: tuple[int, threading.Event] | None = None

    @property
    def running_id(self) -> int | None:
        with self._lock:
            return self._current[0] if self._current else None

    def start(self, flow: ExecutionFlow, trigger: ExecutionTrigger) -> int:
        """Cria a execução (status running) e dispara a simulação em segundo plano. Retorna o ID."""
        settings = get_settings()
        with self._lock:
            if self._current:
                raise ExecutionAlreadyRunning(self._current[0])

            plan = build_plan(random.Random(), flow=flow, failure_rate=settings.simulator_failure_rate)
            with SessionLocal() as db:
                execution = Execution(
                    flow=flow, status="running", trigger=trigger, started_at=datetime.now().astimezone()
                )
                for position, (key, label) in enumerate(plan.all_steps):
                    execution.steps.append(ExecutionStep(position=position, key=key, label=label, status="pending"))
                db.add(execution)
                db.commit()
                execution_id = execution.id

            stop_event = threading.Event()
            self._current = (execution_id, stop_event)

        thread = threading.Thread(
            target=self._run, args=(execution_id, plan, stop_event), name=f"rpa-sim-{execution_id}", daemon=True
        )
        thread.start()
        logger.info("Simulação %d iniciada (%s, %s): %s", execution_id, flow, trigger, plan.status)
        return execution_id

    def stop(self, execution_id: int) -> bool:
        with self._lock:
            if not self._current or self._current[0] != execution_id:
                return False
            self._current[1].set()
            return True

    # ------------------------------------------------------------------

    def _run(self, execution_id: int, plan: RunPlan, stop_event: threading.Event) -> None:
        speed = max(get_settings().simulator_speed, 0.01)
        started = time.monotonic()
        current_key: str | None = None
        try:
            for step in plan.steps:
                current_key = step.key
                self._update_step(execution_id, step.key, status="running")
                step_start = time.monotonic()
                for log in step.logs:
                    self._sleep_until(step_start + log.offset / speed, stop_event)
                    self._add_log(execution_id, log.level, log.message)
                self._sleep_until(step_start + step.duration / speed, stop_event)
                self._update_step(
                    execution_id,
                    step.key,
                    status="failed" if step.failed else "success",
                    duration_seconds=round(time.monotonic() - step_start, 1),
                )
            current_key = None
            self._finish(execution_id, plan, started)
        except _Stopped:
            self._finish_stopped(execution_id, current_key, started)
        except Exception:
            logger.exception("Simulação %d falhou inesperadamente", execution_id)
            self._finish_stopped(execution_id, current_key, started, reason="Erro interno do simulador.")
        finally:
            with self._lock:
                self._current = None

    @staticmethod
    def _sleep_until(deadline: float, stop_event: threading.Event) -> None:
        remaining = deadline - time.monotonic()
        if remaining > 0 and stop_event.wait(remaining):
            raise _Stopped()
        if stop_event.is_set():
            raise _Stopped()

    @staticmethod
    def _update_step(execution_id: int, key: str, **fields) -> None:
        with SessionLocal() as db:
            step = db.scalar(
                select(ExecutionStep).where(ExecutionStep.execution_id == execution_id, ExecutionStep.key == key)
            )
            for name, value in fields.items():
                setattr(step, name, value)
            db.commit()

    @staticmethod
    def _add_log(execution_id: int, level: str, message: str) -> None:
        with SessionLocal() as db:
            db.add(
                ExecutionLog(
                    execution_id=execution_id, timestamp=datetime.now().astimezone(), level=level, message=message
                )
            )
            db.commit()

    @staticmethod
    def _finish(execution_id: int, plan: RunPlan, started: float) -> None:
        with SessionLocal() as db:
            execution = db.get(Execution, execution_id)
            for step in execution.steps:
                if step.status == "pending":
                    step.status = "skipped"
            execution.status = plan.status
            execution.records = plan.records
            execution.finished_at = datetime.now().astimezone()
            execution.duration_seconds = round(time.monotonic() - started, 1)
            if plan.error:
                execution.error_title, execution.error_message, _ = plan.error
            db.commit()
        logger.info("Simulação %d concluída: %s", execution_id, plan.status)

    @staticmethod
    def _finish_stopped(
        execution_id: int, current_key: str | None, started: float, reason: str = "Execução interrompida pelo usuário."
    ) -> None:
        with SessionLocal() as db:
            execution = db.get(Execution, execution_id)
            now = datetime.now().astimezone()
            for step in execution.steps:
                if step.key == current_key:
                    step.status = "failed"
                elif step.status in ("pending", "running"):
                    step.status = "skipped"
            execution.logs.append(ExecutionLog(timestamp=now, level="warning", message=reason))
            closing = "Fechando contexto do navegador. Processo encerrado com código 130."
            execution.logs.append(ExecutionLog(timestamp=now, level="info", message=closing))
            execution.status = "failed"
            execution.finished_at = now
            execution.duration_seconds = round(time.monotonic() - started, 1)
            execution.error_title = "Execução interrompida"
            execution.error_message = reason
            db.commit()
        logger.info("Simulação %d interrompida", execution_id)


def recover_orphans() -> int:
    """Marca como falhas as execuções que ficaram 'running' porque a API foi reiniciada no meio."""
    with SessionLocal() as db:
        orphans = db.scalars(select(Execution).where(Execution.status == "running")).all()
        now = datetime.now().astimezone()
        for execution in orphans:
            for step in execution.steps:
                if step.status == "running":
                    step.status = "failed"
                elif step.status == "pending":
                    step.status = "skipped"
            execution.status = "failed"
            execution.finished_at = execution.finished_at or now
            execution.duration_seconds = round((execution.finished_at - execution.started_at).total_seconds(), 1)
            execution.error_title = "Execução interrompida"
            execution.error_message = "A API foi reiniciada enquanto a execução estava em andamento."
        db.commit()
        return len(orphans)


simulation_manager = SimulationManager()


class ScheduledRunner:
    """Dispara execuções 'scheduled' nos horários da agenda fictícia enquanto a API está no ar."""

    def __init__(self, manager: SimulationManager) -> None:
        self._manager = manager
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="rpa-scheduler", daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        last_check = datetime.now().astimezone()
        while not self._stop.wait(20):
            now = datetime.now().astimezone()
            due = [
                slot
                for day in {last_check.date(), now.date()}
                for slot in scheduled_slots(day)
                if last_check < slot <= now
            ]
            last_check = now
            if not due:
                continue
            try:
                self._manager.start("login_capture", "scheduled")
            except ExecutionAlreadyRunning as exc:
                logger.warning("Execução agendada ignorada: %s", exc)
            except Exception:
                logger.exception("Falha ao disparar a execução agendada")


scheduled_runner = ScheduledRunner(simulation_manager)
