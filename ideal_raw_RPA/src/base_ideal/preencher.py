"""
Tratamento da extração (contract_review_management.xlsx) para o formato da Base Ideal:
uma linha por contrato, nas 22 colunas do modelo, com as regras da aba Legenda.

Roda dentro do fluxo do robô (src/pipeline.py) ou sozinho, sem acessar o LMS
(ideal_raw_RPA/preencher_base_ideal.py).
"""

from copy import copy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import re
import tempfile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

MODELO_PADRAO = Path(__file__).resolve().parent / "modelo" / "Base_Ideal_padrao.xlsx"
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
    "Request Date": "Request Date",
    "Request Legal Review": "Request Legal Review",
    "Review completed": "Review Completed",
    "Agreement request": "Legal Team Consent in Progress",
    "Agreement has been completed": "Legal Team Consent Completed",
    "Approval request": "Processing Approval for Execution",
    "Approval request completed": "Approval Completed",
    "Register the conclusion of contract": "Contract Expired",
    "Biz-Drop Completed": "Biz-Drop Completed",
    "Qty Review": "Qty Review",
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
# Nomes que a coluna "Request Date" já teve na extração (planilhas antigas continuam aceitas)
ALIASES_ORIGEM = {
    "Request Date": ("I requested a review of the contract.", "I request a review of the contract"),
}
# Colunas adicionadas recentemente na extração (planilhas antigas sem elas recebem valor padrão)
COLUNAS_OPCIONAIS_ORIGEM = {"Qty Review"}
CAMPOS_DATA = {
    "Start date",
    "End date",
    "Request Date",
    "Request Legal Review",
    "Review completed",
    "Agreement request",
    "Agreement has been completed",
    "Approval request",
    "Approval request completed",
    "Register the conclusion of contract",
    "Biz-Drop Completed",
}


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
    if campo == "Qty Review":
        if valor is None or str(valor).strip() == "":
            return 0
        if isinstance(valor, bool):
            return int(valor)
        if isinstance(valor, (int, float)):
            return int(valor)
        texto_qty = str(valor).strip()
        if re.fullmatch(r"\d+(?:\.0+)?", texto_qty):
            return int(float(texto_qty))
        return valor
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if campo == "Counterparty":
        identificador = re.search(r"\(\s*\d[\d./\s-]*\)\s*(?::.*)?$", texto, re.DOTALL)
        return texto[: identificador.start()].strip() or valor if identificador else valor
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


def _eh_biz_drop(linha, colunas):
    """Detecta se a linha está em Biz-Drop pela flag Biz-Drop Status ou pela data Biz-Drop Completed."""
    col_status = colunas.get(normalizar("Biz-Drop Status"))
    if col_status is not None:
        val_status = linha[col_status]
        if val_status is True or normalizar(val_status) in {"verdadeiro", "true", "1", "1.0"}:
            return True
    col_data = colunas.get(normalizar("Biz-Drop Completed"))
    val_data = linha[col_data] if col_data is not None else None
    if val_data is not None and str(val_data).strip() != "":
        # Se a planilha tem Biz-Drop Status explícito como False e todas as colunas de data iguais (teste sintético), respeita o False
        if col_status is not None:
            return True
        col_efetivo = colunas.get(normalizar("Effective Contract"))
        if col_efetivo is None or not linha[col_efetivo]:
            return True
    return False


