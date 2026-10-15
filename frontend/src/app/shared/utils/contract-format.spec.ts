import {
  buildContractQuery,
  formatAmount,
  formatContractPeriod,
  formatDateTime,
  formatIsoDate,
  progressStateLabel,
} from './contract-format';

describe('formatIsoDate', () => {
  it('converte AAAA-MM-DD sem mudar de dia por causa do fuso', () => {
    expect(formatIsoDate('2026-12-01')).toBe('01/12/2026');
  });

  it('retorna "-" sem data e o próprio texto quando não reconhece', () => {
    expect(formatIsoDate(null)).toBe('-');
    expect(formatIsoDate('ontem')).toBe('ontem');
  });
});

describe('formatContractPeriod', () => {
  it('monta o período completo ou parcial', () => {
    expect(formatContractPeriod('2026-12-01', '2027-11-30')).toBe('01/12/2026 a 30/11/2027');
    expect(formatContractPeriod('2026-12-01', null)).toBe('desde 01/12/2026');
    expect(formatContractPeriod(null, '2027-11-30')).toBe('até 30/11/2027');
    expect(formatContractPeriod(null, null)).toBe('-');
  });
});

describe('formatAmount', () => {
  it('usa o formato brasileiro com a moeda na frente', () => {
    expect(formatAmount(11145.04, 'USD')).toBe('USD 11.145,04');
    expect(formatAmount(9240.6, null)).toBe('9.240,60');
    expect(formatAmount(null, 'BRL')).toBe('-');
  });
});

describe('progressStateLabel', () => {
  it('traduz os status da legenda e mantém os desconhecidos', () => {
    expect(progressStateLabel('Legal Review in Progress')).toBe('Revisão do jurídico');
    expect(progressStateLabel('Effective Contract')).toBe('Contrato vigente');
    expect(progressStateLabel('Novo Status do LMS')).toBe('Novo Status do LMS');
    expect(progressStateLabel(null)).toBe('Sem status');
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
