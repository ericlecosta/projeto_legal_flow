import random

import pytest

from app.simulator.plan import STEP_ERRORS, STEPS, build_plan


@pytest.mark.parametrize("seed", range(20))
def test_plano_e_consistente(seed):
    plan = build_plan(random.Random(seed), failure_rate=0.3)
    keys = [step.key for step in plan.steps]
    assert keys == [key for key, _ in STEPS][: len(keys)]
    if plan.failed_step:
        assert plan.status == "failed"
        assert plan.steps[-1].key == plan.failed_step
        assert plan.records is None
    else:
        assert plan.status in ("success", "atypical")
        assert plan.records and plan.records > 0


@pytest.mark.parametrize("seed", range(5))
def test_com_falha_garantida_o_erro_e_o_da_etapa(seed):
    plan = build_plan(random.Random(seed), failure_rate=1.0)
    assert plan.status == "failed"
    assert plan.error == STEP_ERRORS[plan.failed_step]


def test_fluxo_somente_otp_tem_duas_etapas_e_nao_captura():
    plan = build_plan(random.Random(3), flow="otp_only", failure_rate=0)
    assert [key for key, _ in plan.all_steps] == ["start_session", "otp_captcha"]
    assert plan.records is None
