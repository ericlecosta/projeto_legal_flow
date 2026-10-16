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

Paralelismo: `paralelo` frentes de coleta, cada uma com sua aba de busca e sua aba de
detalhe, na mesma sessão do navegador. As buscas são uma por vez (_Vez); o carregamento
das telas de detalhe, que é a parte lenta, roda em paralelo. As esperas são passos de gerador (`yield`) e um
único laço alterna entre as frentes: enquanto uma aba espera o LMS, as outras avançam.
Tudo roda na thread do Playwright síncrono, sem novo login.

Internet lenta: cada contrato tem até `tentativas` chances, com a aba de detalhe
reaberta do zero a cada nova tentativa. Na última falha, um print da tela vai para
a pasta "erros" ao lado da planilha, para diagnóstico.
"""

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Iterator, Optional
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

# Padrões, sobrescritos por LMS_TIMEOUT_MS, LMS_TIMEOUT_ABERTURA_MS, LMS_TENTATIVAS e LMS_PARALELO no main.py
TIMEOUT_PADRAO_MS = 90_000
# Abrir o LMS do zero numa aba nova (baixar o app inteiro) é bem mais lento que trocar de tela:
# com internet ruim, o dashboard já levou ~80s só para abrir depois do login
TIMEOUT_ABERTURA_PADRAO_MS = 300_000
TENTATIVAS_PADRAO = 3
PARALELO_PADRAO = 3

# Tempo sem requisições pendentes nem mudanças no DOM para considerar a tela pronta
QUIETUDE_DETALHE_MS = 500
# Na busca, concluir "não encontrado" exige uma quietude maior, para não
# confundir o intervalo antes da requisição de busca com uma busca vazia
QUIETUDE_BUSCA_VAZIA_MS = 2000
# Teto da espera pelos comentários depois que o detalhe aparece
ESPERA_MAX_DETALHE_MS = 15_000
INTERVALO_POLLING_MS = 100
# Menos texto que isso na página = o LMS ainda não desenhou nada (tela em branco ou só o spinner)
TEXTO_MINIMO_APP = 100
TIPOS_REQUISICAO_APP = ("xhr", "fetch")
POLLING_MIN_REPETICOES = 3

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
    texto: document.body ? document.body.innerText.trim().length : 0,
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

    Só contam as requisições da tela atual, ou seja, iniciadas depois da última navegação da aba
    (marcar_navegacao). As anteriores são sobras da tela de antes. Dentro da tela, uma requisição
    (método + URL) repetida POLLING_MIN_REPETICOES vezes é polling do LMS (notificações etc.):
    nunca para e, com várias abas, o navegador ainda a enfileira (limite de conexões por servidor).
    A contagem recomeça a cada navegação porque o LMS pode buscar os dados de todo contrato na
    mesma URL (id no corpo do POST); na mesma tela, essa requisição acontece uma vez só.
    """

    def __init__(self, context: BrowserContext) -> None:
        self.context = context
        self._pendentes: dict[Page, dict[Request, float]] = {}
        self._navegacao: dict[Page, float] = {}
        self._repeticoes: dict[Page, dict[str, int]] = {}
        context.on("request", self._inicio)
        context.on("requestfinished", self._fim)
        context.on("requestfailed", self._fim)

    @staticmethod
    def _pagina(request: Request) -> Optional[Page]:
        try:
            return request.frame.page
        except Exception:  # requisições de service worker não têm aba
            return None

    @staticmethod
    def _chave(request: Request) -> str:
        return f"{request.method} {request.url}"

    def marcar_navegacao(self, page: Page) -> None:
        """Chamar logo antes de navegar a aba: o que já estava em andamento deixa de contar."""
        self._navegacao[page] = time.monotonic()
        self._repeticoes[page] = {}

    def _inicio(self, request: Request) -> None:
        if request.resource_type in TIPOS_REQUISICAO_APP:
            pagina = self._pagina(request)
            if pagina is not None:
                self._pendentes.setdefault(pagina, {})[request] = time.monotonic()
                contagem = self._repeticoes.setdefault(pagina, {})
                chave = self._chave(request)
                contagem[chave] = contagem.get(chave, 0) + 1

    def _fim(self, request: Request) -> None:
        pagina = self._pagina(request)
        if pagina is not None:
            self._pendentes.get(pagina, {}).pop(request, None)

    def pendentes(self, page: Page) -> list[str]:
        desde = self._navegacao.get(page, 0.0)
        contagem = self._repeticoes.get(page, {})
        return [
            request.url
            for request, inicio in self._pendentes.get(page, {}).items()
            if inicio >= desde and contagem.get(self._chave(request), 0) < POLLING_MIN_REPETICOES
        ]

    def esquecer(self, page: Page) -> None:
        self._pendentes.pop(page, None)
        self._navegacao.pop(page, None)
        self._repeticoes.pop(page, None)

    def desligar(self) -> None:
        self.context.remove_listener("request", self._inicio)
        self.context.remove_listener("requestfinished", self._fim)
        self.context.remove_listener("requestfailed", self._fim)


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


