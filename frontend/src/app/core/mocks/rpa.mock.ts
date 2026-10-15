/**
 * Dados simulados usados quando a API FastAPI não está disponível (environment.useMocks).
 * Os horários são gerados a partir de "agora", para que "Hoje"/"Ontem" façam sentido em qualquer dia.
 */
import {
  Execution,
  ExecutionDetail,
  ExecutionError,
  ExecutionFilters,
  ExecutionStep,
  LogEntry,
  Page,
  PERIOD_LABELS,
  StepKey,
} from '../../shared/models/execution.model';
import { OperationalStatus, Overview } from '../../shared/models/overview.model';

const RUNNING_RATE_TARGET = 85;

const STEPS: { key: StepKey; label: string }[] = [
  { key: 'start_session', label: 'Iniciar Sessão' },
  { key: 'otp_captcha', label: 'Geração OTP e Captcha' },
  { key: 'sso_login', label: 'Login SSO' },
  { key: 'lms_access', label: 'Acesso LMS' },
  { key: 'contract_capture', label: 'Captura de Contratos' },
];

const STEP_ERRORS: Record<StepKey, Omit<ExecutionError, 'screenshotUrl'>> = {
  start_session: {
    title: 'Falha ao iniciar o navegador',
    message: 'O Chromium não pôde ser iniciado no runner. Verifique a memória compartilhada do contêiner.',
  },
  otp_captcha: {
    title: 'Captcha não reconhecido',
    message: 'O OCR local não atingiu a confiança mínima após 3 tentativas de leitura do captcha.',
  },
  sso_login: {
    title: 'Timeout no Elemento SSO',
    message:
      'O seletor de login corporativo #sso-login-btn não foi encontrado ou demorou mais de 30 segundos para responder. O RPA abortou a operação.',
  },
  lms_access: {
    title: 'Sessão não reconhecida pelo LMS',
    message: 'Após o login no SSO, o LMS redirecionou para a tela de login. A sessão autenticada não foi reaproveitada.',
  },
  contract_capture: {
    title: 'Tabela de contratos não carregou',
    message: 'A grade de busca de contratos não retornou resultados dentro do tempo limite.',
  },
};

/** Etapa onde cada falha simulada ocorreu. */
const FAILED_AT = new Map<number, StepKey>();

function at(daysAgo: number, hours: number, minutes = 0, seconds = 0): Date {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  date.setHours(hours, minutes, seconds, 0);
  return date;
}

function buildExecution(
  id: number,
  start: Date,
  status: Execution['status'],
  durationSeconds: number,
  records: number | null,
  options: Partial<Pick<Execution, 'trigger' | 'flow'>> = {},
): Execution {
  return {
    id,
    flow: options.flow ?? 'login_capture',
    status,
    trigger: options.trigger ?? 'scheduled',
    startedAt: start.toISOString(),
    finishedAt: new Date(start.getTime() + durationSeconds * 1000).toISOString(),
    durationSeconds,
    records,
  };
}

function buildExecutions(): Execution[] {
  // As 6 execuções mais recentes reproduzem o mock de Execuções (tela3).
  const recent: Execution[] = [
    buildExecution(1042, at(0, 14, 15, 22), 'failed', 45, null),
    buildExecution(1041, at(0, 12), 'success', 150, 450),
    buildExecution(1040, at(0, 8), 'success', 160, 1102),
    buildExecution(1039, at(1, 18), 'atypical', 495, 89, { trigger: 'manual' }),
    buildExecution(1038, at(1, 12), 'failed', 70, null),
    buildExecution(1037, at(1, 8), 'success', 145, 954),
  ];
  FAILED_AT.set(1042, 'sso_login');
  FAILED_AT.set(1038, 'otp_captcha');

  // Histórico mais antigo, determinístico: 3 execuções por dia (08h, 12h, 18h).
  const failedSteps: StepKey[] = ['sso_login', 'otp_captcha', 'sso_login', 'lms_access'];
  const older: Execution[] = [];
  for (let id = 1036; id >= 1000; id--) {
    const offset = 1036 - id; // 0 = ontem 18h
    const daysAgo = 2 + Math.floor(offset / 3);
    const hour = [18, 12, 8][offset % 3];
    const flow = id % 7 === 0 ? 'otp_only' : 'login_capture';
    const status = id % 23 === 0 ? 'failed' : id % 17 === 0 ? 'atypical' : 'success';
    const duration = status === 'failed' ? 40 + (id % 5) * 9 : status === 'atypical' ? 420 + (id % 4) * 30 : 130 + ((id * 13) % 60);
    const records = flow === 'otp_only' || status === 'failed' ? null : 400 + ((id * 37) % 800);
    older.push(
      buildExecution(id, at(daysAgo, hour), status, duration, records, {
        flow,
        trigger: id % 9 === 0 ? 'manual' : 'scheduled',
      }),
    );
    if (status === 'failed') {
      const step = failedSteps[id % failedSteps.length];
      FAILED_AT.set(id, flow === 'otp_only' && step !== 'otp_captcha' ? 'otp_captcha' : step);
    }
  }
  return [...recent, ...older];
}

