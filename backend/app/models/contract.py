"""
Modelo da base Ideal Raw: um registro por contrato do Contract Review Management (LMS).

O robô grava e atualiza os contratos a cada execução (upsert pelo número do contrato).
Como o tratamento da base ainda está em evolução, a linha original da planilha fica em `raw`.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    management_number: Mapped[str | None] = mapped_column(String(32))
    counterparty: Mapped[str | None] = mapped_column(Text)
    contract_name: Mapped[str | None] = mapped_column(Text)
    contract_type: Mapped[str | None] = mapped_column(String(128))
    requester: Mapped[str | None] = mapped_column(String(128))
    department: Mapped[str | None] = mapped_column(String(128), index=True)
    progress_state: Mapped[str | None] = mapped_column(String(64), index=True)
    legal_reviewer: Mapped[str | None] = mapped_column(String(128))

    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)

    # Marcos do fluxo (uma data por coluna da Base Ideal)
    review_requested_at: Mapped[date | None] = mapped_column(Date)
    legal_review_started_at: Mapped[date | None] = mapped_column(Date)
    review_completed_at: Mapped[date | None] = mapped_column(Date)
    consent_requested_at: Mapped[date | None] = mapped_column(Date)
    consent_completed_at: Mapped[date | None] = mapped_column(Date)
    approval_requested_at: Mapped[date | None] = mapped_column(Date)
    approval_completed_at: Mapped[date | None] = mapped_column(Date)
    effective_at: Mapped[date | None] = mapped_column(Date)
    biz_drop_completed_at: Mapped[date | None] = mapped_column(Date)

    currency: Mapped[str | None] = mapped_column(String(8))
    amount: Mapped[float | None] = mapped_column(Float)

    flags: Mapped[dict] = mapped_column(JSON, default=dict)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    last_execution_id: Mapped[int | None] = mapped_column(ForeignKey("executions.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
