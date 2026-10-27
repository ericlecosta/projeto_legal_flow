import logging

import pytest

from src.reporting import ApiLogHandler, MonitorClient, nivel_api


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data
        self.content = b"x" if data is not None else b""
        self.text = str(data)

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, respostas=None, erro=None):
        self.chamadas = []
        self.respostas = list(respostas or [])
        self.erro = erro

    def request(self, method, url, json=None, headers=None, timeout=None):
        self.chamadas.append({"method": method, "url": url, "json": json, "headers": headers})
        if self.erro:
            raise self.erro
        return self.respostas.pop(0) if self.respostas else FakeResponse(200, {})


def cliente_com(respostas=None, erro=None):
    session = FakeSession(respostas, erro)
    return MonitorClient("http://api/api/", "segredo", session=session), session


def test_cliente_sem_url_fica_desativado_e_nao_chama_nada():
    session = FakeSession()
    cliente = MonitorClient(None, session=session)
    assert not cliente.ativo
    assert cliente.iniciar_execucao("contract_extraction", "manual", [("lms_login", "Login")]) is None
    assert cliente.enviar_contratos([{"contractNumber": "C1"}]) is None
    assert session.chamadas == []


def test_iniciar_execucao_envia_etapas_e_guarda_o_id():
    cliente, session = cliente_com([FakeResponse(201, {"id": 7})])
    assert cliente.iniciar_execucao("contract_extraction", "scheduled", [("lms_login", "Login no LMS")]) == 7

    chamada = session.chamadas[0]
    assert chamada["method"] == "POST"
    assert chamada["url"] == "http://api/api/rpa/executions/"
    assert chamada["headers"] == {"X-RPA-Token": "segredo"}
    assert chamada["json"] == {
        "flow": "contract_extraction",
        "trigger": "scheduled",
        "steps": [{"key": "lms_login", "label": "Login no LMS"}],
    }


def test_chamadas_da_execucao_usam_o_id_recebido():
    cliente, session = cliente_com([FakeResponse(201, {"id": 3})])
    cliente.iniciar_execucao("contract_extraction", "manual", [])
    cliente.atualizar_etapa("lms_login", "success", 12.345)
    cliente.enviar_logs([{"timestamp": "t", "level": "info", "message": "m"}])
    cliente.finalizar_execucao("success", registros=5)

    urls = [(c["method"], c["url"]) for c in session.chamadas[1:]]
    assert urls == [
        ("PATCH", "http://api/api/rpa/executions/3/steps/lms_login/"),
        ("POST", "http://api/api/rpa/executions/3/logs/"),
        ("POST", "http://api/api/rpa/executions/3/finish/"),
    ]
    assert session.chamadas[1]["json"] == {"status": "success", "durationSeconds": 12.3}
    assert session.chamadas[3]["json"]["records"] == 5


def test_sem_execucao_iniciada_nao_reporta_etapas_nem_logs():
    cliente, session = cliente_com()
    cliente.atualizar_etapa("lms_login", "running")
    cliente.enviar_logs([{"message": "x"}])
    cliente.finalizar_execucao("failed")
    assert session.chamadas == []


def test_erro_http_vira_none_e_aviso(caplog):
    cliente, _ = cliente_com([FakeResponse(403, {"detail": "token inválido"})])
    with caplog.at_level(logging.WARNING, logger="rpa_monitor"):
        assert cliente.iniciar_execucao("contract_extraction", "manual", []) is None
    assert "403" in caplog.text


def test_falha_de_rede_nao_derruba_o_robo(caplog):
    cliente, _ = cliente_com(erro=ConnectionError("recusado"))
    with caplog.at_level(logging.WARNING, logger="rpa_monitor"):
        assert cliente.enviar_contratos([]) is None
    assert "indisponível" in caplog.text


def test_enviar_contratos_inclui_a_execucao():
    cliente, session = cliente_com([FakeResponse(201, {"id": 9}), FakeResponse(200, {"received": 1})])
    cliente.iniciar_execucao("contract_extraction", "manual", [])
    assert cliente.enviar_contratos([{"contractNumber": "C1"}]) == {"received": 1}
    assert session.chamadas[1]["json"] == {"executionId": 9, "contracts": [{"contractNumber": "C1"}]}


# ---------------------------------------------------------------------------
# ApiLogHandler
# ---------------------------------------------------------------------------