const EXECUTIONS = buildExecutions();

function periodStart(period: ExecutionFilters['period']): number {
  if (period === 'all') return 0;
  return at(period === '7d' ? 6 : 29, 0).getTime();
}

export function listExecutionsMock(
  filters: ExecutionFilters,
  page: number,
  pageSize: number,
): Page<Execution> {
  const since = periodStart(filters.period);
  const filtered = EXECUTIONS.filter(
    (e) =>
      new Date(e.startedAt).getTime() >= since &&
      (filters.status === 'all' || e.status === filters.status) &&
      (filters.flow === 'all' || e.flow === filters.flow),
  );
  const start = (page - 1) * pageSize;
  return { count: filtered.length, results: filtered.slice(start, start + pageSize) };
}

export function getExecutionMock(id: number): ExecutionDetail | null {
  const execution = EXECUTIONS.find((e) => e.id === id);
  if (!execution) return null;
  if (id === 1042) return buildExecution1042(execution);

  const flowSteps = execution.flow === 'otp_only' ? STEPS.slice(0, 2) : STEPS;
  const failedAt = FAILED_AT.get(id);
  const failedIndex = failedAt ? flowSteps.findIndex((s) => s.key === failedAt) : -1;
  const perStep = (execution.durationSeconds ?? 0) / Math.max(1, failedIndex >= 0 ? failedIndex + 1 : flowSteps.length);

  const steps: ExecutionStep[] = flowSteps.map((s, i) => ({
    ...s,
    status: failedIndex < 0 || i < failedIndex ? 'success' : i === failedIndex ? 'failed' : 'skipped',
    durationSeconds: failedIndex >= 0 && i > failedIndex ? null : Math.round(perStep * 10) / 10,
  }));

  const startMs = new Date(execution.startedAt).getTime();
  const logs: LogEntry[] = [];
  steps.forEach((step, i) => {
    const ts = new Date(startMs + i * perStep * 1000).toISOString();
    if (step.status === 'skipped') return;
    logs.push({ timestamp: ts, level: 'info', message: `Iniciando etapa: ${step.label}` });
    if (step.status === 'failed') {
      logs.push({ timestamp: execution.finishedAt!, level: 'error', message: STEP_ERRORS[step.key].title });
    }
  });
  if (execution.status === 'atypical') {
    logs.push({ timestamp: execution.finishedAt!, level: 'warning', message: 'Execução acima do tempo esperado (limite: 05m 00s).' });
  }
  if (failedIndex < 0) {
    logs.push({
      timestamp: execution.finishedAt!,
      level: 'success',
      message: execution.records != null ? `${execution.records} registros capturados.` : 'Fluxo concluído.',
    });
  }

  return {
    ...execution,
    steps,
    logs,
    error: failedAt ? { ...STEP_ERRORS[failedAt], screenshotUrl: null } : null,
  };
}

