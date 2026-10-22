"""
Modelos ORM das execuções do RPA, espelhando os contratos do front-end
(frontend/src/app/shared/models/execution.model.ts).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flow: Mapped[str] = mapped_column(String(32))  # login_capture | otp_only
    status: Mapped[str] = mapped_column(String(16), index=True)  # success | failed | atypical | running
    trigger: Mapped[str] = mapped_column(String(16))  # scheduled | manual
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    records: Mapped[int | None] = mapped_column(Integer)

    error_title: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    error_screenshot_url: Mapped[str | None] = mapped_column(String(512))

    steps: Mapped[list["ExecutionStep"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionStep.position"
    )
    logs: Mapped[list["ExecutionLog"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionLog.timestamp"
    )


class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    key: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    duration_seconds: Mapped[float | None] = mapped_column(Float)

    execution: Mapped[Execution] = relationship(back_populates="steps")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    level: Mapped[str] = mapped_column(String(16))  # info | warning | error | success
    message: Mapped[str] = mapped_column(Text)

    execution: Mapped[Execution] = relationship(back_populates="logs")


class RpaJob(Base):
    """
    Pedido de execução feito pelo painel no modo real. O worker do robô reivindica o pedido,
    roda o fluxo gravando na execução ligada a ele e consulta `stop_requested` para saber se deve parar.
    """

    __tablename__ = "rpa_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), unique=True, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_requested: Mapped[bool] = mapped_column(Boolean, default=False)

    execution: Mapped[Execution] = relationship()