def record(level, msg, **extra):
    rec = logging.LogRecord("rpa_lms.teste", level, __file__, 1, msg, None, None)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


@pytest.mark.parametrize(
    "rec, esperado",
    [
        (record(logging.INFO, "a"), "info"),
        (record(logging.WARNING, "a"), "warning"),
        (record(logging.ERROR, "a"), "error"),
        (record(logging.CRITICAL, "a"), "error"),
        (record(logging.INFO, "a", rpa_level="success"), "success"),
        (record(logging.INFO, "a", rpa_level="invalido"), "info"),
    ],
)
def test_nivel_api(rec, esperado):
    assert nivel_api(rec) == esperado


class ClienteLogs:
    def __init__(self):
        self.lotes = []

    def enviar_logs(self, logs):
        self.lotes.append(logs)


def test_handler_envia_em_lotes():
    cliente = ClienteLogs()
    handler = ApiLogHandler(cliente, tamanho_lote=2)
    for i in range(3):
        handler.emit(record(logging.INFO, f"linha {i}"))
    assert [[log["message"] for log in lote] for lote in cliente.lotes] == [["linha 0", "linha 1"]]

    handler.flush()
    assert cliente.lotes[-1][0]["message"] == "linha 2"
    assert cliente.lotes[-1][0]["timestamp"]


def test_handler_flush_sem_logs_nao_chama_a_api():
    cliente = ClienteLogs()
    ApiLogHandler(cliente).flush()
    assert cliente.lotes == []


def test_execucao_aberta_pelo_painel_e_assumida_em_vez_de_criada():
    session = FakeSession([FakeResponse(200, {"id": 5})])
    cliente = MonitorClient("http://api/api", "segredo", session=session, execution_id=5)
    assert cliente.iniciar_execucao("contract_extraction", "manual", [("lms_login", "Login no LMS")]) == 5
    assert session.chamadas[0]["url"] == "http://api/api/rpa/executions/5/start/"


def test_execution_id_vem_do_ambiente(monkeypatch):
    monkeypatch.setenv("API_URL", "http://api/api")
    monkeypatch.setenv("RPA_EXECUTION_ID", "12")
    assert MonitorClient.from_env().execution_id == 12
    monkeypatch.delenv("RPA_EXECUTION_ID")
    assert MonitorClient.from_env().execution_id is None


def test_reivindicar_execucao_com_e_sem_pedido_na_fila():
    cliente, session = cliente_com([FakeResponse(200, {"executionId": 3}), FakeResponse(204)])
    assert cliente.reivindicar_execucao() == 3
    assert cliente.reivindicar_execucao() is None
    assert session.chamadas[0]["method"] == "POST"
    assert session.chamadas[0]["url"] == "http://api/api/rpa/jobs/claim/"


def test_parada_solicitada_e_falha_de_rede_conta_como_nao():
    cliente, session = cliente_com([FakeResponse(200, {"stopRequested": True})])
    assert cliente.parada_solicitada(3) is True
    assert session.chamadas[0]["url"] == "http://api/api/rpa/jobs/3/"

    cliente, _ = cliente_com(erro=ConnectionError("fora do ar"))
    assert cliente.parada_solicitada(3) is False


def test_listar_contratos_pagina_unica_e_multiplas_paginas():
    respostas = [
        FakeResponse(
            200,
            {
                "count": 3,
                "results": [
                    {"contractNumber": "C1", "progressState": "Effective Contract"},
                    {"contractNumber": "C2", "progressState": "Review Completed"},
                ],
            },
        ),
        FakeResponse(
            200,
            {
                "count": 3,
                "results": [
                    {"contractNumber": "C3", "progressState": "Contract Expired"},
                ],
            },
        ),
    ]
    cliente, session = cliente_com(respostas)
    contratos = cliente.listar_contratos(page_size=2)

    assert list(contratos.keys()) == ["C1", "C2", "C3"]
    assert contratos["C1"]["progressState"] == "Effective Contract"
    assert [c["url"] for c in session.chamadas] == [
        "http://api/api/contracts/?page=1&page_size=2",
        "http://api/api/contracts/?page=2&page_size=2",
    ]


def test_listar_contratos_sem_url_ou_com_erro_devolve_vazio():
    session = FakeSession()
    assert MonitorClient(None, session=session).listar_contratos() == {}
    assert session.chamadas == []

    cliente, _ = cliente_com(erro=ConnectionError("indisponível"))
    assert cliente.listar_contratos() == {}
