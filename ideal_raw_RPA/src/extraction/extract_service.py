"""
Módulo responsável pela extração de relatórios e dados do sistema LMS (Legal Management System).
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, Download

logger = logging.getLogger("rpa_lms.extract")


class ExtractError(Exception):
    """Exceção disparada quando ocorre falha no fluxo de extração de dados."""
    pass


def extrair_relatorio_contratos(
    page: Page,
    subsidiary_code: str = "LGESP",
    periodo: str = "3",
    caminho_destino: Optional[str] = None,
    contract_search_url: Optional[str] = None,
    timeout: int = 30000,
) -> str:
    """
    Realiza o fluxo de extração de contratos no sistema LMS, aplicando os filtros 
    de Subsidiary Code e período (Request Date), e realizando o download do relatório.

    Args:
        page: Instância já autenticada da página do Playwright (Page).
        subsidiary_code: Código da subsidiária a ser filtrado.
        periodo: Opção do período de busca (ex: 'Last 10 years').
        caminho_destino: Caminho local completo para salvar o relatório baixado.
        contract_search_url: URL direta da tela de pesquisa de contratos.
        timeout: Timeout máximo em milissegundos para os seletores e ações.

    Returns:
        str: Caminho absoluto onde o arquivo de relatório foi salvo.
    """
    contract_search_url = (
        contract_search_url 
        or os.getenv("LMS_CONTRACT_SEARCH_URL", "https://lms.lge.com/#/app/contract/search")
    )

    if not caminho_destino:
        pasta_download = Path.cwd() / "downloads"
        pasta_download.mkdir(parents=True, exist_ok=True)
        caminho_destino = str(pasta_download / "relatorio_contratos.xlsx")

    try:
        # 0. Navega para a URL direta da tela de pesquisa e gestão de contratos
        logger.info(f"Navegando para a URL de busca de contratos: {contract_search_url}")
        page.goto(contract_search_url, wait_until="domcontentloaded", timeout=timeout)
        time.sleep(3)  # Pausa breve para renderização dos componentes React

        # =========================================================================
        # Passo 1: Seleção da Subsidiária (Subsidiary Code)
        # =========================================================================
        logger.info(f"Filtrando por Subsidiary Code: {subsidiary_code}...")

        # 1. Localiza o contêiner do React Select pelo texto
        combo_container = page.locator(".react-select").filter(has_text="Subsidiary Code").first
        combo_container.wait_for(state="visible", timeout=timeout)

        # 2. Localiza o input de busca e ativa o foco
        combo_input = combo_container.locator("input.select__input")
        combo_input.click()
        combo_input.fill(subsidiary_code)

        # 3. Clica na opção correspondente no dropdown
        opcao_subsidiary = page.locator(".select__option").filter(has_text=subsidiary_code).first
        opcao_subsidiary.wait_for(state="visible", timeout=timeout)
        opcao_subsidiary.click()

        # =========================================================================
        # Passo 2: Seleção do Período (Request Date)
        # =========================================================================
        logger.info(f"Filtrando por período de data (Request Date): {periodo}...")

        # 1. Localiza o dropdown pelo texto e abre
        dropdown_periodo = page.locator(".react-select").filter(has_text="Request Date").first
        dropdown_periodo.wait_for(state="visible", timeout=timeout)
        dropdown_periodo.click()

        # 2. Aguarda a opção aparecer e clica nela
        opcao_periodo = page.locator(".select__option").filter(has_text=periodo).last
        opcao_periodo.wait_for(state="visible", timeout=timeout)
        opcao_periodo.click()

        # 3. Aguarda que a tabela apareça
        page.wait_for_selector('span.visually-hidden:has-text("Loading...")', state="detached", timeout=300000)
        # =========================================================================
        # Passo 3: Exportação / Download do Relatório
        # =========================================================================
        logger.info("Iniciando o download do arquivo de exportação de contratos...")

        with page.expect_download(timeout=timeout) as download_info:
            page.click('button:has-text("Download")')

        download: Download = download_info.value

        # Garante que o diretório pai do caminho destino exista
        Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)

        # Salva o arquivo baixado no destino final
        download.save_as(caminho_destino)
        logger.info(f"Relatório de contratos salvo com sucesso em: {caminho_destino}")

        return caminho_destino

    except Exception as exc:
        logger.error(f"Erro durante a extração do relatório de contratos: {exc}")
        raise ExtractError(f"Falha ao extrair relatório de contratos no LMS: {exc}") from exc