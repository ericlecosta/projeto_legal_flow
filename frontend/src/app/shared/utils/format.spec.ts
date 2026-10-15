import { formatDuration, formatRelativeDateTime, formatStepDuration } from './format';

describe('formatDuration', () => {
  it('formata minutos e segundos com dois dígitos', () => {
    expect(formatDuration(165)).toBe('02m 45s');
    expect(formatDuration(45)).toBe('00m 45s');
  });

  it('usa horas quando passa de 60 minutos', () => {
    expect(formatDuration(3720)).toBe('1h 02m');
  });

  it('retorna "-" sem duração', () => {
    expect(formatDuration(null)).toBe('-');
  });
});

describe('formatStepDuration', () => {
  it('mostra uma casa decimal', () => {
    expect(formatStepDuration(12)).toBe('12.0s');
    expect(formatStepDuration(0.5)).toBe('0.5s');
  });

  it('não quebra quando a etapa não tem duração (ex.: falha reportada pelo robô)', () => {
    expect(formatStepDuration(null)).toBe('-');
  });
});

describe('formatRelativeDateTime', () => {
  const now = new Date(2026, 9, 2, 15, 0, 0);

  it('usa Hoje, Ontem e Amanhã', () => {
    expect(formatRelativeDateTime(new Date(2026, 9, 2, 14, 15, 22).toISOString(), now)).toBe('Hoje, 14:15:22');
    expect(formatRelativeDateTime(new Date(2026, 9, 1, 18, 0, 0).toISOString(), now)).toBe('Ontem, 18:00:00');
    expect(formatRelativeDateTime(new Date(2026, 9, 3, 8, 0, 0).toISOString(), now, false)).toBe('Amanhã, 08:00');
  });

  it('usa dia/mês para datas mais distantes', () => {
    expect(formatRelativeDateTime(new Date(2026, 8, 28, 12, 0, 0).toISOString(), now)).toBe('28/09, 12:00:00');
  });
});
