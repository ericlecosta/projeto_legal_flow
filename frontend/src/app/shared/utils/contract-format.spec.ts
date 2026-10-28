import {
  buildContractFilterParams,
  buildContractQuery,
  formatBaseIdealValue,
  formatDateTime,
} from './contract-format';

describe('formatBaseIdealValue', () => {
  it('mostra Amount como o formato #,##0.00 da planilha, em português', () => {
    expect(formatBaseIdealValue('Amount', 810184.8)).toBe('810.184,80');
    expect(formatBaseIdealValue('Amount', 0)).toBe('0,00');
  });

  it('mantém datas, status e textos como vieram da planilha', () => {
    expect(formatBaseIdealValue('Start date', '2026-11-01')).toBe('2026-11-01');
    expect(formatBaseIdealValue('Progress State', 'Legal Review in Progress')).toBe(
      'Legal Review in Progress',
    );
    expect(formatBaseIdealValue('Register the conclusion of contract', 'Expirado')).toBe(
      'Expirado',
    );
    expect(formatBaseIdealValue('Qty Review', 2)).toBe('2');
    expect(formatBaseIdealValue('Amount', 'a definir')).toBe('a definir');
  });

  it('deixa a célula vazia quando a planilha não tem valor', () => {
    expect(formatBaseIdealValue('Review completed', null)).toBe('');
    expect(formatBaseIdealValue('Qty Review', undefined)).toBe('');
  });
});

describe('formatDateTime', () => {
  it('mostra data e hora local', () => {
    const iso = new Date(2026, 9, 15, 9, 5).toISOString();
    expect(formatDateTime(iso)).toBe('15/10/2026 09:05');
    expect(formatDateTime(undefined)).toBe('-');
  });
});

describe('buildContractQuery', () => {
  it('envia só os filtros preenchidos', () => {
    expect(buildContractQuery({ search: '  norte ', progressState: '' }, 2, 20)).toEqual({
      page: '2',
      page_size: '20',
      search: 'norte',
    });
    expect(buildContractQuery({ search: '', progressState: 'Biz-Drop' }, 1, 10)).toEqual({
      page: '1',
      page_size: '10',
      progress_state: 'Biz-Drop',
    });
  });
});

describe('buildContractFilterParams', () => {
  it('só os filtros, sem paginação (usado na exportação)', () => {
    expect(
      buildContractFilterParams({ search: ' sesi ', progressState: 'Review Completed' }),
    ).toEqual({ search: 'sesi', progress_state: 'Review Completed' });
    expect(buildContractFilterParams({ search: '', progressState: '' })).toEqual({});
  });
});
