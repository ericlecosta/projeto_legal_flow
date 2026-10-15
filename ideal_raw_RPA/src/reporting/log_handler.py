"""
Handler de logging que encaminha os logs do robô para a tela de detalhe da execução no monitor.

Os registros ficam num buffer e são enviados em lote (a cada `tamanho_lote` linhas ou quando o
fluxo chama flush() no fim de cada etapa), para não fazer uma requisição por linha de log.
"""

import logging
import threading
from datetime import datetime

from .monitor_client import MonitorClient


def nivel_api(record: logging.LogRecord) -> str:
    """Nível no formato da API. Use extra={"rpa_level": "success"} para marcar um sucesso."""
    explicito = getattr(record, "rpa_level", None)
    if explicito in ("info", "warning", "error", "success"):
        return explicito
    if record.levelno >= logging.ERROR:
        return "error"
    if record.levelno >= logging.WARNING:
        return "warning"
    return "info"


class ApiLogHandler(logging.Handler):
    def __init__(self, cliente: MonitorClient, tamanho_lote: int = 20) -> None:
        super().__init__(level=logging.INFO)
        self.cliente = cliente
        self.tamanho_lote = tamanho_lote
        self._buffer: list[dict] = []
        self._trava = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entrada = {
                "timestamp": datetime.fromtimestamp(record.created).astimezone().isoformat(),
                "level": nivel_api(record),
                "message": record.getMessage(),
            }
        except Exception:
            self.handleError(record)
            return
        with self._trava:
            self._buffer.append(entrada)
            cheio = len(self._buffer) >= self.tamanho_lote
        if cheio:
            self.flush()

    def flush(self) -> None:
        with self._trava:
            lote, self._buffer = self._buffer, []
        if lote:
            self.cliente.enviar_logs(lote)
