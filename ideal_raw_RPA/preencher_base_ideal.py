"""Preenche o modelo Base Ideal com a extração local, sem acessar o LMS."""

import argparse
from copy import copy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import re
import tempfile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
MAPEAMENTO = {
    "Contract number": "Management Number",
    "Counterparty": "Counterparty",
    "Contract name": "Contract Name",
    "Main Contract Type": "Contract Type",
    "Contract type": "Contract Type",
    "The person in charge": "Requester",
    "Department of the person in charge": "Department of the person in charge",
    "Progress State": "Progress State",
    "Start date": "Contract Period",
    "End date": "Contract Period",
    "Request Date": "I requested a review of the contract.",
    "Request Legal Review": "Request Legal Review",
    "Review completed": "Review Completed",
    "Agreement request": "Legal Team Consent in Progress",
    "Agreement has been completed": "Legal Team Consent Completed",
    "Approval request": "Processing Approval for Execution",
    "Approval request completed": "Approval Completed",
    "Register the conclusion of contract": "Contract Expired",
    "Biz-Drop Completed": "Biz-Drop Completed",
    "Reviewer": "A person in charge of legal (team)",
    "Contract currency": "Contract Amount",
    "Amount": "Contract Amount",
}

STATUS_PROGRESS_STATE = {
    "Approval Completed": 0,
    "Approval for the Biz-Drop": 1,
    "Approval Rejected": 1,
    "Biz-Drop": 0,
    "Biz-Holding": 2,
    "Contract Expired": 0,
    "Effective Contract": 0,
    "Legal Comments Provided": 1,
    "Legal Review in Progress": 0,
    "Legal Team Consent Completed": 0,
    "Legal Team Consent in Progress": 0,
    "Pending Assignment": 1,
    "Processing Approval for Execution": 0,
    "Request for Consent Rejected": 1,
    "Request Temporarily Saved": 1,
    "Review Completed": 0,
    "Signed Contract Registered": 2,
}
CAMPOS_DATA = {
    "Start date", "End date", "Request Date", "Request Legal Review",
    "Review completed", "Agreement request", "Agreement has been completed",
    "Approval request", "Approval request completed",
    "Register the conclusion of contract", "Biz-Drop Completed",
}
DATAS_SEMPRE_PREENCHIDAS = {"Start date", "End date", "Request Date"}


def normalizar(valor):
    return " ".join(str(valor or "").split()).casefold().rstrip(".")


def status_progress_state(valor):
    """Reconhece o estado mesmo quando o LMS acrescenta uma mensagem a ele."""
    texto = normalizar(valor)
    for estado, status in STATUS_PROGRESS_STATE.items():
        chave = normalizar(estado)
        if texto == chave or (texto.startswith(chave) and not texto[len(chave)].isalnum()):
            return status
    return None


def somente_data(valor):
    """Remove o horário e formata datas como AAAA-MM-DD."""
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d")
    if isinstance(valor, date):
        return valor.strftime("%Y-%m-%d")
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        try:
            return datetime.fromisoformat(texto).strftime("%Y-%m-%d")
        except ValueError:
            for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
                try:
                    return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return valor


def transformar(campo, valor):
    """Separa categorias, período ISO e valor original (ignora a conversão USD)."""
    if campo == "Progress State":
        texto_estado = normalizar(valor)
        for estado in STATUS_PROGRESS_STATE:
            chave = normalizar(estado)
            if texto_estado == chave or (texto_estado.startswith(chave) and not texto_estado[len(chave)].isalnum()):
                return estado
        return valor
    if campo == "Reviewer":
        texto_reviewer = str(valor or "").strip()
        gerente = re.search(r"\[Main manager\][ \t]*([^\r\n]*)", texto_reviewer, re.IGNORECASE)
        nome = gerente[1].strip() if gerente else ""
        return nome or valor
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if campo == "Counterparty":
        identificador = re.search(r"\(\s*\d[\d./\s-]*\)\s*(?::.*)?$", texto, re.DOTALL)
        return texto[:identificador.start()].strip() or valor if identificador else valor
    if campo == "The person in charge":
        return texto.split("(", 1)[0].strip() or valor
    if campo in ("Main Contract Type", "Contract type"):
        partes = [p.strip() for p in texto.splitlines() if p.strip()]
        return partes[0] if campo == "Main Contract Type" else partes[-1]
    if campo in ("Start date", "End date"):
        partes = re.split(r"\s*~\s*", texto)
        if len(partes) != 2:
            return "DATA INVÁLIDA"
        return somente_data(partes[0 if campo == "Start date" else 1])
    if campo in CAMPOS_DATA:
        return somente_data(valor)
    if campo in ("Contract currency", "Amount"):
        match = re.search(r"([\d,.]+)\s*\[([A-Za-z]{3})\]", texto)
        if not match:
            raise ValueError(f"Contract Amount sem valor/moeda reconhecíveis: {texto!r}")
        if campo == "Contract currency":
            return match[2].upper()
        # O LMS usa vírgula para milhares e ponto para decimais.
        return float(Decimal(match[1].replace(",", "")))
    return valor


