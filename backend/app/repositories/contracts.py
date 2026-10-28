"""
Contratos da base Ideal Raw: gravação em lote vinda do robô e consultas para o front.
"""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Contract, Execution
from app.services.base_ideal import Value, base_ideal_row
from app.schemas import (
    Contract as ContractSchema,
    ContractIn,
    ContractSummary,
    ContractsUploadResult,
    Page,
    ProgressStateCount,
)

UPDATABLE_FIELDS = [name for name in ContractIn.model_fields if name != "contract_number"]


def upsert_contracts(db: Session, contracts: list[ContractIn], execution_id: int | None) -> ContractsUploadResult:
    """Cria os contratos novos e atualiza os existentes (pelo número). Repetidos no lote: o último vence."""
    by_number = {contract.contract_number: contract for contract in contracts}
    if execution_id is not None and db.get(Execution, execution_id) is None:
        execution_id = None

    existing = {
        row.contract_number: row
        for row in db.scalars(select(Contract).where(Contract.contract_number.in_(list(by_number)))).all()
    }
    now = datetime.now().astimezone()
    created = 0
    for number, data in by_number.items():
        row = existing.get(number)
        if row is None:
            row = Contract(contract_number=number)
            db.add(row)
            created += 1
        for name in UPDATABLE_FIELDS:
            setattr(row, name, getattr(data, name))
        row.last_execution_id = execution_id
        row.updated_at = now
    db.commit()
    return ContractsUploadResult(received=len(contracts), created=created, updated=len(by_number) - created)


def _to_schema(row: Contract) -> ContractSchema:
    return ContractSchema.model_validate(
        {
            "contract_number": row.contract_number,
            **{name: getattr(row, name) for name in UPDATABLE_FIELDS},
            "flags": row.flags or {},
            "raw": row.raw or {},
            "id": row.id,
            "last_execution_id": row.last_execution_id,
            "updated_at": row.updated_at,
            "base_ideal": base_ideal_row(row),
        }
    )


def _filtered(search: str | None, progress_state: str | None, department: str | None):
    """Mesma busca e filtros na listagem e na exportação, na mesma ordem."""
    query = select(Contract)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Contract.contract_number.ilike(term),
                Contract.counterparty.ilike(term),
                Contract.contract_name.ilike(term),
                Contract.legal_reviewer.ilike(term),
            )
        )
    if progress_state:
        query = query.where(Contract.progress_state == progress_state)
    if department:
        query = query.where(Contract.department == department)
    return query


_ORDER = (Contract.review_requested_at.desc().nulls_last(), Contract.contract_number)


def list_contracts(
    db: Session, search: str | None, progress_state: str | None, department: str | None, page: int, page_size: int
) -> Page[ContractSchema]:
    query = _filtered(search, progress_state, department)
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(*_ORDER).offset((page - 1) * page_size).limit(page_size)).all()
    return Page[ContractSchema](count=count, results=[_to_schema(row) for row in rows])


def base_ideal_rows(
    db: Session, search: str | None, progress_state: str | None, department: str | None
) -> list[dict[str, Value]]:
    """Todos os contratos do filtro (sem paginação), como linhas da Base Ideal, para exportar."""
    rows = db.scalars(_filtered(search, progress_state, department).order_by(*_ORDER)).all()
    return [base_ideal_row(row) for row in rows]


def get_summary(db: Session) -> ContractSummary:
    counts = db.execute(
        select(Contract.progress_state, func.count())
        .group_by(Contract.progress_state)
        .order_by(func.count().desc(), Contract.progress_state)
    ).all()
    last = db.execute(
        select(Contract.updated_at, Contract.last_execution_id).order_by(Contract.updated_at.desc()).limit(1)
    ).first()
    return ContractSummary(
        total=sum(count for _, count in counts),
        by_progress_state=[ProgressStateCount(progress_state=state, count=count) for state, count in counts],
        last_updated_at=last[0] if last else None,
        last_execution_id=last[1] if last else None,
    )
