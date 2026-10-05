"""
Módulo responsável pela extração detalhada de contratos a partir do
relatório consolidado (relatorio_contratos.xlsx).

Fluxo:
1. Lê a planilha baixada em extract_service.py
2. Filtra linhas onde "Departament of the person in charge" contenha "mao"
3. Para cada linha, abre a tela do contrato via elastic_search e coleta
   os campos detalhados (Management Number, Counterparty, status, etc.)
4. Consolida tudo em contract_review_management.xlsx
"""

import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("rpa_lms.extract_contract")


class ExtractContractError(Exception):
    """Exceção disparada quando ocorre falha no fluxo de extração detalhada."""
    pass


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BASE_URL = "https://lms.lge.com/#/app/elastic_search?q={contract_number}"

# Colunas "tabela" — extraídas via td adjacente ao label
TABELA_FIELDS = {
    "Management Number":                    "Management Number",
    "Counterparty":                         "Counterparty",
    "Contract Name":                        "Contract Name",
    "Contract Type":                        "Contract type",
    "Requester":                            "Requester",
    "Contract Period":                      "Contract Period",
    "Contract Amount":                      "Contract amount",
    "A person in charge of legal (team)":   "A person in charge of legal (team)",
}

# Colunas "status/comentário" — extraídas via .Comment_Content ou span
STATUS_FIELDS = {
    "Review Request Msg":   ('span:has-text("I request a review of the contract.")', "span"),
    "Review Completed":     ('.Comment_Content:has-text("Completion of contract review")', "comment"),
    "Legal Team Consent":   ('.Comment_Content:has-text("Legal Team Consent")', "comment"),
    "Approval Completed":   ('.Comment_Content:has-text("Status changed to in Approval Completed")', "comment"),
    "Processing Approval":  ('.Comment_Content:has-text("Status changed to in Processing Approval")', "comment"),
    "Contract Expired":     ('.Comment_Content:has-text("Contract Expired")', "comment"),
}

