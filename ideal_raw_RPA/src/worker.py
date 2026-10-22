"""
Worker do robô: fica de prontidão e executa o fluxo completo (main.py) quando o painel pede,
pelo botão "Executar Fluxo Agora". Só faz sentido com a API no modo real (RPA_MODE=real).

Ciclo:
1. A cada RPA_WORKER_POLL_SECONDS, pede à API o próximo pedido da fila (POST /api/rpa/jobs/claim/).
2. Roda main.py num processo à parte, com RPA_EXECUTION_ID: o robô grava etapas e logs nessa execução.
3. Enquanto o robô roda, consulta se o painel pediu para interromper; se sim, encerra o robô
   (e o navegador junto) e fecha a execução como falha.

Cada execução num processo novo garante navegador e sessão limpos, como no docker compose run.
"""

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from src.reporting import MonitorClient

# Fora da árvore "rpa_lms": os logs do worker não vão para a tela da execução
logger = logging.getLogger("rpa_worker")

RPA_DIR = Path(__file__).resolve().parents[1]
COMANDO_PADRAO = [sys.executable, str(RPA_DIR / "main.py")]
ESPERA_ENCERRAR_S = 15
# main.py devolve 0 (sucesso) ou 1 (falha já registrada na API); outro código é queda do processo
CODIGOS_FINALIZADOS = (0, 1)


def _sinalizar(proc: subprocess.Popen, forcar: bool) -> None:
    """Manda o sinal para o grupo do robô inteiro (driver do Playwright e navegador inclusos)."""
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGKILL if forcar else signal.SIGTERM)
        elif forcar:
            proc.kill()
        else:
            proc.terminate()
    except ProcessLookupError:
        pass


def _encerrar(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    _sinalizar(proc, forcar=False)
    try:
        proc.wait(timeout=ESPERA_ENCERRAR_S)
    except subprocess.TimeoutExpired:
        _sinalizar(proc, forcar=True)
        proc.wait()


def executar_pedido(
    cliente: MonitorClient,
    execution_id: int,
    comando: list[str] | None = None,
    intervalo: float = 3.0,
) -> str:
    """
    Roda o robô para um pedido do painel e devolve como terminou:
    "finalizado" (o próprio robô fechou a execução), "interrompido" ou "caiu".
    """
    env = {**os.environ, "RPA_EXECUTION_ID": str(execution_id), "RPA_TRIGGER": "manual"}
    logger.info("Executando o pedido %s do painel", execution_id)
    proc = subprocess.Popen(comando or COMANDO_PADRAO, env=env, cwd=RPA_DIR, start_new_session=True)

    interrompido = False
    try:
        while True:
            try:
                proc.wait(timeout=intervalo)
                break
            except subprocess.TimeoutExpired:
                pass
            if cliente.parada_solicitada(execution_id):
                logger.info("Interrupção pedida pelo painel; encerrando o robô (execução %s)", execution_id)
                interrompido = True
                _encerrar(proc)
                break
    finally:
        _encerrar(proc)

    cliente.execution_id = execution_id
    if interrompido:
        cliente.finalizar_execucao(
            "failed", erro_titulo="Execução interrompida", erro_mensagem="Execução interrompida pelo usuário."
        )
        return "interrompido"
    if proc.returncode not in CODIGOS_FINALIZADOS:
        logger.error("O robô terminou com código %s (execução %s)", proc.returncode, execution_id)
        cliente.finalizar_execucao(
            "failed",
            erro_titulo="Falha inesperada no robô",
            erro_mensagem=f"O processo do robô terminou com código {proc.returncode}.",
        )
        return "caiu"
    return "finalizado"


def _parar_com_sinal(signum, _frame):
    # docker stop: SystemExit passa pelo finally de executar_pedido, que encerra o robô em andamento
    raise SystemExit(128 + signum)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    intervalo = float(os.getenv("RPA_WORKER_POLL_SECONDS", "3"))
    cliente = MonitorClient.from_env()
    if not cliente.ativo:
        logger.error("API_URL não definida: o worker não tem de onde receber os pedidos do painel.")
        return 1

    signal.signal(signal.SIGTERM, _parar_com_sinal)
    logger.info("Worker do robô pronto. Aguardando pedidos do painel em %s", cliente.base_url)
    while True:
        cliente.execution_id = None
        execution_id = cliente.reivindicar_execucao()
        if execution_id is None:
            time.sleep(intervalo)
            continue
        resultado = executar_pedido(cliente, execution_id, intervalo=intervalo)
        logger.info("Pedido %s %s", execution_id, resultado)
