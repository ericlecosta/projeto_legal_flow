"""
Script utilitário para execução e validação do fluxo completo de Login no LMS.
Obtém o OTP temporário, autentica no SSO e navega diretamente para o LMS.
"""

import sys
from pathlib import Path

# Garante que o diretório atual do RPA esteja no sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import time
import logging
from src.auth import fazer_login_lms, fechar_sessao_lms, LoginError

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("\n" + "=" * 55)
    print("        RPA LMS - FLUXO COMPLETO DE LOGIN")
    print("=" * 55 + "\n")

    page = None
    try:
        import os
        headless_mode = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

        # Executa o login completo e navega para LMS_INDEX
        page = fazer_login_lms(headless=headless_mode)

        print("\n" + "=" * 55)
        print("  LOGIN REALIZADO COM SUCESSO!")
        print(f"  URL Atual : {page.url}")
        print(f"  Título    : {page.title()}")
        print("=" * 55 + "\n")

        # Mantém a janela visível por alguns segundos para conferência visual apenas em modo com interface
        if not headless_mode:
            print("Navegador mantido aberto por 15 segundos para conferência visual...")
            time.sleep(15)

    except LoginError as e:
        print(f"\n[ERRO DE LOGIN] {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}\n", file=sys.stderr)
        sys.exit(1)
    finally:
        if page:
            print("Encerrando sessão do navegador...")
            fechar_sessao_lms(page)
            print("Sessão finalizada com sucesso.")
