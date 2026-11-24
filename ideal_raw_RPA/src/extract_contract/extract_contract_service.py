"""
Módulo responsável pela extração detalhada de contratos a partir do
relatório consolidado (relatorio_contratos.xlsx).

Fluxo:
1. Lê a planilha baixada em extract_service.py
2. Filtra linhas onde "Department of the person in charge" contenha "mao"
3. Para cada linha, abre a tela do contrato via elastic_search e coleta
   os campos detalhados (Management Number, Counterparty, status, etc.)
4. Consolida tudo em contract_review_management.xlsx
"""

import logging
import re
import time
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
from openpyxl import Workbook
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("rpa_lms.extract_contract")


class ExtractContractError(Exception):
    """Exceção disparada quando ocorre falha no fluxo de extração detalhada."""

    pass


def salvar_pendencias(pendencias: list[dict], destino: Path) -> None:
    """Salva as pendências da execução atual, mesmo quando a lista está vazia."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    livro = Workbook()
    folha = livro.active
    folha.title = "Pendências"
    colunas = ("Contract Number", "Department of the person in charge", "Motivo")
    folha.append(colunas)
    for item in pendencias:
        folha.append([item.get(coluna, "") for coluna in colunas])
        for celula in folha[folha.max_row]:
            celula.data_type = "s"
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".xlsx", delete=False) as arquivo:
            temporario = Path(arquivo.name)
        livro.save(temporario)
        livro.close()
        temporario.replace(destino)
    finally:
        livro.close()
        if temporario is not None:
            temporario.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BASE_URL = "https://lms.lge.com/#/app/elastic_search?q={contract_number}"

# Colunas "tabela" — extraídas via td adjacente ao label
TABELA_FIELDS = {
    "Management Number": "Management Number",
    "Counterparty": "Counterparty",
    "Contract Name": "Contract Name",
    "Contract Type": "Contract type",
    "Requester": "Requester",
    "Contract Period": "Contract Period",
    "Contract Amount": "Contract amount",
    "A person in charge of legal (team)": "A person in charge of legal (team)",
}

# Colunas "status" — True/False conforme visibilidade do seletor.
# Os nomes não podem repetir os de DATE_FIELDS, senão o True/False sobrescreve a data.
STATUS_FIELDS = {
    "Review Request Msg": 'span:has-text("I request a review of the contract.")',
    "Review Completed Flag": '.Comment_Content:has-text("Completion of contract review")',
    "Legal Team Consent": '.Comment_Content:has-text("Legal Team Consent")',
    "Approval Completed Flag": '.Comment_Content:has-text("Status changed to in Approval Completed")',
    "Processing Approval": '.Comment_Content:has-text("Status changed to in Processing Approval")',
    "Contract Expired Flag": '.Comment_Content:has-text("Contract Expired")',
}

# Colunas que são DATAS — extraídas como "o span.Date mais próximo
# que precede o texto âncora na ordem do documento"
DATE_FIELDS = {
    "I requested a review of the contract.": "I request a review of the contract.",
    "Request Legal Review": "Status changed to in ‘Legal Review in Progress’",
    "Review Completed": "Status changed to in ‘Review Completed’",
    "Legal Team Consent in Progress": "Status changed to in ‘Legal Team Consent in Progress’",
    "Legal Team Consent Completed": "Status changed to in ‘Legal Team Consent Completed’",
    "Processing Approval for Execution": "Status changed to in ‘Processing Approval for Execution ’",
    "Approval Completed": "Status changed to in ‘Approval Completed ’",
    "Effective Contract": "Status changed to in ‘Effective Contract’",
    "Contract Expired": "Status changed to in ‘Contract Expired’",
    "Biz-Drop Completed": "Status changed to in ‘Biz-Drop Completed’",
}

_PROGRESS_STATE_RE = re.compile(r"Status changed to in\s+(.+)", re.IGNORECASE)

# Colunas copiadas do relatório consolidado (a tela de detalhe não mostra o departamento)
COLUNAS_RELATORIO = ["Contract Number", "Department of the person in charge"]

# Nome das colunas no Excel final (na ordem desejada)
COLUNAS_FINAIS = list(COLUNAS_RELATORIO)
for nome in TABELA_FIELDS:
    COLUNAS_FINAIS.append(nome)
    if nome == "Requester":
        COLUNAS_FINAIS.append("Progress State")
    if nome == "Contract Period":
        COLUNAS_FINAIS.append("I requested a review of the contract.")
        COLUNAS_FINAIS.append("Request Legal Review")
        COLUNAS_FINAIS.append("Review Completed")
        COLUNAS_FINAIS.append("Legal Team Consent in Progress")
        COLUNAS_FINAIS.append("Legal Team Consent Completed")
        COLUNAS_FINAIS.append("Processing Approval for Execution")
        COLUNAS_FINAIS.append("Approval Completed")
        COLUNAS_FINAIS.append("Effective Contract")
        COLUNAS_FINAIS.append("Contract Expired")
        COLUNAS_FINAIS.append("Biz-Drop Completed")

COLUNAS_FINAIS.extend(STATUS_FIELDS)


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


def parse_progress_state(texto: str) -> str:
    """
    'Status changed to in ‘Legal Review in Progress’' -> 'Legal Review in Progress'.
    Normaliza espaços e remove as aspas tipográficas que o LMS coloca ao redor do status.
    """
    texto_completo = " ".join(str(texto).split())
    match = _PROGRESS_STATE_RE.search(texto_completo)
    if not match:
        return ""
    return match.group(1).strip().strip("‘’'\"").strip()


def filtrar_contratos(df: pd.DataFrame, coluna_filtro: str, filtro: str) -> pd.DataFrame:
    """Linhas cujo departamento contém o filtro (sem diferenciar maiúsculas)."""
    return df[df[coluna_filtro].str.contains(filtro, case=False, na=False, regex=False)].copy()


def _extrair_progress_state(page: Page) -> str:
    """
    Localiza o último <span> cujo texto contenha 'Status changed to in ...'
    e retorna apenas a parte variável {texto}.
    """
    try:
        locator = page.locator('span:has-text("Status changed to in")').last
        if locator.count() == 0:
            return ""

        return parse_progress_state(locator.inner_text())

    except Exception as exc:
        logger.warning(f"Falha ao extrair 'Progress State': {exc}")
        return ""


def _extrair_data_por_texto(page: Page, texto_ancora: str) -> str:
    """
    Encontra o texto-âncora na página e retorna o texto do span.Date
    mais próximo que aparece ANTES dele na ordem do documento.

    Usa normalize-space(.) para tolerar quebras de linha/espaços extras.
    """
    try:
        # Escapa aspas duplas se houver (para o XPath não quebrar)
        ancora = texto_ancora.replace('"', '\\"')

        xpath = (
            f'xpath=//span[contains(normalize-space(.), "{ancora}")]' f'/preceding::span[contains(@class,"Date")][1]'
        )

        data_locator = page.locator(xpath).first
        if data_locator.count() == 0:
            return ""

        return data_locator.inner_text().strip()

    except Exception as exc:
        logger.warning(f"Falha ao extrair data para '{texto_ancora}': {exc}")
        return ""


def _abrir_contrato_via_busca(page: Page, contract_number: str, timeout: int) -> Optional[Page]:
    """
    Navega até elastic_search, clica no link do contrato e abre em nova aba.
    Retorna a nova Page em sucesso, None caso não encontre o link.
    """
    url = BASE_URL.format(contract_number=contract_number)
    logger.info(f"Abrindo contrato via busca: {contract_number}")

    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    time.sleep(2)

    # Link do contrato: <a href="#/app/contract/save?id=...">
    link_contrato = page.locator('a[href*="/app/contract/save?id="]').first
    try:
        link_contrato.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        logger.warning("Link do contrato %s não apareceu no prazo da busca; será registrado como pendência.", contract_number)
        return None

    # Abre em nova aba (target=_blank) e captura a nova Page
    with page.context.expect_page(timeout=timeout) as new_page_info:
        link_contrato.click()

    nova_page = new_page_info.value
    nova_page.wait_for_load_state("domcontentloaded", timeout=timeout)
    nova_page.wait_for_selector('span[class="ContractName_Label"]', timeout=timeout)
    time.sleep(5)

    return nova_page


def _coletar_dados_contrato(page: Page, timeout: int) -> dict:
    """Extrai todos os campos do contrato da página de detalhe."""
    dados = {}

    # Campos de tabela + campos derivados (Progress State e datas)
    for coluna_excel, label_tela in TABELA_FIELDS.items():
        dados[coluna_excel] = _extrair_campo_tabela(page, label_tela)
        if coluna_excel == "Requester":
            dados["Progress State"] = _extrair_progress_state(page)
            for coluna_data, texto_ancora in DATE_FIELDS.items():
                dados[coluna_data] = _extrair_data_por_texto(page, texto_ancora)

    # Campos de status (bool)
    for coluna_excel, selector in STATUS_FIELDS.items():
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
    coluna_filtro: str = "Department of the person in charge",
    coluna_contract_number: str = "Contract Number",
    timeout: int = 30000,
    pendencias: Optional[list] = None,
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
        pendencias: Lista opcional que receberá os contratos sem link encontrado.

    Returns:
        Caminho absoluto do arquivo contract_review_management.xlsx.
    """
    caminho_relatorio = Path(caminho_relatorio).resolve()
    if not caminho_relatorio.exists():
        raise ExtractContractError(f"Relatório não encontrado: {caminho_relatorio}")

    if pendencias is None:
        pendencias = []

    if not caminho_destino:
        caminho_destino = str(caminho_relatorio.parent / "contract_review_management.xlsx")

    try:
        # ------------------------------------------------------------------
        # 1. Lê e filtra a planilha
        # ------------------------------------------------------------------
        logger.info(f"Lendo planilha: {caminho_relatorio}")
        df = pd.read_excel(caminho_relatorio, dtype=str).fillna("")

        for coluna in (coluna_filtro, coluna_contract_number):
            if coluna not in df.columns:
                raise ExtractContractError(
                    f"Coluna '{coluna}' não encontrada. " f"Colunas disponíveis: {list(df.columns)}"
                )

        df_filtrado = filtrar_contratos(df, coluna_filtro, filtro_departamento)

        logger.info(
            f"Linhas após filtro '{filtro_departamento}' em '{coluna_filtro}': " f"{len(df_filtrado)} de {len(df)}"
        )

        if df_filtrado.empty:
            raise ExtractContractError("Nenhum contrato corresponde ao filtro de departamento.")

        # ------------------------------------------------------------------
        # 2. Itera sobre cada contrato
        # ------------------------------------------------------------------
        resultados = []
        total = len(df_filtrado)

        for posicao, (idx, row) in enumerate(df_filtrado.iterrows(), 1):
            contract_number = str(row[coluna_contract_number]).strip()
            if not contract_number:
                raise ExtractContractError(f"Linha {idx} sem Contract Number.")

            logger.info(f"[{posicao}/{total}] Processando {contract_number}")
            origem = {
                "Contract Number": contract_number,
                "Department of the person in charge": str(row[coluna_filtro]).strip(),
            }

            nova_page = None
            try:
                nova_page = _abrir_contrato_via_busca(page, contract_number, timeout)
                if nova_page is None:
                    pendencias.append({
                        "Contract Number": contract_number,
                        "Department of the person in charge": origem["Department of the person in charge"],
                        "Motivo": "Link não encontrado no prazo; verificar no LMS",
                    })
                    continue

                resultados.append({**_coletar_dados_contrato(nova_page, timeout), **origem})

            except Exception as exc:
                raise ExtractContractError(f"Erro ao processar {contract_number}: {exc}") from exc
            finally:
                if nova_page:
                    try:
                        nova_page.close()
                    except Exception:
                        pass

        # ------------------------------------------------------------------
        # 3. Consolida e salva
        # ------------------------------------------------------------------
        df_resultado = pd.DataFrame(resultados, columns=COLUNAS_FINAIS)

        Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)
        df_resultado.to_excel(caminho_destino, index=False)
        arquivo_pendencias = Path(caminho_destino).parent / "Pendencias contratos.xlsx"
        salvar_pendencias(pendencias, arquivo_pendencias)

        if pendencias:
            logger.warning("Extração parcial: %s contrato(s) com pendência. Consulte: %s", len(pendencias), arquivo_pendencias)
        else:
            logger.info("Nenhum contrato pendente. Lista da execução: %s", arquivo_pendencias)

        logger.info(f"Planilha consolidada salva em: {caminho_destino} " f"({len(df_resultado)} registros)")
        return caminho_destino

    except ExtractContractError:
        raise
    except Exception as exc:
        logger.error(f"Erro durante extração detalhada: {exc}")
        raise ExtractContractError(f"Falha ao extrair contract_review_management: {exc}") from exc
