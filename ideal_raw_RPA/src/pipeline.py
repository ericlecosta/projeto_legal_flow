"""
Fluxo completo do robô, etapa por etapa, reportando o andamento ao monitor:

1. Login no LMS
2. Download do relatório consolidado (relatorio_contratos.xlsx)
3. Extração detalhada dos contratos (contract_review_management.xlsx)
4. Consolidação da base Ideal Raw e envio para o banco

As funções que tocam o navegador entram por `Servicos`, para o fluxo poder ser testado sem o LMS.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from src.consolidation import consolidar, ler_planilha
from src.reporting import MonitorClient

logger = logging.getLogger("rpa_lms.pipeline")

FLOW = "contract_extraction"

ETAPAS: list[tuple[str, str]] = [
    ("lms_login", "Login no LMS"),
    ("report_download", "Download do relatório"),
    ("contract_details", "Extração dos contratos"),
    ("data_upload", "Envio para a base"),
]

TITULOS_ERRO = {
    "lms_login": "Falha no login do LMS",
    "report_download": "Falha ao baixar o relatório de contratos",
    "contract_details": "Falha na extração dos contratos",
    "data_upload": "Falha ao enviar os contratos para a base",
}


class EnvioError(Exception):
    """A API do monitor não aceitou os contratos consolidados."""


@dataclass
class Servicos:
    login: Callable[[], Any]
    extrair_relatorio: Callable[[Any], str]
    extrair_detalhes: Callable[[Any, str], str]
    fechar: Callable[[Any], None]
    ler_planilha: Callable[[str], list[dict[str, Any]]] = ler_planilha


@dataclass
class Resultado:
    status: str
    registros: int = 0
    caminho_relatorio: str | None = None
    caminho_detalhes: str | None = None
    erro_titulo: str | None = None
    erro_mensagem: str | None = None
    envio: dict[str, Any] | None = field(default=None)

    @property
    def sucesso(self) -> bool:
        return self.status == "success"


def executar_fluxo(
    servicos: Servicos,
    cliente: MonitorClient,
    trigger: str = "manual",
    ao_fim_da_etapa: Callable[[], None] = lambda: None,
) -> Resultado:
    """
    Roda as quatro etapas. Uma falha interrompe o fluxo, marca a etapa como falha e
    finaliza a execução no monitor com o motivo. O navegador é sempre fechado.

    `ao_fim_da_etapa` é chamado depois de cada etapa (o main usa para enviar os logs em lote).
    """
    cliente.iniciar_execucao(FLOW, trigger, ETAPAS)
    resultado = Resultado(status="running")
    page = None
    etapa_atual: str | None = None

    def etapa(key: str, acao: Callable[[], Any]) -> Any:
        nonlocal etapa_atual
        etapa_atual = key
        cliente.atualizar_etapa(key, "running")
        inicio = time.monotonic()
        valor = acao()
        cliente.atualizar_etapa(key, "success", time.monotonic() - inicio)
        ao_fim_da_etapa()
        return valor

    def enviar() -> int:
        registros = consolidar(servicos.ler_planilha(resultado.caminho_detalhes))
        logger.info("Base Ideal Raw consolidada: %d contrato(s).", len(registros))
        resultado.envio = cliente.enviar_contratos(registros)
        if cliente.ativo and resultado.envio is None:
            raise EnvioError("A API não confirmou o recebimento dos contratos.")
        if resultado.envio:
            logger.info(
                "Contratos gravados no banco: %d novo(s), %d atualizado(s).",
                resultado.envio.get("created", 0),
                resultado.envio.get("updated", 0),
                extra={"rpa_level": "success"},
            )
        return len(registros)

    try:
        page = etapa("lms_login", servicos.login)
        resultado.caminho_relatorio = etapa("report_download", lambda: servicos.extrair_relatorio(page))
        resultado.caminho_detalhes = etapa(
            "contract_details", lambda: servicos.extrair_detalhes(page, resultado.caminho_relatorio)
        )
        resultado.registros = etapa("data_upload", enviar)
        resultado.status = "success"
        logger.info("Fluxo concluído com sucesso.", extra={"rpa_level": "success"})
    except Exception as exc:
        resultado.status = "failed"
        resultado.erro_titulo = TITULOS_ERRO.get(etapa_atual or "", "Falha inesperada no robô")
        resultado.erro_mensagem = str(exc) or exc.__class__.__name__
        logger.error("%s: %s", resultado.erro_titulo, resultado.erro_mensagem)
        if etapa_atual:
            cliente.atualizar_etapa(etapa_atual, "failed")
    finally:
        if page is not None:
            try:
                servicos.fechar(page)
            except Exception as exc:
                logger.warning("Não foi possível fechar o navegador: %s", exc)
        ao_fim_da_etapa()

    cliente.finalizar_execucao(
        resultado.status,
        registros=resultado.registros if resultado.sucesso else None,
        erro_titulo=resultado.erro_titulo,
        erro_mensagem=resultado.erro_mensagem,
    )
    return resultado