def ler_registros(origem):
    """Lê a extração e devolve um registro (dict com os campos da Base Ideal) por contrato.

    Contratos com status que a base não usa (Biz-Holding, Signed Contract Registered) ficam de fora;
    nos status sem data (amarelos da Legenda), as datas ficam vazias. Valida tudo antes de devolver.
    """
    fonte = load_workbook(Path(origem), data_only=True)
    try:
        entrada = fonte.active
        colunas = {normalizar(c.value): i for i, c in enumerate(entrada[1]) if c.value}
        for coluna, aliases in ALIASES_ORIGEM.items():
            for alias in aliases:
                if normalizar(alias) in colunas:
                    colunas.setdefault(normalizar(MAPEAMENTO[coluna]), colunas[normalizar(alias)])
        obrigatorias = {v for v in (*MAPEAMENTO.values(), "Effective Contract") if v not in COLUNAS_OPCIONAIS_ORIGEM}
        faltantes = sorted({v for v in obrigatorias if normalizar(v) not in colunas})
        if faltantes:
            raise ValueError(f"Colunas ausentes na origem: {', '.join(faltantes)}")
        registros = []
        for numero, linha in enumerate(entrada.iter_rows(min_row=2, values_only=True), 2):
            if all(v is None for v in linha):
                continue
            estado_bruto = "Biz-Drop" if _eh_biz_drop(linha, colunas) else linha[colunas[normalizar("Progress State")]]
            status = status_progress_state(estado_bruto)
            if status == 2:
                continue
            try:
                registros.append(
                    {
                        campo: (
                            None
                            if status == 1 and campo in CAMPOS_DATA
                            else (
                                conclusao_contrato(
                                    linha[colunas[normalizar("Contract Expired")]],
                                    linha[colunas[normalizar("Effective Contract")]],
                                )
                                if campo == "Register the conclusion of contract"
                                else (
                                    transformar("Progress State", estado_bruto)
                                    if campo == "Progress State"
                                    else transformar(
                                        campo,
                                        linha[colunas[normalizar(coluna)]] if normalizar(coluna) in colunas else None,
                                    )
                                )
                            )
                        )
                        for campo, coluna in MAPEAMENTO.items()
                    }
                )
            except ValueError as exc:
                raise ValueError(f"Linha {numero}: {exc}") from exc
        return registros
    finally:
        fonte.close()


def gravar_base_ideal(registros, modelo, destino):
    """Grava os registros no modelo, substituindo os exemplos e mantendo o cabeçalho na linha 1."""
    modelo, destino = Path(modelo).resolve(), Path(destino).resolve()
    base = load_workbook(modelo)
    temporario = None
    try:
        saida = base.active
        destinos = {str(c.value).strip(): c.column for c in saida[1] if c.value}
        if set(MAPEAMENTO) - destinos.keys():
            raise ValueError(f"Campos ausentes no modelo: {sorted(set(MAPEAMENTO) - destinos.keys())}")
        estilos = {c.column: (copy(c._style), c.number_format) for c in saida[3]}
        if saida.max_row > 1:
            saida.delete_rows(2, saida.max_row - 1)
        for numero, registro in enumerate(registros, 2):
            for campo, valor in registro.items():
                celula = saida.cell(numero, destinos[campo], valor)
                if celula.column in estilos:
                    celula._style = copy(estilos[celula.column][0])
                if campo == "Amount":
                    celula.number_format = "#,##0.00"
                # Texto da origem nunca deve virar uma fórmula Excel.
                if isinstance(valor, str):
                    celula.data_type = "s"
        for coluna in saida.iter_cols():
            largura = max(
                (
                    len(linha)
                    for celula in coluna
                    if celula.value is not None
                    for linha in str(celula.value).splitlines()
                ),
                default=0,
            )
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
        # NamedTemporaryFile cria com permissão 0600 (só o dono lê); libera leitura/escrita para o host quando roda em Docker
        temporario.chmod(0o666)
        temporario.replace(destino)
    finally:
        base.close()
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def preencher_base_ideal(origem, modelo, destino):
    """Substitui os exemplos por uma linha por contrato, mantendo o cabeçalho na linha 1.

    Valida todos os dados antes de salvar; não permite sobrescrever a origem.
    O destino pode ser o próprio modelo, quando explicitamente solicitado.
    """
    if Path(destino).resolve() == Path(origem).resolve():
        raise ValueError("O destino não pode sobrescrever a planilha de origem.")
    registros = ler_registros(origem)
    gravar_base_ideal(registros, modelo, destino)
    return len(registros)
