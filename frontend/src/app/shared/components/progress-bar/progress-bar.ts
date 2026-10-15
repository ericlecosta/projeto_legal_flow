import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  template: `
    <div
      class="w-full overflow-hidden rounded-full bg-border-soft"
      [class]="thickness() === 'thin' ? 'h-1.5' : 'h-2'"
      role="progressbar"
      aria-valuemin="0"
      aria-valuemax="100"
      [attr.aria-valuenow]="clamped()"
      [attr.aria-label]="label()"
    >
      <div
        class="h-full rounded-full transition-[width] duration-300 ease-out"
        [class]="colorClass()"
        [style.width.%]="clamped()"
      ></div>
    </div>
  `,
})
export class ProgressBar {
  readonly value = input.required<number>();
  /** Classe de cor do preenchimento (ex.: "bg-success"). */
  readonly colorClass = input('bg-primary');
  readonly thickness = input<'thin' | 'regular'>('regular');
  readonly label = input<string>();

  protected readonly clamped = computed(() => Math.min(100, Math.max(0, this.value())));
}
