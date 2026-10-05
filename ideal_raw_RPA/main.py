"""
Script utilitário para execução do fluxo completo de automação LMS:
1. Login e navegação inicial no SSO LGE + LMS.
2. Filtro e extração do relatório consolidado de contratos (relatorio_contratos.xlsx).
3. Extração detalhada de contratos filtrados por departamento "mao"
   (contract_review_management.xlsx).
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
from src.extraction import extrair_relatorio_contratos, ExtractError
from src.extract_contract import (
    extrair_contract_review_management,
    ExtractContractError,
)


# ---------------------------------------------------------------------------
# Configurações (podem ser sobrescritas por variáveis de ambiente)
# ---------------------------------------------------------------------------
SUBSIDIARY_CODE = os.getenv("LMS_SUBSIDIARY_CODE", "LGESP")
PERIODO = os.getenv("LMS_PERIODO", "3")
FILTRO_DEPARTAMENTO = os.getenv("LMS_FILTRO_DEPARTAMENTO", "mao")


def _configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def _banner(texto: str):
    print("\n" + "=" * 55)
    print(f"  {texto}")
    print("=" * 55)


def main() -> int:
    _configurar_logging()
    logger = logging.getLogger("rpa_lms.main")

    _banner("RPA LMS - EXTRAÇÃO DE CONTRATOS")
    print()

    page = None
    headless_mode = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

    try:
        # ------------------------------------------------------------------
        # ETAPA 1 — Login
        # ------------------------------------------------------------------
        logger.info("Iniciando Login no LMS...")
        page = fazer_login_lms(headless=headless_mode)

        # ------------------------------------------------------------------
        # ETAPA 2 — Extração do relatório consolidado
        # ------------------------------------------------------------------
        logger.info("Iniciando extração do relatório de contratos...")
        caminho_relatorio = extrair_relatorio_contratos(
            page=page,
            subsidiary_code=SUBSIDIARY_CODE,
            periodo=PERIODO,
        )
        logger.info(f"Relatório consolidado salvo em: {caminho_relatorio}")

        # ------------------------------------------------------------------
        # ETAPA 3 — Extração detalhada (contract_review_management)
        # ------------------------------------------------------------------
        logger.info(
            f"Iniciando extração detalhada "
            f"(filtro departamento='{FILTRO_DEPARTAMENTO}')..."
        )
        caminho_review = extrair_contract_review_management(
            page=page,
            caminho_relatorio=caminho_relatorio,
            filtro_departamento=FILTRO_DEPARTAMENTO,
        )
        logger.info(f"Contract review management salvo em: {caminho_review}")

        # ------------------------------------------------------------------
        # Sucesso
        # ------------------------------------------------------------------
        _banner("PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"  Relatório consolidado : {caminho_relatorio}")
        print(f"  Contract Review Mgmt  : {caminho_review}")
        print("=" * 55 + "\n")

        if not headless_mode:
            print("Navegador mantido aberto por 5 segundos para validação...")
            time.sleep(5)

        return 0

    except LoginError as e:
        print(f"\n[ERRO DE LOGIN] {e}\n", file=sys.stderr)
        return 1
    except ExtractError as e:
        print(f"\n[ERRO DE EXTRAÇÃO] {e}\n", file=sys.stderr)
        return 1
    except ExtractContractError as e:
        print(f"\n[ERRO DE EXTRAÇÃO DETALHADA] {e}\n", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}\n", file=sys.stderr)
        return 1
    finally:
        if page:
            print("Encerrando sessão do navegador...")
            fechar_sessao_lms(page)
            print("Sessão finalizada.")


if __name__ == "__main__":
    sys.exit(main())