# As esperas abaixo são geradores: cedem a vez (yield) enquanto a tela não está pronta, e o
# laço de _executar_frentes faz uma única pausa por rodada para todas as frentes.


def _aguardar_quietude(
    page: Page, monitor: _MonitorRede, quietude_ms: int, espera_max_ms: int, tela: str = "de detalhe"
) -> Iterator[None]:
    """Espera a tela parar de carregar, sem passar de espera_max_ms (aí segue com o que já carregou)."""
    quietude = _Quietude(monitor, page, quietude_ms)
    limite = time.monotonic() + espera_max_ms / 1000
    while time.monotonic() < limite:
        assinatura = _ler_estado(page, f"() => {_JS_ASSINATURA}", None)
        if assinatura is not None and quietude.quieta(assinatura):
            return
        yield
    pendentes = monitor.pendentes(page)
    logger.warning(
        f"Tela {tela} ainda carregando após {espera_max_ms / 1000:.0f}s; seguindo com o que já carregou."
        + (f" Requisições pendentes: {', '.join(pendentes[:3])}" if pendentes else "")
    )


def _pesquisar_contrato(
    page: Page, monitor: _MonitorRede, contract_number: str, timeout: int
) -> Generator[None, None, Optional[str]]:
    """
    Pesquisa o contrato no elastic_search e devolve o href do link do resultado,
    None se a busca terminar sem o contrato, ou EsperaEsgotada se a busca não terminar.
    """
    url = BASE_URL.format(contract_number=contract_number)
    logger.info(f"Pesquisando contrato: {contract_number}")

    # Marca os links da busca anterior para não clicar num resultado velho
    page.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LINK_CONTRATO)
    monitor.marcar_navegacao(page)
    page.goto(url, wait_until="commit", timeout=timeout)

    quietude = _Quietude(monitor, page, QUIETUDE_BUSCA_VAZIA_MS)
    limite = time.monotonic() + timeout / 1000
    while time.monotonic() < limite:
        estado = _ler_estado(page, _JS_ESTADO_BUSCA, SELETOR_LINK_CONTRATO)
        if estado:
            if estado["novo"]:
                return estado["novo"]
            # Página em branco também fica "quieta": sem o LMS desenhado, ainda não há resultado nenhum
            if estado["texto"] >= TEXTO_MINIMO_APP and quietude.quieta(estado["assinatura"]):
                if estado["restante"] is None and contract_number not in page.url:
                    # O LMS trocou de tela no meio (ex.: voltou ao dashboard): a busca nem chegou a rodar
                    raise EsperaEsgotada(f"a busca foi redirecionada para {page.url}")
                if estado["restante"] is None:
                    logger.warning(f"Contrato {contract_number} não encontrado na busca.")
                return estado["restante"]
        yield
    raise EsperaEsgotada(f"a busca não terminou de carregar em {timeout / 1000:.0f}s")


_JS_TEXTO_E_ASSINATURA = (
    "() => ({ texto: document.body ? document.body.innerText.trim().length : 0, assinatura: " + _JS_ASSINATURA + " })"
)


