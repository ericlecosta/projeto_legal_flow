import { DecimalPipe } from '@angular/common';
import { Component, HostListener, computed, inject, signal } from '@angular/core';
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
  BASE_IDEAL_COLUMNS,
  BaseIdealValue,
  Contract,
  ContractFilters,
  ContractSummary,
  EXPORT_FORMATS,
  ExportFormat,
  ProgressTone,
  progressTone,
} from '../../../../shared/models/contract.model';
import { Page } from '../../../../shared/models/execution.model';
import { formatBaseIdealValue, formatDateTime } from '../../../../shared/utils/contract-format';
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

/** Colunas de texto longo: largura limitada, com o texto inteiro no title. */
const LONG_TEXT_COLUMNS = new Set([
  'Counterparty',
  'Contract name',
  'Main Contract Type',
  'Contract type',
  'Department of the person in charge',
]);
const NUMBER_COLUMNS = new Set(['Amount', 'Qty Review']);

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

  protected readonly columns = BASE_IDEAL_COLUMNS;
  protected readonly exportFormats = EXPORT_FORMATS;
  protected readonly exportMenuOpen = signal(false);
  protected readonly canExport = computed(
    () => this.contracts.exportUrl('xlsx', EMPTY_FILTERS) !== null,
  );
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

  protected cell(column: string, value: BaseIdealValue | undefined): string {
    return formatBaseIdealValue(column, value);
  }

  /** A primeira coluna (Contract number) fica fixa ao rolar a tabela para o lado. */
  protected headerClass(column: string, first: boolean): string {
    return [
      first ? 'sticky left-0 z-10 bg-surface' : '',
      NUMBER_COLUMNS.has(column) ? 'text-right' : '',
    ].join(' ');
  }

  protected cellClass(column: string, first: boolean): string {
    if (first)
      return 'sticky left-0 z-10 bg-surface-sunken font-mono font-semibold group-hover:bg-surface-elevated';
    if (NUMBER_COLUMNS.has(column)) return 'text-right font-mono';
    if (LONG_TEXT_COLUMNS.has(column)) return 'max-w-[16rem] truncate text-fg-muted';
    return 'text-fg-muted';
  }

  protected exportUrl(format: ExportFormat): string | null {
    return this.contracts.exportUrl(format, this.filters());
  }

  protected toggleExportMenu(event: Event): void {
    event.stopPropagation();
    this.exportMenuOpen.update((open) => !open);
  }

  @HostListener('document:click')
  @HostListener('document:keydown.escape')
  protected closeExportMenu(): void {
    this.exportMenuOpen.set(false);
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
