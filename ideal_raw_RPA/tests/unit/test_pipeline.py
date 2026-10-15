from src.pipeline import ETAPAS, Servicos, executar_fluxo


class FakeCliente:
    """Registra as chamadas que o fluxo faria na API do monitor."""

    def __init__(self, ativo=True):
        self.ativo = ativo
        self.eventos = []
        self.duracoes = {}

    def iniciar_execucao(self, flow, trigger, etapas):
        self.eventos.append(("iniciar", flow, trigger, tuple(k for k, _ in etapas)))
        return 1

    def atualizar_etapa(self, key, status, duracao=None):
        self.eventos.append(("etapa", key, status))
        self.duracoes[(key, status)] = duracao

    def finalizar_execucao(self, status, registros=None, erro_titulo=None, erro_mensagem=None):
        self.eventos.append(("fim", status, erro_titulo))


def servicos(**sobrescrever):
    fechados = []
    base = dict(
        login=lambda: "page",
        extrair_relatorio=lambda page: "/tmp/relatorio.xlsx",
        extrair_detalhes=lambda page, caminho: "/tmp/detalhes.xlsx",
        fechar=fechados.append,
    )
    base.update(sobrescrever)
    return Servicos(**base), fechados


def falha(mensagem):
    def _acao(*_):
        raise RuntimeError(mensagem)

    return _acao


def test_fluxo_completo_reporta_cada_etapa():
    cliente = FakeCliente()
    svc, fechados = servicos()

    resultado = executar_fluxo(svc, cliente, trigger="scheduled")

    assert resultado.sucesso
    assert resultado.caminho_relatorio == "/tmp/relatorio.xlsx"
    assert resultado.caminho_detalhes == "/tmp/detalhes.xlsx"
    assert cliente.eventos[0] == ("iniciar", "contract_extraction", "scheduled", tuple(k for k, _ in ETAPAS))
    etapas = [e[1:] for e in cliente.eventos if e[0] == "etapa"]
    assert etapas == [(key, status) for key, _ in ETAPAS for status in ("running", "success")]
    assert cliente.eventos[-1] == ("fim", "success", None)
    assert fechados == ["page"]


def test_extracao_detalhada_recebe_o_relatorio_baixado():
    recebido = []
    svc, _ = servicos(extrair_detalhes=lambda page, caminho: recebido.append((page, caminho)) or "/tmp/d.xlsx")
    executar_fluxo(svc, FakeCliente())
    assert recebido == [("page", "/tmp/relatorio.xlsx")]


def test_falha_no_login_interrompe_o_fluxo_sem_abrir_o_navegador():
    cliente = FakeCliente()
    svc, fechados = servicos(login=falha("OTP inválido"))

    resultado = executar_fluxo(svc, cliente)

    assert resultado.status == "failed"
    assert resultado.erro_titulo == "Falha no login do LMS"
    assert resultado.erro_mensagem == "OTP inválido"
    assert ("etapa", "lms_login", "failed") in cliente.eventos
    assert not any(e[1] == "report_download" for e in cliente.eventos if e[0] == "etapa")
    assert cliente.eventos[-1] == ("fim", "failed", "Falha no login do LMS")
    assert fechados == []


def test_falha_na_extracao_marca_a_etapa_com_duracao_e_fecha_o_navegador():
    cliente = FakeCliente()
    svc, fechados = servicos(extrair_detalhes=falha("timeout na busca"))

    resultado = executar_fluxo(svc, cliente)

    assert resultado.erro_titulo == "Falha na extração dos contratos"
    assert ("etapa", "contract_details", "failed") in cliente.eventos
    # A etapa que falhou também leva a duração (a tela mostra "Falhou após X s")
    assert cliente.duracoes[("contract_details", "failed")] >= 0
    assert fechados == ["page"]


def test_sem_api_configurada_o_fluxo_roda_normalmente():
    svc, _ = servicos()
    assert executar_fluxo(svc, FakeCliente(ativo=False)).sucesso


def test_erro_ao_fechar_o_navegador_nao_muda_o_resultado():
    svc, _ = servicos(fechar=falha("já fechado"))
    assert executar_fluxo(svc, FakeCliente()).sucesso


def test_ao_fim_da_etapa_e_chamado_a_cada_etapa_e_no_final():
    chamadas = []
    svc, _ = servicos()
    executar_fluxo(svc, FakeCliente(), ao_fim_da_etapa=lambda: chamadas.append(1))
    assert len(chamadas) == len(ETAPAS) + 1
