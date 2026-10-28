import { BASE_IDEAL_COLUMNS, progressTone } from './contract.model';
import { FLOW_LABELS } from './execution.model';

describe('progressTone', () => {
  it('separa concluídos, desistências e rejeições', () => {
    expect(progressTone('Effective Contract')).toBe('success');
    expect(progressTone('Biz-Drop')).toBe('warning');
    expect(progressTone('Approval Rejected')).toBe('danger');
    expect(progressTone('Contract Expired')).toBe('neutral');
  });

  it('trata status em andamento e ausentes', () => {
    expect(progressTone('Legal Review in Progress')).toBe('info');
    expect(progressTone(null)).toBe('neutral');
  });
});

describe('Base Ideal', () => {
  it('tem as 23 colunas da planilha, sem repetição', () => {
    expect(BASE_IDEAL_COLUMNS).toHaveLength(23);
    expect(new Set(BASE_IDEAL_COLUMNS).size).toBe(23);
    expect(BASE_IDEAL_COLUMNS[0]).toBe('Contract number');
    expect(BASE_IDEAL_COLUMNS.at(-1)).toBe('Amount');
  });

  it('tem nome para o fluxo do robô real', () => {
    expect(FLOW_LABELS.contract_extraction).toBe('Extração de contratos');
  });
});
