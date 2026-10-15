"""
Autenticação das rotas usadas pelo robô (/api/rpa/): token fixo compartilhado no cabeçalho X-RPA-Token.
"""

import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_rpa_token(x_rpa_token: str | None = Header(default=None)) -> None:
    expected = get_settings().rpa_api_token
    if not expected:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Integração com o robô desativada: defina RPA_API_TOKEN na API."
        )
    if not x_rpa_token or not secrets.compare_digest(x_rpa_token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token do robô inválido ou ausente.")
