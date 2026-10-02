import { DecimalPipe, NgTemplateOutlet } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { catchError, map, of, startWith, switchMap } from 'rxjs';

import { StatusBadge } from '../../../../shared/components/status-badge/status-badge';
import {
  Execution,
  ExecutionFilters,
  FLOW_LABELS,
  Page,
  PERIOD_LABELS,
  STATUS_LABELS,
  TRIGGER_LABELS,
} from '../../../../shared/models/execution.model';
import { DurationPipe, RelativeDateTimePipe } from '../../../../shared/pipes/format.pipes';
import { ExecutionsService } from '../../services/executions.service';

type ViewState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; page: Page<Execution> };

const DEFAULT_FILTERS: ExecutionFilters = { period: '7d', status: 'all', flow: 'all' };

@Component({
  selector: 'app-execution-list-page',
  imports: [RouterLink, DecimalPipe, NgTemplateOutlet, DurationPipe, RelativeDateTimePipe, StatusBadge],
  templateUrl: './execution-list-page.html',
  host: { class: 'flex flex-1 flex-col min-h-0' },
})
export class ExecutionListPage {
  private readonly executions = inject(ExecutionsService);
  private readonly router = inject(Router);

  protected readonly pageSize = 10;
  protected readonly periodOptions = Object.entries(PERIOD_LABELS);
  protected readonly statusOptions = Object.entries(STATUS_LABELS);
  protected readonly flowOptions = Object.entries(FLOW_LABELS);
  protected readonly triggerLabels = TRIGGER_LABELS;

  protected readonly filters = signal<ExecutionFilters>(DEFAULT_FILTERS);
  protected readonly page = signal(1);

  protected readonly state = toSignal(
    toObservable(computed(() => ({ filters: this.filters(), page: this.page() }))).pipe(
      switchMap(({ filters, page }) =>
        this.executions.list(filters, page, this.pageSize).pipe(
          map((result): ViewState => ({ status: 'ready', page: result })),
          catchError(() => of<ViewState>({ status: 'error' })),
          startWith<ViewState>({ status: 'loading' }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as ViewState },
  );

  protected readonly result = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state.page : null;
  });

  protected readonly totalPages = computed(() => Math.max(1, Math.ceil((this.result()?.count ?? 0) / this.pageSize)));

  protected readonly rangeLabel = computed(() => {
    const result = this.result();
    if (!result || result.count === 0) return '';
    const first = (this.page() - 1) * this.pageSize + 1;
    return `Mostrando ${first}-${first + result.results.length - 1} de ${result.count} resultados`;
  });

  protected readonly hasActiveFilters = computed(() => {
    const f = this.filters();
    return f.period !== DEFAULT_FILTERS.period || f.status !== 'all' || f.flow !== 'all';
  });

  protected setFilter<K extends keyof ExecutionFilters>(key: K, value: string): void {
    this.filters.update((f) => ({ ...f, [key]: value as ExecutionFilters[K] }));
    this.page.set(1);
  }

  protected clearFilters(): void {
    this.filters.set(DEFAULT_FILTERS);
    this.page.set(1);
  }

  protected goToPage(page: number): void {
    this.page.set(Math.min(Math.max(1, page), this.totalPages()));
  }

  protected open(execution: Execution): void {
    this.router.navigate(['/execucoes', execution.id]);
  }
}
