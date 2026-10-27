import { DecimalPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  map,
  of,
  startWith,
  switchMap,
} from 'rxjs';

import {
  Contract,
  ContractFilters,
  ContractSummary,
  ProgressTone,
  progressTone,
} from '../../../../shared/models/contract.model';
import { Page } from '../../../../shared/models/execution.model';
import {
  formatAmount,
  formatContractPeriod,
  formatDateTime,
  formatIsoDate,
  progressStateLabel,
} from '../../../../shared/utils/contract-format';
import { ContractsService } from '../../services/contracts.service';

type ListState =
  { status: 'loading' } | { status: 'error' } | { status: 'ready'; page: Page<Contract> };
type SummaryState =
  { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: ContractSummary };

const TONE_CLASSES: Record<ProgressTone, string> = {
  success: 'bg-success/10 text-success border-success/30',
  warning: 'bg-warning/10 text-warning border-warning/30',
  danger: 'bg-danger/10 text-danger border-danger/30',
  info: 'bg-info/10 text-info border-info/30',
  neutral: 'bg-surface-elevated text-fg-muted border-border-soft',
};

const EMPTY_FILTERS: ContractFilters = { search: '', progressState: '' };

@Component({
  selector: 'app-contract-list-page',
  imports: [RouterLink, DecimalPipe],
  templateUrl: './contract-list-page.html',
  host: { class: 'flex flex-1 flex-col min-h-0' },
})
export class ContractListPage {
  private readonly contracts = inject(ContractsService);

  protected readonly pageSize = 20;
  protected readonly filters = signal<ContractFilters>(EMPTY_FILTERS);
  protected readonly page = signal(1);
  protected readonly searchInput = signal('');

  protected readonly summary = toSignal(
    this.contracts.summary().pipe(
      map((data): SummaryState => ({ status: 'ready', data })),
      catchError(() => of<SummaryState>({ status: 'error' })),
      startWith<SummaryState>({ status: 'loading' }),
    ),
    { initialValue: { status: 'loading' } as SummaryState },
  );

  protected readonly state = toSignal(
    toObservable(computed(() => ({ filters: this.filters(), page: this.page() }))).pipe(
      switchMap(({ filters, page }) =>
        this.contracts.list(filters, page, this.pageSize).pipe(
          map((result): ListState => ({ status: 'ready', page: result })),
          catchError(() => of<ListState>({ status: 'error' })),
          startWith<ListState>({ status: 'loading' }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as ListState },
  );

  protected readonly summaryData = computed(() => {
    const s = this.summary();
    return s.status === 'ready' ? s.data : null;
  });

  protected readonly result = computed(() => {
    const s = this.state();
    return s.status === 'ready' ? s.page : null;
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil((this.result()?.count ?? 0) / this.pageSize)),
  );

  protected readonly rangeLabel = computed(() => {
    const result = this.result();
    if (!result || result.count === 0) return '';
    const first = (this.page() - 1) * this.pageSize + 1;
    return `Mostrando ${first}-${first + result.results.length - 1} de ${result.count} contratos`;
  });

  protected readonly hasActiveFilters = computed(() => {
    const f = this.filters();
    return f.search.trim() !== '' || f.progressState !== '';
  });

  protected readonly label = progressStateLabel;
  protected readonly period = formatContractPeriod;
  protected readonly amount = formatAmount;
  protected readonly date = formatIsoDate;
  protected readonly dateTime = formatDateTime;

  constructor() {
    toObservable(this.searchInput)
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed())
      .subscribe((search) => {
        if (search === this.filters().search) return;
        this.filters.update((f) => ({ ...f, search }));
        this.page.set(1);
      });
  }

  protected tone(state: string | null): string {
    return TONE_CLASSES[progressTone(state)];
  }

  protected toggleState(state: string): void {
    this.filters.update((f) => ({ ...f, progressState: f.progressState === state ? '' : state }));
    this.page.set(1);
  }

  protected clearFilters(): void {
    this.searchInput.set('');
    this.filters.set(EMPTY_FILTERS);
    this.page.set(1);
  }

  protected goToPage(page: number): void {
    this.page.set(Math.min(Math.max(1, page), this.totalPages()));
  }
}
