"""
Converte os registros da Base Ideal (colunas do modelo) para o formato que a API do monitor
grava na tabela de contratos (PUT /api/rpa/contracts/, campos em camelCase).
"""

import re
from typing import Any

# Campo da Base Ideal -> campo da API
CAMPOS_API = {
    "Contract number": "contractNumber",
    "Counterparty": "counterparty",
    "Contract name": "contractName",
    "Contract type": "contractType",
    "The person in charge": "requester",
    "Department of the person in charge": "department",
    "Progress State": "progressState",
    "Reviewer": "legalReviewer",
    "Contract currency": "currency",
    "Amount": "amount",
}

DATAS_API = {
    "Start date": "periodStart",
    "End date": "periodEnd",
    "Request Date": "reviewRequestedAt",
    "Request Legal Review": "legalReviewStartedAt",
    "Review completed": "reviewCompletedAt",
    "Agreement request": "consentRequestedAt",
    "Agreement has been completed": "consentCompletedAt",
    "Approval request": "approvalRequestedAt",
    "Approval request completed": "approvalCompletedAt",
    "Biz-Drop Completed": "bizDropCompletedAt",
}

# Tamanho máximo das colunas no banco (o texto completo continua em `raw`)
LIMITES = {
    "contractNumber": 32,
    "contractType": 128,
    "requester": 128,
    "department": 128,
    "progressState": 64,
    "legalReviewer": 128,
    "currency": 8,
}

CONCLUSAO = "Register the conclusion of contract"
_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _data(valor: Any) -> str | None:
    """Só datas AAAA-MM-DD vão para os campos de data; o resto ("DATA INVÁLIDA"...) fica no raw."""
    return valor if isinstance(valor, str) and _DATA_ISO.match(valor) else None


def _texto(valor: Any, limite: int | None = None) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto[:limite] if limite else texto


def para_contrato_api(registro: dict[str, Any]) -> dict[str, Any]:
    """
    Um contrato da Base Ideal no formato da API. A linha completa da base vai em `raw`
    (é o que não tem coluna própria no banco, como Main Contract Type e a conclusão "Expirado").
    """
    contrato: dict[str, Any] = {api: registro.get(campo) for campo, api in CAMPOS_API.items()}
    for campo in ("contractNumber", "counterparty", "contractName", *LIMITES):
        contrato[campo] = _texto(contrato[campo], LIMITES.get(campo))
    contrato["managementNumber"] = contrato["contractNumber"]
    for campo, api in DATAS_API.items():
        contrato[api] = _data(registro.get(campo))

    conclusao = registro.get(CONCLUSAO)
    contrato["effectiveAt"] = _data(conclusao)
    contrato["flags"] = {"expired": conclusao == "Expirado"} if conclusao else {}
    contrato["raw"] = {campo: _texto(valor) for campo, valor in registro.items()}
    return contrato


def para_contratos_api(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converte os registros, deixando de fora os que vieram sem número de contrato."""
    return [para_contrato_api(r) for r in registros if str(r.get("Contract number") or "").strip()]
