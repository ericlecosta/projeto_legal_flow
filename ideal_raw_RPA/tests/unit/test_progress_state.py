import runpy
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook


modulo = runpy.run_path(str(Path(__file__).parents[2] / "preencher_base_ideal.py"))


class ProgressStateTest(unittest.TestCase):
    def test_counterparty(self):
        transformar = modulo["transformar"]
        casos = {
            "ALDO AZEVEDO OLIVEIRA(20261015-024): SEM BRCODE": "ALDO AZEVEDO OLIVEIRA",
            "EMPRESA LTDA(60.902.939/0001-73)": "EMPRESA LTDA",
            "LG CNS Co., Ltd.(116-81-19477)": "LG CNS Co., Ltd.",
            "Empresa (Brasil)(12345678000190): Novo fornecedor": "Empresa (Brasil)",
            "Empresa (Brasil)": "Empresa (Brasil)",
            "Nome sem identificador": "Nome sem identificador",
            None: None,
            "": None,
        }
        for origem, esperado in casos.items():
            self.assertEqual(transformar("Counterparty", origem), esperado)

    def test_pessoa_responsavel(self):
        transformar = modulo["transformar"]
        self.assertEqual(transformar("The person in charge", "MARCELLE CUNHA(LGESP GA Support Part - MAO)"),
                         "MARCELLE CUNHA")
        self.assertEqual(transformar("The person in charge", " ANA SOUZA (Departamento) "), "ANA SOUZA")
        self.assertEqual(transformar("The person in charge", "IOMAR FALCAO"), "IOMAR FALCAO")
        self.assertIsNone(transformar("The person in charge", None))
        self.assertIsNone(transformar("The person in charge", ""))

    def test_reviewer(self):
        transformar = modulo["transformar"]
        for nome in ("BARBARA LUSTOSA", "DYDRA ANDRADE"):
            self.assertEqual(transformar("Reviewer", f"[Main manager]{nome}\nLegal Team Leader Approval Required"), nome)
            self.assertEqual(transformar("Reviewer", nome), nome)
        self.assertEqual(transformar("Reviewer", "Unassigned"), "Unassigned")
        for valor in (None, "", "   ", "[Main manager]\nLegal Team Leader Approval Required",
                      "Responsável não definido\nAguardando atribuição"):
            self.assertEqual(transformar("Reviewer", valor), valor)

    def test_regras_na_planilha(self):
        with tempfile.TemporaryDirectory() as pasta:
            origem, modelo, destino = [Path(pasta) / nome for nome in
                                       ("origem.xlsx", "modelo.xlsx", "destino.xlsx")]
            colunas = list(dict.fromkeys([*modulo["MAPEAMENTO"].values(), "Effective Contract"]))
            estados = modulo["STATUS_PROGRESS_STATE"]
            wb = Workbook()
            wb.active.append(colunas)
            for estado in [*estados, None, "Estado desconhecido"]:
                dados = dict.fromkeys(colunas, "2026-10-15 13:55:58")
                dados.update({"Management Number": estado or "sem estado",
                              "Progress State": f"{estado}\nDetalhes do LMS" if estado else None,
                              "Contract Period": "2026-01-01 12:34:56 ~ 2026-12-31 23:59:59",
                              "Contract Expired": False,
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
                for coluna in wb.active.iter_cols():
                    largura = max((len(linha) for celula in coluna if celula.value is not None
                                   for linha in str(celula.value).splitlines()), default=0)
                    self.assertEqual(wb.active.column_dimensions[coluna[0].column_letter].width,
                                     max(15, min(largura + 2, 45)))
                    for celula in coluna:
                        self.assertFalse(celula.alignment.wrap_text)
                        self.assertEqual(celula.alignment.vertical, "top")
                self.assertEqual([r["Contract number"] for r in registros],
                                 esperados + ["sem estado", "Estado desconhecido"])
                for estado in ("Legal Comments Provided", "Request for Consent Rejected"):
                    registro = next(r for r in registros if r["Contract number"] == estado)
                    self.assertEqual(registro["Start date"], "2026-01-01")
                    self.assertEqual(registro["End date"], "2026-12-31")
                    self.assertEqual(registro["Request Date"], "2026-10-15")
                for registro in registros:
                    status = estados.get(registro["Contract number"])
                    for campo in modulo["CAMPOS_DATA"]:
                        if status == 1 and campo not in modulo["DATAS_SEMPRE_PREENCHIDAS"]:
                            self.assertIsNone(registro[campo], (registro, campo))
                        else:
                            self.assertIsNotNone(registro[campo], (registro, campo))
                            self.assertRegex(registro[campo], r"^\d{4}-\d{2}-\d{2}$")
                    self.assertEqual(registro["Amount"], 100)
                    self.assertEqual(registro["Contract currency"], "BRL")
            finally:
                wb.close()

    def test_identificacao(self):
        identificar = modulo["status_progress_state"]
        for estado, status in modulo["STATUS_PROGRESS_STATE"].items():
            self.assertEqual(identificar(estado), status)
            self.assertEqual(identificar(f"  {estado.upper()}\nDetalhes"), status)
            self.assertEqual(modulo["transformar"]("Progress State", f"  {estado.upper()}\nDetalhes"), estado)
            self.assertEqual(modulo["transformar"]("Progress State", estado), estado)
        self.assertIsNone(identificar("Biz-Dropper"))
        self.assertIsNone(identificar(None))
        self.assertEqual(modulo["transformar"]("Progress State", "Biz-Dropper"), "Biz-Dropper")
        self.assertIsNone(modulo["transformar"]("Progress State", None))

    def test_conclusao_contrato(self):
        from datetime import datetime

        concluir = modulo["conclusao_contrato"]
        data = datetime(2026, 10, 8, 13, 55, 58)
        for expirado in (True, "VERDADEIRO", "true"):
            self.assertEqual(concluir(expirado, data), "Expirado")
        for expirado in (False, "FALSO", "false"):
            self.assertEqual(concluir(expirado, data), "2026-10-08")
            self.assertEqual(concluir(expirado, "2026-10-08 13:55:58"), "2026-10-08")
            for vazio in (None, "", "sem data", False):
                self.assertIsNone(concluir(expirado, vazio))
        self.assertIsNone(concluir(None, data))

    def test_datas_sem_horario(self):
        from datetime import date, datetime

        for campo in modulo["CAMPOS_DATA"] - {"Start date", "End date"}:
            for valor in (datetime(2026, 10, 8, 13, 55, 58), date(2026, 10, 8),
                          "2026-10-08 13:55:58", "2026-10-08T13:55:58",
                          "08/10/2026 13:55:58", "2026-10-08"):
                self.assertEqual(modulo["transformar"](campo, valor), "2026-10-08")
            self.assertIsNone(modulo["transformar"](campo, None))
        self.assertEqual(modulo["somente_data"]("Expirado"), "Expirado")


if __name__ == "__main__":
    unittest.main()