def _aguardar_lms(page: Page, monitor: _MonitorRede, timeout: int) -> Iterator[None]:
    """Espera o LMS terminar de abrir numa aba nova: algo desenhado na tela e nada mais carregando."""
    quietude = _Quietude(monitor, page, QUIETUDE_BUSCA_VAZIA_MS)
    limite = time.monotonic() + timeout / 1000
    while time.monotonic() < limite:
        estado = _ler_estado(page, _JS_TEXTO_E_ASSINATURA, None)
        if estado and estado["texto"] >= TEXTO_MINIMO_APP and quietude.quieta(estado["assinatura"]):
            return
        yield
    raise EsperaEsgotada(f"o LMS não abriu na aba nova em {timeout / 1000:.0f}s")


def _abrir_aba_detalhe(page: Page, href: str, timeout: int) -> Page:
    """
    Abre a aba de detalhe clicando no link da busca (target=_blank), o mesmo caminho
    que um usuário faz; os contratos seguintes da frente reaproveitam esta aba.
    """
    link = page.locator(f'{SELETOR_LINK_CONTRATO}[href="{href}"]').first
    # expect_popup (e não context.expect_page) para pegar a aba aberta por esta busca, não a de outra frente
    with page.expect_popup(timeout=timeout) as popup:
        link.click(timeout=timeout)
    return popup.value


def _aguardar_detalhe(
    detalhe: Page, monitor: _MonitorRede, timeout: int, aceita_reaproveitada: bool
) -> Generator[None, None, str]:
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
        yield
    raise EsperaEsgotada(f"a tela de detalhe não carregou em {timeout / 1000:.0f}s")


def _navegar_detalhe(detalhe: Page, monitor: _MonitorRede, href: str, timeout: int) -> Iterator[None]:
    """Leva a aba de detalhe já aberta para outro contrato, trocando só a rota do SPA."""
    detalhe.evaluate(_JS_MARCA_ANTIGOS, SELETOR_LABEL_DETALHE)
    monitor.marcar_navegacao(detalhe)
    detalhe.goto(urljoin(detalhe.url, href), wait_until="commit", timeout=timeout)

    if (yield from _aguardar_detalhe(detalhe, monitor, timeout, aceita_reaproveitada=True)) == "reaproveitado":
        # O SPA manteve a tela do contrato anterior: recarrega para garantir dados do novo
        logger.info("Tela de detalhe não foi recriada pelo SPA; recarregando a aba.")
        monitor.marcar_navegacao(detalhe)
        detalhe.reload(wait_until="commit", timeout=timeout)
        yield from _aguardar_detalhe(detalhe, monitor, timeout, aceita_reaproveitada=False)


def _coletar_dados_contrato(page: Page, monitor: _MonitorRede) -> Generator[None, None, dict]:
    """Extrai todos os campos do contrato da página de detalhe numa única chamada."""
    yield from _aguardar_quietude(page, monitor, QUIETUDE_DETALHE_MS, ESPERA_MAX_DETALHE_MS)

    bruto = page.evaluate(
        _JS_COLETA,
        {"tabela": TABELA_FIELDS, "datas": DATE_FIELDS, "status": STATUS_FIELDS},
    )
    if not any(bruto["tabela"].values()):
        # O contrato existe (veio da busca), então tabela vazia é tela lida antes dos dados chegarem
        raise EsperaEsgotada("a tela de detalhe abriu sem os dados do contrato")
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
# Coleta em paralelo
# ---------------------------------------------------------------------------
@dataclass
class _Contrato:
    posicao: int
    numero: str
    origem: dict


class _Vez:
    """
    Turno exclusivo entre as frentes. A busca do LMS pode guardar o estado da pesquisa na sessão
    ou no localStorage, que são os mesmos para todas as abas: duas buscas ao mesmo tempo se
    atropelariam. A busca é rápida; o que roda em paralelo é o carregamento do detalhe.

    Por ordem de chegada: quem devolve a vez e pede de novo vai para o fim da fila, para uma
    frente não monopolizar a busca.
    """

    def __init__(self) -> None:
        self.dono: Optional[object] = None
        self.espera: deque = deque()

    def aguardar(self, dono: object) -> Iterator[None]:
        if self.dono is dono:
            return
        self.espera.append(dono)
        try:
            while self.dono is not None or self.espera[0] is not dono:
                yield
        except BaseException:
            self.espera.remove(dono)
            raise
        self.espera.popleft()
        self.dono = dono

    def liberar(self, dono: object) -> None:
        if self.dono is dono:
            self.dono = None


