"""
Módulo responsável pela extração detalhada de contratos a partir do
relatório consolidado (relatorio_contratos.xlsx).

Fluxo:
1. Lê a planilha baixada em extract_service.py
2. Filtra linhas onde "Department of the person in charge" contenha "mao"
3. Para cada linha, pesquisa o contrato via elastic_search e coleta
   os campos detalhados (Management Number, Counterparty, status, etc.)
4. Consolida tudo em contract_review_management.xlsx

Desempenho:
- Nada de esperas fixas: a página é considerada pronta quando não há
  requisições XHR/fetch pendentes e o DOM parou de mudar (_JS_MONITOR).
- A aba de detalhe é aberta uma única vez (pelo clique no resultado)
  e reaproveitada: os contratos seguintes só trocam a rota do SPA.
- Todos os campos são lidos numa única chamada ao navegador (_JS_COLETA).
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

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

SELETOR_LINK_CONTRATO = 'a[href*="/app/contract/save?id="]'
SELETOR_LABEL_DETALHE = 'span[class="ContractName_Label"]'

# Tempo sem requisições pendentes nem mudanças no DOM para considerar a tela pronta
QUIETUDE_DETALHE_MS = 500
# Na busca, concluir "não encontrado" exige uma quietude maior, para não
# confundir o intervalo antes da requisição de busca com uma busca vazia
QUIETUDE_BUSCA_VAZIA_MS = 2000
# Teto da espera pelo carregamento dos comentários (era o antigo time.sleep(5))
ESPERA_MAX_DETALHE_MS = 5000

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

# Colunas "status" — True/False conforme visibilidade do primeiro elemento
# (seletor CSS, texto contido sem diferenciar maiúsculas).
# Os nomes não podem repetir os de DATE_FIELDS, senão o True/False sobrescreve a data.
STATUS_FIELDS = {
    "Review Request Msg": ("span", "I request a review of the contract."),
    "Review Completed Flag": (".Comment_Content", "Completion of contract review"),
    "Legal Team Consent": (".Comment_Content", "Legal Team Consent"),
    "Approval Completed Flag": (".Comment_Content", "Status changed to in Approval Completed"),
    "Processing Approval": (".Comment_Content", "Status changed to in Processing Approval"),
    "Contract Expired": (".Comment_Content", "Contract Expired"),
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
        COLUNAS_FINAIS.append("Biz-Drop Completed")

COLUNAS_FINAIS.extend(STATUS_FIELDS)


# ---------------------------------------------------------------------------
# JavaScript executado no navegador
# ---------------------------------------------------------------------------
# Conta as requisições XHR/fetch em andamento e expõe window.__rpa.quieto(ms):
# true quando nada está pendente e o DOM não muda há pelo menos `ms`.
# Num SPA a troca de rota não gera novo "networkidle", por isso o contador próprio.
_JS_MONITOR = """
(() => {
  if (window.__rpa) return;
  const rpa = { pendentes: 0, assinatura: null, desde: 0 };
  window.__rpa = rpa;

  const send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (...args) {
    let aberto = true;
    const fim = () => { if (aberto) { aberto = false; rpa.pendentes--; } };
    rpa.pendentes++;
    this.addEventListener("loadend", fim);
    try { return send.apply(this, args); } catch (e) { fim(); throw e; }
  };

  if (window.fetch) {
    const fetchOriginal = window.fetch;
    window.fetch = function (...args) {
      rpa.pendentes++;
      let promessa;
      try { promessa = fetchOriginal.apply(this, args); } catch (e) { rpa.pendentes--; throw e; }
      return promessa.finally(() => { rpa.pendentes--; });
    };
  }

  rpa.reiniciar = () => { rpa.assinatura = null; };
  rpa.quieto = (ms) => {
    const corpo = document.body;
    const assinatura = document.getElementsByTagName("*").length + ":" + (corpo ? corpo.textContent.length : 0);
    const agora = Date.now();
    if (rpa.pendentes > 0 || assinatura !== rpa.assinatura) {
      rpa.assinatura = assinatura;
      rpa.desde = agora;
      return false;
    }
    return agora - rpa.desde >= ms;
  };
})()
"""

# Mesma regra de visibilidade do locator.is_visible() do Playwright
_JS_VISIVEL = """
const visivel = (el) => {
  if (el.checkVisibility && !el.checkVisibility()) return false;
  if (getComputedStyle(el).visibility !== "visible") return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};