/** Reproduz exatamente o mock de Detalhe de Execução (tela2). */
function buildExecution1042(execution: Execution): ExecutionDetail {
  const t = (h: number, m: number, s: number) => at(0, h, m, s).toISOString();
  return {
    ...execution,
    steps: [
      { key: 'start_session', label: 'Iniciar Sessão', status: 'success', durationSeconds: 0.5 },
      { key: 'otp_captcha', label: 'Geração OTP e Captcha', status: 'success', durationSeconds: 12 },
      { key: 'sso_login', label: 'Login SSO', status: 'failed', durationSeconds: 30 },
      { key: 'lms_access', label: 'Acesso LMS', status: 'skipped', durationSeconds: null },
      { key: 'contract_capture', label: 'Captura de Contratos', status: 'skipped', durationSeconds: null },
    ],
    logs: [
      { timestamp: t(14, 15, 22), level: 'info', message: 'Starting Playwright browser (headless: true)...' },
      { timestamp: t(14, 15, 22), level: 'info', message: 'Navigating to target URL: https://sso.lge.com/' },
      { timestamp: t(14, 15, 24), level: 'info', message: 'Captcha detected. Initializing local OCR model.' },
      { timestamp: t(14, 15, 33), level: 'info', message: 'OCR solved with 98% confidence. Generating OTP.' },
      { timestamp: t(14, 15, 34), level: 'success', message: 'OTP Generated successfully: ***1A4' },
      { timestamp: t(14, 15, 34), level: 'info', message: 'SSO Login triggered. Waiting for redirect...' },
      { timestamp: t(14, 15, 38), level: 'warning', message: 'Element #sso-btn is slow to render. Initiating polling.' },
      { timestamp: t(14, 15, 48), level: 'warning', message: 'Polling retry 1/3...' },
      { timestamp: t(14, 15, 58), level: 'warning', message: 'Polling retry 2/3...' },
      {
        timestamp: t(14, 16, 7),
        level: 'error',
        message:
          "TimeoutError: page.waitForSelector: Timeout 30000ms exceeded.\nCall log:\n- waiting for locator('#sso-login-btn') to be visible",
      },
      { timestamp: t(14, 16, 7), level: 'info', message: 'Saving failure screenshot to /dumps/err_1042.png' },
      { timestamp: t(14, 16, 7), level: 'info', message: 'Closing browser context. Process exited with code 1.' },
    ],
    error: { ...STEP_ERRORS.sso_login, screenshotUrl: null },
  };
}

export function getOverviewMock(): Overview {
  const since = periodStart('7d');
  const inPeriod = EXECUTIONS.filter((e) => new Date(e.startedAt).getTime() >= since);
  const failed = inPeriod.filter((e) => e.status === 'failed');
  const succeeded = inPeriod.length - failed.length;
  const runningRate = inPeriod.length ? (succeeded / inPeriod.length) * 100 : 0;

  const failuresByLabel = new Map<string, number>();
  for (const e of failed) {
    const label = STEPS.find((s) => s.key === FAILED_AT.get(e.id))?.label ?? 'Desconhecida';
    failuresByLabel.set(label, (failuresByLabel.get(label) ?? 0) + 1);
  }

  const trend = Array.from({ length: 7 }, (_, i) => {
    const day = at(6 - i, 0).toDateString();
    return inPeriod
      .filter((e) => new Date(e.startedAt).toDateString() === day)
      .reduce((sum, e) => sum + (e.records ?? 0), 0);
  });

  const status: OperationalStatus = runningRate >= RUNNING_RATE_TARGET ? 'green' : runningRate >= 70 ? 'yellow' : 'red';

  return {
    operationalStatus: status,
    statusMessage:
      status === 'green'
        ? 'O RPA está rodando conforme o esperado.'
        : status === 'yellow'
          ? 'Comportamento atípico: running rate abaixo da meta. Verifique o motivo das falhas.'
          : 'RPA fora de operação. Intervenção imediata necessária.',
    updatedAt: new Date().toISOString(),
    periodLabel: PERIOD_LABELS['7d'],
    runningRate: Math.round(runningRate * 10) / 10,
    runningRateTarget: RUNNING_RATE_TARGET,
    totalExecutions: inPeriod.length,
    succeeded,
    failed: failed.length,
    avgDurationSeconds: Math.round(inPeriod.reduce((sum, e) => sum + (e.durationSeconds ?? 0), 0) / Math.max(1, inPeriod.length)),
    capturedRecords: inPeriod.reduce((sum, e) => sum + (e.records ?? 0), 0),
    capturedTrend: trend,
    failuresByStep: [...failuresByLabel.entries()]
      .map(([label, count]) => ({ label, percent: Math.round((count / failed.length) * 100) }))
      .sort((a, b) => b.percent - a.percent),
    upcomingRuns: [
      { name: 'Fechamento Diário', scheduledAt: at(0, 18).toISOString(), source: 'cron' },
      { name: 'Abertura D+1', scheduledAt: at(-1, 8).toISOString(), source: 'cron' },
    ],
  };
}