@dataclass
class _Coleta:
    """Estado compartilhado pelas frentes: a fila de contratos e onde guardar o resultado."""

    monitor: _MonitorRede
    url_inicial: str
    fila: deque  # de _Contrato
    total: int
    timeout: int
    timeout_abertura: int
    tentativas: int
    pasta_erros: Path
    resultados: list[Optional[dict]]
    falhas: list[str] = field(default_factory=list)
    vez_da_busca: _Vez = field(default_factory=_Vez)
    # As frentes extras só abrem suas abas depois do primeiro contrato coletado: aí o app do LMS
    # já está no cache do navegador, e as abas novas não disputam a banda com a primeira abertura
    aquecida: bool = False


class _Frente:
    """Uma frente de coleta: aba de busca e aba de detalhe próprias, pegando contratos da fila."""

    def __init__(self, coleta: _Coleta, nome: int, busca: Optional[Page] = None) -> None:
        self.coleta = coleta
        self.nome = nome
        self.busca = busca
        self.aba_propria = busca is None  # a frente 1 usa a aba do login, que não é fechada aqui
        self.detalhe: Optional[Page] = None

    def rodar(self) -> Iterator[None]:
        coleta = self.coleta
        try:
            if self.busca is None:
                while not coleta.aquecida and coleta.fila:
                    yield
                if not coleta.fila:
                    return
                try:
                    yield from self._abrir_aba_busca()
                except Exception as exc:
                    logger.warning(f"Frente {self.nome} não conseguiu abrir o LMS ({exc}); seguindo com as demais.")
                    _salvar_diagnostico(self.busca, coleta.pasta_erros, f"frente_{self.nome}")
                    return
                logger.info(f"Frente {self.nome} pronta")
            while coleta.fila:
                yield from self._processar(coleta.fila.popleft())
        finally:
            _fechar_pagina(self.detalhe, self.coleta.monitor)
            if self.aba_propria:
                _fechar_pagina(self.busca, self.coleta.monitor)

    def _abrir_aba_busca(self) -> Iterator[None]:
        """
        Abre a aba de busca da frente na mesma tela em que a aba do login está e espera o LMS
        carregar. Assim as buscas desta aba também são só troca de rota, como na frente 1: abrir
        a aba direto na URL da busca faria o LMS iniciar por um caminho que ele pode redirecionar.
        """
        coleta = self.coleta
        self.busca = coleta.monitor.context.new_page()
        coleta.monitor.marcar_navegacao(self.busca)
        self.busca.goto(coleta.url_inicial, wait_until="commit", timeout=coleta.timeout_abertura)
        yield from _aguardar_lms(self.busca, coleta.monitor, coleta.timeout_abertura)

    def _pesquisar(self, contrato: _Contrato) -> Generator[None, None, Optional[str]]:
        """Pesquisa na vez desta frente: uma busca por vez entre todas as frentes."""
        coleta = self.coleta
        yield from coleta.vez_da_busca.aguardar(self)
        try:
            return (yield from _pesquisar_contrato(self.busca, coleta.monitor, contrato.numero, coleta.timeout))
        finally:
            coleta.vez_da_busca.liberar(self)

    def _processar(self, contrato: _Contrato) -> Iterator[None]:
        coleta = self.coleta
        logger.info(f"[{contrato.posicao + 1}/{coleta.total}] Processando {contrato.numero} (frente {self.nome})")
        inicio = time.monotonic()
        dados = None

        for tentativa in range(1, coleta.tentativas + 1):
            try:
                href = yield from self._pesquisar(contrato)
                if href is None:
                    _salvar_diagnostico(self.busca, coleta.pasta_erros, f"nao_encontrado_{contrato.numero}")
                    dados = {}
                    break

                if self.detalhe is None or self.detalhe.is_closed():
                    # Aba nova: o LMS abre do zero, por isso o timeout de abertura
                    self.detalhe = _abrir_aba_detalhe(self.busca, href, coleta.timeout)
                    yield from _aguardar_detalhe(self.detalhe, coleta.monitor, coleta.timeout_abertura, False)
                else:
                    yield from _navegar_detalhe(self.detalhe, coleta.monitor, href, coleta.timeout)

                dados = yield from _coletar_dados_contrato(self.detalhe, coleta.monitor)
                coleta.aquecida = True
                logger.info(f"{contrato.numero} coletado em {time.monotonic() - inicio:.1f}s")
                break

            except Exception as exc:
                motivo = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
                if tentativa < coleta.tentativas:
                    logger.warning(
                        f"Tentativa {tentativa}/{coleta.tentativas} de {contrato.numero} falhou ({motivo}). "
                        "Tentando de novo com a aba de detalhe reaberta."
                    )
                else:
                    logger.error(f"{contrato.numero} ficou sem dados após {coleta.tentativas} tentativas: {motivo}")
                    _salvar_diagnostico(self.detalhe or self.busca, coleta.pasta_erros, contrato.numero)
                    coleta.falhas.append(contrato.numero)
                # Descarta a aba de detalhe: a próxima tentativa abre outra limpa
                _fechar_pagina(self.detalhe, coleta.monitor)
                self.detalhe = None

        coleta.resultados[contrato.posicao] = {**{c: "" for c in COLUNAS_FINAIS}, **(dados or {}), **contrato.origem}


