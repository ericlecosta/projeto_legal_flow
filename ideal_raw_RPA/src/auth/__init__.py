"""
Módulo de autenticação e gerenciamento de OTP para o portal LGE e LMS.
"""

from src.auth.otp_service import obter_otp_temporario, OTPRetrievalError
from src.auth.login_service import fazer_login_lms, fechar_sessao_lms, LoginError

__all__ = [
    "obter_otp_temporario",
    "OTPRetrievalError",
    "fazer_login_lms",
    "fechar_sessao_lms",
    "LoginError",
]
