import { Component, ElementRef, afterRenderEffect, computed, inject, input, signal, viewChild } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { catchError, map, of, startWith, switchMap } from 'rxjs';

import { StatusBadge } from '../../../../shared/components/status-badge/status-badge';
import { ExecutionDetail, FLOW_LABELS, LogLevel } from '../../../../shared/models/execution.model';
import { formatClock } from '../../../../shared/utils/format';
import {
  ClockPipe,
  DurationPipe,
  RelativeDateTimePipe,
  StepDurationPipe,
} from '../../../../shared/pipes/format.pipes';
import { ExecutionsService } from '../../services/executions.service';

type ViewState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: ExecutionDetail };

export const LOG_TAGS: Record<LogLevel, string> = {
  info: 'INFO',
  success: 'SUCC',
  warning: 'WARN',
  error: 'FAIL',
};

@Component({
  selector: 'app-execution-detail-page',
  imports: [RouterLink, StatusBadge, DurationPipe, StepDurationPipe, RelativeDateTimePipe, ClockPipe],
  templateUrl: './execution-detail-page.html',
  host: { class: 'flex flex-1 flex-col min-h-0' },
})
export class ExecutionDetailPage {
  private readonly executions = inject(ExecutionsService);

  /** Parâmetro de rota :id (via withComponentInputBinding). */
  readonly id = input.required<string>();

  protected readonly flowLabels = FLOW_LABELS;
  protected readonly logTags = LOG_TAGS;
  protected readonly autoScroll = signal(true);

  private readonly console = viewChild<ElementRef<HTMLElement>>('console');

  protected readonly state = toSignal(
    toObservable(this.id).pipe(
      switchMap((id) =>
        this.executions.get(Number(id)).pipe(
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
}
