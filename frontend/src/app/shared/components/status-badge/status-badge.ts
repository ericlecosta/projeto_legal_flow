import { Component, computed, input } from '@angular/core';

import { ExecutionStatus, STATUS_LABELS } from '../../models/execution.model';

const TONE: Record<ExecutionStatus, string> = {
  success: 'bg-success/10 text-success border-success/30',
  failed: 'bg-danger/10 text-danger border-danger/30',
  atypical: 'bg-warning/10 text-warning border-warning/30',
  running: 'bg-info/10 text-info border-info/30',
};

const DOT: Record<ExecutionStatus, string> = {
  success: 'bg-success',
  failed: 'bg-danger',
  atypical: 'bg-warning',
  running: 'bg-info animate-pulse',
};

/** Selo de status: cor + ponto + texto, para não depender só da cor. */
@Component({
  selector: 'app-status-badge',
  template: `
    <span
      class="inline-flex w-max items-center gap-1.5 rounded-md border px-2.5 py-1 font-bold uppercase tracking-wide"
      [class]="tone() + (size() === 'lg' ? ' text-sm' : ' text-xs')"
    >
      <span class="h-2 w-2 rounded-full" [class]="dot()" aria-hidden="true"></span>
      {{ label() }}
    </span>
  `,
})
export class StatusBadge {
  readonly status = input.required<ExecutionStatus>();
  readonly size = input<'md' | 'lg'>('md');

  protected readonly label = computed(() => STATUS_LABELS[this.status()]);
  protected readonly tone = computed(() => TONE[this.status()]);
  protected readonly dot = computed(() => DOT[this.status()]);
}
