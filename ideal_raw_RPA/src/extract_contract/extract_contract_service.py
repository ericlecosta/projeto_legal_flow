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
  requisições XHR/fetch pendentes e o DOM parou de mudar (_MonitorRede,
  que acompanha a rede pelos eventos do Playwright, sem mexer na página).
- A aba de detalhe é aberta uma única vez (pelo clique no resultado)
  e reaproveitada: os contratos seguintes só trocam a rota do SPA.
- Todos os campos são lidos numa única chamada ao navegador (_JS_COLETA).

Internet lenta: cada contrato tem até `tentativas` chances, com a aba de detalhe
reaberta do zero a cada nova tentativa. Na última falha, um print da tela vai para
a pasta "erros" ao lado da planilha, para diagnóstico.
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, Request

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

# Padrões, sobrescritos por LMS_TIMEOUT_MS e LMS_TENTATIVAS no main.py
TIMEOUT_PADRAO_MS = 90_000
TENTATIVAS_PADRAO = 3

# Tempo sem requisições pendentes nem mudanças no DOM para considerar a tela pronta
QUIETUDE_DETALHE_MS = 500
# Na busca, concluir "não encontrado" exige uma quietude maior, para não
# confundir o intervalo antes da requisição de busca com uma busca vazia
QUIETUDE_BUSCA_VAZIA_MS = 2000
# Teto da espera pelos comentários depois que o detalhe aparece
ESPERA_MAX_DETALHE_MS = 15_000
INTERVALO_POLLING_MS = 100
TIPOS_REQUISICAO_APP = ("xhr", "fetch")

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
# Muda sempre que o SPA renderiza algo: serve para saber se a tela parou de mexer
_JS_ASSINATURA = (
    "document.getElementsByTagName('*').length + ':' + (document.body ? document.body.textContent.length : 0)"
)

# Mesma regra de visibilidade do locator.is_visible() do Playwright
_JS_VISIVEL = """
const visivel = (el) => {
  if (el.checkVisibility && !el.checkVisibility()) return false;
  if (getComputedStyle(el).visibility !== "visible") return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};
"""

# Busca: href do primeiro link de contrato que não sobrou da busca anterior (marcada
# com data-rpa-old), o primeiro link visível qualquer (vale quando a tela termina de
# carregar, ex.: o mesmo contrato pesquisado duas vezes seguidas) e a assinatura do DOM.
_JS_ESTADO_BUSCA = (
    "(seletor) => {"
    + _JS_VISIVEL
    + """
  const links = Array.from(document.querySelectorAll(seletor));
  const novo = links.find((a) => a.getAttribute("data-rpa-old") !== a.getAttribute("href"));
  const restante = links.find(visivel);
  return {
    novo: novo && visivel(novo) ? novo.getAttribute("href") : null,
    restante: restante ? restante.getAttribute("href") : null,
    assinatura: """
    + _JS_ASSINATURA
    + """,
  };
}
"""
)

# Detalhe: se já há um label visível que não é da tela anterior, quantos labels existem
# e a assinatura do DOM (para notar quando o SPA manteve a tela antiga)
_JS_ESTADO_DETALHE = (
    "(seletor) => {"
    + _JS_VISIVEL
    + """
  const labels = Array.from(document.querySelectorAll(seletor));
  return {
    novo: labels.some((el) => !el.hasAttribute("data-rpa-old") && visivel(el)),
    labels: labels.length,
    assinatura: """
    + _JS_ASSINATURA
    + """,
  };
}
"""
)