def conclusao_contrato(expirado, efetivo):
    if expirado is True or normalizar(expirado) in {"verdadeiro", "true"}:
        return "Expirado"
    if expirado is False or normalizar(expirado) in {"falso", "false"}:
        if isinstance(efetivo, (date, datetime)):
            return somente_data(efetivo)
        if isinstance(efetivo, str):
            try:
                datetime.fromisoformat(efetivo.strip())
            except ValueError:
                return None
            return somente_data(efetivo)
    return None


def preencher_base_ideal(origem, modelo, destino):
    """Substitui os exemplos por uma linha por contrato, mantendo o cabeçalho na linha 1.

    Valida todos os dados antes de salvar; não permite sobrescrever a origem.
    O destino pode ser o próprio modelo, quando explicitamente solicitado.
    """
    origem, modelo, destino = map(lambda p: Path(p).resolve(), (origem, modelo, destino))
    if destino == origem:
        raise ValueError("O destino não pode sobrescrever a planilha de origem.")
    fonte = load_workbook(origem, data_only=True)
    base = load_workbook(modelo)
    temporario = None
    try:
        entrada, saida = fonte.active, base.active
        colunas = {normalizar(c.value): i for i, c in enumerate(entrada[1]) if c.value}
        # Compatibilidade com a grafia fornecida no mapeamento do usuário.
        alias = normalizar("I request a review of the contract")
        if alias in colunas:
            colunas.setdefault(normalizar(MAPEAMENTO["Request Date"]), colunas[alias])
        faltantes = sorted({v for v in (*MAPEAMENTO.values(), "Effective Contract")
                            if normalizar(v) not in colunas})
        destinos = {str(c.value).strip(): c.column for c in saida[1] if c.value}
        if faltantes:
            raise ValueError(f"Colunas ausentes na origem: {', '.join(faltantes)}")
        if set(MAPEAMENTO) - destinos.keys():
            raise ValueError(f"Campos ausentes no modelo: {sorted(set(MAPEAMENTO) - destinos.keys())}")
        estilos = {c.column: (copy(c._style), c.number_format) for c in saida[3]}
        registros = []
        for numero, linha in enumerate(entrada.iter_rows(min_row=2, values_only=True), 2):
            if all(v is None for v in linha):
                continue
            status = status_progress_state(linha[colunas[normalizar("Progress State")]])
            if status == 2:
                continue
            try:
                registros.append({campo: None if status == 1 and campo in CAMPOS_DATA - DATAS_SEMPRE_PREENCHIDAS
                                  else conclusao_contrato(linha[colunas[normalizar("Contract Expired")]],
                                                          linha[colunas[normalizar("Effective Contract")]])
                                  if campo == "Register the conclusion of contract"
                                  else transformar(campo, linha[colunas[normalizar(coluna)]])
                                  for campo, coluna in MAPEAMENTO.items()})
            except ValueError as exc:
                raise ValueError(f"Linha {numero}: {exc}") from exc
        if saida.max_row > 1:
            saida.delete_rows(2, saida.max_row - 1)
        for numero, registro in enumerate(registros, 2):
            for campo, valor in registro.items():
                celula = saida.cell(numero, destinos[campo], valor)
                if celula.column in estilos:
                    celula._style = copy(estilos[celula.column][0])
                if campo == "Amount":
                    celula.number_format = '#,##0.00'
                # Texto da origem nunca deve virar uma fórmula Excel.
                if isinstance(valor, str):
                    celula.data_type = "s"
        for coluna in saida.iter_cols():
            largura = max((len(linha) for celula in coluna if celula.value is not None
                           for linha in str(celula.value).splitlines()), default=0)
            saida.column_dimensions[get_column_letter(coluna[0].column)].width = max(15, min(largura + 2, 45))
            for celula in coluna:
                alinhamento = copy(celula.alignment)
                alinhamento.wrap_text = False
                alinhamento.vertical = "top"
                celula.alignment = alinhamento
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".xlsx", delete=False) as arquivo:
            temporario = Path(arquivo.name)
        base.save(temporario)
        base.close()
        temporario.replace(destino)
        return len(registros)
    finally:
        fonte.close()
        base.close()
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, default=ROOT / "docs/planilha_de_dados/contract_review_management.xlsx")
    parser.add_argument("--modelo", type=Path, default=ROOT / "docs/Base_Ideal_padrao.xlsx")
    parser.add_argument("--destino", type=Path, default=ROOT / "docs/Base Ideal preenchida.xlsx")
    args = parser.parse_args()
    quantidade = preencher_base_ideal(args.origem, args.modelo, args.destino)
    print(f"{quantidade} contratos gravados em {args.destino.resolve()}")


if __name__ == "__main__":
    main()
