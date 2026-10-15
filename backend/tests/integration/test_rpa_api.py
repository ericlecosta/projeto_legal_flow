"""
Integração pela API HTTP: o robô registra uma execução e grava contratos pelas rotas /api/rpa/,
e o front lê o resultado pelas rotas públicas (/api/executions/, /api/contracts/, /api/overview/).
"""

import pytest

from tests.constants import RPA_HEADERS

pytestmark = pytest.mark.integration

ETAPAS = [
    {"key": "lms_login", "label": "Login no LMS"},
    {"key": "report_download", "label": "Download do relatório"},
    {"key": "contract_details", "label": "Extração dos contratos"},
    {"key": "data_upload", "label": "Envio para a base"},
]

CONTRATO = {
    "contractNumber": "C2026825327",
    "counterparty": "ACME TELECOM LTDA",
    "contractName": "Support Contract Renew for L4 Switches",
    "contractType": "General Services/Contracting",
    "department": "LGESP IT CNS Team - MAO",
    "progressState": "Effective Contract",
    "legalReviewer": "Revisor Exemplo",
    "periodStart": "2026-12-01",
    "periodEnd": "2027-11-30",
    "reviewRequestedAt": "2026-07-28",
    "effectiveAt": "2026-08-19",
    "currency": "USD",
    "amount": 11145.04,
    "flags": {"reviewCompleted": True},
    "raw": {"Contract Amount": "USD 11,145.04"},
}


def iniciar(client, **extra):
    resposta = client.post("/api/rpa/executions/", json={"steps": ETAPAS, **extra}, headers=RPA_HEADERS)
    assert resposta.status_code == 201
    return resposta.json()["id"]


def test_execucao_real_completa_aparece_no_detalhe_e_nos_contratos(client):
    exec_id = iniciar(client, trigger="scheduled")

    for etapa in ETAPAS:
        r = client.patch(
            f"/api/rpa/executions/{exec_id}/steps/{etapa['key']}/", json={"status": "running"}, headers=RPA_HEADERS
        )
        assert r.status_code == 200
        r = client.patch(
            f"/api/rpa/executions/{exec_id}/steps/{etapa['key']}/",
            json={"status": "success", "durationSeconds": 3.2},
            headers=RPA_HEADERS,
        )
        assert r.json() == {"status": "success"}

    logs = {"logs": [{"timestamp": "2026-10-15T09:00:00-04:00", "level": "success", "message": "Login concluído"}]}
    assert client.post(f"/api/rpa/executions/{exec_id}/logs/", json=logs, headers=RPA_HEADERS).json() == {"received": 1}

    upload = client.put(
        "/api/rpa/contracts/", json={"executionId": exec_id, "contracts": [CONTRATO]}, headers=RPA_HEADERS
    )
    assert upload.json() == {"received": 1, "created": 1, "updated": 0}

    fim = client.post(
        f"/api/rpa/executions/{exec_id}/finish/", json={"status": "success", "records": 1}, headers=RPA_HEADERS
    )
    assert fim.json() == {"status": "success"}

    detalhe = client.get(f"/api/executions/{exec_id}/").json()
    assert (detalhe["flow"], detalhe["status"], detalhe["trigger"], detalhe["records"]) == (
        "contract_extraction",
        "success",
        "scheduled",
        1,
    )
    assert [(s["key"], s["status"], s["durationSeconds"]) for s in detalhe["steps"]] == [
        (e["key"], "success", 3.2) for e in ETAPAS
    ]
    assert detalhe["logs"][0]["message"] == "Login concluído"
    assert detalhe["error"] is None

    lista = client.get("/api/executions/", params={"flow": "contract_extraction"}).json()
    assert [e["id"] for e in lista["results"]] == [exec_id]

    contratos = client.get("/api/contracts/").json()
    assert contratos["count"] == 1
    item = contratos["results"][0]
    assert item["contractNumber"] == "C2026825327"
    assert item["lastExecutionId"] == exec_id
    assert (item["periodStart"], item["amount"], item["flags"]) == ("2026-12-01", 11145.04, {"reviewCompleted": True})

    resumo = client.get("/api/contracts/summary/").json()
    assert resumo["total"] == 1
    assert resumo["byProgressState"] == [{"progressState": "Effective Contract", "count": 1}]
    assert resumo["lastExecutionId"] == exec_id

    overview = client.get("/api/overview/").json()
    assert (overview["totalExecutions"], overview["succeeded"], overview["capturedRecords"]) == (1, 1, 1)


