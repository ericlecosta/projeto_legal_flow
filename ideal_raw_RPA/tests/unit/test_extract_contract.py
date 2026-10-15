import pandas as pd

from src.extract_contract import COLUNAS_FINAIS, filtrar_contratos, parse_progress_state


def test_parse_progress_state_remove_prefixo_e_aspas_tipograficas():
    assert parse_progress_state("Status changed to in ‘Legal Review in Progress’") == "Legal Review in Progress"
    assert parse_progress_state("Status   changed to in\n‘Approval Completed ’") == "Approval Completed"


def test_parse_progress_state_sem_status():
    assert parse_progress_state("Comentário qualquer") == ""


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
