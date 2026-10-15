import { Component, computed, input } from '@angular/core';

const WIDTH = 100;
const HEIGHT = 50;
const PADDING_TOP = 5;

/** Linha de tendência decorativa (sem eixos), desenhada em SVG com currentColor. */
@Component({
  selector: 'app-sparkline',
  template: `
    @if (points(); as pts) {
      <svg class="h-full w-full" preserveAspectRatio="none" [attr.viewBox]="viewBox" aria-hidden="true">
        <path [attr.d]="'M0,' + height + ' L' + pts + ' L' + width + ',' + height + ' Z'" fill="currentColor" fill-opacity="0.2" />
        <path [attr.d]="'M' + pts" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke" />
      </svg>
    }
  `,
  host: { class: 'block' },
})
export class Sparkline {
  readonly values = input.required<number[]>();

  protected readonly width = WIDTH;
  protected readonly height = HEIGHT;
  protected readonly viewBox = `0 0 ${WIDTH} ${HEIGHT}`;

  protected readonly points = computed(() => {
    const values = this.values();
    if (values.length < 2) return null;
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    const step = WIDTH / (values.length - 1);
    return values
      .map((v, i) => {
        const y = PADDING_TOP + (HEIGHT - PADDING_TOP) * (1 - (v - min) / range);
        return `${(i * step).toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' L');
  });
}
