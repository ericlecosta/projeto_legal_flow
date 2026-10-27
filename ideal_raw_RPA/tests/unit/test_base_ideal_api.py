from src.base_ideal import MAPEAMENTO, para_contrato_api, para_contratos_api


def registro(**valores):
    base = dict.fromkeys(MAPEAMENTO)
    base.update(valores)
    return base


def test_campos_e_datas_vao_para_os_nomes_da_api():
    contrato = para_contrato_api(
        registro(
            **{
                "Contract number": " C2026833165 ",
                "Counterparty": "SESI",
                "Main Contract Type": "Service Utilization",
                "Contract type": "General Services/Contracting",
                "The person in charge": "IOMAR FALCAO",
                "Progress State": "Legal Review in Progress",
                "Start date": "2026-11-01",
                "End date": "2028-10-31",
                "Request Date": "2026-10-13",
                "Request Legal Review": "2026-10-13",
                "Reviewer": "BARBARA LUSTOSA",
                "Contract currency": "BRL",
                "Amount": 810184.8,
            }
        )
    )
    assert contrato["contractNumber"] == contrato["managementNumber"] == "C2026833165"
    assert contrato["contractType"] == "General Services/Contracting"
    assert contrato["requester"] == "IOMAR FALCAO"
    assert contrato["legalReviewer"] == "BARBARA LUSTOSA"
    assert (contrato["periodStart"], contrato["periodEnd"]) == ("2026-11-01", "2028-10-31")
    assert contrato["reviewRequestedAt"] == contrato["legalReviewStartedAt"] == "2026-10-13"
    assert contrato["reviewCompletedAt"] is None
    assert (contrato["currency"], contrato["amount"]) == ("BRL", 810184.8)
    # O que não tem coluna própria no banco fica no raw
    assert contrato["raw"]["Main Contract Type"] == "Service Utilization"
    assert contrato["flags"] == {}


def test_conclusao_do_contrato_vira_data_de_vigencia_ou_flag_de_expirado():
    vigente = para_contrato_api(
        registro(**{"Contract number": "C1", "Register the conclusion of contract": "2026-10-08"})
    )
    assert vigente["effectiveAt"] == "2026-10-08"
    assert vigente["flags"] == {"expired": False}

    expirado = para_contrato_api(
        registro(**{"Contract number": "C2", "Register the conclusion of contract": "Expirado"})
    )
    assert expirado["effectiveAt"] is None
    assert expirado["flags"] == {"expired": True}
    assert expirado["raw"]["Register the conclusion of contract"] == "Expirado"


def test_data_invalida_nao_vai_para_campo_de_data():
    contrato = para_contrato_api(registro(**{"Contract number": "C1", "Start date": "DATA INVÁLIDA"}))
    assert contrato["periodStart"] is None
    assert contrato["raw"]["Start date"] == "DATA INVÁLIDA"


def test_textos_longos_sao_cortados_no_limite_do_banco():
    status = "Estado desconhecido " * 10
    contrato = para_contrato_api(registro(**{"Contract number": "C1", "Progress State": status}))
    assert len(contrato["progressState"]) == 64
    assert contrato["raw"]["Progress State"] == status.strip()


def test_raw_so_tem_texto_ou_vazio():
    contrato = para_contrato_api(registro(**{"Contract number": "C1", "Amount": 1234.5}))
    assert contrato["raw"]["Amount"] == "1234.5"
    assert all(v is None or isinstance(v, str) for v in contrato["raw"].values())


def test_registros_sem_numero_ficam_de_fora():
    contratos = para_contratos_api(
        [registro(**{"Contract number": "C1"}), registro(), registro(**{"Contract number": " "})]
    )
    assert [c["contractNumber"] for c in contratos] == ["C1"]
