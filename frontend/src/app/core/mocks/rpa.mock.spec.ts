import { getExecutionMock, getOverviewMock, listExecutionsMock } from './rpa.mock';

describe('rpa.mock', () => {
  it('pagina e filtra execuções por status', () => {
    const page = listExecutionsMock({ period: 'all', status: 'failed', flow: 'all' }, 1, 10);
    expect(page.count).toBeGreaterThan(0);
    expect(page.results.length).toBeLessThanOrEqual(10);
    expect(page.results.every((e) => e.status === 'failed')).toBe(true);
  });

  it('retorna as execuções mais recentes primeiro', () => {
    const { results } = listExecutionsMock({ period: '7d', status: 'all', flow: 'all' }, 1, 10);
    expect(results[0].id).toBe(1042);
  });

  it('marca a etapa da falha e cancela as seguintes', () => {
    const detail = getExecutionMock(1042)!;
    expect(detail.steps.map((s) => s.status)).toEqual(['success', 'success', 'failed', 'skipped', 'skipped']);
    expect(detail.error?.title).toBe('Timeout no Elemento SSO');
  });

  it('retorna null para execução inexistente', () => {
    expect(getExecutionMock(1)).toBeNull();
  });

  it('calcula a visão geral de forma consistente', () => {
    const overview = getOverviewMock();
    expect(overview.succeeded + overview.failed).toBe(overview.totalExecutions);
    expect(overview.capturedTrend).toHaveLength(7);
  });
});
