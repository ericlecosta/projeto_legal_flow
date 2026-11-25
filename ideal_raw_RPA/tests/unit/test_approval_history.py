import pytest
from playwright.sync_api import sync_playwright

from src.extract_contract.extract_contract_service import (
    ExtractContractError,
    _extrair_data_mais_antiga_historico,
    _extrair_data_ultima_aprovacao,
)


@pytest.fixture
def page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        pagina = browser.new_page()
        yield pagina
        browser.close()


def montar_pagina(page, linhas, evento=True):
    comentario = "<span>Status changed to in ‘Approval Completed ’</span>" if evento else ""
    corpo = "".join(
        f'<div role="row"><div role="cell" data-column-id="ApprSignType">{status}</div>'
        f'<div role="cell" data-column-id="ProcessingDate">{data}</div></div>'
        for status, data in linhas
    )
    page.set_content(f'''{comentario}
      <div class="ButtonsGroupTabs_Body"><ul class="nav-tabs">
        <li><a class="nav-link" onclick="this.classList.add('active')">Approval History</a></li>
      </ul><ul class="nav-pills">
        <li><a class="nav-link" onclick="this.classList.add('active')">Contract conclusion</a></li>
      </ul><div role="table"><div role="columnheader" data-column-id="ProcessingDate">Processing Date</div>
      <div class="rdt_TableBody">{corpo}</div></div></div>''')


def test_escolhe_data_mais_recente_dos_aprovadores(page):
    montar_pagina(page, [
        ("Approver", "2026-11-11 03:37"),
        ("Approver", "2026-11-10 02:20"),
        ("agreement", "2026-11-20 10:00"),
    ])
    assert _extrair_data_ultima_aprovacao(page, 1000) == "2026-11-11 03:37"


def test_sem_evento_nao_abre_historico(page):
    montar_pagina(page, [("Approver", "2026-11-11 03:37")], evento=False)
    assert _extrair_data_ultima_aprovacao(page, 1000) == ""
    assert page.locator(".nav-tabs .active").count() == 0


@pytest.mark.parametrize("linhas", [[("agreement", "2026-11-11 03:37")], [("Approver", "")], [("Approver", "inválida")]])
def test_nao_inventa_data_quando_tabela_nao_permite_identifica_la(page, linhas):
    montar_pagina(page, linhas)
    with pytest.raises(ExtractContractError):
        _extrair_data_ultima_aprovacao(page, 1000)


def test_data_do_historico_e_a_mais_antiga_sem_depender_da_ordem(page):
    page.set_content('''
      <span class="Date">2000-01-01 00:00:00</span>
      <div class="CommentTimeline_Body"><div class="Container"><div class="Base_Justify_Left"><span class="Date">2026-11-05 16:00:00</span></div></div></div>
      <div class="CommentTimeline_Body"><div class="Container"><div class="Base_Justify_Left"><span class="Date">2026-11-03 15:44:19</span></div><div class="Comment_Content"><span class="Date">1999-01-01</span></div></div></div>
    ''')
    assert _extrair_data_mais_antiga_historico(page) == "2026-11-03 15:44:19"


def test_historico_sem_data_retorna_vazio_e_data_invalida_falha(page):
    page.set_content('<div class="CommentTimeline_Body"></div>')
    assert _extrair_data_mais_antiga_historico(page) == ""
    page.set_content('<div class="CommentTimeline_Body"><div class="Container"><div class="Base_Justify_Left"><span class="Date">data inválida</span></div></div></div>')
    with pytest.raises(ExtractContractError, match="Data ausente ou inválida"):
        _extrair_data_mais_antiga_historico(page)