def _executar_frentes(page: Page, frentes: list[_Frente]) -> None:
    """Alterna entre as frentes até a fila acabar, com uma pausa por rodada para o navegador trabalhar."""
    passos = [frente.rodar() for frente in frentes]
    try:
        while passos:
            for passo in list(passos):
                try:
                    next(passo)
                except StopIteration:
                    passos.remove(passo)
            if passos:
                page.wait_for_timeout(INTERVALO_POLLING_MS)
    finally:
        for passo in passos:
            passo.close()  # erro inesperado: fecha as abas das frentes que ainda estavam rodando


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
    timeout_abertura: int = TIMEOUT_ABERTURA_PADRAO_MS,
    tentativas: int = TENTATIVAS_PADRAO,
    paralelo: int = PARALELO_PADRAO,
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
        timeout_abertura: Timeout (ms) para o LMS abrir do zero numa aba nova.
        tentativas: Quantas vezes tentar cada contrato antes de deixá-lo sem dados.
        paralelo: Quantos contratos coletar ao mesmo tempo (frentes de coleta).

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
        contratos = []
        for idx, row in df_filtrado.iterrows():
            contract_number = str(row[coluna_contract_number]).strip()
            if not contract_number:
                logger.warning(f"Linha {idx} sem Contract Number. Pulando.")
                continue
            origem = {
                "Contract Number": contract_number,
                "Department of the person in charge": str(row[coluna_filtro]).strip(),
            }
            contratos.append(_Contrato(len(contratos), contract_number, origem))

        inicio_total = time.monotonic()
        monitor = _MonitorRede(page.context)
        coleta = _Coleta(
            monitor=monitor,
            url_inicial=page.url,
            fila=deque(contratos),
            total=len(contratos),
            timeout=timeout,
            timeout_abertura=timeout_abertura,
            tentativas=tentativas,
            pasta_erros=Path(caminho_destino).parent / "erros",
            resultados=[None] * len(contratos),
        )
        n_frentes = max(1, min(paralelo, len(contratos)))
        logger.info(
            f"Coletando {len(contratos)} contratos com {n_frentes} frente(s) em paralelo"
            + (" (as demais entram depois do primeiro contrato coletado)" if n_frentes > 1 else "")
        )

        try:
            frentes = [_Frente(coleta, 1, busca=page)] + [_Frente(coleta, n) for n in range(2, n_frentes + 1)]
            _executar_frentes(page, frentes)
        finally:
            monitor.desligar()

        resultados = [linha for linha in coleta.resultados if linha is not None]
        falhas = coleta.falhas
        pasta_erros = coleta.pasta_erros
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
