"""
Preenche o modelo Base Ideal com uma extração já baixada, sem acessar o LMS.
O tratamento fica em src/base_ideal; no fluxo do robô ele roda como a etapa "Tratamento da base".

    python preencher_base_ideal.py [--origem ...] [--modelo ...] [--destino ...]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.base_ideal import MODELO_PADRAO, preencher_base_ideal  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, default=ROOT / "docs/planilha_de_dados/contract_review_management.xlsx")
    parser.add_argument("--modelo", type=Path, default=MODELO_PADRAO)
    parser.add_argument("--destino", type=Path, default=ROOT / "docs/Base Ideal preenchida.xlsx")
    args = parser.parse_args()
    quantidade = preencher_base_ideal(args.origem, args.modelo, args.destino)
    print(f"{quantidade} contratos gravados em {args.destino.resolve()}")


if __name__ == "__main__":
    main()
