import { BaseIdealValue } from '../models/contract.model';

const pad = (value: number) => String(value).padStart(2, '0');

/**
 * Valor de uma célula da Base Ideal como a planilha mostra: Amount no formato #,##0.00
 * (em português: 810.184,80); o resto do jeito que veio; célula vazia como ''.
 */
export function formatBaseIdealValue(column: string, value: BaseIdealValue | undefined): string {
  if (value == null) return '';
  if (column === 'Amount' && typeof value === 'number') {
    return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return String(value);
}

/** '2026-10-15T09:30:00-04:00' → '15/10/2026 09:30' (horário local). */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** Filtros da tela como parâmetros da API (só os preenchidos). */
export function buildContractFilterParams(filters: {
  search: string;
  progressState: string;
}): Record<string, string> {
  const params: Record<string, string> = {};
  const search = filters.search.trim();
  if (search) params['search'] = search;
  if (filters.progressState) params['progress_state'] = filters.progressState;
  return params;
}

/** Parâmetros de /api/contracts/ (só os filtros preenchidos). */
export function buildContractQuery(
  filters: { search: string; progressState: string },
  page: number,
  pageSize: number,
): Record<string, string> {
  return {
    page: String(page),
    page_size: String(pageSize),
    ...buildContractFilterParams(filters),
  };
}
