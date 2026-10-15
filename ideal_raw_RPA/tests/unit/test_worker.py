import sys

from src.worker import executar_pedido


class FakeCliente:
    def __init__(self, parar_apos=None):
        self.consultas = 0
        self.parar_apos = parar_apos
        self.execution_id = None
        self.finalizacoes = []

    def parada_solicitada(self, execution_id):
        self.consultas += 1
        return self.parar_apos is not None and self.consultas >= self.parar_apos

    def finalizar_execucao(self, status, erro_titulo=None, erro_mensagem=None):
        self.finalizacoes.append((self.execution_id, status, erro_titulo))


def robo(codigo: str) -> list[str]:
    return [sys.executable, "-c", codigo]


def test_robo_que_termina_sozinho_ja_fechou_a_execucao(tmp_path):
    saida = tmp_path / "env.txt"
    cliente = FakeCliente()
    codigo = f"import os, pathlib; pathlib.Path({str(saida)!r}).write_text(os.environ['RPA_EXECUTION_ID'])"

    assert executar_pedido(cliente, 42, comando=robo(codigo), intervalo=0.1) == "finalizado"
    assert saida.read_text() == "42"  # o robô recebe a execução aberta pelo painel
    assert cliente.finalizacoes == []


def test_falha_registrada_pelo_robo_nao_e_finalizada_de_novo():
    cliente = FakeCliente()
    assert executar_pedido(cliente, 1, comando=robo("raise SystemExit(1)"), intervalo=0.1) == "finalizado"
    assert cliente.finalizacoes == []


def test_robo_que_cai_tem_a_execucao_fechada_pelo_worker():
    cliente = FakeCliente()
    assert executar_pedido(cliente, 7, comando=robo("import os; os._exit(3)"), intervalo=0.1) == "caiu"
    assert cliente.finalizacoes == [(7, "failed", "Falha inesperada no robô")]


def test_interrupcao_pedida_pelo_painel_encerra_o_robo():
    cliente = FakeCliente(parar_apos=2)
    assert executar_pedido(cliente, 9, comando=robo("import time; time.sleep(60)"), intervalo=0.1) == "interrompido"
    assert cliente.finalizacoes == [(9, "failed", "Execução interrompida")]
