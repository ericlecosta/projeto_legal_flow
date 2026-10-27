from src.pipeline import ETAPAS, TAMANHO_LOTE, Servicos, executar_fluxo

REGISTRO = {"Contract number": "C1", "Progress State": "Review Completed", "Amount": 10.0}


class FakeCliente:
    """Registra as chamadas que o fluxo faria na API do monitor."""

    def __init__(self, ativo=True, aceitar_contratos=True):
        self.ativo = ativo
        self.aceitar_contratos = aceitar_contratos
        self.eventos = []
        self.duracoes = {}
        self.lotes = []

    def iniciar_execucao(self, flow, trigger, etapas):
        self.eventos.append(("iniciar", flow, trigger, tuple(k for k, _ in etapas)))
        return 1

    def atualizar_etapa(self, key, status, duracao=None):
        self.eventos.append(("etapa", key, status))
        self.duracoes[(key, status)] = duracao

    def finalizar_execucao(self, status, registros=None, erro_titulo=None, erro_mensagem=None):
        self.eventos.append(("fim", status, erro_titulo))
        self.registros = registros

    def enviar_contratos(self, contratos):
        self.lotes.append(contratos)
        if not self.aceitar_contratos:
            return None
        return {"received": len(contratos), "created": len(contratos), "updated": 0}


def servicos(**sobrescrever):
    fechados = []
    base = dict(
        login=lambda: "page",
        extrair_relatorio=lambda page: "/tmp/relatorio.xlsx",
        extrair_detalhes=lambda page, caminho: "/tmp/detalhes.xlsx",
        fechar=fechados.append,
        tratar=lambda caminho: ("/tmp/base_ideal.xlsx", [REGISTRO]),
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
    assert resultado.caminho_base_ideal == "/tmp/base_ideal.xlsx"
    assert resultado.registros == 1
    assert cliente.eventos[0] == ("iniciar", "contract_extraction", "scheduled", tuple(k for k, _ in ETAPAS))
    etapas = [e[1:] for e in cliente.eventos if e[0] == "etapa"]
    assert etapas == [(key, status) for key, _ in ETAPAS for status in ("running", "success")]
    assert cliente.eventos[-1] == ("fim", "success", None)
    assert cliente.registros == 1
    assert fechados == ["page"]


def test_contratos_tratados_vao_para_a_api_no_formato_dela():
    cliente = FakeCliente()
    svc, _ = servicos()
    executar_fluxo(svc, cliente)
    [[contrato]] = cliente.lotes
    assert contrato["contractNumber"] == "C1"
    assert contrato["progressState"] == "Review Completed"
    assert contrato["amount"] == 10.0


def test_tratamento_recebe_a_extracao_detalhada():
    recebido = []
    svc, _ = servicos(tratar=lambda caminho: recebido.append(caminho) or ("/tmp/b.xlsx", []))
    executar_fluxo(svc, FakeCliente())
    assert recebido == ["/tmp/detalhes.xlsx"]


def test_envio_em_lotes():
    cliente = FakeCliente()
    registros = [{"Contract number": f"C{i}"} for i in range(TAMANHO_LOTE + 5)]
    svc, _ = servicos(tratar=lambda caminho: ("/tmp/b.xlsx", registros))
    resultado = executar_fluxo(svc, cliente)
    assert [len(lote) for lote in cliente.lotes] == [TAMANHO_LOTE, 5]
    assert resultado.registros == TAMANHO_LOTE + 5


def test_api_recusando_os_contratos_falha_a_etapa_de_envio():
    cliente = FakeCliente(aceitar_contratos=False)
    svc, fechados = servicos()

    resultado = executar_fluxo(svc, cliente)

    assert resultado.status == "failed"
    assert resultado.erro_titulo == "Falha ao gravar os contratos no banco"
    assert ("etapa", "data_upload", "failed") in cliente.eventos
    # A planilha tratada continua disponível mesmo sem o envio
    assert resultado.caminho_base_ideal == "/tmp/base_ideal.xlsx"
    assert fechados == ["page"]


def test_falha_no_tratamento_nao_envia_nada():
    cliente = FakeCliente()
    svc, _ = servicos(tratar=falha("Colunas ausentes na origem: Progress State"))

    resultado = executar_fluxo(svc, cliente)

    assert resultado.erro_titulo == "Falha no tratamento da base Ideal"
    assert resultado.erro_mensagem == "Colunas ausentes na origem: Progress State"
    assert cliente.lotes == []


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
    cliente = FakeCliente(ativo=False)
    svc, _ = servicos()
    assert executar_fluxo(svc, cliente).sucesso
    assert cliente.lotes == []


def test_erro_ao_fechar_o_navegador_nao_muda_o_resultado():
    svc, _ = servicos(fechar=falha("já fechado"))
    assert executar_fluxo(svc, FakeCliente()).sucesso


def test_ao_fim_da_etapa_e_chamado_a_cada_etapa_e_no_final():
    chamadas = []
    svc, _ = servicos()
    executar_fluxo(svc, FakeCliente(), ao_fim_da_etapa=lambda: chamadas.append(1))
    assert len(chamadas) == len(ETAPAS) + 1