"""

# Resultado da busca: href do primeiro link de contrato que não sobrou da busca
# anterior (marcada com data-rpa-old) ou false para continuar esperando. Quando a
# tela termina de carregar, os links que estiverem nela valem (ex.: o mesmo contrato
# pesquisado duas vezes seguidas); sem nenhum, devolve "__vazio__".
_JS_AGUARDA_BUSCA = (
    "({ seletor, quietudeVazia }) => {"
    + _JS_VISIVEL
    + """
  const links = Array.from(document.querySelectorAll(seletor));
  const novo = links.find((a) => a.getAttribute("data-rpa-old") !== a.getAttribute("href"));
  if (novo && visivel(novo)) return novo.getAttribute("href");
  const rpa = window.__rpa;
  if (rpa && rpa.quieto(quietudeVazia)) {
    const restante = links.find(visivel);
    return restante ? restante.getAttribute("href") : "__vazio__";
  }
  return false;
}
"""
)

# Detalhe: "pronto" quando há um label que não é da tela anterior; "reaproveitado"
# se a tela ficou quieta e o SPA manteve o elemento antigo (aí recarregamos a aba).
_JS_AGUARDA_DETALHE = """({ seletor, quietude }) => {
  const labels = Array.from(document.querySelectorAll(seletor));
  if (labels.some((el) => !el.hasAttribute("data-rpa-old"))) return "pronto";
  const rpa = window.__rpa;
  if (labels.length && rpa && rpa.quieto(quietude)) return "reaproveitado";
  return false;
}
"""

_JS_MARCA_ANTIGOS = """(seletor) => {
  for (const el of document.querySelectorAll(seletor)) {
    el.setAttribute("data-rpa-old", el.getAttribute("href") || "1");
  }
  if (window.__rpa) window.__rpa.reiniciar();
}
"""

# Coleta todos os campos de uma vez, reproduzindo as regras dos seletores antigos:
# - tabela: td:has(span:text-is(label)) + td  -> innerText do primeiro td encontrado
# - datas:  //span[contains(normalize-space(.), âncora)]/preceding::span[contains(@class,"Date")][1]
# - progress: innerText do último span:has-text("Status changed to in")
# - status: is_visible() do primeiro `seletor:has-text(texto)`
_JS_COLETA = (
    "({ tabela, datas, status }) => {"
    + _JS_VISIVEL
    + """
  const norm = (s) => (s || "").replace(/\\s+/g, " ").trim();
  const antes = (a, b) => !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);

  const spans = Array.from(document.querySelectorAll("span"));
  const textos = spans.map((s) => norm(s.textContent));
  const tds = Array.from(document.querySelectorAll("td"));

  const resultadoTabela = {};
  for (const [coluna, label] of Object.entries(tabela)) {
    let alvo = null;
    for (const td of tds) {
      const proximo = td.nextElementSibling;
      if (!proximo || proximo.tagName !== "TD") continue;
      if (!Array.from(td.querySelectorAll("span")).some((s) => norm(s.textContent) === label)) continue;
      if (!alvo || antes(proximo, alvo)) alvo = proximo;
    }
    resultadoTabela[coluna] = alvo ? alvo.innerText.trim() : "";
  }

  const ehData = (s) => (s.getAttribute("class") || "").includes("Date");
  const resultadoDatas = {};
  for (const [coluna, ancora] of Object.entries(datas)) {
    let melhor = -1;
    textos.forEach((texto, i) => {
      if (!texto.includes(ancora)) return;
      for (let j = i - 1; j >= 0; j--) {
        if (ehData(spans[j]) && !spans[j].contains(spans[i])) {
          if (melhor < 0 || j < melhor) melhor = j;
          break;
        }
      }
    });
    resultadoDatas[coluna] = melhor >= 0 ? spans[melhor].innerText.trim() : "";
  }

  let progress = "";
  for (let i = spans.length - 1; i >= 0; i--) {
    if (textos[i].toLowerCase().includes("status changed to in")) {
      progress = spans[i].innerText;
      break;
    }
  }

  const resultadoStatus = {};
  for (const [coluna, [seletor, texto]] of Object.entries(status)) {
    const procurado = norm(texto).toLowerCase();
    const el = Array.from(document.querySelectorAll(seletor)).find((e) =>
      norm(e.textContent).toLowerCase().includes(procurado)
    );
    resultadoStatus[coluna] = el ? visivel(el) : false;
  }

  return { tabela: resultadoTabela, datas: resultadoDatas, progress, status: resultadoStatus };
}
"""
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def _instalar_monitor(page: Page) -> None:
    """Garante o contador de requisições na página atual (o init script só vale para documentos novos)."""
    page.evaluate(_JS_MONITOR)


def _aguardar_quietude(page: Page, quietude_ms: int, espera_max_ms: int) -> None:
    """Espera a tela parar de carregar, sem passar de espera_max_ms."""
    try:
        page.wait_for_function(
            "(ms) => !window.__rpa || window.__rpa.quieto(ms)",
            arg=quietude_ms,
            polling=100,
            timeout=espera_max_ms,
        )
    except PlaywrightTimeoutError:
        logger.debug(f"Tela ainda carregando após {espera_max_ms} ms; seguindo com o que já carregou.")


def _pesquisar_contrato(page: Page, contract_number: str, timeout: int) -> Optional[str]:
    """
    Pesquisa o contrato no elastic_search e devolve o href do link do resultado,
    ou None se a busca não trouxer o contrato.
    """
    url = BASE_URL.format(contract_number=contract_number)
    logger.info(f"Pesquisando contrato: {contract_number}")

    # Marca os links da busca anterior para não clicar num resultado velho
    page.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LINK_CONTRATO)
    page.goto(url, wait_until="commit", timeout=timeout)
    _instalar_monitor(page)

    try:
        href = page.wait_for_function(
            _JS_AGUARDA_BUSCA,
            arg={"seletor": SELETOR_LINK_CONTRATO, "quietudeVazia": QUIETUDE_BUSCA_VAZIA_MS},
            polling=100,
            timeout=timeout,
        ).json_value()
    except PlaywrightTimeoutError:
        href = "__vazio__"

    if href == "__vazio__":
        logger.warning(f"Contrato {contract_number} não encontrado na busca.")
        return None
    return href


def _abrir_aba_detalhe(page: Page, href: str, timeout: int) -> Page:
    """
    Abre a primeira aba de detalhe clicando no link da busca (target=_blank),
    o mesmo caminho que um usuário faz; as seguintes reaproveitam esta aba.
    """
    link = page.locator(f'{SELETOR_LINK_CONTRATO}[href="{href}"]').first
    with page.context.expect_page(timeout=timeout) as new_page_info:
        link.click(timeout=timeout)

    detalhe = new_page_info.value
    detalhe.wait_for_selector(SELETOR_LABEL_DETALHE, timeout=timeout)
    _instalar_monitor(detalhe)
    return detalhe


def _navegar_detalhe(detalhe: Page, href: str, timeout: int) -> None:
    """Leva a aba de detalhe já aberta para outro contrato, trocando só a rota do SPA."""
    detalhe.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LABEL_DETALHE)
    detalhe.goto(urljoin(detalhe.url, href), wait_until="commit", timeout=timeout)
    _instalar_monitor(detalhe)

    situacao = detalhe.wait_for_function(
        _JS_AGUARDA_DETALHE,
        arg={"seletor": SELETOR_LABEL_DETALHE, "quietude": QUIETUDE_DETALHE_MS},
        polling=100,
        timeout=timeout,
    ).json_value()

    if situacao == "reaproveitado":
        # O SPA manteve a tela do contrato anterior: recarrega para garantir dados do novo
        logger.info("Tela de detalhe não foi recriada pelo SPA; recarregando a aba.")
        detalhe.reload(wait_until="domcontentloaded", timeout=timeout)
        detalhe.wait_for_selector(SELETOR_LABEL_DETALHE, timeout=timeout)
        _instalar_monitor(detalhe)


def _coletar_dados_contrato(page: Page) -> dict:
    """Extrai todos os campos do contrato da página de detalhe numa única chamada."""
    _aguardar_quietude(page, QUIETUDE_DETALHE_MS, ESPERA_MAX_DETALHE_MS)

    bruto = page.evaluate(
        _JS_COLETA,
        {"tabela": TABELA_FIELDS, "datas": DATE_FIELDS, "status": STATUS_FIELDS},
    )
    return {
        **bruto["tabela"],
        "Progress State": parse_progress_state(bruto["progress"]),
        **bruto["datas"],
        **bruto["status"],
    }


def _fechar_pagina(page: Optional[Page]) -> None:
    if page:
        try:
            page.close()
        except Exception:
            pass


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
        raise ExtractContractError(f"Relatório não encontrado: {caminho_relatorio}")

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
            logger.warning("Nenhuma linha corresponde ao filtro. Encerrando.")
            pd.DataFrame(columns=COLUNAS_FINAIS).to_excel(caminho_destino, index=False)
            return caminho_destino

        # ------------------------------------------------------------------
        # 2. Itera sobre cada contrato
        # ------------------------------------------------------------------
        resultados = []
        total = len(df_filtrado)
        inicio_total = time.monotonic()

        # Abas abertas a partir daqui (a de detalhe) já nascem com o monitor
        page.context.add_init_script(_JS_MONITOR)
        detalhe: Optional[Page] = None

        try:
            for idx, row in df_filtrado.iterrows():
                contract_number = str(row[coluna_contract_number]).strip()
                if not contract_number:
                    logger.warning(f"Linha {idx} sem Contract Number. Pulando.")
                    continue

                logger.info(f"[{len(resultados)+1}/{total}] Processando {contract_number}")
                origem = {
                    "Contract Number": contract_number,
                    "Department of the person in charge": str(row[coluna_filtro]).strip(),
                }
                inicio = time.monotonic()

                try:
                    href = _pesquisar_contrato(page, contract_number, timeout)
                    if href is None:
                        resultados.append({**{c: "" for c in COLUNAS_FINAIS}, **origem})
                        continue

                    if detalhe is None or detalhe.is_closed():
                        detalhe = _abrir_aba_detalhe(page, href, timeout)
                    else:
                        _navegar_detalhe(detalhe, href, timeout)

                    resultados.append({**_coletar_dados_contrato(detalhe), **origem})
                    logger.info(f"{contract_number} coletado em {time.monotonic() - inicio:.1f}s")

                except Exception as exc:
                    logger.error(f"Erro ao processar {contract_number}: {exc}")
                    resultados.append({**{c: "" for c in COLUNAS_FINAIS}, **origem})
                    # Descarta a aba de detalhe: o próximo contrato abre outra limpa
                    _fechar_pagina(detalhe)
                    detalhe = None
        finally:
            _fechar_pagina(detalhe)

        logger.info(f"{len(resultados)} contratos processados em {time.monotonic() - inicio_total:.1f}s")

        # ------------------------------------------------------------------
        # 3. Consolida e salva
        # ------------------------------------------------------------------
        df_resultado = pd.DataFrame(resultados, columns=COLUNAS_FINAIS)

        Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)
        df_resultado.to_excel(caminho_destino, index=False)

        logger.info(f"Planilha consolidada salva em: {caminho_destino} " f"({len(df_resultado)} registros)")
        return caminho_destino

    except ExtractContractError:
        raise
    except Exception as exc:
        logger.error(f"Erro durante extração detalhada: {exc}")
        raise ExtractContractError(f"Falha ao extrair contract_review_management: {exc}") from exc
