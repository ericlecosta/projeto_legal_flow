import importlib.util
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook


spec = importlib.util.spec_from_file_location("preencher_base_ideal", Path(__file__).parents[2] / "preencher_base_ideal.py")
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


def test_transformacoes():
    assert modulo.transformar("Main Contract Type", "Others\nLeasing") == "Others"
    assert modulo.transformar("Contract type", "Others\nLeasing") == "Leasing"
    assert modulo.transformar("Start date", "2026-10-12\n~\n2027-10-11") == "2026-10-12"
    assert modulo.transformar("End date", "2026-10-12\n~\n2027-10-11") == "2027-10-11"
    assert modulo.transformar("Amount", "32,368.68[BRL] Brazil\n6,438.72 USD") == 32368.68
    assert modulo.transformar("Contract currency", "32,368.68[BRL] Brazil\n6,438.72 USD") == "BRL"
    assert modulo.transformar("Register the conclusion of contract", False) is False
    assert modulo.transformar("Amount", None) is None
    with pytest.raises(ValueError):
        modulo.transformar("Amount", "não reconhecido")


def test_preenchimento_preserva_cabecalhos_e_substitui_exemplos(tmp_path):
    origem, modelo, destino = [tmp_path / nome for nome in ("origem.xlsx", "modelo.xlsx", "destino.xlsx")]
    wb = Workbook()
    colunas = list(dict.fromkeys(modulo.MAPEAMENTO.values()))
    wb.active.append(colunas)
    dados = {"Contract Name": "=texto", "Contract Type": "Others\nLeasing",
             "Contract Period": "2026-01-01 ~ 2026-12-31", "Contract Amount": "1,234.56[BRL] Brazil",
             "Contract Expired": False}
    wb.active.append([dados.get(c) for c in colunas])
    wb.active.cell(2, colunas.index("Contract Name") + 1).data_type = "s"
    wb.save(origem)
    wb = Workbook()
    wb.active.append(list(modulo.MAPEAMENTO))
    wb.active.append(["Espelho sistema"])
    wb.active.append(["exemplo"])
    wb.active.append(["exemplo antigo"])
    wb.save(modelo)
    assert modulo.preencher_base_ideal(origem, modelo, destino) == 1
    wb = load_workbook(destino)
    assert wb.active.max_row == 2
    assert [c.value for c in wb.active[1]] == list(modulo.MAPEAMENTO)
    nomes = list(modulo.MAPEAMENTO)
    assert wb.active.cell(2, nomes.index("Amount") + 1).value == 1234.56
    celula = wb.active.cell(2, nomes.index("Contract name") + 1)
    assert celula.value == "=texto" and celula.data_type == "s"
    wb.close()
