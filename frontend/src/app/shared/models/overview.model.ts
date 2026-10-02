/** Status operacional do RPA no padrão do Control Tower (Developer Guide, 12.2). */
export type OperationalStatus = 'green' | 'yellow' | 'red';

export interface StepFailureShare {
  label: string;
  /** Percentual das falhas do período que ocorreram nesta etapa (0–100). */
  percent: number;
}

export interface UpcomingRun {
  name: string;
  /** ISO 8601 */
  scheduledAt: string;
  source: 'cron' | 'manual';
}

export interface Overview {
  operationalStatus: OperationalStatus;
  statusMessage: string;
  /** ISO 8601 */
  updatedAt: string;
  periodLabel: string;
  /** Percentual de execuções bem-sucedidas (0–100). */
  runningRate: number;
  runningRateTarget: number;
  totalExecutions: number;
  succeeded: number;
  failed: number;
  avgDurationSeconds: number;
  capturedRecords: number;
  /** Série de registros capturados por dia, do mais antigo ao mais recente. */
  capturedTrend: number[];
  failuresByStep: StepFailureShare[];
  upcomingRuns: UpcomingRun[];
}
