"""
Cliente da API do LMS RPA Monitor (backend FastAPI).

O robô usa este cliente para registrar a execução (etapas, logs e resultado) e enviar os
contratos tratados (Base Ideal) para o banco. Falhas de comunicação nunca derrubam o robô: viram um
aviso no log local e a chamada devolve None.

Sem API_URL configurada, o cliente fica desativado e o robô roda sozinho, como antes.
Com RPA_EXECUTION_ID (definido pelo worker), o robô grava na execução que o painel abriu
em vez de criar uma nova.
"""

import logging
import os
from typing import Any

import requests

# Fora da árvore "rpa_lms" de propósito: os avisos daqui não podem voltar para a API pelo ApiLogHandler.
logger = logging.getLogger("rpa_monitor")

TOKEN_HEADER = "X-RPA-Token"


class MonitorClient:
    def __init__(
        self,
        base_url: str | None,
        token: str | None = None,
        session: Any = None,
        timeout: float | None = 15.0,
        execution_id: int | None = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.token = token or ""
        self.session = session if session is not None else requests.Session()
        self.timeout = timeout
        self.execution_id: int | None = execution_id

    @classmethod
    def from_env(cls) -> "MonitorClient":
        execution_id = os.getenv("RPA_EXECUTION_ID")
        return cls(
            os.getenv("API_URL"), os.getenv("RPA_API_TOKEN"), execution_id=int(execution_id) if execution_id else None
        )

    @property
    def ativo(self) -> bool:
        return bool(self.base_url)

    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if not self.ativo:
            return None
        url = f"{self.base_url}{path}"
        extra = {"timeout": self.timeout} if self.timeout is not None else {}
        try:
            response = self.session.request(method, url, json=payload, headers={TOKEN_HEADER: self.token}, **extra)
        except Exception as exc:  # rede fora, DNS, timeout...
            logger.warning("API do monitor indisponível (%s %s): %s", method, path, exc)
            return None
        if response.status_code >= 400:
            logger.warning("API do monitor recusou %s %s: %s %s", method, path, response.status_code, response.text)
            return None
        return response.json() if response.content else {}

    # ------------------------------------------------------------------

    def iniciar_execucao(self, flow: str, trigger: str, etapas: list[tuple[str, str]]) -> int | None:
        body = {"flow": flow, "trigger": trigger, "steps": [{"key": k, "label": label} for k, label in etapas]}
        if self.execution_id is not None:
            # Execução aberta pelo painel: o robô só registra as etapas nela
            data = self._request("POST", f"/rpa/executions/{self.execution_id}/start/", body)
        else:
            data = self._request("POST", "/rpa/executions/", body)
        self.execution_id = data.get("id") if data else None
        return self.execution_id

    def atualizar_etapa(self, key: str, status: str, duracao: float | None = None) -> None:
        if self.execution_id is None:
            return
        body: dict[str, Any] = {"status": status}
        if duracao is not None:
            body["durationSeconds"] = round(duracao, 1)
        self._request("PATCH", f"/rpa/executions/{self.execution_id}/steps/{key}/", body)

    def enviar_logs(self, logs: list[dict[str, Any]]) -> None:
        if self.execution_id is None or not logs:
            return
        self._request("POST", f"/rpa/executions/{self.execution_id}/logs/", {"logs": logs})

    def finalizar_execucao(
        self,
        status: str,
        registros: int | None = None,
        erro_titulo: str | None = None,
        erro_mensagem: str | None = None,
    ) -> None:
        if self.execution_id is None:
            return
        body = {"status": status, "records": registros, "errorTitle": erro_titulo, "errorMessage": erro_mensagem}
        self._request("POST", f"/rpa/executions/{self.execution_id}/finish/", body)

    # ------------------------------------------------------------------
    # Worker: pedidos feitos pelo painel

    def reivindicar_execucao(self) -> int | None:
        """Pega o próximo pedido do painel. Devolve o ID da execução, ou None se a fila estiver vazia."""
        data = self._request("POST", "/rpa/jobs/claim/")
        return data.get("executionId") if data else None

    def parada_solicitada(self, execution_id: int) -> bool:
        """Se o painel pediu para interromper a execução. Falha de comunicação conta como não."""
        data = self._request("GET", f"/rpa/jobs/{execution_id}/")
        return bool(data and data.get("stopRequested"))

    def enviar_contratos(self, contratos: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Envia os contratos tratados (upsert pelo número). Devolve {received, created, updated}."""
        return self._request("PUT", "/rpa/contracts/", {"executionId": self.execution_id, "contracts": contratos})

    def listar_contratos(self, page_size: int = 100) -> dict[str, dict[str, Any]]:
        """
        Busca os contratos salvos na API do monitor (GET /contracts/), indexados por contractNumber.
        Falha de comunicação ou API desativada devolve dict vazio (fallback para extração completa).
        """
        if not self.ativo:
            return {}
        contratos: dict[str, dict[str, Any]] = {}
        pagina = 1
        while True:
            data = self._request("GET", f"/contracts/?page={pagina}&page_size={page_size}")
            if not data:
                break
            resultados = data.get("results") or []
            if not resultados:
                break
            for item in resultados:
                numero = str(item.get("contractNumber") or "").strip()
                if numero:
                    contratos[numero] = item
            total = data.get("count")
            if len(resultados) < page_size or (isinstance(total, int) and len(contratos) >= total):
                break
            pagina += 1
        return contratos
