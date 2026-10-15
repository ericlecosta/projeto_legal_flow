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
  lastExecutionId: number | null;
  /** ISO 8601 */
  updatedAt: string;
}

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

/** Tradução dos status do LMS (aba "Legenda" da Base Ideal). */
export const PROGRESS_STATE_LABELS: Record<string, string> = {
  'Approval Completed': 'Aprovação concluída',
  'Approval for the Biz-Drop': 'Aprovação da desistência',
  'Approval Rejected': 'Aprovação rejeitada',
  'Biz-Drop': 'Desistência do contrato',
  'Biz-Holding': 'Suspensão do contrato',
  'Contract Expired': 'Vigência expirada',
  'Effective Contract': 'Contrato vigente',
  'Legal Comments Provided': 'Comentários do jurídico',
  'Legal Review in Progress': 'Revisão do jurídico',
  'Legal Team Consent Completed': 'Consenso do jurídico concluído',
  'Legal Team Consent in Progress': 'Consenso do jurídico',
  'Pending Assignment': 'Pendente de revisor',
  'Processing Approval for Execution': 'Aprovação em andamento',
  'Request for Consent Rejected': 'Consenso rejeitado',
  'Request Temporarily Saved': 'Rascunho',
  'Review Completed': 'Revisão concluída',
  'Signed Contract Registered': 'Contrato registrado',
};

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