def test_execucao_com_falha_mostra_o_erro_no_detalhe(client):
    exec_id = iniciar(client)
    client.patch(f"/api/rpa/executions/{exec_id}/steps/lms_login/", json={"status": "running"}, headers=RPA_HEADERS)
    client.post(
        f"/api/rpa/executions/{exec_id}/finish/",
        json={"status": "failed", "errorTitle": "Falha no login do LMS", "errorMessage": "OTP recusado"},
        headers=RPA_HEADERS,
    )

    detalhe = client.get(f"/api/executions/{exec_id}/").json()
    assert detalhe["status"] == "failed"
    assert [s["status"] for s in detalhe["steps"]] == ["failed", "skipped", "skipped", "skipped"]
    assert detalhe["error"] == {"title": "Falha no login do LMS", "message": "OTP recusado", "screenshotUrl": None}


def test_reenvio_de_contratos_atualiza_sem_duplicar(client):
    client.put("/api/rpa/contracts/", json={"contracts": [CONTRATO]}, headers=RPA_HEADERS)
    novo_estado = {**CONTRATO, "progressState": "Contract Expired"}
    resposta = client.put("/api/rpa/contracts/", json={"contracts": [novo_estado]}, headers=RPA_HEADERS).json()

    assert resposta == {"received": 1, "created": 0, "updated": 1}
    lista = client.get("/api/contracts/", params={"progress_state": "Contract Expired"}).json()
    assert lista["count"] == 1


def test_busca_de_contratos_pela_api(client):
    client.put(
        "/api/rpa/contracts/",
        json={"contracts": [CONTRATO, {**CONTRATO, "contractNumber": "C2", "counterparty": "Norte Tech"}]},
        headers=RPA_HEADERS,
    )
    assert client.get("/api/contracts/", params={"search": "norte"}).json()["count"] == 1
    assert client.get("/api/contracts/", params={"page_size": 1, "page": 2}).json()["count"] == 2


@pytest.mark.parametrize(
    "metodo, caminho",
    [("post", "/api/rpa/executions/"), ("put", "/api/rpa/contracts/"), ("post", "/api/rpa/executions/1/finish/")],
)
def test_rotas_do_robo_exigem_token(client, metodo, caminho):
    resposta = getattr(client, metodo)(caminho, json={}, headers={"X-RPA-Token": "errado"})
    assert resposta.status_code == 401
    assert getattr(client, metodo)(caminho, json={}).status_code == 401


def test_rotas_do_robo_desativadas_sem_token_na_api(client, settings):
    settings.rpa_api_token = ""
    assert client.post("/api/rpa/executions/", json={}, headers=RPA_HEADERS).status_code == 503


def test_erros_de_execucao(client):
    assert client.post("/api/rpa/executions/999/logs/", json={"logs": []}, headers=RPA_HEADERS).status_code == 404
    exec_id = iniciar(client)
    etapa_invalida = client.patch(
        f"/api/rpa/executions/{exec_id}/steps/xpto/", json={"status": "running"}, headers=RPA_HEADERS
    )
    assert etapa_invalida.status_code == 404
    client.post(f"/api/rpa/executions/{exec_id}/finish/", json={"status": "success"}, headers=RPA_HEADERS)
    fechada = client.post(f"/api/rpa/executions/{exec_id}/logs/", json={"logs": []}, headers=RPA_HEADERS)
    assert fechada.status_code == 409


def test_payload_invalido_responde_422(client):
    resposta = client.put(
        "/api/rpa/contracts/",
        json={"contracts": [{"contractNumber": "C1", "reviewRequestedAt": "ontem"}]},
        headers=RPA_HEADERS,
    )
    assert resposta.status_code == 422


def test_health(client):
    assert client.get("/api/health/").json() == {"status": "ok", "database": "ok"}
