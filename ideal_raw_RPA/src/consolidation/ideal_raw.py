"""
Consolidação da base Ideal Raw: converte as linhas extraídas do LMS
(contract_review_management.xlsx) no formato que a API do monitor grava no banco.

O tratamento ainda está em evolução, então cada registro leva também a linha original (`raw`):
o que não for reconhecido aqui continua disponível para conferência.
"""

import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

# Colunas de texto: coluna da planilha -> campo da API
CAMPOS_TEXTO = {
    "Contract Number": "contractNumber",
    "Management Number": "managementNumber",
    "Counterparty": "counterparty",
    "Contract Name": "contractName",
    "Contract Type": "contractType",
    "Requester": "requester",
    "Department of the person in charge": "department",
    "Progress State": "progressState",
    "A person in charge of legal (team)": "legalReviewer",
}

# Marcos do fluxo: coluna da planilha -> campo de data da API
CAMPOS_DATA = {
    "I requested a review of the contract.": "reviewRequestedAt",
    "Request Legal Review": "legalReviewStartedAt",
    "Review Completed": "reviewCompletedAt",
    "Legal Team Consent in Progress": "consentRequestedAt",
    "Legal Team Consent Completed": "consentCompletedAt",
    "Processing Approval for Execution": "approvalRequestedAt",
    "Approval Completed": "approvalCompletedAt",
    "Effective Contract": "effectiveAt",
    "Biz-Drop Completed": "bizDropCompletedAt",
}

# Indicadores de presença (True/False) vistos na timeline do contrato
CAMPOS_FLAG = {
    "Review Request Msg": "reviewRequestMsg",
    "Review Completed Flag": "reviewCompleted",
    "Legal Team Consent": "legalTeamConsent",
    "Approval Completed Flag": "approvalCompleted",
    "Processing Approval": "processingApproval",
    "Contract Expired": "contractExpired",
}

_DATA_ISO_RE = re.compile(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})")
_DATA_BR_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_MOEDA_RE = re.compile(r"\b([A-Z]{3})\b")
_NUMERO_RE = re.compile(r"-?\d[\d.,]*")


def _vazio(valor: Any) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and not valor.replace("\xa0", " ").strip()


def limpar_texto(valor: Any) -> str | None:
    """Texto sem espaços sobrando (inclui o espaço não separável que vem do LMS); None se vazio."""
    if _vazio(valor):
        return None
    texto = " ".join(str(valor).replace("\xa0", " ").split())
    return texto or None


def _data_valida(ano: str, mes: str, dia: str) -> str | None:
    try:
        return date(int(ano), int(mes), int(dia)).isoformat()
    except ValueError:
        return None


def parse_data(valor: Any) -> str | None:
    """
    Primeira data encontrada no valor, em ISO (AAAA-MM-DD).
    Aceita datetime/date, '2026-05-20', '2026.05.20 14:33', '2026-08-12\\xa0' e '20/05/2026'.
    """
    if _vazio(valor):
        return None
    if isinstance(valor, (datetime, pd.Timestamp)):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    texto = str(valor)
    if match := _DATA_ISO_RE.search(texto):
        return _data_valida(*match.groups())
    if match := _DATA_BR_RE.search(texto):
        dia, mes, ano = match.groups()
        return _data_valida(ano, mes, dia)
    return None


def parse_periodo(valor: Any) -> tuple[str | None, str | None]:
    """'2026-03-24 ~ 2026-04-18' -> ('2026-03-24', '2026-04-18')."""
    if _vazio(valor):
        return None, None
    texto = str(valor)
    datas = [_data_valida(*m.groups()) for m in _DATA_ISO_RE.finditer(texto)]
    datas = [d for d in datas if d]
    inicio = datas[0] if datas else None
    fim = datas[1] if len(datas) > 1 else None
    return inicio, fim


def parse_numero(texto: str) -> float | None:
    """
    Converte valores escritos em formatos diferentes:
    '11145.04', '11,145.04', '11.145,04', '9.240.61' (separador de milhar repetido) e '1,000'.
    O último separador é decimal só quando vem seguido de 1 ou 2 dígitos.
    """
    match = _NUMERO_RE.search(texto.replace(" ", ""))
    if not match:
        return None
    numero = match.group(0).rstrip(".,")
    separadores = [i for i, c in enumerate(numero) if c in ".,"]
    if not separadores:
        return float(numero)
    ultimo = separadores[-1]
    digitos_finais = len(numero) - ultimo - 1
    inteiro = re.sub(r"[.,]", "", numero[:ultimo])
    if 1 <= digitos_finais <= 2:
        return float(f"{inteiro}.{numero[ultimo + 1:]}")
    return float(inteiro + numero[ultimo + 1 :])


def parse_valor(valor: Any) -> tuple[str | None, float | None]:
    """'USD 11,145.04' -> ('USD', 11145.04). Sem moeda no texto, devolve (None, número)."""
    if _vazio(valor):
        return None, None
    if isinstance(valor, (int, float)):
        return None, float(valor)
    texto = str(valor).replace("\xa0", " ")
    moeda = _MOEDA_RE.search(texto)
    return (moeda.group(1) if moeda else None), parse_numero(texto)


def parse_flag(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"true", "1", "sim", "yes", "verdadeiro"}


def montar_registro(linha: dict[str, Any]) -> dict[str, Any] | None:
    """
    Converte uma linha da planilha no payload de contrato da API.
    Devolve None quando a linha não tem número de contrato (nem Contract Number nem Management Number).
    """
    registro: dict[str, Any] = {campo: limpar_texto(linha.get(coluna)) for coluna, campo in CAMPOS_TEXTO.items()}
    registro["contractNumber"] = registro["contractNumber"] or registro["managementNumber"]
    if not registro["contractNumber"]:
        return None

    for coluna, campo in CAMPOS_DATA.items():
        registro[campo] = parse_data(linha.get(coluna))

    registro["periodStart"], registro["periodEnd"] = parse_periodo(linha.get("Contract Period"))
    registro["currency"], registro["amount"] = parse_valor(linha.get("Contract Amount"))
    registro["flags"] = {campo: parse_flag(linha.get(coluna)) for coluna, campo in CAMPOS_FLAG.items()}
    registro["raw"] = {str(k): limpar_texto(v) for k, v in linha.items()}
    return registro


def consolidar(linhas: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Monta os registros e remove duplicados pelo número do contrato (a última leitura vence)."""
    por_numero: dict[str, dict[str, Any]] = {}
    for linha in linhas:
        registro = montar_registro(linha)
        if registro:
            por_numero[registro["contractNumber"]] = registro
    return list(por_numero.values())


def ler_planilha(caminho: str | Path) -> list[dict[str, Any]]:
    """Lê o contract_review_management.xlsx como lista de dicionários (células vazias viram None)."""
    df = pd.read_excel(caminho, dtype=object)
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict(orient="records")
