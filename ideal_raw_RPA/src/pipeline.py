"""
Fluxo completo do robô, etapa por etapa, reportando o andamento ao monitor:

1. Login no LMS
2. Download do relatório consolidado (relatorio_contratos.xlsx)
3. Extração detalhada dos contratos (contract_review_management.xlsx)
4. Tratamento da base Ideal (base_ideal.xlsx, regras em src/base_ideal)
5. Envio dos contratos tratados para o banco (PUT /api/rpa/contracts/), que alimenta a tela Contratos

As funções que tocam o navegador entram por `Servicos`, para o fluxo poder ser testado sem o LMS.
O tratamento é puro (só planilhas) e também entra por `Servicos`, com o padrão já preenchido.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.base_ideal import MODELO_PADRAO, gravar_base_ideal, ler_registros, para_contratos_api
from src.reporting import MonitorClient

logger = logging.getLogger("rpa_lms.pipeline")

FLOW = "contract_extraction"

ETAPAS: list[tuple[str, str]] = [
    ("lms_login", "Login no LMS"),
    ("report_download", "Download do relatório"),
    ("contract_details", "Extração dos contratos"),
    ("base_ideal", "Tratamento da base"),
    ("data_upload", "Envio para o banco"),
]

# Contratos por requisição no envio para o banco
TAMANHO_LOTE = 200

TITULOS_ERRO = {
    "lms_login": "Falha no login do LMS",
    "report_download": "Falha ao baixar o relatório de contratos",
    "contract_details": "Falha na extração dos contratos",
    "base_ideal": "Falha no tratamento da base Ideal",
    "data_upload": "Falha ao gravar os contratos no banco",
}


def tratar_base_ideal(caminho_detalhes: str) -> tuple[str, list[dict[str, Any]]]:
    """Gera base_ideal.xlsx ao lado da extração e devolve o caminho e os registros tratados."""
    registros = ler_registros(caminho_detalhes)
    destino = Path(caminho_detalhes).parent / "base_ideal.xlsx"
    gravar_base_ideal(registros, MODELO_PADRAO, destino)
    logger.info("Base Ideal tratada: %s contrato(s) em %s", len(registros), destino)
    return str(destino), registros


@dataclass
class Servicos:
    login: Callable[[], Any]
    extrair_relatorio: Callable[[Any], str]
    extrair_detalhes: Callable[[Any, str], str]
    fechar: Callable[[Any], None]
    tratar: Callable[[str], tuple[str, list[dict[str, Any]]]] = tratar_base_ideal


def enviar_contratos(cliente: MonitorClient, registros: list[dict[str, Any]]) -> int:
    """
    Envia os contratos tratados em lotes. Sem API configurada, não há para onde enviar e a etapa
    só registra isso; com API, uma recusa (token, validação, rede) faz a etapa falhar.
    """
    contratos = para_contratos_api(registros)
    if not cliente.ativo:
        logger.warning("API_URL não definida: %s contrato(s) ficaram só na planilha.", len(contratos))
        return len(contratos)
    criados = atualizados = 0
    for inicio in range(0, len(contratos), TAMANHO_LOTE):
        resposta = cliente.enviar_contratos(contratos[inicio : inicio + TAMANHO_LOTE])
        if resposta is None:
            raise RuntimeError("a API do monitor não aceitou os contratos (veja o log do robô)")
        criados += resposta.get("created", 0)
        atualizados += resposta.get("updated", 0)
    logger.info("%s contrato(s) gravados no banco: %s novos, %s atualizados", len(contratos), criados, atualizados)
    return len(contratos)


@dataclass
class Resultado:
    status: str
    caminho_relatorio: str | None = None
    caminho_detalhes: str | None = None
    caminho_base_ideal: str | None = None
    registros: int | None = None
    erro_titulo: str | None = None
    erro_mensagem: str | None = None

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
    Roda as etapas em ordem. Uma falha interrompe o fluxo, marca a etapa como falha e
    finaliza a execução no monitor com o motivo. O navegador é sempre fechado.

    `ao_fim_da_etapa` é chamado depois de cada etapa (o main usa para enviar os logs em lote).
    """
    cliente.iniciar_execucao(FLOW, trigger, ETAPAS)
    resultado = Resultado(status="running")
    page = None
    etapa_atual: str | None = None
    inicio_etapa = time.monotonic()

    def etapa(key: str, acao: Callable[[], Any]) -> Any:
        nonlocal etapa_atual, inicio_etapa
        etapa_atual = key
        cliente.atualizar_etapa(key, "running")
        inicio_etapa = time.monotonic()
        valor = acao()
        cliente.atualizar_etapa(key, "success", time.monotonic() - inicio_etapa)
        ao_fim_da_etapa()
        return valor

    try:
        page = etapa("lms_login", servicos.login)
        resultado.caminho_relatorio = etapa("report_download", lambda: servicos.extrair_relatorio(page))
        resultado.caminho_detalhes = etapa(
            "contract_details", lambda: servicos.extrair_detalhes(page, resultado.caminho_relatorio)
        )
        resultado.caminho_base_ideal, registros = etapa(
            "base_ideal", lambda: servicos.tratar(resultado.caminho_detalhes)
        )
        resultado.registros = etapa("data_upload", lambda: enviar_contratos(cliente, registros))
        resultado.status = "success"
        logger.info("Fluxo concluído com sucesso.", extra={"rpa_level": "success"})
    except Exception as exc:
        resultado.status = "failed"
        resultado.erro_titulo = TITULOS_ERRO.get(etapa_atual or "", "Falha inesperada no robô")
        resultado.erro_mensagem = str(exc) or exc.__class__.__name__
        logger.error("%s: %s", resultado.erro_titulo, resultado.erro_mensagem)
        if etapa_atual:
            cliente.atualizar_etapa(etapa_atual, "failed", time.monotonic() - inicio_etapa)
    finally:
        if page is not None:
            try:
                servicos.fechar(page)
            except Exception as exc:
                logger.warning("Não foi possível fechar o navegador: %s", exc)
        ao_fim_da_etapa()

    cliente.finalizar_execucao(
        resultado.status,
        registros=resultado.registros,
        erro_titulo=resultado.erro_titulo,
        erro_mensagem=resultado.erro_mensagem,
    )
    return resultado
