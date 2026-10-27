"""
Integração robô + API: roda o fluxo real do robô (ideal_raw_RPA/src/pipeline.py), com o cliente
real da API, falando com esta API pelo TestClient. Só o navegador é falso: a "extração" devolve a
planilha de exemplo (docs/planilha_de_dados), e o tratamento da Base Ideal e o envio são os de verdade.
"""

import logging
import shutil
import sys
from pathlib import Path

import pytest

from tests.constants import RPA_HEADERS, TOKEN

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[3]
RPA_DIR = ROOT / "ideal_raw_RPA"
EXTRACAO_EXEMPLO = ROOT / "docs" / "planilha_de_dados" / "contract_review_management.xlsx"
if str(RPA_DIR) not in sys.path:
    sys.path.insert(0, str(RPA_DIR))

from src.base_ideal import ler_registros  # noqa: E402
from src.pipeline import Servicos, executar_fluxo  # noqa: E402
from src.reporting import ApiLogHandler, MonitorClient  # noqa: E402


@pytest.fixture
def extracao(tmp_path):
    """Cópia da extração de exemplo numa pasta temporária (o tratamento grava base_ideal.xlsx ao lado)."""
    destino = tmp_path / "contract_review_management.xlsx"
    shutil.copy(EXTRACAO_EXEMPLO, destino)
    return str(destino)


def servicos(extracao, falhar_em=None):
    def etapa(nome, valor):
        def _acao(*_):
            if nome == falhar_em:
                raise RuntimeError(f"erro simulado em {nome}")
            logging.getLogger(f"rpa_lms.{nome}").info("Etapa %s concluída", nome)
            return valor

        return _acao

    return Servicos(
        login=etapa("login", "page"),
        extrair_relatorio=etapa("relatorio", "relatorio_contratos.xlsx"),
        extrair_detalhes=etapa("detalhes", extracao),
        fechar=lambda page: None,
    )


def rodar_com_logs(cliente, svc, **kwargs):
    handler = ApiLogHandler(cliente)
    logger = logging.getLogger("rpa_lms")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        return executar_fluxo(svc, cliente, ao_fim_da_etapa=handler.flush, **kwargs)
    finally:
        logger.removeHandler(handler)


ETAPAS_OK = [
    ("lms_login", "success"),
    ("report_download", "success"),
    ("contract_details", "success"),
    ("base_ideal", "success"),
    ("data_upload", "success"),
]


def test_robo_grava_execucao_etapas_e_logs(client, extracao):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)
    resultado = rodar_com_logs(cliente, servicos(extracao), trigger="scheduled")

    assert resultado.sucesso, resultado.erro_mensagem
    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert (detalhe["flow"], detalhe["status"], detalhe["trigger"]) == ("contract_extraction", "success", "scheduled")
    assert [(s["key"], s["status"]) for s in detalhe["steps"]] == ETAPAS_OK
    assert detalhe["records"] == resultado.registros > 0
    mensagens = [log["message"] for log in detalhe["logs"]]
    assert "Etapa detalhes concluída" in mensagens
    assert any(m.startswith("Base Ideal tratada:") for m in mensagens)
    assert any(log["level"] == "success" for log in detalhe["logs"])


def test_botao_do_painel_ate_a_tela_de_contratos(client, extracao):
    """O painel pede, o worker assume (RPA_EXECUTION_ID), o robô roda e a base aparece em /api/contracts/."""
    # Mesmo corpo que o botão "Executar Fluxo Agora" envia; no modo real o fluxo é sempre a extração
    pedido = client.post("/api/executions/", json={"flow": "login_capture", "headless": True}).json()
    execution_id = client.post("/api/rpa/jobs/claim/", headers=RPA_HEADERS).json()["executionId"]
    assert execution_id == pedido["id"]

    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None, execution_id=execution_id)
    resultado = rodar_com_logs(cliente, servicos(extracao))
    assert resultado.sucesso, resultado.erro_mensagem

    detalhe = client.get(f"/api/executions/{pedido['id']}/").json()
    assert (detalhe["status"], detalhe["trigger"]) == ("success", "manual")
    assert [(s["key"], s["status"]) for s in detalhe["steps"]] == ETAPAS_OK

    esperados = ler_registros(extracao)
    resumo = client.get("/api/contracts/summary/").json()
    assert resumo["total"] == len(esperados) == detalhe["records"]
    assert resumo["lastExecutionId"] == pedido["id"]
    estados = {item["progressState"] for item in resumo["byProgressState"]}
    assert not estados & {"Biz-Holding", "Signed Contract Registered"}

    primeiro = esperados[0]
    pagina = client.get("/api/contracts/", params={"search": primeiro["Contract number"]}).json()
    [contrato] = pagina["results"]
    assert contrato["counterparty"] == primeiro["Counterparty"]
    assert contrato["amount"] == primeiro["Amount"]
    assert contrato["currency"] == primeiro["Contract currency"]
    assert contrato["periodStart"] == primeiro["Start date"]
    assert contrato["raw"]["Main Contract Type"] == primeiro["Main Contract Type"]


def test_nova_execucao_atualiza_os_contratos_sem_duplicar(client, extracao):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)
    executar_fluxo(servicos(extracao), cliente)
    total = client.get("/api/contracts/summary/").json()["total"]

    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)
    assert executar_fluxo(servicos(extracao), cliente).sucesso
    resumo = client.get("/api/contracts/summary/").json()
    assert resumo["total"] == total
    assert resumo["lastExecutionId"] == cliente.execution_id


def test_falha_do_robo_aparece_no_monitor(client, extracao):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)

    resultado = executar_fluxo(servicos(extracao, falhar_em="relatorio"), cliente)

    assert resultado.status == "failed"
    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert detalhe["status"] == "failed"
    assert [s["status"] for s in detalhe["steps"]] == ["success", "failed", "skipped", "skipped", "skipped"]
    assert detalhe["steps"][1]["durationSeconds"] is not None
    assert detalhe["error"]["title"] == "Falha ao baixar o relatório de contratos"
    assert detalhe["error"]["message"] == "erro simulado em relatorio"
    assert client.get("/api/contracts/summary/").json()["total"] == 0
