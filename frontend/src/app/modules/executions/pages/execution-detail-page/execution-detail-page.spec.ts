import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ExecutionDetail } from '../../../../shared/models/execution.model';
import { ExecutionDetailPage } from './execution-detail-page';

/** Execução real do robô que falhou na extração (formato devolvido por /api/executions/:id/). */
const FALHA_DO_ROBO: ExecutionDetail = {
  id: 1,
  flow: 'contract_extraction',
  status: 'failed',
  trigger: 'manual',
  startedAt: '2026-10-15T09:06:18-04:00',
  finishedAt: '2026-10-15T09:08:19-04:00',
  durationSeconds: 121,
  records: null,
  steps: [
    { key: 'lms_login', label: 'Login no LMS', status: 'success', durationSeconds: 42 },
    {
      key: 'report_download',
      label: 'Download do relatório',
      status: 'success',
      durationSeconds: 0.3,
    },
    // Sem duração: o robô pode reportar a falha sem tempo medido
    {
      key: 'contract_details',
      label: 'Extração dos contratos',
      status: 'failed',
      durationSeconds: null,
    },
    { key: 'data_upload', label: 'Envio para o banco', status: 'skipped', durationSeconds: null },
  ],
  logs: [
    {
      timestamp: '2026-10-15T09:06:18-04:00',
      level: 'info',
      message: 'OTP obtido com sucesso: 483920',
    },
    {
      timestamp: '2026-10-15T09:06:20-04:00',
      level: 'info',
      message: "Captcha reconhecido: 'x7k2'",
    },
    {
      timestamp: '2026-10-15T09:08:19-04:00',
      level: 'error',
      message: 'Falha na extração dos contratos: page.wait_for_selector: Timeout 30000ms exceeded',
    },
  ],
  error: {
    title: 'Falha na extração dos contratos',
    message: 'page.wait_for_selector: Timeout 30000ms exceeded',
    screenshotUrl: null,
  },
};

const EM_ANDAMENTO: ExecutionDetail = {
  ...FALHA_DO_ROBO,
  id: 2,
  status: 'running',
  finishedAt: null,
  durationSeconds: null,
  error: null,
  steps: [
    { key: 'lms_login', label: 'Login no LMS', status: 'success', durationSeconds: 40 },
    {
      key: 'report_download',
      label: 'Download do relatório',
      status: 'success',
      durationSeconds: 12,
    },
    {
      key: 'contract_details',
      label: 'Extração dos contratos',
      status: 'running',
      durationSeconds: null,
    },
  ],
  logs: [
    { timestamp: '2026-10-15T09:07:00-04:00', level: 'info', message: '[12/52] Processando C12' },
    { timestamp: '2026-10-15T09:07:05-04:00', level: 'info', message: '[13/52] Processando C13' },
  ],
};

const SUCESSO_COM_AVISO: ExecutionDetail = {
  ...FALHA_DO_ROBO,
  id: 3,
  status: 'success',
  records: 52,
  error: null,
  steps: FALHA_DO_ROBO.steps.map((s) => ({ ...s, status: 'success', durationSeconds: 5 })),
  logs: [
    {
      timestamp: '2026-10-15T09:07:00-04:00',
      level: 'warning',
      message: 'Contrato C9 não encontrado na busca.',
    },
    {
      timestamp: '2026-10-15T09:08:00-04:00',
      level: 'success',
      message: 'Fluxo concluído com sucesso.',
    },
  ],
};