# Nome das colunas no Excel final (na ordem desejada)
COLUNAS_FINAIS = [
    "Contract Number",
    "Management Number",
    "Counterparty",
    "Contract Name",
    "Contract Type",
    "Requester",
    "Contract Period",
    "Contract Amount",
    "A person in charge of legal (team)",
    "Review Request Msg",
    "Review Completed",
    "Legal Team Consent",
    "Approval Completed",
    "Processing Approval",
    "Contract Expired",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extrair_campo_tabela(page: Page, label: str) -> str:
    """Extrai o valor de uma célula adjacente ao label passado."""
    try:
        locator = page.locator(f'td:has(span:text-is("{label}")) + td')
        if locator.count() == 0:
            return ""
        return locator.first.inner_text().strip()
    except Exception as exc:
        logger.warning(f"Falha ao extrair '{label}': {exc}")
        return ""


def _extrair_status(page: Page, selector: str) -> bool:
    """Retorna True se o seletor estiver visível, False caso contrário."""
    try:
        return page.locator(selector).first.is_visible()
    except Exception:
        return False


def _abrir_contrato_via_busca(page: Page, contract_number: str, timeout: int) -> bool:
    """
    Navega até elastic_search, clica no link do contrato e abre em nova aba.
    Retorna True em sucesso, False caso não encontre o link.
    """
    url = BASE_URL.format(contract_number=contract_number)
    logger.info(f"Abrindo contrato via busca: {contract_number}")

    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    time.sleep(2)  # render React

    # Link do contrato: <a href="#/app/contract/save?id=...">
    link_contrato = page.locator('a[href*="/app/contract/save?id="]').first
    try:
        link_contrato.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        logger.warning(f"Contrato {contract_number} não encontrado na busca.")
        return False

    # Abre em nova aba (target=_blank) e captura a nova Page
    with page.context.expect_page() as new_page_info:
        link_contrato.click()

    nova_page = new_page_info.value
    nova_page.wait_for_load_state("domcontentloaded", timeout=timeout)
    time.sleep(3)  # aguarda render do detalhe do contrato

    return nova_page


def _coletar_dados_contrato(page: Page, timeout: int) -> dict:
    """Extrai todos os campos do contrato da página de detalhe."""
    dados = {}

    # Campos de tabela
    for coluna_excel, label_tela in TABELA_FIELDS.items():
        dados[coluna_excel] = _extrair_campo_tabela(page, label_tela)

    # Campos de status
    for coluna_excel, (selector, _tipo) in STATUS_FIELDS.items():
        dados[coluna_excel] = _extrair_status(page, selector)

    return dados


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def extrair_contract_review_management(
    page: Page,
    caminho_relatorio: str,
    caminho_destino: Optional[str] = None,
    filtro_departamento: str = "mao",
    coluna_filtro: str = "Departament of the person in charge",
    coluna_contract_number: str = "Contract Number",
    timeout: int = 30000,
) -> str:
    """
    Executa a extração detalhada de contratos a partir do relatório consolidado.

    Args:
        page: Instância Playwright já autenticada.
        caminho_relatorio: Caminho do relatorio_contratos.xlsx.
        caminho_destino: Caminho de saída. Padrão: mesma pasta do relatório,
                         com nome 'contract_review_management.xlsx'.
        filtro_departamento: Texto para filtrar a coluna de departamento.
        coluna_filtro: Nome da coluna de departamento.
        coluna_contract_number: Nome da coluna com o número do contrato.
        timeout: Timeout (ms) para seletores e navegação.

    Returns:
        Caminho absoluto do arquivo contract_review_management.xlsx.
    """
    caminho_relatorio = Path(caminho_relatorio).resolve()
    if not caminho_relatorio.exists():
        raise ExtractContractError(
            f"Relatório não encontrado: {caminho_relatorio}"
        )

    if not caminho_destino:
        caminho_destino = str(
            caminho_relatorio.parent / "contract_review_management.xlsx"
        )

    try:
        # ------------------------------------------------------------------
        # 1. Lê e filtra a planilha
        # ------------------------------------------------------------------
        logger.info(f"Lendo planilha: {caminho_relatorio}")
        df = pd.read_excel(caminho_relatorio, dtype=str).fillna("")

        if coluna_filtro not in df.columns:
            raise ExtractContractError(
                f"Coluna '{coluna_filtro}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )
        if coluna_contract_number not in df.columns:
            raise ExtractContractError(
                f"Coluna '{coluna_contract_number}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        df_filtrado = df[
            df[coluna_filtro].str.contains(filtro_departamento, case=False, na=False)
        ].copy()

        logger.info(
            f"Linhas após filtro '{filtro_departamento}' em '{coluna_filtro}': "
            f"{len(df_filtrado)} de {len(df)}"
        )

        if df_filtrado.empty:
            logger.warning("Nenhuma linha corresponde ao filtro. Encerrando.")
            # Gera planilha vazia mas com cabeçalho correto
            pd.DataFrame(columns=COLUNAS_FINAIS).to_excel(
                caminho_destino, index=False
            )
            return caminho_destino

        # ------------------------------------------------------------------
        # 2. Itera sobre cada contrato
        # ------------------------------------------------------------------
        resultados = []
        total = len(df_filtrado)

        for idx, row in df_filtrado.iterrows():
            contract_number = str(row[coluna_contract_number]).strip()
            if not contract_number:
                logger.warning(f"Linha {idx} sem Contract Number. Pulando.")
                continue

            logger.info(f"[{len(resultados)+1}/{total}] Processando {contract_number}")

            nova_page = None
            try:
                nova_page = _abrir_contrato_via_busca(page, contract_number, timeout)
                if not nova_page:
                    resultados.append({
                        "Contract Number": contract_number,
                        **{c: "" for c in COLUNAS_FINAIS if c != "Contract Number"}
                    })
                    continue

                dados = _coletar_dados_contrato(nova_page, timeout)
                dados["Contract Number"] = contract_number
                resultados.append(dados)

            except Exception as exc:
                logger.error(f"Erro ao processar {contract_number}: {exc}")
                resultados.append({
                    "Contract Number": contract_number,
                    **{c: "" for c in COLUNAS_FINAIS if c != "Contract Number"}
                })
            finally:
                # Fecha a aba do contrato para não acumular
                if nova_page:
                    try:
                        nova_page.close()
                    except Exception:
                        pass

        # ------------------------------------------------------------------
        # 3. Consolida e salva
        # ------------------------------------------------------------------
        df_resultado = pd.DataFrame(resultados, columns=COLUNAS_FINAIS)

        # Garante diretório de saída
        Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)

        df_resultado.to_excel(caminho_destino, index=False)
        logger.info(
            f"Planilha consolidada salva em: {caminho_destino} "
            f"({len(df_resultado)} registros)"
        )

        return caminho_destino

    except ExtractContractError:
        raise
    except Exception as exc:
        logger.error(f"Erro durante extração detalhada: {exc}")
        raise ExtractContractError(
            f"Falha ao extrair contract_review_management: {exc}"
        ) from exc