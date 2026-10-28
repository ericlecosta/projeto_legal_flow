import {
  Component,
  ElementRef,
  afterRenderEffect,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { catchError, map, of, startWith, switchMap, takeWhile, timer } from 'rxjs';

import { StatusBadge } from '../../../../shared/components/status-badge/status-badge';
import {
  ExecutionDetail,
  ExecutionStep,
  FLOW_LABELS,
  LogLevel,
  StepKey,
} from '../../../../shared/models/execution.model';
import { formatClock } from '../../../../shared/utils/format';
import {
  friendlyDuration,
  friendlyError,
  friendlyLogs,
  latestProgress,
} from '../../../../shared/utils/friendly-log';
import { ClockPipe, RelativeDateTimePipe } from '../../../../shared/pipes/format.pipes';
import { ExecutionsService } from '../../services/executions.service';

/** Intervalo de atualização enquanto a execução está em andamento. */
const POLL_INTERVAL_MS = 2000;

type ViewState =
  { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: ExecutionDetail };

/** O que cada etapa faz, em linguagem simples (robô real e simulador). */
export const STEP_DESCRIPTIONS: Record<StepKey, string> = {
  lms_login: 'Gera um código de acesso temporário e entra no LMS com o usuário do robô.',
  report_download: 'Baixa do LMS a lista de contratos do período.',
  contract_details: 'Abre cada contrato do departamento no LMS e lê o status e as datas.',
  base_ideal: 'Organiza os dados no formato da planilha Base Ideal.',
  data_upload: 'Salva os contratos no painel (tela Contratos).',
  start_session: 'Abre o navegador do robô.',
  otp_captcha: 'Gera o código de acesso temporário.',
  sso_login: 'Entra no portal da LG.',
  lms_access: 'Abre o LMS.',
  contract_capture: 'Lê os contratos no LMS.',
};

const STOP_CONFIRMATION =
  'Parar a execução agora? O robô interrompe o que está fazendo e a execução fica registrada como falha.';

const LEVEL_NAMES: Record<LogLevel, string> = {
  info: 'Informação',
  success: 'Concluído',
  warning: 'Atenção',
  error: 'Erro',
};

export const LOG_TAGS: Record<LogLevel, string> = {
  info: 'INFO',
  success: 'SUCC',
  warning: 'WARN',
  error: 'FAIL',
};

@Component({
  selector: 'app-execution-detail-page',
  imports: [RouterLink, StatusBadge, RelativeDateTimePipe, ClockPipe],
  templateUrl: './execution-detail-page.html',
  host: { class: 'flex flex-1 flex-col min-h-0' },
})
export class ExecutionDetailPage {
  private readonly executions = inject(ExecutionsService);

  /** Parâmetro de rota :id (via withComponentInputBinding). */
  readonly id = input.required<string>();

  protected readonly flowLabels = FLOW_LABELS;
  protected readonly logTags = LOG_TAGS;
  protected readonly levelNames = LEVEL_NAMES;
  protected readonly stepDescriptions = STEP_DESCRIPTIONS;
  protected readonly duration = friendlyDuration;
  protected readonly autoScroll = signal(true);
  protected readonly stopping = signal(false);
  /** Mostra os logs originais do robô (para o time técnico) no lugar das mensagens traduzidas. */
  protected readonly technical = signal(false);

  private readonly console = viewChild<ElementRef<HTMLElement>>('console');

  protected readonly state = toSignal(
    toObservable(this.id).pipe(
      switchMap((id) =>
        // Recarrega a cada 2s até a execução terminar (o último estado também é emitido).
        timer(0, POLL_INTERVAL_MS).pipe(
          switchMap(() => this.executions.get(Number(id))),
          takeWhile((data) => data.status === 'running', true),
          map((data): ViewState => ({ status: 'ready', data })),
          catchError(() => of<ViewState>({ status: 'error' })),
          startWith<ViewState>({ status: 'loading' }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as ViewState },
  );

  protected readonly execution = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : null;
  });

  /** Mensagens do robô em linguagem simples. */
  protected readonly activity = computed(() => friendlyLogs(this.execution()?.logs ?? []));

  protected readonly hiddenLogs = computed(
    () => (this.execution()?.logs.length ?? 0) > this.activity().length,
  );

  protected readonly warnings = computed(
    () =>
      this.activity().filter((entry) => entry.level === 'warning' || entry.level === 'error')
        .length,
  );

  protected readonly progress = computed(() => latestProgress(this.execution()?.logs ?? []));

  protected readonly currentStep = computed(
    () => this.execution()?.steps.find((step) => step.status === 'running') ?? null,
  );

  protected readonly error = computed(() => {
    const error = this.execution()?.error;
    return error ? { ...friendlyError(error), technical: error } : null;
  });

  constructor() {
    // Mantém o console no fim dos logs quando o auto-scroll está ligado.
    afterRenderEffect(() => {
      const el = this.console()?.nativeElement;
      if (el && this.autoScroll() && this.execution()) el.scrollTop = el.scrollHeight;
    });
  }

  protected exportLogs(): void {
    const execution = this.execution();
    if (!execution) return;
    const content = execution.logs
      .map((log) => `[${formatClock(log.timestamp)}] [${LOG_TAGS[log.level]}] ${log.message}`)
      .join('\n');
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `rpa_execution_${execution.id}.log`;
    link.click();
    URL.revokeObjectURL(url);
  }

  protected percent(done: number, total: number): number {
    return total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
  }

  protected stepStatus(step: ExecutionStep): string {
    switch (step.status) {
      case 'success':
        return step.durationSeconds == null
          ? 'Concluída'
          : `Concluída em ${friendlyDuration(step.durationSeconds)}`;
      case 'failed':
        return step.durationSeconds == null
          ? 'Não deu certo'
          : `Não deu certo depois de ${friendlyDuration(step.durationSeconds)}`;
      case 'running':
        return 'Em andamento…';
      case 'skipped':
        return 'Não executada';
      default:
        return 'Aguardando';
    }
  }

  protected stop(): void {
    const execution = this.execution();
    if (!execution || execution.status !== 'running') return;
    if (!window.confirm(STOP_CONFIRMATION)) return;
    // O polling em andamento traz o estado final (falha por interrupção) em até 2s.
    this.stopping.set(true);
    this.executions.stop(execution.id).subscribe({
      error: () => this.stopping.set(false),
    });
  }
}
