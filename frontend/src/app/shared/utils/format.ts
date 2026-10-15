const pad = (value: number) => String(value).padStart(2, '0');

/** 165 → "02m 45s"; 3720 → "1h 02m". */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '-';
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours > 0) return `${hours}h ${pad(minutes)}m`;
  return `${pad(minutes)}m ${pad(total % 60)}s`;
}

/** 12 → "12.0s" (durações curtas de etapas); sem duração → "-". */
export function formatStepDuration(seconds: number | null | undefined): string {
  return seconds == null ? '-' : `${seconds.toFixed(1)}s`;
}

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

/**
 * "Hoje, 14:15:22", "Ontem, 18:00:00", "Amanhã, 08:00:00" ou "28/09, 12:00:00".
 * Com `withSeconds = false`, omite os segundos ("Hoje, 18:00").
 */
export function formatRelativeDateTime(
  iso: string,
  now: Date = new Date(),
  withSeconds = true,
): string {
  const date = new Date(iso);
  const time = withSeconds
    ? `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
    : `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  const dayDiff = Math.round((startOfDay(date) - startOfDay(now)) / 86_400_000);
  const day =
    dayDiff === 0
      ? 'Hoje'
      : dayDiff === -1
        ? 'Ontem'
        : dayDiff === 1
          ? 'Amanhã'
          : `${pad(date.getDate())}/${pad(date.getMonth() + 1)}`;
  return `${day}, ${time}`;
}

/** "14:15:22" */
export function formatClock(iso: string): string {
  const date = new Date(iso);
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
