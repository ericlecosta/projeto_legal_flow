import csv
import io
import re
from datetime import date, datetime
from pathlib import Path

import pytest
import xlrd
from openpyxl import load_workbook

from app.models import Contract
from app.services import contract_export
from app.services.base_ideal import BASE_IDEAL_COLUMNS, base_ideal_row

MODELO_DO_ROBO = (
    Path(__file__).resolve().parents[3] / "ideal_raw_RPA" / "src" / "base_ideal" / "modelo" / "Base_Ideal_padrao.xlsx"
)
GERADO_EM = datetime(2026, 10, 27, 21, 30)

RAW = {
    "Contract number": "C2026833165",
    "Counterparty": "SESI - SERVICO SOCIAL DA INDUSTRIA",
    "Contract name": "SESI - SERVIÇOS DE ERGONOMIA",
    "Main Contract Type": "Service Utilization",
    "Contract type": "General Services/Contracting",
    "The person in charge": "IOMAR FALCAO",
    "Department of the person in charge": "LGESP Safety Part - MAO",
    "Progress State": "Legal Review in Progress",
    "Start date": "2026-11-01",
    "End date": "2028-10-31",
    "Request Date": "2026-10-13",
    "Request Legal Review": "2026-10-13",
    "Review completed": None,
    "Agreement request": None,
    "Agreement has been completed": None,
    "Approval request": None,
    "Approval request completed": None,
    "Register the conclusion of contract": None,
    "Biz-Drop Completed": None,
    "Qty Review": "2",
    "Reviewer": "BARBARA LUSTOSA",
    "Contract currency": "BRL",
    "Amount": "810184.8",
}


def contrato(raw=None, **campos):
    return Contract(contract_number=campos.pop("contract_number", "C2026833165"), raw=raw or {}, flags={}, **campos)


def linhas():
    return [
        base_ideal_row(contrato(RAW)),
        base_ideal_row(contrato({"Contract number": "C2", "Progress State": "Contract Expired", "Amount": None})),
    ]


def test_colunas_seguem_o_modelo_da_planilha_do_robo():
    cabecalho = [str(c.value).strip() for c in load_workbook(MODELO_DO_ROBO).active[1] if c.value]
    # Toda coluna do modelo aparece, na mesma ordem (Qty Review entra junto com a extração incremental)
    assert [c for c in BASE_IDEAL_COLUMNS if c in cabecalho] == cabecalho
    assert set(BASE_IDEAL_COLUMNS) - set(cabecalho) <= {"Qty Review"}


def test_linha_usa_os_valores_da_planilha_com_numeros_onde_ela_tem_numeros():
    linha = base_ideal_row(contrato(RAW))
    assert list(linha) == BASE_IDEAL_COLUMNS
    assert linha["Progress State"] == "Legal Review in Progress"
    assert linha["Main Contract Type"] == "Service Utilization"
    assert linha["Start date"] == "2026-11-01"
    assert linha["Amount"] == 810184.8
    assert linha["Qty Review"] == 2
    assert linha["Review completed"] is None


def test_sem_raw_usa_os_campos_do_contrato():
    linha = base_ideal_row(
        contrato(
            None,
            progress_state="Effective Contract",
            period_start=date(2026, 1, 1),
            effective_at=date(2026, 2, 3),
            legal_reviewer="DYDRA ANDRADE",
            amount=10.5,
        )
    )
    assert linha["Progress State"] == "Effective Contract"
    assert linha["Start date"] == "2026-01-01"
    assert linha["Register the conclusion of contract"] == "2026-02-03"
    assert linha["Reviewer"] == "DYDRA ANDRADE"
    assert linha["Amount"] == 10.5
    assert linha["Main Contract Type"] is None


def test_contrato_expirado_sem_raw():
    expirado = Contract(contract_number="C1", raw={}, flags={"expired": True})
    assert base_ideal_row(expirado)["Register the conclusion of contract"] == "Expirado"


def test_valor_que_nao_e_numero_fica_como_veio():
    assert base_ideal_row(contrato({"Amount": "a definir"}))["Amount"] == "a definir"


def test_csv_para_excel_em_portugues():
    conteudo = contract_export.to_csv(linhas())
    assert conteudo.startswith("﻿".encode())
    leitor = list(csv.reader(io.StringIO(conteudo.decode("utf-8-sig")), delimiter=";"))
    assert leitor[0] == BASE_IDEAL_COLUMNS
    linha = dict(zip(leitor[0], leitor[1]))
    assert linha["Contract name"] == "SESI - SERVIÇOS DE ERGONOMIA"
    assert linha["Amount"] == "810184,80"
    assert linha["Review completed"] == ""
    assert len(leitor) == 3


def test_xlsx_tem_cabecalho_e_numeros_da_planilha():
    ws = load_workbook(io.BytesIO(contract_export.to_xlsx(linhas()))).active
    assert [c.value for c in ws[1]] == BASE_IDEAL_COLUMNS
    linha = {c: ws.cell(2, i + 1) for i, c in enumerate(BASE_IDEAL_COLUMNS)}
    assert linha["Amount"].value == 810184.8
    assert linha["Amount"].number_format == "#,##0.00"
    assert linha["Qty Review"].value == 2
    assert linha["Start date"].value == "2026-11-01"
    assert ws.max_row == 3
    assert ws.freeze_panes == "B2"


def test_texto_que_parece_formula_continua_texto_no_xlsx():
    ws = load_workbook(
        io.BytesIO(contract_export.to_xlsx([base_ideal_row(contrato({"Contract name": "=1+1"}))]))
    ).active
    celula = ws.cell(2, BASE_IDEAL_COLUMNS.index("Contract name") + 1)
    assert (celula.value, celula.data_type) == ("=1+1", "s")


def test_xls_abre_no_formato_antigo():
    planilha = xlrd.open_workbook(file_contents=contract_export.to_xls(linhas())).sheet_by_index(0)
    assert planilha.row_values(0) == BASE_IDEAL_COLUMNS
    linha = dict(zip(BASE_IDEAL_COLUMNS, planilha.row_values(1)))
    assert linha["Amount"] == 810184.8
    assert linha["Contract name"] == "SESI - SERVIÇOS DE ERGONOMIA"
    assert planilha.nrows == 3


def test_pdf_e_gerado_com_todas_as_linhas():
    muitas = linhas() * 60  # ocupa mais de uma página
    conteudo = contract_export.to_pdf(muitas, GERADO_EM, "Progress State = Contract Expired")
    assert conteudo.startswith(b"%PDF")
    paginas = len(re.findall(rb"/Type /Page(?!s)", conteudo))
    assert paginas >= 2
    assert b"Base Ideal" in conteudo


@pytest.mark.parametrize("formato", ["csv", "xlsx", "xls", "pdf"])
def test_base_vazia_exporta_so_o_cabecalho(formato):
    assert contract_export.export([], formato, GERADO_EM)


def test_nome_do_arquivo():
    assert contract_export.filename("xlsx", GERADO_EM) == "base_ideal_20261027_2130.xlsx"
