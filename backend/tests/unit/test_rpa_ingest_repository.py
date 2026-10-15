from datetime import datetime, timedelta

import pytest

from app.models import Execution
from app.repositories import rpa_ingest
from app.schemas import LogEntry, RpaExecutionFinish, RpaExecutionStart, RpaStepIn, RpaStepUpdate

ETAPAS = [
    RpaStepIn(key="lms_login", label="Login no LMS"),
    RpaStepIn(key="report_download", label="Download do relatório"),
    RpaStepIn(key="contract_details", label="Extração dos contratos"),
]


@pytest.fixture
def execucao(db):
    return rpa_ingest.start_execution(db, RpaExecutionStart(trigger="scheduled", steps=ETAPAS))


def test_start_cria_execucao_em_andamento_com_etapas_pendentes(db, execucao):
    salvo = db.get(Execution, execucao.id)
    assert (salvo.flow, salvo.status, salvo.trigger) == ("contract_extraction", "running", "scheduled")
    assert [(s.position, s.key, s.status) for s in salvo.steps] == [
        (0, "lms_login", "pending"),
        (1, "report_download", "pending"),
        (2, "contract_details", "pending"),
    ]


def test_update_step_grava_status_e_duracao(db, execucao):
    step = rpa_ingest.update_step(db, execucao.id, "lms_login", RpaStepUpdate(status="success", duration_seconds=12.5))
    assert (step.status, step.duration_seconds) == ("success", 12.5)


def test_update_step_de_etapa_inexistente_devolve_none(db, execucao):
    assert rpa_ingest.update_step(db, execucao.id, "data_upload", RpaStepUpdate(status="running")) is None


def test_execucao_inexistente(db):
    with pytest.raises(rpa_ingest.ExecutionNotFound):
        rpa_ingest.add_logs(db, 999, [])


def test_add_logs(db, execucao):
    agora = datetime.now().astimezone()
    logs = [
        LogEntry(timestamp=agora, level="info", message="Iniciando"),
        LogEntry(timestamp=agora + timedelta(seconds=1), level="success", message="Login concluído"),
    ]
    assert rpa_ingest.add_logs(db, execucao.id, logs) == 2
    assert [log.message for log in db.get(Execution, execucao.id).logs] == ["Iniciando", "Login concluído"]


def test_finish_com_falha_fecha_as_etapas_e_guarda_o_erro(db, execucao):
    rpa_ingest.update_step(db, execucao.id, "lms_login", RpaStepUpdate(status="success"))
    rpa_ingest.update_step(db, execucao.id, "report_download", RpaStepUpdate(status="running"))

    rpa_ingest.finish_execution(
        db,
        execucao.id,
        RpaExecutionFinish(status="failed", error_title="Falha ao baixar o relatório", error_message="timeout"),
    )

    salvo = db.get(Execution, execucao.id)
    assert salvo.status == "failed"
    assert [s.status for s in salvo.steps] == ["success", "failed", "skipped"]
    assert (salvo.error_title, salvo.error_message) == ("Falha ao baixar o relatório", "timeout")
    assert salvo.finished_at is not None
    assert salvo.duration_seconds >= 0


def test_finish_com_sucesso_guarda_os_registros(db, execucao):
    rpa_ingest.finish_execution(db, execucao.id, RpaExecutionFinish(status="success", records=37))
    salvo = db.get(Execution, execucao.id)
    assert (salvo.status, salvo.records, salvo.error_title) == ("success", 37, None)


def test_execucao_finalizada_nao_aceita_mais_alteracoes(db, execucao):
    rpa_ingest.finish_execution(db, execucao.id, RpaExecutionFinish(status="success"))
    with pytest.raises(rpa_ingest.ExecutionClosed):
        rpa_ingest.update_step(db, execucao.id, "lms_login", RpaStepUpdate(status="failed"))
    with pytest.raises(rpa_ingest.ExecutionClosed):
        rpa_ingest.finish_execution(db, execucao.id, RpaExecutionFinish(status="failed"))
