/** Contrato da base Ideal Raw, como a API devolve em /api/contracts/ (datas em AAAA-MM-DD). */
export interface Contract {
  id: number;
  contractNumber: string;
  managementNumber: string | null;
  counterparty: string | null;
  contractName: string | null;
  contractType: string | null;
  requester: string | null;
  department: string | null;
  /** Status do LMS (Progress State), em inglês como vem do sistema. */
  progressState: string | null;
  legalReviewer: string | null;
  periodStart: string | null;
  periodEnd: string | null;
  reviewRequestedAt: string | null;
  legalReviewStartedAt: string | null;
  reviewCompletedAt: string | null;
  consentRequestedAt: string | null;
  consentCompletedAt: string | null;
  approvalRequestedAt: string | null;
  approvalCompletedAt: string | null;
  effectiveAt: string | null;
  bizDropCompletedAt: string | null;
  currency: string | null;
  amount: number | null;
  flags: Record<string, boolean>;
  raw: Record<string, string | null>;
  /** Linha da Base Ideal: colunas e valores da planilha (BASE_IDEAL_COLUMNS). */
  baseIdeal: Record<string, BaseIdealValue>;
  lastExecutionId: number | null;
  /** ISO 8601 */
  updatedAt: string;
}

export type BaseIdealValue = string | number | null;

/**
 * Colunas da Base Ideal, com os mesmos nomes e na mesma ordem da planilha do robô
 * (backend/app/services/base_ideal.py).
 */
export const BASE_IDEAL_COLUMNS = [
  'Contract number',
  'Counterparty',
  'Contract name',
  'Main Contract Type',
  'Contract type',
  'The person in charge',
  'Department of the person in charge',
  'Progress State',
  'Start date',
  'End date',
  'Request Date',
  'Request Legal Review',
  'Review completed',
  'Agreement request',
  'Agreement has been completed',
  'Approval request',
  'Approval request completed',
  'Register the conclusion of contract',
  'Biz-Drop Completed',
  'Qty Review',
  'Reviewer',
  'Contract currency',
  'Amount',
] as const;

export type BaseIdealColumn = (typeof BASE_IDEAL_COLUMNS)[number];

/** Formatos da exportação (GET /api/contracts/export/?format=). */
export type ExportFormat = 'xlsx' | 'xls' | 'csv' | 'pdf';

export const EXPORT_FORMATS: { format: ExportFormat; label: string; description: string }[] = [
  { format: 'xlsx', label: 'Excel (.xlsx)', description: 'Excel 2007 ou mais novo' },
  { format: 'xls', label: 'Excel 97-2003 (.xls)', description: 'Formato antigo do Excel' },
  { format: 'csv', label: 'CSV (.csv)', description: 'Separado por ponto e vírgula' },
  { format: 'pdf', label: 'PDF (.pdf)', description: 'Para imprimir ou compartilhar' },
];

export interface ContractFilters {
  search: string;
  /** '' = todos os status */
  progressState: string;
}

export interface ProgressStateCount {
  progressState: string | null;
  count: number;
}

export interface ContractSummary {
  total: number;
  byProgressState: ProgressStateCount[];
  /** ISO 8601 */
  lastUpdatedAt: string | null;
  lastExecutionId: number | null;
}

export type ProgressTone = 'success' | 'warning' | 'danger' | 'neutral' | 'info';

const TONES: Record<string, ProgressTone> = {
  'Effective Contract': 'success',
  'Approval Completed': 'success',
  'Contract Expired': 'neutral',
  'Biz-Drop': 'warning',
  'Approval for the Biz-Drop': 'warning',
  'Biz-Holding': 'warning',
  'Approval Rejected': 'danger',
  'Request for Consent Rejected': 'danger',
};

export function progressTone(state: string | null): ProgressTone {
  if (!state) return 'neutral';
  return TONES[state] ?? 'info';
}
