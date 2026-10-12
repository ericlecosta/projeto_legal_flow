export type ExecutionStatus = 'success' | 'failed' | 'atypical' | 'running';
export type ExecutionTrigger = 'scheduled' | 'manual';
export type ExecutionFlow = 'login_capture' | 'otp_only';

export type StepKey = 'start_session' | 'otp_captcha' | 'sso_login' | 'lms_access' | 'contract_capture';
export type StepStatus = 'success' | 'failed' | 'running' | 'pending' | 'skipped';
export type LogLevel = 'info' | 'warning' | 'error' | 'success';

export interface Execution {
  id: number;
  flow: ExecutionFlow;
  status: ExecutionStatus;
  trigger: ExecutionTrigger;
  /** ISO 8601 */
  startedAt: string;
  finishedAt: string | null;
  durationSeconds: number | null;
  /** Registros capturados; null quando a execução não chegou a capturar. */
  records: number | null;
}

export interface ExecutionStep {
  key: StepKey;
  label: string;
  status: StepStatus;
  durationSeconds: number | null;
}

export interface LogEntry {
  /** ISO 8601 */
  timestamp: string;
  level: LogLevel;
  message: string;
}

export interface ExecutionError {
  title: string;
  message: string;
  screenshotUrl: string | null;
}

export interface ExecutionDetail extends Execution {
  steps: ExecutionStep[];
  logs: LogEntry[];
  error: ExecutionError | null;
}

export type PeriodFilter = '7d' | '30d' | 'all';

export interface ExecutionFilters {
  period: PeriodFilter;
  status: ExecutionStatus | 'all';
  flow: ExecutionFlow | 'all';
}

/** Formato de paginação da API (`{ count, results }`). */
export interface Page<T> {
  count: number;
  results: T[];
}

export const FLOW_LABELS: Record<ExecutionFlow, string> = {
  login_capture: 'Login + Captura LMS',
  otp_only: 'Somente OTP',
};

export const TRIGGER_LABELS: Record<ExecutionTrigger, string> = {
  scheduled: 'Agendado',
  manual: 'Manual',
};

export const STATUS_LABELS: Record<ExecutionStatus, string> = {
  success: 'Sucesso',
  failed: 'Falha',
  atypical: 'Atípico',
  running: 'Em execução',
};

export const PERIOD_LABELS: Record<PeriodFilter, string> = {
  '7d': 'Últimos 7 dias',
  '30d': 'Últimos 30 dias',
  all: 'Todo o período',
};
