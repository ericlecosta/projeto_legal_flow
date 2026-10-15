"""
Script utilitário para execução do fluxo completo de automação LMS:
1. Login e navegação inicial.
2. Filtro e extração do relatório de contratos.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Garante que o diretório atual do RPA esteja no sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.auth import fazer_login_lms, fechar_sessao_lms, LoginError
from src.extraction.extract_service import extrair_relatorio_contratos, ExtractError

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("\n" + "=" * 55)
    print("      RPA LMS - EXECUÇÃO DE EXTRAÇÃO DE CONTRATOS")
    print("=" * 55 + "\n")

    page = None
    try:
        headless_mode = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

        # 1. Executa o fluxo de Login
        logger = logging.getLogger("rpa_lms.main")
        logger.info("Iniciando Login no LMS...")
        page = fazer_login_lms(headless=headless_mode)

        # 2. Executa a extração do relatório
        logger.info("Iniciando extração do relatório de contratos...")
        caminho_relatorio = extrair_relatorio_contratos(
            page=page,
            subsidiary_code="LGESP",
            periodo="3",
        )

        print("\n" + "=" * 55)
        print("  PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"  Relatório salvo em: {caminho_relatorio}")
        print("=" * 55 + "\n")

        if not headless_mode:
            print("Navegador mantido aberto por 5 segundos para validação...")
            time.sleep(5)

    except LoginError as e:
        print(f"\n[ERRO DE LOGIN] {e}\n", file=sys.stderr)
        sys.exit(1)
    except ExtractError as e:
        print(f"\n[ERRO DE EXTRAÇÃO] {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}\n", file=sys.stderr)
        sys.exit(1)
    finally:
        if page:
            print("Encerrando sessão do navegador...")
            fechar_sessao_lms(page)
            print("Sessão finalizada.")
