"""
Tratamento com a extração de verdade (docs/planilha_de_dados/contract_review_management.xlsx),
no formato antigo e no formato atual da extração (colunas Request Date, Qty Review, Biz-Drop Status).
"""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from src.base_ideal import MAPEAMENTO, MODELO_PADRAO, ler_registros, para_contratos_api
from src.extract_contract import COLUNAS_FINAIS
from src.pipeline import tratar_base_ideal

pytestmark = pytest.mark.integration

EXTRACAO = Path(__file__).resolve().parents[3] / "docs" / "planilha_de_dados" / "contract_review_management.xlsx"
STATUS_FORA_DA_BASE = {"Biz-Holding", "Signed Contract Registered"}
STATUS_SEM_DATA = {
    "Approval for the Biz-Drop",
    "Approval Rejected",
    "Legal Comments Provided",
    "Pending Assignment",
    "Request for Consent Rejected",
    "Request Temporarily Saved",
}
PERIODO = {"Start date", "End date"}
DATAS = ["Start date", "End date", "Request Date", "Request Legal Review", "Review completed", "Biz-Drop Completed"]


@pytest.fixture
def extracao_atual(tmp_path):
    """A mesma extração, com o cabeçalho que a extração atual grava (COLUNAS_FINAIS)."""
    wb = load_workbook(EXTRACAO)
    ws = wb.active
    cabecalho = {c.value: c.column for c in ws[1]}
    ws.cell(1, cabecalho["I requested a review of the contract."], "Request Date")
    for coluna in ("Qty Review", "Biz-Drop Status"):
        ws.cell(1, ws.max_column + 1, coluna)
    assert {c.value for c in ws[1]} == set(COLUNAS_FINAIS)
    caminho = tmp_path / "contract_review_management.xlsx"
    wb.save(caminho)
    return caminho


def contar_contratos():
    ws = load_workbook(EXTRACAO, read_only=True).active
    return sum(1 for linha in ws.iter_rows(min_row=2, values_only=True) if linha[0])


def test_extracao_de_exemplo_vira_base_ideal(tmp_path):
    registros = ler_registros(EXTRACAO)

    assert 0 < len(registros) <= contar_contratos()
    assert all(r["Progress State"] not in STATUS_FORA_DA_BASE for r in registros)
    for r in registros:
        assert set(r) == set(MAPEAMENTO)
        assert r["Contract number"].startswith("C")
        for campo in DATAS:
            # Vigência em texto livre ("4 anos a partir da assinatura") fica marcada como DATA INVÁLIDA
            valido = r[campo] is None or len(r[campo]) == 10 or (campo in PERIODO and r[campo] == "DATA INVÁLIDA")
            assert valido, (r["Contract number"], campo, r[campo])
        if r["Progress State"] in STATUS_SEM_DATA:
            assert all(r[campo] is None for campo in DATAS)
        assert isinstance(r["Amount"], float) and r["Contract currency"].isalpha()


def test_formato_atual_da_extracao_da_o_mesmo_resultado(extracao_atual):
    assert ler_registros(extracao_atual) == ler_registros(EXTRACAO)


def test_etapa_de_tratamento_grava_a_planilha_no_modelo(extracao_atual):
    caminho, registros = tratar_base_ideal(str(extracao_atual))

    assert Path(caminho) == extracao_atual.parent / "base_ideal.xlsx"
    ws = load_workbook(caminho).active
    modelo = load_workbook(MODELO_PADRAO).active
    assert [c.value for c in ws[1]] == [c.value for c in modelo[1]]
    assert ws.max_row == len(registros) + 1
    assert [ws.cell(i + 2, 1).value for i in range(len(registros))] == [r["Contract number"] for r in registros]


def test_todos_os_contratos_tratados_cabem_no_formato_da_api():
    registros = ler_registros(EXTRACAO)
    contratos = para_contratos_api(registros)
    assert len(contratos) == len(registros)
    assert len({c["contractNumber"] for c in contratos}) == len(contratos)
