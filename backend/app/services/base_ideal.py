"""
Linha da Base Ideal de cada contrato: as mesmas colunas, na mesma ordem e com os mesmos valores
da planilha que o robô gera (ideal_raw_RPA/src/base_ideal). É o que a tela Contratos mostra
e o que vai para os arquivos exportados.

O robô envia a linha completa da planilha em `raw`; os campos estruturados do contrato só
preenchem o que faltar nela (contratos gravados antes de uma coluna existir).
"""

from datetime import date
from typing import Any

from app.models import Contract

# Cabeçalho do modelo Base_Ideal_padrao.xlsx (sem os espaços sobrando no fim de alguns nomes)
BASE_IDEAL_COLUMNS = [
    "Contract number",
    "Counterparty",
    "Contract name",
    "Main Contract Type",
    "Contract type",
    "The person in charge",
    "Department of the person in charge",
    "Progress State",
    "Start date",
    "End date",
    "Request Date",
    "Request Legal Review",
    "Review completed",
    "Agreement request",
    "Agreement has been completed",
    "Approval request",
    "Approval request completed",
    "Register the conclusion of contract",
    "Biz-Drop Completed",
    "Qty Review",
    "Reviewer",
    "Contract currency",
    "Amount",
]

AMOUNT_COLUMN = "Amount"
INTEGER_COLUMNS = {"Qty Review"}

# Coluna da Base Ideal -> campo do contrato no banco
_FIELDS = {
    "Contract number": "contract_number",
    "Counterparty": "counterparty",
    "Contract name": "contract_name",
    "Contract type": "contract_type",
    "The person in charge": "requester",
    "Department of the person in charge": "department",
    "Progress State": "progress_state",
    "Start date": "period_start",
    "End date": "period_end",
    "Request Date": "review_requested_at",
    "Request Legal Review": "legal_review_started_at",
    "Review completed": "review_completed_at",
    "Agreement request": "consent_requested_at",
    "Agreement has been completed": "consent_completed_at",
    "Approval request": "approval_requested_at",
    "Approval request completed": "approval_completed_at",
    "Biz-Drop Completed": "biz_drop_completed_at",
    "Reviewer": "legal_reviewer",
    "Contract currency": "currency",
    "Amount": "amount",
}
_CONCLUSION = "Register the conclusion of contract"

Value = str | int | float | None


def _from_fields(contract: Contract, column: str) -> Any:
    if column == _CONCLUSION:
        if (contract.flags or {}).get("expired"):
            return "Expirado"
        return contract.effective_at
    name = _FIELDS.get(column)
    return getattr(contract, name) if name else None


def _typed(column: str, value: Any) -> Value:
    """Número onde a planilha tem número (Amount, Qty Review); o resto como texto, igual à planilha."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if column == AMOUNT_COLUMN or column in INTEGER_COLUMNS:
        try:
            number = float(str(value).replace(",", "")) if isinstance(value, str) else float(value)
        except ValueError:
            return str(value)
        return int(number) if column in INTEGER_COLUMNS else number
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def base_ideal_row(contract: Contract) -> dict[str, Value]:
    raw = contract.raw or {}
    return {
        column: _typed(column, raw[column] if column in raw else _from_fields(contract, column))
        for column in BASE_IDEAL_COLUMNS
    }
