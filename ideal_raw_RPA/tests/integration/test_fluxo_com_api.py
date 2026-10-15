"""
Integração do robô sem o LMS: o fluxo completo grava uma planilha real (no formato do
contract_review_management.xlsx), lê de volta, consolida e conversa por HTTP de verdade com uma
API local que imita o monitor.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd
import pytest

from src.extract_contract import COLUNAS_FINAIS
from src.pipeline import ETAPAS, Servicos, executar_fluxo
from src.reporting import ApiLogHandler, MonitorClient

pytestmark = pytest.mark.integration

TOKEN = "token-de-teste"


class ApiFalsa(BaseHTTPRequestHandler):
    requisicoes: list = []

    def _responder(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        self.requisicoes.append((self.command, self.path, corpo, self.headers.get("X-RPA-Token")))
        if self.headers.get("X-RPA-Token") != TOKEN:
            self.send_response(401)
            self.end_headers()
            return
        resposta = {"id": 42} if self.path == "/api/rpa/executions/" else {}
        if self.path == "/api/rpa/contracts/":
            resposta = {"received": len(corpo["contracts"]), "created": len(corpo["contracts"]), "updated": 0}
        dados = json.dumps(resposta).encode()
        self.send_response(201 if self.command == "POST" else 200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    do_POST = do_PATCH = do_PUT = _responder

    def log_message(self, *args):  # silencia o log padrão do http.server
        pass


@pytest.fixture
def api():
    ApiFalsa.requisicoes = []
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), ApiFalsa)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{servidor.server_port}/api", ApiFalsa.requisicoes
    servidor.shutdown()


def escrever_planilha(caminho):
    linhas = []
    for numero, estado in [("C2026000001", "Legal Review in Progress"), ("C2026000002", "Effective Contract")]:
        linha = {coluna: "" for coluna in COLUNAS_FINAIS}
        linha.update(
            {
                "Contract Number": numero,
                "Management Number": numero,
                "Department of the person in charge": "LGESP GA Support Part - MAO",
                "Counterparty": "ACME LTDA",
                "Progress State": estado,
                "Contract Period": "2026-03-24 ~ 2027-03-23",
                "I requested a review of the contract.": "2026-04-17",
                "Contract Amount": "BRL 9.240.61",
                "Review Completed Flag": True,
            }
        )
        linhas.append(linha)
    pd.DataFrame(linhas, columns=COLUNAS_FINAIS).to_excel(caminho, index=False)
    return str(caminho)


def test_fluxo_completo_registra_execucao_e_contratos_na_api(api, tmp_path):
    url, requisicoes = api
    cliente = MonitorClient(url, TOKEN)
    handler = ApiLogHandler(cliente)
    logger_rpa = logging.getLogger("rpa_lms")
    logger_rpa.addHandler(handler)
    logger_rpa.setLevel(logging.INFO)

    def extrair_detalhes(page, caminho_relatorio):
        logging.getLogger("rpa_lms.extract_contract").info("Processando 2 contratos")
        return escrever_planilha(tmp_path / "contract_review_management.xlsx")

    servicos = Servicos(
        login=lambda: object(),
        extrair_relatorio=lambda page: str(tmp_path / "relatorio_contratos.xlsx"),
        extrair_detalhes=extrair_detalhes,
        fechar=lambda page: None,
    )

    try:
        resultado = executar_fluxo(servicos, cliente, ao_fim_da_etapa=handler.flush)
    finally:
        logger_rpa.removeHandler(handler)

    assert resultado.sucesso
    assert resultado.registros == 2
    assert resultado.envio == {"received": 2, "created": 2, "updated": 0}
    assert all(token == TOKEN for *_, token in requisicoes)

    caminhos = [(metodo, caminho) for metodo, caminho, *_ in requisicoes]
    assert caminhos[0] == ("POST", "/api/rpa/executions/")
    assert caminhos[-1] == ("POST", "/api/rpa/executions/42/finish/")
    for key, _ in ETAPAS:
        assert ("PATCH", f"/api/rpa/executions/42/steps/{key}/") in caminhos

    contratos = next(corpo for metodo, caminho, corpo, _ in requisicoes if caminho == "/api/rpa/contracts/")
    assert contratos["executionId"] == 42
    primeiro = contratos["contracts"][0]
    assert primeiro["contractNumber"] == "C2026000001"
    assert primeiro["reviewRequestedAt"] == "2026-04-17"
    assert (primeiro["currency"], primeiro["amount"]) == ("BRL", 9240.61)
    assert primeiro["flags"]["reviewCompleted"] is True

    mensagens = [
        log["message"] for _, caminho, corpo, _ in requisicoes if caminho.endswith("/logs/") for log in corpo["logs"]
    ]
    assert "Processando 2 contratos" in mensagens
    assert any("2 novo(s)" in m for m in mensagens)

    fim = requisicoes[-1][2]
    assert fim == {"status": "success", "records": 2, "errorTitle": None, "errorMessage": None}


def test_token_errado_nao_impede_o_robo_de_terminar(api, tmp_path):
    url, requisicoes = api
    cliente = MonitorClient(url, "token-errado")
    servicos = Servicos(
        login=lambda: object(),
        extrair_relatorio=lambda page: "relatorio.xlsx",
        extrair_detalhes=lambda page, caminho: escrever_planilha(tmp_path / "detalhes.xlsx"),
        fechar=lambda page: None,
    )

    resultado = executar_fluxo(servicos, cliente)

    # A API recusou o início, então o envio também é recusado: o robô termina com falha no envio, sem exceção.
    assert resultado.status == "failed"
    assert resultado.erro_titulo == "Falha ao enviar os contratos para a base"
    assert [caminho for _, caminho, *_ in requisicoes] == ["/api/rpa/executions/", "/api/rpa/contracts/"]
