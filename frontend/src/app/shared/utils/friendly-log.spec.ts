import { LogEntry, LogLevel } from '../models/execution.model';
import {
  friendlyDuration,
  friendlyError,
  friendlyLogs,
  friendlyText,
  latestProgress,
} from './friendly-log';

const log = (message: string, level: LogLevel = 'info', second = 0): LogEntry => ({
  timestamp: `2026-10-27T10:00:${String(second).padStart(2, '0')}-04:00`,
  level,
  message,
});

const text = (message: string, level: LogLevel = 'info') => friendlyText(log(message, level));

describe('friendlyText', () => {
  it('traduz as mensagens do robô para linguagem simples', () => {
    expect(text('Navegando para o portal de login: https://sso.lge.com/login')?.text).toBe(
      'Entrando no portal da LG…',
    );
    expect(text('Filtrando por Subsidiary Code: LGESP...')?.text).toBe(
      'Filtrando os contratos da empresa LGESP…',
    );
    expect(
      text("Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 785")?.text,
    ).toBe('52 contratos do departamento MAO para conferir (de 785 no relatório).');
    expect(text('52 contratos processados em 95.3s')).toEqual({
      text: '52 contratos conferidos no LMS em 1 min 35 s.',
      level: 'success',
    });
    expect(text('52 contrato(s) gravados no banco: 3 novos, 49 atualizados')?.text).toBe(
      '52 contratos salvos no painel (3 novos e 49 atualizados).',
    );
    expect(text('Base Ideal tratada: 1 contrato(s) em /app/downloads/base_ideal.xlsx')?.text).toBe(
      'Base Ideal montada com 1 contrato.',
    );
  });

  it('nunca mostra o código de acesso, nem em logs antigos que o gravaram', () => {
    expect(text('OTP obtido com sucesso: 483920')?.text).toBe(
      'Código de acesso temporário gerado.',
    );
    expect(text('OTP temporário obtido para login: 483920')?.text).not.toContain('483920');
    expect(text('OTP temporário gerado: ***4F2', 'success')?.text).not.toContain('4F2');
    expect(text('Resposta do serviço: 0#OK#483920')).toBeNull();
  });

  it('esconde detalhes internos (captcha, seletores, caminhos, erros de biblioteca)', () => {
    for (const message of [
      "Captcha reconhecido: 'x7k2'",
      '5. Tentativa 1/5 de validação do formulário...',
      'Pesquisando contrato: C2026833448',
      'C2026833448 coletado em 3.2s',
      'Lendo planilha: /app/downloads/relatorio_contratos.xlsx',
      'Erro durante extração detalhada: Timeout 90000ms exceeded',
      'TimeoutError: page.wait_for_selector: Timeout 30000ms exceeded.',
      "Falha ao iniciar com canal 'chrome' (erro). Tentando com o Chromium padrão do Playwright...",
      '[Alerta do Navegador] Sessão expirada',
    ]) {
      expect(text(message)).toBeNull();
    }
  });

  it('nova tentativa é rotina; contrato sem dados é erro', () => {
    expect(
      text('Tentativa 1/3 de C2026833448 falhou (Timeout). Tentando de novo...', 'warning'),
    ).toEqual({
      text: 'O LMS não respondeu a tempo no contrato C2026833448. Tentando de novo…',
      level: 'info',
    });
    expect(text('C2026833448 ficou sem dados após 3 tentativas: Timeout', 'error')?.level).toBe(
      'error',
    );
  });

  it('a falha final mostra o título explicado, sem o detalhe técnico', () => {
    expect(text('Falha na extração dos contratos: page.goto: net::ERR_TIMED_OUT', 'error')).toEqual(
      { text: 'Não foi possível ler os contratos no LMS.', level: 'error' },
    );
  });

  it('mensagem sem regra aparece como veio', () => {
    expect(text('Execução cancelada antes de o robô começar.', 'warning')).toEqual({
      text: 'Execução cancelada antes de o robô começar.',
      level: 'warning',
    });
  });
});

describe('friendlyLogs', () => {
  it('junta o andamento dos contratos numa linha só e tira repetições', () => {
    const entries = friendlyLogs([
      log('Iniciando obtenção de OTP para o usuário: robo', 'info', 1),
      log('Nenhum OTP prévio informado. Iniciando geração de OTP temporário...', 'info', 2),
      log("Captcha reconhecido: 'x7k2'", 'info', 3),
      log('[1/52] Processando C1', 'info', 4),
      log('Pesquisando contrato: C1', 'info', 5),
      log('[2/52] Processando C2', 'info', 6),
      log('Contrato C3 não encontrado na busca.', 'warning', 7),
      log('[3/52] Processando C4', 'info', 8),
    ]);
    expect(entries.map((e) => e.text)).toEqual([
      'Gerando o código de acesso temporário…',
      'Conferindo os contratos no LMS: 2 de 52.',
      'O contrato C3 não foi encontrado na busca do LMS.',
      'Conferindo os contratos no LMS: 3 de 52.',
    ]);
    expect(entries[1].progress).toEqual({ done: 2, total: 52 });
    expect(entries[1].timestamp).toBe('2026-10-27T10:00:06-04:00');
  });

  it('entende os logs do simulador', () => {
    const entries = friendlyLogs([
      log('Aplicando filtro Subsidiary LGESP e período de 3 meses.'),
      log('Extraindo Approval History: 120/480 contratos...'),
      log('480 registros capturados.', 'success'),
    ]);
    expect(entries.map((e) => e.text)).toEqual([
      'Filtrando os contratos da empresa LGESP dos últimos 3 meses…',
      'Conferindo os contratos no LMS: 120 de 480.',
      '480 contratos capturados.',
    ]);
  });
});

describe('latestProgress', () => {
  it('pega o andamento mais recente', () => {
    expect(
      latestProgress([log('[1/52] Processando C1'), log('[7/52] Processando C7'), log('Outro')]),
    ).toEqual({ done: 7, total: 52 });
    expect(latestProgress([log('Login no LMS')])).toBeNull();
  });
});

describe('friendlyError', () => {
  it('explica os erros conhecidos e diz o que fazer', () => {
    const error = friendlyError({
      title: 'Falha no login do LMS',
      message: 'TimeoutError: page.fill: Timeout 30000ms exceeded',
      screenshotUrl: null,
    });
    expect(error.title).toBe('Não foi possível entrar no LMS');
    expect(error.explanation).not.toMatch(/Timeout|page\./);
    expect(error.action).toContain('usuário e a senha');
  });

  it('erro desconhecido ainda orienta a pessoa', () => {
    const error = friendlyError({ title: 'Algo novo', message: 'stack', screenshotUrl: null });
    expect(error.title).toBe('Algo novo');
    expect(error.action).toContain('Baixar registro');
  });
});

describe('friendlyDuration', () => {
  it('escreve o tempo por extenso', () => {
    expect(friendlyDuration(0.2)).toBe('menos de 1 s');
    expect(friendlyDuration(42)).toBe('42 s');
    expect(friendlyDuration(95.3)).toBe('1 min 35 s');
    expect(friendlyDuration(120)).toBe('2 min');
    expect(friendlyDuration(3720)).toBe('1 h 2 min');
    expect(friendlyDuration(null)).toBe('');
  });
});
