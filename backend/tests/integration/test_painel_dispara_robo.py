"""
Modo real: o botão do painel enfileira um pedido, o worker do robô reivindica e executa,
e o Interromper do painel chega ao worker pela rota /api/rpa/jobs/{id}/.
"""

from datetime import timedelta

import pytest

from app.models import RpaJob
from tests.constants import RPA_HEADERS

pytestmark = pytest.mark.integration

ETAPAS = [{"key": "lms_login", "label": "Login no LMS"}, {"key": "report_download", "label": "Download do relatório"}]


def pedir(client):
    resposta = client.post("/api/executions/", json={"flow": "login_capture"})
    assert resposta.status_code == 201
    return resposta.json()


def reivindicar(client):
    return client.post("/api/rpa/jobs/claim/", headers=RPA_HEADERS)


def test_painel_pede_worker_assume_e_robo_grava_na_mesma_execucao(client):
    pedido = pedir(client)
    assert (pedido["flow"], pedido["status"], pedido["trigger"], pedido["steps"]) == (
        "contract_extraction",
        "running",
        "manual",
        [],
    )
    assert "Aguardando o robô" in pedido["logs"][0]["message"]

    assert reivindicar(client).json() == {"executionId": pedido["id"]}
    assert reivindicar(client).status_code == 204  # o pedido só é entregue uma vez

    inicio = client.post(f"/api/rpa/executions/{pedido['id']}/start/", json={"steps": ETAPAS}, headers=RPA_HEADERS)
    assert inicio.json() == {"id": pedido["id"]}
    client.post(f"/api/rpa/executions/{pedido['id']}/finish/", json={"status": "success"}, headers=RPA_HEADERS)

    detalhe = client.get(f"/api/executions/{pedido['id']}/").json()
    assert detalhe["status"] == "success"
    assert [(s["key"], s["status"]) for s in detalhe["steps"]] == [
        ("lms_login", "skipped"),
        ("report_download", "skipped"),
    ]


def test_fila_vazia_responde_204_e_exige_token(client):
    assert reivindicar(client).status_code == 204
    assert client.post("/api/rpa/jobs/claim/").status_code == 401


def test_so_uma_execucao_por_vez(client):
    primeiro = pedir(client)
    segundo = client.post("/api/executions/", json={})
    assert segundo.status_code == 409
    assert str(primeiro["id"]) in segundo.json()["detail"]

    # Execuções disparadas fora do painel (docker compose run) também bloqueiam
    client.post(f"/api/executions/{primeiro['id']}/stop/")
    client.post("/api/rpa/executions/", json={"steps": ETAPAS}, headers=RPA_HEADERS)
    assert client.post("/api/executions/", json={}).status_code == 409


def test_interromper_pedido_na_fila_cancela_na_hora(client):
    pedido = pedir(client)
    assert client.post(f"/api/executions/{pedido['id']}/stop/").status_code == 202

    detalhe = client.get(f"/api/executions/{pedido['id']}/").json()
    assert detalhe["status"] == "failed"
    assert detalhe["error"]["title"] == "Execução interrompida"
    assert reivindicar(client).status_code == 204


def test_interromper_execucao_em_andamento_avisa_o_worker(client):
    pedido = pedir(client)
    reivindicar(client)
    assert client.get(f"/api/rpa/jobs/{pedido['id']}/", headers=RPA_HEADERS).json() == {"stopRequested": False}

    assert client.post(f"/api/executions/{pedido['id']}/stop/").status_code == 202
    assert client.get(f"/api/rpa/jobs/{pedido['id']}/", headers=RPA_HEADERS).json() == {"stopRequested": True}
    # Quem fecha a execução é o worker, depois de encerrar o robô
    assert client.get(f"/api/executions/{pedido['id']}/").json()["status"] == "running"


def test_interromper_execucao_de_fora_do_painel_responde_409(client):
    exec_id = client.post("/api/rpa/executions/", json={"steps": ETAPAS}, headers=RPA_HEADERS).json()["id"]
    assert client.post(f"/api/executions/{exec_id}/stop/").status_code == 409
    assert client.get(f"/api/rpa/jobs/{exec_id}/", headers=RPA_HEADERS).status_code == 404


def test_pedido_sem_worker_falha_depois_do_prazo(client, db, settings):
    pedido = pedir(client)
    job = db.query(RpaJob).one()
    job.requested_at -= timedelta(seconds=settings.rpa_claim_timeout_seconds + 1)
    db.commit()

    detalhe = client.get(f"/api/executions/{pedido['id']}/").json()
    assert detalhe["status"] == "failed"
    assert detalhe["error"]["title"] == "Robô indisponível"
    assert "rpa-worker" in detalhe["error"]["message"]
    assert reivindicar(client).status_code == 204
    assert pedir(client)["id"] != pedido["id"]  # libera um novo pedido


def test_sem_token_na_api_o_painel_avisa(client, settings):
    settings.rpa_api_token = ""
    resposta = client.post("/api/executions/", json={})
    assert resposta.status_code == 503
    assert "RPA_API_TOKEN" in resposta.json()["detail"]
