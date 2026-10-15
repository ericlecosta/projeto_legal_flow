import { PROGRESS_STATE_LABELS, progressTone } from './contract.model';
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

describe('legendas', () => {
  it('cobre os 17 status da Base Ideal', () => {
    expect(Object.keys(PROGRESS_STATE_LABELS)).toHaveLength(17);
  });

  it('tem nome para o fluxo do robô real', () => {
    expect(FLOW_LABELS.contract_extraction).toBe('Extração de contratos');
  });
});
