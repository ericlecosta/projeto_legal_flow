"""
Integração robô + API: roda o fluxo real do robô (ideal_raw_RPA/src/pipeline.py), com o cliente
real da API e a consolidação real, falando com esta API pelo TestClient. Só o navegador é falso.
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

LINHAS = [
    {
        "Contract Number": "C2026814234",
        "Department of the person in charge": "LGESP GA Support Part - MAO",
        "Management Number": "C2026814234",
        "Counterparty": "Rio Negro Imóveis Ltda",
        "Contract Name": "Termination - Rental MAO",
        "Contract Type": "Leasing/Rental/Real Estate",
        "Progress State": "Approval Completed",
        "Contract Period": "2026-03-24 ~ 2026-04-18",
        "I requested a review of the contract.": "2026-04-17",
        "Review Completed": "2026-05-25",
        "Approval Completed": "2026-06-02",
        "Contract Amount": "BRL 9.240.61",
        "A person in charge of legal (team)": "Revisor Exemplo",
        "Review Completed Flag": True,
    },
    {
        "Contract Number": "C2026825327",
        "Department of the person in charge": "LGESP IT CNS Team - MAO",
        "Progress State": "Legal Review in Progress",
        "I requested a review of the contract.": "2026-07-28",
        "Contract Amount": "USD 11,145.04",
    },
]


def servicos(linhas, falhar_em=None):
    def etapa(nome, valor):
        def _acao(*_):
            if nome == falhar_em:
                raise RuntimeError(f"erro simulado em {nome}")
            return valor

        return _acao

    return Servicos(
        login=etapa("login", "page"),
        extrair_relatorio=etapa("relatorio", "relatorio_contratos.xlsx"),
        extrair_detalhes=etapa("detalhes", "contract_review_management.xlsx"),
        fechar=lambda page: None,
        ler_planilha=lambda caminho: linhas,
    )


def test_robo_grava_execucao_logs_e_contratos(client):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)
    handler = ApiLogHandler(cliente)
    logger = logging.getLogger("rpa_lms")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        resultado = executar_fluxo(servicos(LINHAS), cliente, trigger="scheduled", ao_fim_da_etapa=handler.flush)
    finally:
        logger.removeHandler(handler)

    assert resultado.sucesso
    assert resultado.envio == {"received": 2, "created": 2, "updated": 0}

    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert (detalhe["status"], detalhe["trigger"], detalhe["records"]) == ("success", "scheduled", 2)
    assert [s["status"] for s in detalhe["steps"]] == ["success"] * 4
    assert any("2 novo(s)" in log["message"] and log["level"] == "success" for log in detalhe["logs"])

    contratos = {c["contractNumber"]: c for c in client.get("/api/contracts/").json()["results"]}
    assert set(contratos) == {"C2026814234", "C2026825327"}
    imovel = contratos["C2026814234"]
    assert (imovel["periodStart"], imovel["periodEnd"]) == ("2026-03-24", "2026-04-18")
    assert (imovel["currency"], imovel["amount"]) == ("BRL", 9240.61)
    assert imovel["approvalCompletedAt"] == "2026-06-02"
    assert imovel["flags"]["reviewCompleted"] is True
    assert imovel["lastExecutionId"] == cliente.execution_id


def test_falha_do_robo_aparece_no_monitor(client):
    cliente = MonitorClient("http://testserver/api", TOKEN, session=client, timeout=None)

    resultado = executar_fluxo(servicos(LINHAS, falhar_em="relatorio"), cliente)

    assert resultado.status == "failed"
    detalhe = client.get(f"/api/executions/{cliente.execution_id}/").json()
    assert detalhe["status"] == "failed"
    assert [s["status"] for s in detalhe["steps"]] == ["success", "failed", "skipped", "skipped"]
    assert detalhe["error"]["title"] == "Falha ao baixar o relatório de contratos"
    assert detalhe["error"]["message"] == "erro simulado em relatorio"
    assert client.get("/api/contracts/summary/").json()["total"] == 0