describe('ExecutionDetailPage', () => {
  let fixture: ComponentFixture<ExecutionDetailPage>;
  let http: HttpTestingController;
  let el: HTMLElement;

  async function render(execution: ExecutionDetail) {
    await TestBed.configureTestingModule({
      imports: [ExecutionDetailPage],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ExecutionDetailPage);
    el = fixture.nativeElement;
    fixture.componentRef.setInput('id', String(execution.id));
    fixture.detectChanges();
    // A página busca os dados com timer(0, 2000): deixa o primeiro disparo acontecer.
    await new Promise((resolve) => setTimeout(resolve, 0));
    http.expectOne(`/api/executions/${execution.id}/`).flush(execution);
    await settle();
  }

  async function settle() {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  const text = (selector?: string) =>
    (selector ? el.querySelector(selector)! : el).textContent!.replace(/\s+/g, ' ').trim();

  afterEach(() => {
    jest.restoreAllMocks();
    fixture.destroy();
  });

  it('explica a falha em linguagem simples, com o que fazer', async () => {
    await render(FALHA_DO_ROBO);

    const summary = text('[data-testid="summary"]');
    expect(summary).toContain('Não foi possível ler os contratos no LMS');
    expect(summary).toContain('O que fazer:');
    // O detalhe técnico fica guardado para o time de desenvolvimento
    const details = el.querySelector('[data-testid="summary"] details')!;
    expect(details.hasAttribute('open')).toBe(false);
    expect(details.textContent).toContain('page.wait_for_selector: Timeout 30000ms exceeded');

    const steps = [...el.querySelectorAll('[data-testid="step-status"]')].map((s) =>
      s.textContent!.trim(),
    );
    expect(steps).toEqual([
      'Concluída em 42 s',
      'Concluída em menos de 1 s',
      'Não deu certo',
      'Não executada',
    ]);
    expect(text()).toContain('Abre cada contrato do departamento no LMS');
    expect(text()).toContain('Pelo painel');
    expect(text()).toContain('2 min 1 s');
    // Sem botão de parar numa execução encerrada
    expect(text()).not.toContain('Parar execução');
  });

  it('mostra o que aconteceu sem detalhes técnicos nem o código de acesso', async () => {
    await render(FALHA_DO_ROBO);

    const activity = text('[data-testid="activity"]');
    expect(activity).toContain('Código de acesso temporário gerado.');
    expect(activity).toContain('Não foi possível ler os contratos no LMS.');
    expect(activity).not.toContain('Captcha');
    expect(activity).not.toContain('483920');
    expect(activity).not.toContain('wait_for_selector');
    expect(text()).toContain('Mensagens técnicas e repetidas foram ocultadas');
  });

  it('mostra o registro técnico completo quando pedido', async () => {
    await render(FALHA_DO_ROBO);

    const toggle = [...el.querySelectorAll('button')].find((b) =>
      b.textContent!.includes('Mostrar detalhes técnicos'),
    )!;
    toggle.click();
    await settle();

    expect(text('[role="log"]')).toContain("Captcha reconhecido: 'x7k2'");
    expect(text('[role="log"]')).toContain('[FAIL]');
    expect(toggle.getAttribute('aria-pressed')).toBe('true');
    expect(toggle.textContent).toContain('Voltar para o resumo');
  });

  it('em andamento: etapa atual, contratos conferidos e confirmação antes de parar', async () => {
    await render(EM_ANDAMENTO);

    const summary = text('[data-testid="summary"]');
    expect(summary).toContain('O robô está trabalhando');
    expect(summary).toContain('Agora: Extração dos contratos.');
    expect(summary).toContain('13 de 52 (25%)');
    expect(el.querySelector('[role="progressbar"]')!.getAttribute('aria-valuenow')).toBe('13');
    // As duas linhas de andamento viram uma só
    expect(el.querySelectorAll('[data-testid="activity"] li')).toHaveLength(1);

    const confirm = jest.spyOn(window, 'confirm').mockReturnValue(false);
    const stop = [...el.querySelectorAll('button')].find((b) =>
      b.textContent!.includes('Parar execução'),
    )!;
    stop.click();
    expect(confirm).toHaveBeenCalled();
    http.expectNone('/api/executions/2/stop/');

    confirm.mockReturnValue(true);
    stop.click();
    http.expectOne('/api/executions/2/stop/').flush({ status: 'stopping' });
    await settle();
    expect(stop.textContent).toContain('Parando...');
  });

  it('sucesso com avisos: quantos contratos e quantos avisos', async () => {
    await render(SUCESSO_COM_AVISO);

    const summary = text('[data-testid="summary"]');
    expect(summary).toContain('Execução concluída, com avisos');
    expect(summary).toContain('52 contratos atualizados no painel.');
    expect(summary).toContain('Houve 1 aviso durante a execução');
    expect(text('[data-testid="activity"]')).toContain(
      'O contrato C9 não foi encontrado na busca do LMS.',
    );
  });
});
