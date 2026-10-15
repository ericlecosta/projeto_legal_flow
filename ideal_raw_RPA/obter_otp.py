"""
Script utilitário para execução direta do serviço de OTP temporário.
"""

import sys
from pathlib import Path

# Garante que o diretório atual do RPA esteja no sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import logging
from src.auth.otp_service import obter_otp_temporario, OTPRetrievalError

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    print("\n" + "=" * 50)
    print("      RPA LMS - OBTENÇÃO DE OTP TEMPORÁRIO")
    print("=" * 50 + "\n")

    try:
        import os

        headless_mode = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

        otp = obter_otp_temporario(headless=headless_mode)
        print("\n" + "=" * 50)
        print(f"  SUCESSO! OTP TEMPORÁRIO OBTIDO: {otp}")
        print("=" * 50 + "\n")
    except OTPRetrievalError as e:
        print(f"\n[ERRO] Falha no fluxo de OTP: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}\n", file=sys.stderr)
        sys.exit(1)
