import logging
import pandas as pd
import pytest

from src.base_ideal import ler_registros, para_contrato_api
from src.extract_contract import (
    COLUNAS_FINAIS,
    contrato_mudou,
    escolher_data_biz_drop,
    escolher_request_date,
    extrair_contract_review_management,
    filtrar_contratos,
    parse_progress_state,
    parse_qty_review,
    reconstruir_dados_contrato,
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


# ---------------------------------------------------------------------------
# Extração incremental (Opção 1)
# ---------------------------------------------------------------------------


def _contrato_api_exemplo(**sobrescrever):
    registro_ideal = {
        "Contract number": "C2026831822",
        "Counterparty": "SESI",
        "Contract name": "Contrato de Prestação de Serviços",
        "Main Contract Type": "Service Utilization",
        "Contract type": "General Services/Contracting",
        "The person in charge": "IOMAR FALCAO",
        "Department of the person in charge": "LGESP Safety Part - MAO",
        "Progress State": "Effective Contract",
        "Start date": "2026-11-01",
        "End date": "2028-10-31",
        "Request Date": "2026-10-13",
        "Request Legal Review": "2026-10-13",
        "Review completed": "2026-10-14",
        "Agreement request": "2026-10-15",
        "Agreement has been completed": "2026-10-16",
        "Approval request": "2026-10-17",
        "Approval request completed": "2026-10-18",
        "Register the conclusion of contract": "2026-10-19",
        "Biz-Drop Completed": None,
        "Qty Review": 2,
        "Reviewer": "BARBARA LUSTOSA",
        "Contract currency": "BRL",
        "Amount": 810184.8,
    }
    registro_ideal.update(sobrescrever)
    return para_contrato_api(registro_ideal)


def test_contrato_mudou_casos_basicos():
    salvo = _contrato_api_exemplo()
    assert contrato_mudou("Effective Contract", None) is True
    assert contrato_mudou("Effective Contract", {}) is True
    assert contrato_mudou("", salvo) is True
    assert contrato_mudou("Effective Contract", salvo) is False
    # Espaços extras e letras maiúsculas/minúsculas no relatório consolidado
    assert contrato_mudou("  Effective Contract  ", salvo) is False
    assert contrato_mudou("Review Completed", salvo) is True


def test_contrato_mudou_biz_drop_exige_data_de_conclusao():
    # No LMS, contratos em Biz-Drop podem ter progressState="Review Completed" no banco e bizDropCompletedAt preenchido
    salvo_com_data = _contrato_api_exemplo(**{"Progress State": "Review Completed", "Biz-Drop Completed": "2026-08-26"})
    salvo_sem_data = _contrato_api_exemplo(**{"Progress State": "Biz-Drop", "Biz-Drop Completed": None})

    assert contrato_mudou("Biz-Drop", salvo_com_data) is False
    assert contrato_mudou("Biz-Drop", salvo_sem_data) is True
    # Se o banco tinha Biz-Drop concluído mas o relatório agora indica outro status, deve reextrair
    assert contrato_mudou("Effective Contract", salvo_com_data) is True


def test_reconstruir_dados_contrato_preserva_roundtrip_com_base_ideal(tmp_path):
    contrato_api = _contrato_api_exemplo()
    reconstruido = reconstruir_dados_contrato(
        contrato_api,
        dados_planilha_anterior={
            "Management Number": "C2026831822",
            "Qty Review": "2",
            "Review Request Msg": "True",
            "Review Completed Flag": "False",
        },
    )

    assert reconstruido["Qty Review"] == 2
    assert reconstruido["Review Request Msg"] is True
    assert reconstruido["Review Completed Flag"] is False
    assert reconstruido["Contract Expired"] is False

    caminho_crm = tmp_path / "contract_review_management.xlsx"
    pd.DataFrame([reconstruido], columns=COLUNAS_FINAIS).to_excel(caminho_crm, index=False)

    [registro_lido] = ler_registros(caminho_crm)
    reenviado = para_contrato_api(registro_lido)
    assert reenviado == contrato_api


def test_reconstruir_dados_contrato_expirado(tmp_path):
    contrato_api = _contrato_api_exemplo(
        **{"Progress State": "Contract Expired", "Register the conclusion of contract": "Expirado"}
    )
    reconstruido = reconstruir_dados_contrato(contrato_api)
    assert reconstruido["Contract Expired"] is True
    assert reconstruido["Effective Contract"] == ""

    caminho_crm = tmp_path / "crm_expirado.xlsx"
    pd.DataFrame([reconstruido], columns=COLUNAS_FINAIS).to_excel(caminho_crm, index=False)
    [registro_lido] = ler_registros(caminho_crm)
    assert para_contrato_api(registro_lido) == contrato_api


def test_ler_registros_define_progress_state_biz_drop_e_qty_review(tmp_path):
    contrato_api = _contrato_api_exemplo(
        **{
            "Progress State": "Review Completed",
            "Biz-Drop Completed": "2026-08-26",
            "Qty Review": 3,
        }
    )
    reconstruido = reconstruir_dados_contrato(contrato_api)
    assert reconstruido["Progress State"] == "Biz-Drop"
    assert reconstruido["Qty Review"] == 3

    caminho_crm = tmp_path / "crm_bizdrop.xlsx"
    pd.DataFrame([reconstruido], columns=COLUNAS_FINAIS).to_excel(caminho_crm, index=False)
    [registro_lido] = ler_registros(caminho_crm)
    assert registro_lido["Progress State"] == "Biz-Drop"
    assert registro_lido["Biz-Drop Completed"] == "2026-08-26"
    assert registro_lido["Qty Review"] == 3


def test_extrair_contract_review_management_reaproveita_contratos_sem_abrir_navegador(tmp_path):
    caminho_relatorio = tmp_path / "relatorio_contratos.xlsx"
    caminho_destino = tmp_path / "contract_review_management.xlsx"
    pd.DataFrame(
        [
            {
                "Contract Number": "C2026831822",
                "Department of the person in charge": "LGESP Safety Part - MAO",
                "Progress State": "Effective Contract",
            }
        ]
    ).to_excel(caminho_relatorio, index=False)

    contratos_anteriores = {"C2026831822": _contrato_api_exemplo()}

    # page=None comprova que nenhuma interação com o Playwright ocorre quando tudo é reaproveitado
    saida = extrair_contract_review_management(
        page=None,
        caminho_relatorio=str(caminho_relatorio),
        caminho_destino=str(caminho_destino),
        contratos_anteriores=contratos_anteriores,
    )

    assert saida == str(caminho_destino)
    [registro] = ler_registros(caminho_destino)
    assert registro["Contract number"] == "C2026831822"
    assert registro["Progress State"] == "Effective Contract"
    assert registro["Amount"] == 810184.8
