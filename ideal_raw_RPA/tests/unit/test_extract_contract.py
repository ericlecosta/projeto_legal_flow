import pandas as pd

from src.extract_contract import COLUNAS_FINAIS, filtrar_contratos, parse_progress_state


def test_parse_progress_state_remove_prefixo_e_aspas_tipograficas():
    assert parse_progress_state("Status changed to in ‘Legal Review in Progress’") == "Legal Review in Progress"
    assert parse_progress_state("Status   changed to in\n‘Approval Completed ’") == "Approval Completed"


def test_parse_progress_state_sem_status():
    assert parse_progress_state("Comentário qualquer") == ""


def test_filtrar_contratos_ignora_maiusculas_e_celulas_vazias():
    df = pd.DataFrame(
        {
            "Department of the person in charge": [
                "LGESP GA Support Part - MAO",
                "LGESP HR - SP",
                None,
                "it team - mao",
            ],
            "Contract Number": ["C1", "C2", "C3", "C4"],
        }
    )
    filtrado = filtrar_contratos(df, "Department of the person in charge", "MAO")
    assert filtrado["Contract Number"].tolist() == ["C1", "C4"]


def test_filtrar_contratos_trata_o_filtro_como_texto_literal():
    df = pd.DataFrame({"Dept": ["Team (MAO)", "Team MAO"], "Contract Number": ["C1", "C2"]})
    assert filtrar_contratos(df, "Dept", "(MAO)")["Contract Number"].tolist() == ["C1"]


def test_colunas_finais_sem_repeticao():
    # Uma coluna repetida faz o True/False de status sobrescrever a data do mesmo nome.
    assert len(COLUNAS_FINAIS) == len(set(COLUNAS_FINAIS))


def test_colunas_finais_comecam_pelas_colunas_do_relatorio():
    assert COLUNAS_FINAIS[:2] == ["Contract Number", "Department of the person in charge"]


# ---------------------------------------------------------------------------
# Coleta em paralelo (sem navegador)
# ---------------------------------------------------------------------------
from src.extract_contract import extract_contract_service as servico  # noqa: E402


class PaginaFalsa:
    def __init__(self):
        self.pausas = 0

    def wait_for_timeout(self, ms):
        self.pausas += 1


class FrenteFalsa:
    def __init__(self, nome, passos, diario, erro=None):
        self.nome, self.passos, self.diario, self.erro = nome, passos, diario, erro
        self.fechada = False

    def rodar(self):
        try:
            for i in range(self.passos):
                self.diario.append((self.nome, i))
                if self.erro and i == 1:
                    raise self.erro
                yield
        finally:
            self.fechada = True


def test_executar_frentes_alterna_entre_as_frentes_com_uma_pausa_por_rodada():
    diario, pagina = [], PaginaFalsa()
    servico._executar_frentes(pagina, [FrenteFalsa("a", 3, diario), FrenteFalsa("b", 1, diario)])
    assert diario == [("a", 0), ("b", 0), ("a", 1), ("a", 2)]
    assert pagina.pausas == 3  # uma por rodada com frente ativa; a última, em que "a" termina, não pausa


def test_erro_inesperado_numa_frente_fecha_as_abas_das_outras():
    diario = []
    boa, ruim = FrenteFalsa("a", 10, diario), FrenteFalsa("b", 10, diario, erro=RuntimeError("navegador caiu"))
    try:
        servico._executar_frentes(PaginaFalsa(), [boa, ruim])
    except RuntimeError:
        pass
    assert boa.fechada and ruim.fechada


class ContextoFalso:
    def __init__(self):
        self.ouvintes = {}

    def on(self, evento, funcao):
        self.ouvintes[evento] = funcao

    def remove_listener(self, evento, funcao):
        self.ouvintes.pop(evento)


class RequisicaoFalsa:
    def __init__(self, url, pagina, tipo="xhr", metodo="GET"):
        self.url, self.resource_type, self.method = url, tipo, metodo
        self.frame = type("Frame", (), {"page": pagina})()


def monitor_falso():
    contexto = ContextoFalso()
    monitor = servico._MonitorRede(contexto)
    return monitor, contexto, contexto.ouvintes["request"], contexto.ouvintes["requestfinished"]


