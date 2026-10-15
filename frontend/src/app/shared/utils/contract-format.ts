import { PROGRESS_STATE_LABELS } from '../models/contract.model';

const pad = (value: number) => String(value).padStart(2, '0');

/** '2026-12-01' → '01/12/2026'. Datas sem horário: não passam por Date para não mudar de dia por fuso. */
export function formatIsoDate(iso: string | null | undefined): string {
  if (!iso) return '-';
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : iso;
}

/** Período do contrato: '01/12/2026 a 30/11/2027', 'desde 01/12/2026' ou '-'. */
export function formatContractPeriod(start: string | null, end: string | null): string {
  if (start && end) return `${formatIsoDate(start)} a ${formatIsoDate(end)}`;
  if (start) return `desde ${formatIsoDate(start)}`;
  if (end) return `até ${formatIsoDate(end)}`;
  return '-';
}

/** 11145.04 + 'USD' → 'USD 11.145,04'; sem moeda, só o número. */
export function formatAmount(amount: number | null, currency: string | null): string {
  if (amount == null) return '-';
  const value = amount.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return currency ? `${currency} ${value}` : value;
}

/** Nome do status em português; status desconhecido aparece como veio do LMS. */
export function progressStateLabel(state: string | null): string {
  if (!state) return 'Sem status';
  return PROGRESS_STATE_LABELS[state] ?? state;
}

/** '2026-10-15T09:30:00-04:00' → '15/10/2026 09:30' (horário local). */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** Parâmetros de /api/contracts/ (só os filtros preenchidos). */
export function buildContractQuery(
  filters: { search: string; progressState: string },
  page: number,
  pageSize: number,
): Record<string, string> {
  const params: Record<string, string> = { page: String(page), page_size: String(pageSize) };
  const search = filters.search.trim();
  if (search) params['search'] = search;
  if (filters.progressState) params['progress_state'] = filters.progressState;
  return params;
}
