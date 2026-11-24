"""Extrai contratos do LMS e preenche a planilha Ideal RAW."""

import logging
import os
from pathlib import Path
import sys
import tempfile

from openpyxl import Workbook

from preencher_base_ideal import preencher_base_ideal
from src.auth import fazer_login_lms, fechar_sessao_lms
from src.extract_contract import extrair_contract_review_management
from src.extraction import extrair_relatorio_contratos


def salvar_pendencias(pendencias, destino):
    """Grava a lista da execução atual, inclusive quando estiver vazia."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    folha = workbook.active
    folha.title = "Pendências"
    colunas = ("Contract Number", "Department of the person in charge", "Motivo")
    folha.append(colunas)
    for item in pendencias:
        folha.append([item.get(coluna, "") for coluna in colunas])
        for celula in folha[folha.max_row]:
            celula.data_type = "s"
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".xlsx", delete=False) as arquivo:
            temporario = Path(arquivo.name)
        workbook.save(temporario)
        workbook.close()
        temporario.replace(destino)
    finally:
        workbook.close()
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    pasta = Path(__file__).resolve().parent
    destino = pasta / "downloads" / "Base Ideal preenchida.xlsx"
    modelo = pasta / "modelo" / "Base Ideal.xlsx"
    arquivo_pendencias = pasta / "downloads" / "Pendencias contratos.xlsx"
    pendencias = []
    page = None
    try:
        page = fazer_login_lms(headless=os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes"))
        relatorio = extrair_relatorio_contratos(
            page, subsidiary_code=os.getenv("LMS_SUBSIDIARY_CODE", "LGESP"),
            periodo=os.getenv("LMS_PERIODO", "3"),
            caminho_destino=str(pasta / "downloads" / "relatorio_contratos.xlsx"),
        )
        detalhes = extrair_contract_review_management(
            page, relatorio, filtro_departamento=os.getenv("LMS_FILTRO_DEPARTAMENTO", "mao"),
            pendencias=pendencias,
        )
        quantidade = preencher_base_ideal(detalhes, modelo, destino)
        salvar_pendencias(pendencias, arquivo_pendencias)
        logging.info("Base Ideal gerada: %s (%s contratos).", destino, quantidade)
        if pendencias:
            logging.warning("Base parcial: %s contrato(s) com pendência. Consulte: %s", len(pendencias), arquivo_pendencias)
        else:
            logging.info("Nenhum contrato pendente. Lista da execução: %s", arquivo_pendencias)
        return 0
    except Exception:
        logging.exception("Falha ao gerar a Base Ideal.")
        return 1
    finally:
        if page is not None:
            fechar_sessao_lms(page)


if __name__ == "__main__":
    sys.exit(main())