def test_monitor_ignora_o_polling_do_lms_e_requisicoes_que_nao_sao_da_aplicacao():
    monitor, contexto, inicio, fim = monitor_falso()
    aba = object()

    comentarios = RequisicaoFalsa("https://lms/api/comments?id=1", aba)
    inicio(comentarios)
    inicio(RequisicaoFalsa("https://lms/logo.png", aba, tipo="image"))
    assert monitor.pendentes(aba) == ["https://lms/api/comments?id=1"]
    fim(comentarios)

    for _ in range(servico.POLLING_MIN_REPETICOES):
        inicio(RequisicaoFalsa("https://lms/api/notifications", aba))
    assert monitor.pendentes(aba) == []  # repetida na mesma tela é polling

    monitor.desligar()
    assert contexto.ouvintes == {}


def test_dados_de_todo_contrato_na_mesma_url_continuam_contando_a_cada_tela():
    # LMS estilo AngularJS: POST /api/contract com o id no corpo, um por contrato aberto na aba
    monitor, _, inicio, fim = monitor_falso()
    aba = object()
    for _ in range(servico.POLLING_MIN_REPETICOES + 2):
        monitor.marcar_navegacao(aba)
        dados = RequisicaoFalsa("https://lms/api/contract", aba, metodo="POST")
        inicio(dados)
        assert monitor.pendentes(aba) == ["https://lms/api/contract"]
        fim(dados)


def test_requisicoes_da_tela_anterior_nao_seguram_a_tela_nova():
    monitor, _, inicio, _ = monitor_falso()
    aba = object()
    inicio(RequisicaoFalsa("https://lms/api/notifications", aba))  # enfileirada pelo navegador, nunca termina
    monitor.marcar_navegacao(aba)
    assert monitor.pendentes(aba) == []


def test_so_uma_frente_pesquisa_por_vez():
    vez, a, b = servico._Vez(), object(), object()
    assert list(vez.aguardar(a)) == []  # livre: pega na hora

    espera_b = vez.aguardar(b)
    next(espera_b)  # ocupada por "a": "b" cede a vez
    vez.liberar(b)  # quem não é dono não libera
    next(espera_b)

    vez.liberar(a)
    assert list(espera_b) == [] and vez.dono is b


def test_vez_da_busca_e_por_ordem_de_chegada():
    vez, a, b, c = servico._Vez(), object(), object(), object()
    list(vez.aguardar(a))
    espera_b, espera_c = vez.aguardar(b), vez.aguardar(c)
    next(espera_b), next(espera_c)

    vez.liberar(a)
    espera_a = vez.aguardar(a)  # "a" pede de novo logo depois de devolver: vai para o fim da fila
    next(espera_a)
    assert list(espera_b) == [] and vez.dono is b
    vez.liberar(b)
    assert list(espera_c) == [] and vez.dono is c


def test_frente_extra_so_abre_abas_depois_do_primeiro_contrato_coletado():
    coleta = servico._Coleta(
        monitor=None,
        url_inicial="https://lms/#/app/dashboard",
        fila=servico.deque(["C1"]),
        total=1,
        timeout=1000,
        timeout_abertura=1000,
        tentativas=1,
        pasta_erros=None,
        resultados=[None],
    )
    abriu = []
    frente = servico._Frente(coleta, 2)
    frente._abrir_aba_busca = lambda: abriu.append(True) or iter(())
    frente._processar = lambda contrato: iter(())
    passos = frente.rodar()

    next(passos)
    next(passos)
    assert abriu == []  # esperando a frente 1 aquecer o cache

    coleta.aquecida = True
    assert list(passos) == []
    assert abriu == [True] and not coleta.fila


def test_frente_extra_que_esperava_sai_quando_a_fila_acaba():
    coleta = servico._Coleta(
        monitor=None,
        url_inicial="",
        fila=servico.deque(),
        total=0,
        timeout=1000,
        timeout_abertura=1000,
        tentativas=1,
        pasta_erros=None,
        resultados=[],
    )
    frente = servico._Frente(coleta, 2)
    frente._abrir_aba_busca = lambda: (_ for _ in ()).throw(AssertionError("não devia abrir aba"))
    assert list(frente.rodar()) == []
