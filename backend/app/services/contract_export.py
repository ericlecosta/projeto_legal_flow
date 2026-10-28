"""
Exportação da Base Ideal (tela Contratos) em CSV, XLSX, XLS e PDF.
Todos os formatos têm o cabeçalho e os valores da planilha do robô (app/services/base_ideal.py).
"""

import csv
import io
from datetime import datetime
from typing import Literal

import xlwt
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

from app.services.base_ideal import AMOUNT_COLUMN, BASE_IDEAL_COLUMNS, Value

ExportFormat = Literal["csv", "xlsx", "xls", "pdf"]

MEDIA_TYPES: dict[str, str] = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "pdf": "application/pdf",
}

SHEET_TITLE = "Base Ideal"
AMOUNT_FORMAT = "#,##0.00"


def _amount_br(value: Value) -> str:
    """72000.5 -> '72.000,50' (como o Excel em português mostra o formato #,##0.00)."""
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return "" if value is None else str(value)


def _text(column: str, value: Value) -> str:
    if column == AMOUNT_COLUMN:
        return _amount_br(value)
    return "" if value is None else str(value)


def _width(rows: list[dict[str, Value]], column: str) -> int:
    """Mesma regra da planilha do robô: entre 15 e 45 caracteres, pelo maior conteúdo."""
    longest = max([len(column), *(len(_text(column, row[column])) for row in rows)])
    return max(15, min(longest + 2, 45))


def to_csv(rows: list[dict[str, Value]]) -> bytes:
    """CSV para o Excel em português: separador ';', decimal com vírgula e BOM para os acentos."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(BASE_IDEAL_COLUMNS)
    for row in rows:
        writer.writerow(
            [
                (
                    f"{row[c]:.2f}".replace(".", ",")
                    if c == AMOUNT_COLUMN and isinstance(row[c], (int, float))
                    else _text(c, row[c])
                )
                for c in BASE_IDEAL_COLUMNS
            ]
        )
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def to_xlsx(rows: list[dict[str, Value]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = SHEET_TITLE
    sheet.append(BASE_IDEAL_COLUMNS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for number, row in enumerate(rows, 2):
        for index, column in enumerate(BASE_IDEAL_COLUMNS, 1):
            cell = sheet.cell(number, index, row[column])
            if isinstance(row[column], str):
                cell.data_type = "s"  # texto vindo do LMS nunca vira fórmula
            if column == AMOUNT_COLUMN:
                cell.number_format = AMOUNT_FORMAT
    for index, column in enumerate(BASE_IDEAL_COLUMNS, 1):
        sheet.column_dimensions[get_column_letter(index)].width = _width(rows, column)
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = sheet.dimensions
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_xls(rows: list[dict[str, Value]]) -> bytes:
    """Excel 97-2003, para quem ainda usa o formato antigo (limite de 65.535 contratos)."""
    workbook = xlwt.Workbook(encoding="utf-8")
    sheet = workbook.add_sheet(SHEET_TITLE)
    header = xlwt.easyxf("font: bold on")
    amount = xlwt.easyxf(num_format_str=AMOUNT_FORMAT)
    for index, column in enumerate(BASE_IDEAL_COLUMNS):
        sheet.write(0, index, column, header)
        sheet.col(index).width = 256 * _width(rows, column)
    for number, row in enumerate(rows, 1):
        for index, column in enumerate(BASE_IDEAL_COLUMNS):
            value = row[column]
            if value is None:
                continue
            if column == AMOUNT_COLUMN and isinstance(value, (int, float)):
                sheet.write(number, index, value, amount)
            else:
                sheet.write(number, index, value)
    sheet.set_panes_frozen(True)
    sheet.set_horz_split_pos(1)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


# Largura relativa das colunas no PDF (textos longos ganham mais espaço)
_PDF_WEIGHTS = {
    "Counterparty": 2.2,
    "Contract name": 2.6,
    "Contract type": 1.6,
    "Department of the person in charge": 1.8,
    "Amount": 1.5,
}


def to_pdf(rows: list[dict[str, Value]], generated_at: datetime, filters: str = "") -> bytes:
    buffer = io.BytesIO()
    page = landscape(A3)
    margin = 8 * mm
    document = SimpleDocTemplate(
        buffer,
        pagesize=page,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=SHEET_TITLE,
    )
    title = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=12, leading=15)
    note = ParagraphStyle("note", fontName="Helvetica", fontSize=7, leading=9, textColor=colors.grey)
    cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=5.5, leading=6.8)
    head = ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold")
    right = ParagraphStyle("right", parent=cell, alignment=2)

    def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    data = [[paragraph(c, head) for c in BASE_IDEAL_COLUMNS]]
    for row in rows:
        data.append([paragraph(_text(c, row[c]), right if c == AMOUNT_COLUMN else cell) for c in BASE_IDEAL_COLUMNS])
    weights = [_PDF_WEIGHTS.get(c, 1.0) for c in BASE_IDEAL_COLUMNS]
    available = page[0] - 2 * margin
    table = Table(data, colWidths=[available * w / sum(weights) for w in weights], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    subtitle = f"{len(rows)} contrato(s) · gerado em {generated_at:%d/%m/%Y %H:%M}"
    if filters:
        subtitle += f" · filtros: {filters}"
    document.build([paragraph(SHEET_TITLE, title), paragraph(subtitle, note), Spacer(1, 3 * mm), table])
    return buffer.getvalue()


def export(rows: list[dict[str, Value]], fmt: ExportFormat, generated_at: datetime, filters: str = "") -> bytes:
    if fmt == "csv":
        return to_csv(rows)
    if fmt == "xlsx":
        return to_xlsx(rows)
    if fmt == "xls":
        return to_xls(rows)
    return to_pdf(rows, generated_at, filters)


def filename(fmt: ExportFormat, generated_at: datetime) -> str:
    return f"base_ideal_{generated_at:%Y%m%d_%H%M}.{fmt}"
