import pytest

from src.pipeline import ETAPAS, Servicos, executar_fluxo


class FakeCliente:
    """Registra as chamadas que o fluxo faria na API do monitor."""

    def __init__(self, ativo=True, resposta_envio=None):
        self.ativo = ativo
        self.resposta_envio = resposta_envio if resposta_envio is not None else {"created": 1, "updated": 0}
        self.eventos = []
        self.contratos = None

    def iniciar_execucao(self, flow, trigger, etapas):
        self.eventos.append(("iniciar", flow, trigger, tuple(k for k, _ in etapas)))
        return 1

    def atualizar_etapa(self, key, status, duracao=None):
        self.eventos.append(("etapa", key, status))
        self.duracoes = getattr(self, "duracoes", {})
        self.duracoes[(key, status)] = duracao

    def enviar_contratos(self, contratos):
        self.contratos = contratos
        return self.resposta_envio if self.ativo else None

    def finalizar_execucao(self, status, registros=None, erro_titulo=None, erro_mensagem=None):
        self.eventos.append(("fim", status, registros, erro_titulo))


LINHA = {"Contract Number": "C2026000001", "Progress State": "Legal Review in Progress"}


def servicos(**sobrescrever):
    fechados = []
    base = dict(
        login=lambda: "page",
        extrair_relatorio=lambda page: "/tmp/relatorio.xlsx",
        extrair_detalhes=lambda page, caminho: "/tmp/detalhes.xlsx",
        fechar=fechados.append,
        ler_planilha=lambda caminho: [LINHA],
    )
    base.update(sobrescrever)
    return Servicos(**base), fechados


def falha(mensagem):
    def _acao(*_):
        raise RuntimeError(mensagem)

    return _acao


def test_fluxo_completo_reporta_cada_etapa_e_envia_os_contratos():
    cliente = FakeCliente()
    svc, fechados = servicos()

    resultado = executar_fluxo(svc, cliente, trigger="scheduled")

    assert resultado.sucesso
    assert resultado.registros == 1
    assert resultado.caminho_detalhes == "/tmp/detalhes.xlsx"
    assert cliente.eventos[0] == ("iniciar", "contract_extraction", "scheduled", tuple(k for k, _ in ETAPAS))
    etapas = [e[1:] for e in cliente.eventos if e[0] == "etapa"]
    assert etapas == [(key, status) for key, _ in ETAPAS for status in ("running", "success")]
    assert cliente.eventos[-1] == ("fim", "success", 1, None)
    assert cliente.contratos[0]["contractNumber"] == "C2026000001"
    assert fechados == ["page"]


def test_falha_no_login_interrompe_o_fluxo_sem_abrir_o_navegador():
    cliente = FakeCliente()
    svc, fechados = servicos(login=falha("OTP inválido"))

    resultado = executar_fluxo(svc, cliente)

    assert resultado.status == "failed"
    assert resultado.erro_titulo == "Falha no login do LMS"
    assert resultado.erro_mensagem == "OTP inválido"
    assert ("etapa", "lms_login", "failed") in cliente.eventos
    assert not any(e[1] == "report_download" for e in cliente.eventos if e[0] == "etapa")
    assert cliente.eventos[-1] == ("fim", "failed", None, "Falha no login do LMS")
    assert fechados == []


def test_falha_na_extracao_marca_a_etapa_e_fecha_o_navegador():
    cliente = FakeCliente()
    svc, fechados = servicos(extrair_detalhes=falha("timeout na busca"))

    resultado = executar_fluxo(svc, cliente)

    assert resultado.erro_titulo == "Falha na extração dos contratos"
    assert ("etapa", "contract_details", "failed") in cliente.eventos
    # A etapa que falhou também leva a duração (a tela mostra "Falhou após X s")
    assert cliente.duracoes[("contract_details", "failed")] >= 0
    assert fechados == ["page"]


def test_envio_sem_confirmacao_da_api_falha_a_execucao():
    cliente = FakeCliente()
    cliente.enviar_contratos = lambda contratos: None
    svc, _ = servicos()

    resultado = executar_fluxo(svc, cliente)

    assert resultado.status == "failed"
    assert resultado.erro_titulo == "Falha ao enviar os contratos para a base"


def test_sem_api_configurada_o_fluxo_roda_normalmente():
    cliente = FakeCliente(ativo=False)
    svc, _ = servicos()
    assert executar_fluxo(svc, cliente).sucesso


def test_erro_ao_fechar_o_navegador_nao_muda_o_resultado():
    cliente = FakeCliente()
    svc, _ = servicos(fechar=falha("já fechado"))
    assert executar_fluxo(svc, cliente).sucesso


def test_ao_fim_da_etapa_e_chamado_a_cada_etapa_e_no_final():
    chamadas = []
    svc, _ = servicos()
    executar_fluxo(svc, FakeCliente(), ao_fim_da_etapa=lambda: chamadas.append(1))
    assert len(chamadas) == len(ETAPAS) + 1


@pytest.mark.parametrize("linhas", [[], [{"Contract Number": ""}]])
def test_planilha_sem_contratos_validos_conclui_com_zero_registros(linhas):
    cliente = FakeCliente()
    svc, _ = servicos(ler_planilha=lambda caminho: linhas)
    resultado = executar_fluxo(svc, cliente)
    assert resultado.sucesso
    assert resultado.registros == 0
