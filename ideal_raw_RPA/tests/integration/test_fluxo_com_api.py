"""
Integração do robô sem o LMS: o fluxo completo conversa por HTTP de verdade com uma API local
que imita o monitor, e os logs dos módulos do robô chegam à API pelo ApiLogHandler.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

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
        dados = json.dumps({"id": 42} if self.path == "/api/rpa/executions/" else {}).encode()
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


def servicos(extrair_detalhes=None):
    return Servicos(
        login=lambda: object(),
        extrair_relatorio=lambda page: "relatorio_contratos.xlsx",
        extrair_detalhes=extrair_detalhes or (lambda page, caminho: "contract_review_management.xlsx"),
        fechar=lambda page: None,
    )


def test_fluxo_completo_registra_etapas_e_logs_na_api(api):
    url, requisicoes = api
    cliente = MonitorClient(url, TOKEN)
    handler = ApiLogHandler(cliente)
    logger_rpa = logging.getLogger("rpa_lms")
    logger_rpa.addHandler(handler)
    logger_rpa.setLevel(logging.INFO)

    def extrair_detalhes(page, caminho_relatorio):
        logging.getLogger("rpa_lms.extract_contract").info("Processando 2 contratos")
        return "contract_review_management.xlsx"

    try:
        resultado = executar_fluxo(servicos(extrair_detalhes), cliente, ao_fim_da_etapa=handler.flush)
    finally:
        logger_rpa.removeHandler(handler)

    assert resultado.sucesso
    assert all(token == TOKEN for *_, token in requisicoes)

    caminhos = [(metodo, caminho) for metodo, caminho, *_ in requisicoes]
    assert caminhos[0] == ("POST", "/api/rpa/executions/")
    assert caminhos[-1] == ("POST", "/api/rpa/executions/42/finish/")
    for key, _ in ETAPAS:
        assert ("PATCH", f"/api/rpa/executions/42/steps/{key}/") in caminhos
    assert ("PUT", "/api/rpa/contracts/") not in caminhos

    mensagens = [
        log["message"] for _, caminho, corpo, _ in requisicoes if caminho.endswith("/logs/") for log in corpo["logs"]
    ]
    assert "Processando 2 contratos" in mensagens
    assert "Fluxo concluído com sucesso." in mensagens

    fim = requisicoes[-1][2]
    assert fim == {"status": "success", "records": None, "errorTitle": None, "errorMessage": None}


def test_token_errado_nao_impede_o_robo_de_terminar(api):
    url, requisicoes = api
    cliente = MonitorClient(url, "token-errado")

    resultado = executar_fluxo(servicos(), cliente)

    # A API recusou a abertura da execução: o robô segue sem reportar e termina normalmente.
    assert resultado.sucesso
    assert [caminho for _, caminho, *_ in requisicoes] == ["/api/rpa/executions/"]
