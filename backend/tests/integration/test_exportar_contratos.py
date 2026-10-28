"""Exportação da tela Contratos pela API: filtros iguais aos da listagem e um arquivo por formato."""

import csv
import io

import pytest
from openpyxl import load_workbook

from app.services.base_ideal import BASE_IDEAL_COLUMNS
from tests.constants import RPA_HEADERS

pytestmark = pytest.mark.integration


def contrato(numero, estado, nome, valor):
    raw = dict.fromkeys(BASE_IDEAL_COLUMNS)
    raw.update({"Contract number": numero, "Progress State": estado, "Contract name": nome, "Amount": str(valor)})
    return {"contractNumber": numero, "progressState": estado, "contractName": nome, "amount": valor, "raw": raw}


@pytest.fixture
def base(client):
    contratos = [
        contrato("C1", "Review Completed", "Rental MAO", 100.0),
        contrato("C2", "Effective Contract", "Support L4", 2500.5),
        contrato("C3", "Review Completed", "Rental SP", 30.0),
    ]
    resposta = client.put("/api/rpa/contracts/", json={"contracts": contratos}, headers=RPA_HEADERS)
    assert resposta.status_code == 200


def baixar(client, **params):
    resposta = client.get("/api/contracts/export/", params=params)
    assert resposta.status_code == 200, resposta.text
    return resposta


def test_listagem_traz_a_linha_da_base_ideal(client, base):
    contrato = client.get("/api/contracts/", params={"search": "C2"}).json()["results"][0]
    assert list(contrato["baseIdeal"]) == BASE_IDEAL_COLUMNS
    assert contrato["baseIdeal"]["Progress State"] == "Effective Contract"
    assert contrato["baseIdeal"]["Amount"] == 2500.5


def test_xlsx_e_o_formato_padrao_com_todos_os_contratos(client, base):
    resposta = baixar(client)
    assert resposta.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert resposta.headers["content-disposition"].startswith('attachment; filename="base_ideal_')
    assert resposta.headers["content-disposition"].endswith('.xlsx"')
    ws = load_workbook(io.BytesIO(resposta.content)).active
    assert [c.value for c in ws[1]] == BASE_IDEAL_COLUMNS
    assert sorted(ws.cell(r, 1).value for r in range(2, ws.max_row + 1)) == ["C1", "C2", "C3"]


def test_exportacao_respeita_busca_e_status_da_tela(client, base):
    resposta = baixar(client, format="csv", progress_state="Review Completed", search="rental")
    linhas = list(csv.reader(io.StringIO(resposta.content.decode("utf-8-sig")), delimiter=";"))
    assert sorted(linha[0] for linha in linhas[1:]) == ["C1", "C3"]
    assert resposta.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.parametrize(
    "formato,inicio",
    [("csv", "﻿Contract number".encode()), ("xlsx", b"PK"), ("xls", b"\xd0\xcf\x11\xe0"), ("pdf", b"%PDF")],
)
def test_cada_formato_tem_o_arquivo_certo(client, base, formato, inicio):
    resposta = baixar(client, format=formato)
    assert resposta.content.startswith(inicio)
    assert resposta.headers["content-disposition"].endswith(f'.{formato}"')


def test_formato_desconhecido_responde_422(client):
    assert client.get("/api/contracts/export/", params={"format": "docx"}).status_code == 422


def test_base_vazia_exporta_so_o_cabecalho(client):
    linhas = baixar(client, format="csv").content.decode("utf-8-sig").splitlines()
    assert linhas == [";".join(BASE_IDEAL_COLUMNS)]
