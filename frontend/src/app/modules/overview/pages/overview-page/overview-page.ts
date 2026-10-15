import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { catchError, map, of, startWith } from 'rxjs';

import { ProgressBar } from '../../../../shared/components/progress-bar/progress-bar';
import { Sparkline } from '../../../../shared/components/sparkline/sparkline';
import { OperationalStatus, Overview } from '../../../../shared/models/overview.model';
import { ClockPipe, DurationPipe, RelativeDateTimePipe } from '../../../../shared/pipes/format.pipes';
import { ExecutionsService } from '../../../executions/services/executions.service';
import { OverviewService } from '../../services/overview.service';

type ViewState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: Overview };

const STATUS_BANNER: Record<OperationalStatus, { title: string; border: string; dot: string }> = {
  green: { title: 'Sistema operacional', border: 'border-l-success', dot: 'bg-success shadow-[0_0_8px_var(--success)]' },
  yellow: { title: 'Atenção', border: 'border-l-warning', dot: 'bg-warning shadow-[0_0_8px_var(--warning)]' },
  red: { title: 'Fora de operação', border: 'border-l-danger', dot: 'bg-danger shadow-[0_0_8px_var(--danger)]' },
};

@Component({
  selector: 'app-overview-page',
  imports: [RouterLink, DecimalPipe, DurationPipe, RelativeDateTimePipe, ClockPipe, ProgressBar, Sparkline],
  templateUrl: './overview-page.html',
})
export class OverviewPage {
  private readonly overview = inject(OverviewService);
  private readonly executions = inject(ExecutionsService);
  private readonly router = inject(Router);

  protected readonly starting = signal(false);
  protected readonly runError = signal<string | null>(null);

  protected readonly state = toSignal(
    this.overview.get().pipe(
      map((data): ViewState => ({ status: 'ready', data })),
      catchError(() => of<ViewState>({ status: 'error' })),
      startWith<ViewState>({ status: 'loading' }),
    ),
    { requireSync: true },
  );

  protected readonly overviewData = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.data : null;
  });

  protected readonly banner = computed(() => {
    const data = this.overviewData();
    return data ? STATUS_BANNER[data.operationalStatus] : null;
  });

  protected readonly nextRun = computed(() => this.overviewData()?.upcomingRuns[0] ?? null);

  /** Dispara uma execução manual e abre o detalhe dela para acompanhar os logs. */
  protected runNow(): void {
    this.starting.set(true);
    this.runError.set(null);
    this.executions.run('login_capture').subscribe({
      next: (execution) => this.router.navigate(['/execucoes', execution.id]),
      error: (error: unknown) => {
        this.starting.set(false);
        this.runError.set(
          error instanceof HttpErrorResponse
            ? (error.error?.detail ?? 'Não foi possível iniciar a execução.')
            : error instanceof Error
              ? error.message
              : 'Não foi possível iniciar a execução.',
        );
      },
    });
  }
}
