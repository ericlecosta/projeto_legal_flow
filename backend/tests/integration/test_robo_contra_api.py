"""
Integração robô + API: roda o fluxo real do robô (ideal_raw_RPA/src/pipeline.py), com o cliente
real da API, falando com esta API pelo TestClient. Só o navegador é falso.
"""

import logging
import sys
from pathlib import Path

import pytest

from tests.constants import TOKEN

pytestmark = pytest.mark.integration

RPA_DIR = Path(__file__).resolve().parents[3] / "ideal_raw_RPA"
if str(RPA_DIR) not in sys.path:
    sys.path.insert(0, str(RPA_DIR))

from src.pipeline import Servicos, executar_fluxo  # noqa: E402
from src.reporting import ApiLogHandler, MonitorClient  # noqa: E402


def servicos(falhar_em=None):
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
        extrair_detalhes=etapa("detalhes", "contract_review_management.xlsx"),
        fechar=lambda page: None,
    )


def test_robo_grava_execucao_etapas_e_logs(client):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)
    handler = ApiLogHandler(cliente)
    logger = logging.getLogger("rpa_lms")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        resultado = executar_fluxo(servicos(), cliente, trigger="scheduled", ao_fim_da_etapa=handler.flush)
    finally:
        logger.removeHandler(handler)

    assert resultado.sucesso
    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert (detalhe["flow"], detalhe["status"], detalhe["trigger"]) == ("contract_extraction", "success", "scheduled")
    assert [(s["key"], s["status"]) for s in detalhe["steps"]] == [
        ("lms_login", "success"),
        ("report_download", "success"),
        ("contract_details", "success"),
    ]
    mensagens = [log["message"] for log in detalhe["logs"]]
    assert "Etapa detalhes concluída" in mensagens
    assert any(log["level"] == "success" for log in detalhe["logs"])


def test_falha_do_robo_aparece_no_monitor(client):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)

    resultado = executar_fluxo(servicos(falhar_em="relatorio"), cliente)

    assert resultado.status == "failed"
    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert detalhe["status"] == "failed"
    assert [s["status"] for s in detalhe["steps"]] == ["success", "failed", "skipped"]
    assert detalhe["steps"][1]["durationSeconds"] is not None
    assert detalhe["error"]["title"] == "Falha ao baixar o relatório de contratos"
    assert detalhe["error"]["message"] == "erro simulado em relatorio"
