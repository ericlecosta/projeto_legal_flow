from datetime import datetime

import pytest

from src.consolidation.ideal_raw import (
    consolidar,
    limpar_texto,
    montar_registro,
    parse_data,
    parse_flag,
    parse_numero,
    parse_periodo,
    parse_valor,
)


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("2026-05-20", "2026-05-20"),
        ("2026-08-12\xa0", "2026-08-12"),
        ("2026.05.20 14:33:21", "2026-05-20"),
        ("20/05/2026", "2026-05-20"),
        (datetime(2026, 12, 1, 9, 30), "2026-12-01"),
        ("", None),
        (None, None),
        (float("nan"), None),
        ("sem data", None),
        ("2026-13-40", None),
    ],
)
def test_parse_data(valor, esperado):
    assert parse_data(valor) == esperado


def test_parse_periodo_separa_inicio_e_fim():
    assert parse_periodo("2026-03-24 ~ 2026-04-18") == ("2026-03-24", "2026-04-18")
    assert parse_periodo("2026-03-24 ~") == ("2026-03-24", None)
    assert parse_periodo("") == (None, None)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("11145.04", 11145.04),
        ("11,145.04", 11145.04),
        ("11.145,04", 11145.04),
        ("9.240.61", 9240.61),
        ("1,000", 1000.0),
        ("1.000.000", 1000000.0),
        ("12,5", 12.5),
        ("abc", None),
    ],
)
def test_parse_numero_aceita_formatos_do_lms(texto, esperado):
    assert parse_numero(texto) == esperado


def test_parse_valor_separa_moeda():
    assert parse_valor("USD 11,145.04") == ("USD", 11145.04)
    assert parse_valor("9.240.61 BRL") == ("BRL", 9240.61)
    assert parse_valor(2500) == (None, 2500.0)
    assert parse_valor(None) == (None, None)


@pytest.mark.parametrize("valor, esperado", [(True, True), ("True", True), ("1", True), ("False", False), ("", False)])
def test_parse_flag(valor, esperado):
    assert parse_flag(valor) is esperado


def test_limpar_texto_remove_espacos_e_nbsp():
    assert limpar_texto("  Service Utilization\n") == "Service Utilization"
    assert limpar_texto("\xa0") is None


def linha_exemplo(**alteracoes):
    """Linha no formato do contract_review_management.xlsx (exemplo da Base Ideal)."""
    linha = {
        "Contract Number": "C2026825327",
        "Department of the person in charge": "LGESP IT CNS Team - MAO",
        "Management Number": "C2026825327",
        "Counterparty": "ACME TELECOM LTDA",
        "Contract Name": "Support Contract Renew for L4 Switches",
        "Contract Type": "General Services/Contracting",
        "Requester": "Requester Exemplo",
        "Progress State": "Effective Contract",
        "Contract Period": "2026-12-01 ~ 2027-11-30",
        "I requested a review of the contract.": "2026-07-28",
        "Request Legal Review": "2026-08-03",
        "Review Completed": "2026-08-06",
        "Legal Team Consent in Progress": "2026-08-06",
        "Legal Team Consent Completed": "2026-08-06",
        "Processing Approval for Execution": "2026-08-12\xa0",
        "Approval Completed": "2026-08-13",
        "Effective Contract": "2026-08-19",
        "Biz-Drop Completed": "",
        "Contract Amount": "USD 11,145.04",
        "A person in charge of legal (team)": "Revisor Exemplo",
        "Review Request Msg": True,
        "Review Completed Flag": True,
        "Legal Team Consent": True,
        "Approval Completed Flag": True,
        "Processing Approval": True,
        "Contract Expired": False,
    }
    linha.update(alteracoes)
    return linha


def test_montar_registro_converte_a_linha_completa():
    registro = montar_registro(linha_exemplo())

    assert registro["contractNumber"] == "C2026825327"
    assert registro["department"] == "LGESP IT CNS Team - MAO"
    assert registro["progressState"] == "Effective Contract"
    assert registro["legalReviewer"] == "Revisor Exemplo"
    assert (registro["periodStart"], registro["periodEnd"]) == ("2026-12-01", "2027-11-30")
    assert registro["reviewRequestedAt"] == "2026-07-28"
    assert registro["approvalRequestedAt"] == "2026-08-12"
    assert registro["bizDropCompletedAt"] is None
    assert (registro["currency"], registro["amount"]) == ("USD", 11145.04)
    assert registro["flags"]["reviewCompleted"] is True
    assert registro["flags"]["contractExpired"] is False
    assert registro["raw"]["Contract Amount"] == "USD 11,145.04"


def test_montar_registro_usa_management_number_quando_falta_o_contract_number():
    registro = montar_registro(linha_exemplo(**{"Contract Number": ""}))
    assert registro["contractNumber"] == "C2026825327"


def test_montar_registro_ignora_linha_sem_numero():
    assert montar_registro(linha_exemplo(**{"Contract Number": None, "Management Number": ""})) is None


def test_consolidar_remove_duplicados_mantendo_a_ultima_leitura():
    linhas = [
        linha_exemplo(**{"Progress State": "Legal Review in Progress"}),
        linha_exemplo(**{"Contract Number": "", "Management Number": ""}),
        linha_exemplo(**{"Progress State": "Effective Contract"}),
    ]
    registros = consolidar(linhas)
    assert len(registros) == 1
    assert registros[0]["progressState"] == "Effective Contract"
