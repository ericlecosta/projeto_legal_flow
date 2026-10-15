import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
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
  finishedAt: '2026-10-15T09:06:19-04:00',
  durationSeconds: 1.3,
  records: null,
  steps: [
    { key: 'lms_login', label: 'Login no LMS', status: 'success', durationSeconds: 0.5 },
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
    { key: 'data_upload', label: 'Envio para a base', status: 'skipped', durationSeconds: null },
  ],
  logs: [
    { timestamp: '2026-10-15T09:06:18-04:00', level: 'info', message: 'Login no LMS realizado.' },
    {
      timestamp: '2026-10-15T09:06:19-04:00',
      level: 'error',
      message: 'Falha na extração dos contratos: Timeout 30000ms exceeded',
    },
  ],
  error: {
    title: 'Falha na extração dos contratos',
    message: 'page.wait_for_selector: Timeout 30000ms exceeded',
    screenshotUrl: null,
  },
};

describe('ExecutionDetailPage', () => {
  it('mostra status, erro, etapas e logs de uma execução real com falha', async () => {
    await TestBed.configureTestingModule({
      imports: [ExecutionDetailPage],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const http = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(ExecutionDetailPage);
    fixture.componentRef.setInput('id', '1');
    fixture.detectChanges();
    // A página busca os dados com timer(0, 2000): deixa o primeiro disparo acontecer.
    await new Promise((resolve) => setTimeout(resolve, 0));

    http.expectOne('/api/executions/1/').flush(FALHA_DO_ROBO);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent!.replace(/\s+/g, ' ');
    expect(text).toContain('Falha');
    expect(text).toContain('Extração de contratos');
    expect(text).toContain('Falha na extração dos contratos');
    expect(text).toContain('page.wait_for_selector: Timeout 30000ms exceeded');
    expect(text).toContain('Falhou após -');
    expect(text).toContain('Envio para a base');
    expect(text).toContain('Login no LMS realizado.');
    http.verify();
  });
});
