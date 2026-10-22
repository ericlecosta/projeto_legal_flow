import logging
import pandas as pd
import pytest

from src.extract_contract import (
    COLUNAS_FINAIS,
    escolher_data_biz_drop,
    escolher_request_date,
    filtrar_contratos,
    parse_progress_state,
    parse_qty_review,
)


def test_parse_progress_state_remove_prefixo_e_aspas_tipograficas():
    assert parse_progress_state("Status changed to in ‘Legal Review in Progress’") == "Legal Review in Progress"
    assert parse_progress_state("Status   changed to in\n‘Approval Completed ’") == "Approval Completed"


def test_parse_progress_state_sem_status():
    assert parse_progress_state("Comentário qualquer") == ""


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("1st", 1),
        ("2nd", 2),
        ("3rd", 3),
        ("11th", 11),
        (" 2nd ", 2),
        ("", 0),
        (None, 0),
    ],
)
def test_parse_qty_review_casos_validos_e_vazios(entrada, esperado):
    assert parse_qty_review(entrada) == esperado


def test_parse_qty_review_texto_sem_numero_devolve_zero_com_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="rpa_lms.extract_contract"):
        assert parse_qty_review("sem numero") == 0
    assert "Qty Review" in caplog.text


def test_escolher_request_date_um_pedido():
    assert escolher_request_date(["2026-08-25 10:35:35"]) == "2026-08-25 10:35:35"


def test_escolher_request_date_dois_pedidos_em_qualquer_ordem():
    d1 = "2026-08-20 09:00:00"
    d2 = "2026-08-25 14:30:00"
    assert escolher_request_date([d1, d2]) == d2
    assert escolher_request_date([d2, d1]) == d2


def test_escolher_request_date_formatos_misturados_preserva_texto_original():
    datas = ["2026-04-17", "2026-05-20 10:35:35", "2026-05-20 09:15"]
    assert escolher_request_date(datas) == "2026-05-20 10:35:35"
    assert escolher_request_date(["2026-05-20 10:35:35", "2026-06-01"]) == "2026-06-01"


def test_escolher_request_date_lista_vazia():
    assert escolher_request_date([]) == ""


def test_escolher_request_date_textos_invalidos_devolve_ultimo_nao_vazio_com_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="rpa_lms.extract_contract"):
        assert escolher_request_date(["invalida-1", "invalida-2", ""]) == "invalida-2"
    assert "Request Date" in caplog.text


def test_escolher_data_biz_drop_tabela_do_print():
    linhas = [
        ["Status", "Current Process", "Processing Man", "Processing Date", "Opinion"],
        ["Requester", "Draft", "SIMEIA BATALHA", "2026-08-25 23:41", ""],
        ["Approver", "Approval", "LAERTE SOUZA", "2026-08-26 02:40", "Confirmed."],
    ]
    assert escolher_data_biz_drop(linhas) == "2026-08-26 02:40"


def test_escolher_data_biz_drop_dois_approvers_devolve_o_ultimo():
    linhas = [
        ["Status", "Current Process", "Processing Man", "Processing Date", "Opinion"],
        ["Requester", "Draft", "SIMEIA BATALHA", "2026-08-25 23:41", ""],
        ["Approver", "Approval", "APROVADOR 1", "2026-08-26 01:00", "Ok"],
        ["Approver", "Approval", "LAERTE SOUZA", "2026-08-26 02:40", "Confirmed."],
    ]
    assert escolher_data_biz_drop(linhas) == "2026-08-26 02:40"


def test_escolher_data_biz_drop_sem_approver():
    linhas = [
        ["Status", "Current Process", "Processing Man", "Processing Date", "Opinion"],
        ["Requester", "Draft", "SIMEIA BATALHA", "2026-08-25 23:41", ""],
    ]
    assert escolher_data_biz_drop(linhas) == ""


def test_escolher_data_biz_drop_colunas_em_outra_ordem_acha_pelo_cabecalho():
    linhas = [
        ["Processing Date", "Opinion", "Status", "Processing Man"],
        ["2026-08-25 23:41", "", "Requester", "SIMEIA BATALHA"],
        ["2026-08-26 02:40", "Confirmed.", "Approver", "LAERTE SOUZA"],
    ]
    assert escolher_data_biz_drop(linhas) == "2026-08-26 02:40"


def test_escolher_data_biz_drop_tabela_vazia():
    assert escolher_data_biz_drop([]) == ""


def test_filtrar_contratos_ignora_maiusculas_e_celulas_vazias():
    df = pd.DataFrame(
        {
            "Department of the person in charge": [
                "LGESP GA Support Part - MAO",
                "LGESP HR - SP",
                None,
                "it team - mao",
            ],
            "Contract Number": ["C1", "C2", "C3", "C4"],
        }
    )
    filtrado = filtrar_contratos(df, "Department of the person in charge", "MAO")
    assert filtrado["Contract Number"].tolist() == ["C1", "C4"]


def test_filtrar_contratos_trata_o_filtro_como_texto_literal():
    df = pd.DataFrame({"Dept": ["Team (MAO)", "Team MAO"], "Contract Number": ["C1", "C2"]})
    assert filtrar_contratos(df, "Dept", "(MAO)")["Contract Number"].tolist() == ["C1"]


def test_colunas_finais_sem_repeticao():
    # Uma coluna repetida faz o True/False de status sobrescrever a data do mesmo nome.
    assert len(COLUNAS_FINAIS) == len(set(COLUNAS_FINAIS))


def test_colunas_finais_comecam_pelas_colunas_do_relatorio():
    assert COLUNAS_FINAIS[:2] == ["Contract Number", "Department of the person in charge"]


def test_colunas_finais_contem_novas_colunas_e_remove_antiga():
    for coluna in ("Request Date", "Qty Review", "Biz-Drop Status", "Biz-Drop Completed"):
        assert coluna in COLUNAS_FINAIS
    assert "I requested a review of the contract." not in COLUNAS_FINAIS
    idx_biz_drop = COLUNAS_FINAIS.index("Biz-Drop Completed")
    assert COLUNAS_FINAIS[idx_biz_drop + 1] == "Qty Review"
    assert COLUNAS_FINAIS[-1] == "Biz-Drop Status"
