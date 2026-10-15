from datetime import date

import pytest
from pydantic import ValidationError

from app.models import Contract
from app.repositories import contracts
from app.repositories.rpa_ingest import start_execution
from app.schemas import ContractIn, RpaExecutionStart


def contrato(numero="C2026000001", **campos):
    return ContractIn(contract_number=numero, **campos)


def test_contract_in_aceita_json_em_camel_case_e_datas_iso():
    data = ContractIn.model_validate(
        {
            "contractNumber": "C2026814234",
            "progressState": "Approval Completed",
            "reviewRequestedAt": "2026-04-17",
            "amount": 9240.61,
            "flags": {"reviewCompleted": True},
        }
    )
    assert data.review_requested_at == date(2026, 4, 17)
    assert data.flags == {"reviewCompleted": True}


def test_contract_in_rejeita_data_invalida_e_numero_vazio():
    with pytest.raises(ValidationError):
        ContractIn.model_validate({"contractNumber": "C1", "reviewRequestedAt": "17/04/2026x"})
    with pytest.raises(ValidationError):
        ContractIn.model_validate({"contractNumber": ""})


def test_upsert_cria_e_depois_atualiza_pelo_numero(db):
    primeiro = contracts.upsert_contracts(db, [contrato(progress_state="Legal Review in Progress")], None)
    assert (primeiro.created, primeiro.updated) == (1, 0)

    segundo = contracts.upsert_contracts(
        db, [contrato(progress_state="Review Completed"), contrato("C2026000002")], None
    )
    assert (segundo.received, segundo.created, segundo.updated) == (2, 1, 1)

    linha = db.query(Contract).filter_by(contract_number="C2026000001").one()
    assert linha.progress_state == "Review Completed"
    assert db.query(Contract).count() == 2


def test_upsert_com_numero_repetido_no_lote_fica_com_o_ultimo(db):
    resultado = contracts.upsert_contracts(db, [contrato(counterparty="Antiga"), contrato(counterparty="Nova")], None)
    assert (resultado.received, resultado.created, resultado.updated) == (2, 1, 0)
    assert db.query(Contract).one().counterparty == "Nova"


def test_upsert_liga_o_contrato_a_execucao_existente(db):
    execucao = start_execution(db, RpaExecutionStart())
    contracts.upsert_contracts(db, [contrato()], execucao.id)
    assert db.query(Contract).one().last_execution_id == execucao.id


def test_upsert_ignora_execucao_inexistente(db):
    contracts.upsert_contracts(db, [contrato()], 999)
    assert db.query(Contract).one().last_execution_id is None


@pytest.fixture
def base_exemplo(db):
    contracts.upsert_contracts(
        db,
        [
            contrato(
                "C1",
                counterparty="Norte Tech",
                progress_state="Legal Review in Progress",
                department="LGESP GA - MAO",
                review_requested_at=date(2026, 9, 1),
            ),
            contrato(
                "C2",
                counterparty="Rio Negro Imóveis",
                progress_state="Effective Contract",
                department="LGESP IT - MAO",
                review_requested_at=date(2026, 10, 1),
            ),
            contrato(
                "C3",
                counterparty="Atlas",
                progress_state="Legal Review in Progress",
                department="LGESP GA - MAO",
                legal_reviewer="Juliana Prado",
            ),
        ],
        None,
    )


def test_list_ordena_pela_solicitacao_mais_recente_e_sem_data_por_ultimo(db, base_exemplo):
    page = contracts.list_contracts(db, None, None, None, 1, 20)
    assert page.count == 3
    assert [c.contract_number for c in page.results] == ["C2", "C1", "C3"]


@pytest.mark.parametrize(
    "busca, estado, departamento, esperado",
    [
        ("norte", None, None, ["C1"]),
        ("juliana", None, None, ["C3"]),
        ("c2", None, None, ["C2"]),
        (None, "Legal Review in Progress", None, ["C1", "C3"]),
        (None, None, "LGESP IT - MAO", ["C2"]),
        ("atlas", "Effective Contract", None, []),
    ],
)
def test_list_filtra(db, base_exemplo, busca, estado, departamento, esperado):
    page = contracts.list_contracts(db, busca, estado, departamento, 1, 20)
    assert [c.contract_number for c in page.results] == esperado
    assert page.count == len(esperado)


def test_list_pagina(db, base_exemplo):
    page = contracts.list_contracts(db, None, None, None, 2, 2)
    assert page.count == 3
    assert [c.contract_number for c in page.results] == ["C3"]


def test_summary_conta_por_status(db, base_exemplo):
    resumo = contracts.get_summary(db)
    assert resumo.total == 3
    assert [(s.progress_state, s.count) for s in resumo.by_progress_state] == [
        ("Legal Review in Progress", 2),
        ("Effective Contract", 1),
    ]
    assert resumo.last_updated_at is not None


def test_summary_com_base_vazia(db):
    resumo = contracts.get_summary(db)
    assert (resumo.total, resumo.by_progress_state, resumo.last_updated_at) == (0, [], None)
