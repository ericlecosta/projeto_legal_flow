import runpy
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook


modulo = runpy.run_path(str(Path(__file__).parents[2] / "preencher_base_ideal.py"))


class ProgressStateTest(unittest.TestCase):
    def test_regras_na_planilha(self):
        with tempfile.TemporaryDirectory() as pasta:
            origem, modelo, destino = [Path(pasta) / nome for nome in
                                       ("origem.xlsx", "modelo.xlsx", "destino.xlsx")]
            colunas = list(dict.fromkeys(modulo["MAPEAMENTO"].values()))
            estados = modulo["STATUS_PROGRESS_STATE"]
            wb = Workbook()
            wb.active.append(colunas)
            for estado in [*estados, None, "Estado desconhecido"]:
                dados = dict.fromkeys(colunas, "2026-10-15")
                dados.update({"Management Number": estado or "sem estado",
                              "Progress State": f"{estado}\nDetalhes do LMS" if estado else None,
                              "Contract Period": "2026-01-01 ~ 2026-12-31",
                              "Contract Amount": "100.00[BRL]"})
                wb.active.append([dados[c] for c in colunas])
            wb.save(origem)
            wb.close()
            wb = Workbook()
            wb.active.append(list(modulo["MAPEAMENTO"]))
            wb.save(modelo)
            wb.close()
            quantidade = modulo["preencher_base_ideal"](origem, modelo, destino)
            wb = load_workbook(destino)
            try:
                nomes = list(modulo["MAPEAMENTO"])
                registros = [dict(zip(nomes, r)) for r in
                             wb.active.iter_rows(min_row=2, values_only=True)]
                esperados = [e for e, status in estados.items() if status != 2]
                self.assertEqual(quantidade, len(esperados) + 2)
                self.assertEqual(wb.active.max_row, quantidade + 1)
                self.assertEqual([r["Contract number"] for r in registros],
                                 esperados + ["sem estado", "Estado desconhecido"])
                for registro in registros:
                    status = estados.get(registro["Contract number"])
                    for campo in modulo["CAMPOS_DATA"]:
                        if status == 1:
                            self.assertIsNone(registro[campo], (registro, campo))
                        else:
                            self.assertIsNotNone(registro[campo], (registro, campo))
                    self.assertEqual(registro["Amount"], 100)
                    self.assertEqual(registro["Contract currency"], "BRL")
            finally:
                wb.close()

    def test_identificacao(self):
        identificar = modulo["status_progress_state"]
        for estado, status in modulo["STATUS_PROGRESS_STATE"].items():
            self.assertEqual(identificar(estado), status)
            self.assertEqual(identificar(f"  {estado.upper()}\nDetalhes"), status)
        self.assertIsNone(identificar("Biz-Dropper"))
        self.assertIsNone(identificar(None))


if __name__ == "__main__":
    unittest.main()
