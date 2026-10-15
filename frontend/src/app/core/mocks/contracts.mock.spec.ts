import { CONTRACTS_MOCK, getContractSummaryMock, listContractsMock } from './contracts.mock';

describe('contracts.mock', () => {
  it('busca por contraparte e revisor sem diferenciar maiúsculas', () => {
    expect(listContractsMock({ search: 'NORTE', progressState: '' }, 1, 10).count).toBe(1);
    expect(
      listContractsMock({ search: 'juliana', progressState: '' }, 1, 10).results[0].counterparty,
    ).toBe('Rio Negro Imóveis Ltda');
  });

  it('filtra por status e pagina', () => {
    const page = listContractsMock({ search: '', progressState: '' }, 2, 3);
    expect(page.count).toBe(CONTRACTS_MOCK.length);
    expect(page.results).toHaveLength(CONTRACTS_MOCK.length - 3);
    expect(
      listContractsMock({ search: '', progressState: 'Pending Assignment' }, 1, 10).count,
    ).toBe(1);
  });

  it('resume a base com a soma igual ao total', () => {
    const summary = getContractSummaryMock();
    expect(summary.byProgressState.reduce((sum, item) => sum + item.count, 0)).toBe(summary.total);
  });
});
