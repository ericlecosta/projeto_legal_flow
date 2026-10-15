import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import require_rpa_token


def test_token_correto_passa(settings):
    settings.rpa_api_token = "abc"
    assert require_rpa_token("abc") is None


@pytest.mark.parametrize("enviado", [None, "", "abd"])
def test_token_ausente_ou_errado_responde_401(settings, enviado):
    settings.rpa_api_token = "abc"
    with pytest.raises(HTTPException) as erro:
        require_rpa_token(enviado)
    assert erro.value.status_code == 401


def test_sem_token_configurado_as_rotas_do_robo_ficam_desativadas(settings):
    settings.rpa_api_token = ""
    with pytest.raises(HTTPException) as erro:
        require_rpa_token("qualquer")
    assert erro.value.status_code == 503


def test_settings_lista_de_origens_e_modo():
    s = Settings(cors_origins=" http://a , ,http://b", rpa_mode="real", _env_file=None)
    assert s.cors_origins_list == ["http://a", "http://b"]
    assert s.simulated is False
    assert Settings(rpa_mode="simulated", _env_file=None).simulated is True