_JS_MARCA_ANTIGOS = """(seletor) => {
  for (const el of document.querySelectorAll(seletor)) {
    el.setAttribute("data-rpa-old", el.getAttribute("href") || "1");
  }
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


class EsperaEsgotada(Exception):
    """A tela não ficou pronta dentro do timeout (internet lenta ou LMS fora do ar)."""


class _MonitorRede:
    """
    Requisições XHR/fetch em andamento em cada aba, vistas pelos eventos do Playwright.
    Num SPA a troca de rota não gera novo "networkidle", por isso a contagem própria.
    """

    def __init__(self, context: BrowserContext) -> None:
        self._context = context
        self._pendentes: dict[Page, dict[Request, float]] = {}
        context.on("request", self._inicio)
        context.on("requestfinished", self._fim)
        context.on("requestfailed", self._fim)

    @staticmethod
    def _pagina(request: Request) -> Optional[Page]:
        try:
            return request.frame.page
        except Exception:  # requisições de service worker não têm aba
            return None

    def _inicio(self, request: Request) -> None:
        if request.resource_type in TIPOS_REQUISICAO_APP:
            pagina = self._pagina(request)
            if pagina is not None:
                self._pendentes.setdefault(pagina, {})[request] = time.monotonic()

    def _fim(self, request: Request) -> None:
        pagina = self._pagina(request)
        if pagina is not None:
            self._pendentes.get(pagina, {}).pop(request, None)

    def pendentes(self, page: Page) -> list[str]:
        return [request.url for request in self._pendentes.get(page, {})]

    def esquecer(self, page: Page) -> None:
        self._pendentes.pop(page, None)

    def desligar(self) -> None:
        self._context.remove_listener("request", self._inicio)
        self._context.remove_listener("requestfinished", self._fim)
        self._context.remove_listener("requestfailed", self._fim)


class _Quietude:
    """
    A aba está quieta quando o DOM não muda há `quietude_ms` e, neste instante, não há requisição
    pendente. Uma requisição não zera a contagem: um polling periódico do LMS (notificações etc.)
    impediria a tela de ficar quieta para sempre.
    """

    def __init__(self, monitor: _MonitorRede, page: Page, quietude_ms: int) -> None:
        self.monitor = monitor
        self.page = page
        self.quietude_s = quietude_ms / 1000
        self.assinatura: Optional[str] = None
        self.desde = time.monotonic()

    def quieta(self, assinatura: str) -> bool:
        agora = time.monotonic()
        if assinatura != self.assinatura:
            self.assinatura = assinatura
            self.desde = agora
            return False
        return agora - self.desde >= self.quietude_s and not self.monitor.pendentes(self.page)


def _ler_estado(page: Page, script: str, arg) -> Optional[dict]:
    """Avalia o script; None enquanto a página troca de documento (contexto destruído)."""
    try:
        return page.evaluate(script, arg)
    except PlaywrightError as exc:
        if page.is_closed():
            raise
        logger.debug(f"Página ainda carregando: {exc}")
        return None


def _aguardar_quietude(page: Page, monitor: _MonitorRede, quietude_ms: int, espera_max_ms: int) -> None:
    """Espera a tela parar de carregar, sem passar de espera_max_ms (aí segue com o que já carregou)."""
    quietude = _Quietude(monitor, page, quietude_ms)
    limite = time.monotonic() + espera_max_ms / 1000
    while time.monotonic() < limite:
        assinatura = _ler_estado(page, f"() => {_JS_ASSINATURA}", None)
        if assinatura is not None and quietude.quieta(assinatura):
            return
        page.wait_for_timeout(INTERVALO_POLLING_MS)
    pendentes = monitor.pendentes(page)
    logger.warning(
        f"Tela de detalhe ainda carregando após {espera_max_ms / 1000:.0f}s; seguindo com o que já carregou."
        + (f" Requisições pendentes: {', '.join(pendentes[:3])}" if pendentes else "")
    )


def _pesquisar_contrato(page: Page, monitor: _MonitorRede, contract_number: str, timeout: int) -> Optional[str]:
    """
    Pesquisa o contrato no elastic_search e devolve o href do link do resultado,
    None se a busca terminar sem o contrato, ou EsperaEsgotada se a busca não terminar.
    """
    url = BASE_URL.format(contract_number=contract_number)
    logger.info(f"Pesquisando contrato: {contract_number}")

    # Marca os links da busca anterior para não clicar num resultado velho
    page.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LINK_CONTRATO)
    page.goto(url, wait_until="commit", timeout=timeout)

    quietude = _Quietude(monitor, page, QUIETUDE_BUSCA_VAZIA_MS)
    limite = time.monotonic() + timeout / 1000
    while time.monotonic() < limite:
        estado = _ler_estado(page, _JS_ESTADO_BUSCA, SELETOR_LINK_CONTRATO)
        if estado:
            if estado["novo"]:
                return estado["novo"]
            if quietude.quieta(estado["assinatura"]):
                if estado["restante"] is None:
                    logger.warning(f"Contrato {contract_number} não encontrado na busca.")
                return estado["restante"]
        page.wait_for_timeout(INTERVALO_POLLING_MS)
    raise EsperaEsgotada(f"a busca não terminou de carregar em {timeout / 1000:.0f}s")


def _abrir_aba_detalhe(page: Page, href: str, timeout: int) -> Page:
    """
    Abre a aba de detalhe clicando no link da busca (target=_blank), o mesmo caminho
    que um usuário faz; os contratos seguintes reaproveitam esta aba.
    """
    link = page.locator(f'{SELETOR_LINK_CONTRATO}[href="{href}"]').first
    with page.context.expect_page(timeout=timeout) as new_page_info:
        link.click(timeout=timeout)
    return new_page_info.value


def _aguardar_detalhe(detalhe: Page, monitor: _MonitorRede, timeout: int, aceita_reaproveitada: bool) -> str:
    """
    Espera o label do contrato novo aparecer. Devolve "pronto", ou "reaproveitado" se a tela
    parou de carregar ainda com o label da tela anterior (SPA que não recria a tela).
    """
    quietude = _Quietude(monitor, detalhe, QUIETUDE_DETALHE_MS)
    limite = time.monotonic() + timeout / 1000
    while time.monotonic() < limite:
        estado = _ler_estado(detalhe, _JS_ESTADO_DETALHE, SELETOR_LABEL_DETALHE)
        if estado:
            if estado["novo"]:
                return "pronto"
            if aceita_reaproveitada and estado["labels"] and quietude.quieta(estado["assinatura"]):
                return "reaproveitado"
        detalhe.wait_for_timeout(INTERVALO_POLLING_MS)
    raise EsperaEsgotada(f"a tela de detalhe não carregou em {timeout / 1000:.0f}s")


def _navegar_detalhe(detalhe: Page, monitor: _MonitorRede, href: str, timeout: int) -> None:
    """Leva a aba de detalhe já aberta para outro contrato, trocando só a rota do SPA."""
    detalhe.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LABEL_DETALHE)
    detalhe.goto(urljoin(detalhe.url, href), wait_until="commit", timeout=timeout)

    if _aguardar_detalhe(detalhe, monitor, timeout, aceita_reaproveitada=True) == "reaproveitado":
        # O SPA manteve a tela do contrato anterior: recarrega para garantir dados do novo
        logger.info("Tela de detalhe não foi recriada pelo SPA; recarregando a aba.")
        detalhe.reload(wait_until="commit", timeout=timeout)
        _aguardar_detalhe(detalhe, monitor, timeout, aceita_reaproveitada=False)


def _coletar_dados_contrato(page: Page, monitor: _MonitorRede) -> dict:
    """Extrai todos os campos do contrato da página de detalhe numa única chamada."""
    _aguardar_quietude(page, monitor, QUIETUDE_DETALHE_MS, ESPERA_MAX_DETALHE_MS)

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


def _salvar_diagnostico(page: Optional[Page], pasta: Path, contract_number: str) -> None:
    """Print da tela em que o contrato falhou, para entender se foi lentidão, login ou erro do LMS."""
    if page is None or page.is_closed():
        return
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / f"{contract_number}.png"
        page.screenshot(path=str(arquivo), timeout=15_000)
        logger.info(f"Print da falha de {contract_number} salvo em {arquivo} (tela: {page.url})")
    except Exception as exc:
        logger.debug(f"Não foi possível salvar o print de {contract_number}: {exc}")


def _fechar_pagina(page: Optional[Page], monitor: Optional[_MonitorRede] = None) -> None:
    if page:
        if monitor:
            monitor.esquecer(page)
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
    timeout: int = TIMEOUT_PADRAO_MS,
    tentativas: int = TENTATIVAS_PADRAO,
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
        timeout: Timeout (ms) de cada espera de tela (busca e detalhe).
        tentativas: Quantas vezes tentar cada contrato antes de deixá-lo sem dados.

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
        falhas: list[str] = []
        total = len(df_filtrado)
        inicio_total = time.monotonic()
        pasta_erros = Path(caminho_destino).parent / "erros"

        monitor = _MonitorRede(page.context)
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
                dados = None

                for tentativa in range(1, tentativas + 1):
                    try:
                        href = _pesquisar_contrato(page, monitor, contract_number, timeout)
                        if href is None:
                            dados = {}
                            break

                        if detalhe is None or detalhe.is_closed():
                            detalhe = _abrir_aba_detalhe(page, href, timeout)
                            _aguardar_detalhe(detalhe, monitor, timeout, aceita_reaproveitada=False)
                        else:
                            _navegar_detalhe(detalhe, monitor, href, timeout)

                        dados = _coletar_dados_contrato(detalhe, monitor)
                        logger.info(f"{contract_number} coletado em {time.monotonic() - inicio:.1f}s")
                        break

                    except Exception as exc:
                        motivo = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
                        if tentativa < tentativas:
                            logger.warning(
                                f"Tentativa {tentativa}/{tentativas} de {contract_number} falhou ({motivo}). "
                                "Tentando de novo com a aba de detalhe reaberta."
                            )
                        else:
                            logger.error(f"{contract_number} ficou sem dados após {tentativas} tentativas: {motivo}")
                            _salvar_diagnostico(detalhe or page, pasta_erros, contract_number)
                            falhas.append(contract_number)
                        # Descarta a aba de detalhe: a próxima tentativa abre outra limpa
                        _fechar_pagina(detalhe, monitor)
                        detalhe = None

                resultados.append({**{c: "" for c in COLUNAS_FINAIS}, **(dados or {}), **origem})
        finally:
            _fechar_pagina(detalhe, monitor)
            monitor.desligar()

        logger.info(f"{len(resultados)} contratos processados em {time.monotonic() - inicio_total:.1f}s")
        if falhas:
            logger.warning(f"{len(falhas)} contrato(s) sem dados por falha de carregamento: {', '.join(falhas)}")
            if len(falhas) == len(resultados):
                raise ExtractContractError(
                    f"Nenhum dos {len(falhas)} contratos carregou (internet lenta ou LMS fora do ar). "
                    f"Prints das telas em {pasta_erros}"
                )

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
