from unittest.mock import Mock, patch

import pandas as pd
import pytest
from openpyxl import load_workbook

from src.extract_contract.extract_contract_service import ExtractContractError, extrair_contract_review_management


def relatorio(tmp_path):
    origem = tmp_path / "relatorio.xlsx"
    pd.DataFrame([
        {"Contract Number": "C1", "Department of the person in charge": "MAO"},
        {"Contract Number": "C2", "Department of the person in charge": "MAO"},
    ]).to_excel(origem, index=False)
    return origem


def test_continua_e_salva_pendencias(tmp_path):
    origem = relatorio(tmp_path)
    pendencias = []
    pagina = Mock()
    with patch("src.extract_contract.extract_contract_service._abrir_contrato_via_busca", side_effect=[None, pagina]), \
         patch("src.extract_contract.extract_contract_service._coletar_dados_contrato", return_value={"Management Number": "C2"}):
        destino = extrair_contract_review_management(Mock(), str(origem), pendencias=pendencias)
    assert pd.read_excel(destino)["Contract Number"].tolist() == ["C2"]
    assert [item["Contract Number"] for item in pendencias] == ["C1"]
    pagina.close.assert_called_once()
    wb = load_workbook(tmp_path / "Pendencias contratos.xlsx")
    assert wb.active.cell(2, 1).value == "C1"
    wb.close()


def test_erro_inesperado_interrompe_extracao(tmp_path):
    origem = relatorio(tmp_path)
    with patch("src.extract_contract.extract_contract_service._abrir_contrato_via_busca", side_effect=RuntimeError("falha de rede")):
        with pytest.raises(ExtractContractError, match="falha de rede"):
            extrair_contract_review_management(Mock(), str(origem), pendencias=[])
