import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from openpyxl import load_workbook

from main import salvar_pendencias
from src.extract_contract.extract_contract_service import (
    ExtractContractError,
    extrair_contract_review_management,
)


class TestPendencias(unittest.TestCase):
    def test_continua_apos_busca_sem_resultado_e_registra_pendencia(self):
        with tempfile.TemporaryDirectory() as diretorio:
            pasta = Path(diretorio)
            origem = pasta / "relatorio.xlsx"
            pd.DataFrame([
                {"Contract Number": "C1", "Department of the person in charge": "MAO"},
                {"Contract Number": "C2", "Department of the person in charge": "MAO"},
            ]).to_excel(origem, index=False)
            pagina = Mock()
            pendencias = []
            with patch("src.extract_contract.extract_contract_service._abrir_contrato_via_busca", side_effect=[None, pagina]), \
                 patch("src.extract_contract.extract_contract_service._coletar_dados_contrato", return_value={"Management Number": "C2"}):
                detalhes = extrair_contract_review_management(Mock(), str(origem), pendencias=pendencias)
            linhas = pd.read_excel(detalhes)
            self.assertEqual(linhas["Contract Number"].tolist(), ["C2"])
            self.assertEqual([item["Contract Number"] for item in pendencias], ["C1"])
            pagina.close.assert_called_once()

            destino = pasta / "Pendencias.xlsx"
            salvar_pendencias(pendencias, destino)
            wb = load_workbook(destino)
            self.assertEqual(wb.active.cell(2, 1).value, "C1")
            wb.close()
            salvar_pendencias([], destino)
            wb = load_workbook(destino)
            self.assertEqual(wb.active.max_row, 1)
            wb.close()

    def test_erro_inesperado_interrompe_extracao(self):
        with tempfile.TemporaryDirectory() as diretorio:
            origem = Path(diretorio) / "relatorio.xlsx"
            pd.DataFrame([{"Contract Number": "C1", "Department of the person in charge": "MAO"}]).to_excel(origem, index=False)
            with patch("src.extract_contract.extract_contract_service._abrir_contrato_via_busca", side_effect=RuntimeError("falha de rede")):
                with self.assertRaisesRegex(ExtractContractError, "falha de rede"):
                    extrair_contract_review_management(Mock(), str(origem), pendencias=[])


if __name__ == "__main__":
    unittest.main()
