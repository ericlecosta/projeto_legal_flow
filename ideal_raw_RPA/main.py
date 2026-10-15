"""
Execução do fluxo completo de automação LMS:
1. Login e navegação inicial no SSO LGE + LMS.
2. Filtro e extração do relatório consolidado de contratos (relatorio_contratos.xlsx).
3. Extração detalhada de contratos filtrados por departamento
   (contract_review_management.xlsx).
Cada etapa, os logs e o resultado são registrados na API do monitor (quando API_URL estiver definida).

Variáveis de ambiente:
    API_URL           URL da API do monitor (ex.: http://api:8000/api). Sem ela, o robô roda sem reportar.
    RPA_API_TOKEN     Token que a API exige para aceitar os dados do robô.
    RPA_TRIGGER       "manual" (padrão) ou "scheduled".
    LMS_SUBSIDIARY_CODE, LMS_PERIODO, LMS_FILTRO_DEPARTAMENTO, HEADLESS
"""

import logging
import os
import sys
import time
from pathlib import Path

# Garante que o diretório atual do RPA esteja no sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.auth import fazer_login_lms, fechar_sessao_lms  # noqa: E402
from src.extract_contract import extrair_contract_review_management  # noqa: E402
from src.extraction import extrair_relatorio_contratos  # noqa: E402
from src.pipeline import Servicos, executar_fluxo  # noqa: E402
from src.reporting import ApiLogHandler, MonitorClient  # noqa: E402

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
    headless_mode = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

    cliente = MonitorClient.from_env()
    handler = ApiLogHandler(cliente)
    logging.getLogger("rpa_lms").addHandler(handler)

    def fechar(page):
        if not headless_mode:
            print("Navegador mantido aberto por 5 segundos para validação...")
            time.sleep(5)
        fechar_sessao_lms(page)

    servicos = Servicos(
        login=lambda: fazer_login_lms(headless=headless_mode),
        extrair_relatorio=lambda page: extrair_relatorio_contratos(
            page=page, subsidiary_code=SUBSIDIARY_CODE, periodo=PERIODO
        ),
        extrair_detalhes=lambda page, caminho: extrair_contract_review_management(
            page=page, caminho_relatorio=caminho, filtro_departamento=FILTRO_DEPARTAMENTO
        ),
        fechar=fechar,
    )

    _banner("RPA LMS - EXTRAÇÃO DE CONTRATOS")
    if not cliente.ativo:
        print("  API_URL não definida: a execução não será registrada no monitor.")

    resultado = executar_fluxo(
        servicos, cliente, trigger=os.getenv("RPA_TRIGGER", "manual"), ao_fim_da_etapa=handler.flush
    )

    if resultado.sucesso:
        _banner("PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"  Relatório consolidado : {resultado.caminho_relatorio}")
        print(f"  Contract Review Mgmt  : {resultado.caminho_detalhes}")
        print("=" * 55 + "\n")
        return 0

    print(f"\n[{resultado.erro_titulo}] {resultado.erro_mensagem}\n", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
