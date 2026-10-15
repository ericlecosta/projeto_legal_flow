import { Contract, ContractFilters, ContractSummary } from '../../shared/models/contract.model';
import { Page } from '../../shared/models/execution.model';

/** Contratos fictícios para trabalhar no front sem a API (environment.useMocks). */
function contract(id: number, overrides: Partial<Contract>): Contract {
  return {
    id,
    contractNumber: `C20268${String(14000 + id).padStart(5, '0')}`,
    managementNumber: null,
    counterparty: null,
    contractName: null,
    contractType: null,
    requester: null,
    department: 'LGESP GA Support Part - MAO',
    progressState: null,
    legalReviewer: null,
    periodStart: null,
    periodEnd: null,
    reviewRequestedAt: null,
    legalReviewStartedAt: null,
    reviewCompletedAt: null,
    consentRequestedAt: null,
    consentCompletedAt: null,
    approvalRequestedAt: null,
    approvalCompletedAt: null,
    effectiveAt: null,
    bizDropCompletedAt: null,
    currency: 'BRL',
    amount: null,
    flags: {},
    raw: {},
    lastExecutionId: 1043,
    updatedAt: '2026-10-15T09:12:00-04:00',
    ...overrides,
  };
}

export const CONTRACTS_MOCK: Contract[] = [
  contract(1, {
    counterparty: 'Rio Negro Imóveis Ltda',
    contractName: 'Termination - Rental MAO',
    contractType: 'Leasing/Rental/Real Estate',
    progressState: 'Approval Completed',
    legalReviewer: 'Juliana Prado',
    periodStart: '2026-03-24',
    periodEnd: '2026-04-18',
    reviewRequestedAt: '2026-04-17',
    amount: 9240.61,
  }),
  contract(2, {
    counterparty: 'Norte Tech Engenharia Ltda',
    contractName: 'Support Contract Renew for L4 Switches',
    contractType: 'General Services/Contracting',
    department: 'LGESP IT CNS Team - MAO',
    progressState: 'Effective Contract',
    legalReviewer: 'Marcos Vieira',
    periodStart: '2026-12-01',
    periodEnd: '2027-11-30',
    reviewRequestedAt: '2026-07-28',
    currency: 'USD',
    amount: 11145.04,
  }),
  contract(3, {
    counterparty: 'Amazonas Logística S.A.',
    contractName: 'Road Freight MAO-SP',
    contractType: 'Logistics',
    progressState: 'Legal Review in Progress',
    legalReviewer: 'Patrícia Nogueira',
    reviewRequestedAt: '2026-10-06',
  }),
  contract(4, {
    counterparty: 'Manaus Embalagens Ltda',
    contractName: 'EPS Packaging Supply',
    contractType: 'Purchase/Supply',
    progressState: 'Pending Assignment',
    reviewRequestedAt: '2026-10-13',
  }),
];

export function listContractsMock(
  filters: ContractFilters,
  page: number,
  pageSize: number,
): Page<Contract> {
  const term = filters.search.trim().toLowerCase();
  const rows = CONTRACTS_MOCK.filter(
    (c) =>
      (!filters.progressState || c.progressState === filters.progressState) &&
      (!term ||
        [c.contractNumber, c.counterparty, c.contractName, c.legalReviewer].some((v) =>
          v?.toLowerCase().includes(term),
        )),
  );
  return { count: rows.length, results: rows.slice((page - 1) * pageSize, page * pageSize) };
}

export function getContractSummaryMock(): ContractSummary {
  const counts = new Map<string | null, number>();
  for (const c of CONTRACTS_MOCK)
    counts.set(c.progressState, (counts.get(c.progressState) ?? 0) + 1);
  return {
    total: CONTRACTS_MOCK.length,
    byProgressState: [...counts].map(([progressState, count]) => ({ progressState, count })),
    lastUpdatedAt: '2026-10-15T09:12:00-04:00',
    lastExecutionId: 1043,
  };
}
