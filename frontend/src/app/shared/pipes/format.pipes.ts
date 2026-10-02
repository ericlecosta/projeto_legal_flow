import { Pipe, PipeTransform } from '@angular/core';

import { formatClock, formatDuration, formatRelativeDateTime, formatStepDuration } from '../utils/format';

@Pipe({ name: 'duration' })
export class DurationPipe implements PipeTransform {
  transform(seconds: number | null | undefined): string {
    return formatDuration(seconds);
  }
}

@Pipe({ name: 'stepDuration' })
export class StepDurationPipe implements PipeTransform {
  transform(seconds: number): string {
    return formatStepDuration(seconds);
  }
}

@Pipe({ name: 'relativeDateTime' })
export class RelativeDateTimePipe implements PipeTransform {
  transform(iso: string | null | undefined, withSeconds = true): string {
    return iso ? formatRelativeDateTime(iso, new Date(), withSeconds) : '-';
  }
}

@Pipe({ name: 'clock' })
export class ClockPipe implements PipeTransform {
  transform(iso: string): string {
    return formatClock(iso);
  }
}
