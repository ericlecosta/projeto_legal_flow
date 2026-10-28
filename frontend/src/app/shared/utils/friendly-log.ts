import { ExecutionError, LogEntry, LogLevel } from '../models/execution.model';

/**
 * Tradução dos logs do robô (e do simulador) para quem não é da área técnica.
 *
 * Cada regra reconhece uma mensagem pelo texto e devolve a frase em linguagem simples, ou
 * `null` para escondê-la (detalhe interno, como captcha, seletor ou caminho de arquivo).
 * Mensagens sem regra aparecem como vieram. O log original continua disponível em
 * "Mostrar detalhes técnicos" e no arquivo baixado.
 */

export interface FriendlyProgress {
  done: number;
  total: number;
}

export interface FriendlyLogEntry {
  timestamp: string;
  level: LogLevel;
  text: string;
  /** Andamento da conferência dos contratos ("12 de 52"); linhas seguidas viram uma só. */
  progress?: FriendlyProgress;
}

interface FriendlyText {
  text: string;
  level?: LogLevel;
  progress?: FriendlyProgress;
}

type Rule = [RegExp, ((match: RegExpMatchArray) => FriendlyText | null) | string | null];

const plural = (n: number, singular: string, plural: string) =>
  `${n} ${n === 1 ? singular : plural}`;

/** 95.3 → "1 min 35 s"; 42 → "42 s"; 3720 → "1 h 2 min". */
export function friendlyDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '';
  const total = Math.round(seconds);
  if (total < 1) return 'menos de 1 s';
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours > 0) return minutes ? `${hours} h ${minutes} min` : `${hours} h`;
  if (minutes > 0) return secs ? `${minutes} min ${secs} s` : `${minutes} min`;
  return `${secs} s`;
}

const contracts = (n: string) => plural(Number(n), 'contrato', 'contratos');

const RULES: Rule[] = [
  // Pedido feito pelo painel
  [/^Execução solicitada pelo painel/, 'Pedido recebido. Aguardando o robô começar…'],

  // Login (código temporário, portal corporativo e LMS)
  [
    /^(Iniciando obtenção de OTP|Nenhum OTP prévio informado|Acessando o autoatendimento LGE)/,
    'Gerando o código de acesso temporário…',
  ],
  [
    /^(OTP obtido com sucesso|OTP temporário obtido|OTP temporário gerado)/,
    () => ({ text: 'Código de acesso temporário gerado.', level: 'info' }),
  ],
  [/^(Navegando para o portal de login|Navegando para https:\/\/sso)/, 'Entrando no portal da LG…'],
  [/^(Navegando para a página do LMS|Redirecionando para o LMS)/, 'Abrindo o LMS…'],
  [
    /^(Página posicionada com sucesso|Sessão autenticada reaproveitada)/,
    () => ({ text: 'Login no LMS concluído.', level: 'success' }),
  ],

  // Relatório de contratos
  [/^Navegando para a URL de busca de contratos/, 'Abrindo a busca de contratos do LMS…'],
  [
    /^Filtrando por Subsidiary Code: ([^.\s]+)/,
    (m) => ({ text: `Filtrando os contratos da empresa ${m[1]}…` }),
  ],
  [/^Filtrando por período/, 'Aplicando o filtro de período…'],
  [
    /^Aplicando filtro Subsidiary (\S+) e período de (\d+) meses/,
    (m) => ({ text: `Filtrando os contratos da empresa ${m[1]} dos últimos ${m[2]} meses…` }),
  ],
  [
    /^(Iniciando o download do arquivo|Baixando relatório de contratos)/,
    'Baixando o relatório de contratos…',
  ],
  [
    /^Relatório de contratos salvo com sucesso/,
    () => ({ text: 'Relatório de contratos baixado.', level: 'success' }),
  ],

  // Conferência de cada contrato no LMS
  [
    /^Linhas após filtro '([^']*)' em '[^']*': (\d+) de (\d+)/,
    (m) => ({
      text: `${contracts(m[2])} do departamento ${m[1].toUpperCase()} para conferir (de ${m[3]} no relatório).`,
    }),
  ],
  [
    /^Filtro departamento (\S+): (\d+) contratos encontrados/,
    (m) => ({ text: `${contracts(m[2])} do departamento ${m[1]} para conferir.` }),
  ],
  [/^\[(\d+)\/(\d+)\] Processando/, (m) => progress(Number(m[1]), Number(m[2]))],
  [/^Extraindo Approval History: (\d+)\/(\d+)/, (m) => progress(Number(m[1]), Number(m[2]))],
  [
    /^Contrato (\S+) não encontrado na busca/,
    (m) => ({ text: `O contrato ${m[1]} não foi encontrado na busca do LMS.`, level: 'warning' }),
  ],
  [
    /^Tentativa \d+\/\d+ de (\S+) falhou/,
    (m) => ({
      // Nova tentativa é rotina; só conta como problema se o contrato ficar sem dados
      text: `O LMS não respondeu a tempo no contrato ${m[1]}. Tentando de novo…`,
      level: 'info',
    }),
  ],
  [
    /^(\S+) ficou sem dados após (\d+) tentativas/,
    (m) => ({
      text: `Não foi possível ler o contrato ${m[1]} depois de ${m[2]} tentativas. Ele fica sem dados nesta execução.`,
      level: 'error',
    }),
  ],
  [
    /^Print da falha de (\S+) salvo/,
    (m) => ({
      text: `Foi guardada uma imagem da tela do contrato ${m[1]} para o time técnico analisar.`,
    }),
  ],
  [
    /^Tela de detalhe ainda carregando/,
    () => ({
      text: 'O LMS está lento; o robô seguiu com o que já tinha carregado.',
      level: 'warning',
    }),
  ],
  [
    /^Não foi possível obter Biz-Drop Completed de (\S+)/,
    (m) => ({
      text: `Não foi possível ler a data de conclusão do Biz-Drop do contrato ${m[1]}.`,
      level: 'warning',
    }),
  ],
  [
    /^(\d+) contratos processados em ([\d.]+)s/,
    (m) => ({
      text: `${contracts(m[1])} conferidos no LMS em ${friendlyDuration(Number(m[2]))}.`,
      level: 'success',
    }),
  ],
  [
    /^(\d+) contrato\(s\) em Biz-Drop sem data de conclusão: (.+)/,
    (m) => ({
      text: `${contracts(m[1])} em Biz-Drop ficaram sem a data de conclusão: ${m[2]}.`,
      level: 'warning',
    }),
  ],
  [
    /^(\d+) contrato\(s\) sem dados por falha de carregamento: (.+)/,
    (m) => ({
      text: `${contracts(m[1])} ficaram sem dados porque o LMS não carregou: ${m[2]}.`,
      level: 'warning',
    }),
  ],
  [
    /^Nenhuma linha corresponde ao filtro/,
    () => ({
      text: 'Nenhum contrato do departamento foi encontrado no relatório.',
      level: 'warning',
    }),
  ],
  [
    /^Planilha consolidada salva em: .*\((\d+) registros\)/,
    (m) => ({ text: `Planilha com os dados de ${contracts(m[1])} gerada.` }),
  ],

  // Base Ideal e painel
  [
    /^Base Ideal tratada: (\d+) contrato/,
    (m) => ({ text: `Base Ideal montada com ${contracts(m[1])}.` }),
  ],
  [
    /^(\d+) contrato\(s\) gravados no banco: (\d+) novos, (\d+) atualizados/,
    (m) => ({
      text: `${contracts(m[1])} salvos no painel (${m[2]} novos e ${m[3]} atualizados).`,
      level: 'success',
    }),
  ],
  [
    /^(\d+) registros capturados/,
    (m) => ({ text: `${contracts(m[1])} capturados.`, level: 'success' }),
  ],
  [/^Fluxo concluído/, () => ({ text: 'Execução concluída com sucesso.', level: 'success' })],
  [
    /^Execução acima do tempo esperado \(limite: (.+)\)/,
    (m) => ({
      text: `A execução demorou mais que o normal (o esperado é até ${m[1]}).`,
      level: 'warning',
    }),
  ],

  // Detalhes internos: escondidos (continuam nos detalhes técnicos)
  [
    /^(\d+\. |Erro durante |Captcha|Texto de Captcha|Resposta do serviço|Submetendo requisição|Falha na validação do Captcha|Exceção durante submissão|Falha ao iniciar com canal|Iniciando navegador|Iniciando nova instância do navegador|Contexto do navegador|Preenchendo User ID|Campo #OTPPASSWORD|\[Alerta do Navegador\]|Pesquisando contrato|Lendo planilha|Tela de detalhe não foi recriada|Tentativa \d+\/\d+ do Biz-Drop|Não foi possível fechar o navegador|Qty Review sem número|Nenhuma Request Date|Linhas após filtro LMS_SOMENTE|API_URL não definida|Screenshot da falha|Fechando contexto do navegador|\w*Error: |BrowserType\.)/,
    null,
  ],
  [/^\S+ coletado em [\d.]+s$/, null],
  [
    /^Nenhum worker do robô assumiu/,
    () => ({ text: 'O robô não respondeu ao pedido a tempo.', level: 'warning' }),
  ],

  // Falha que encerra a execução: "Título: motivo técnico" vira só o título explicado
  [
    /^((?:Falha|Erro)[^:]*?): /,
    (m) => ({
      text: `${friendlyError({ title: m[1], message: '', screenshotUrl: null }).title}.`,
      level: 'error',
    }),
  ],
];

function progress(current: number, total: number): FriendlyText {
  return {
    text: `Conferindo os contratos no LMS: ${current} de ${total}.`,
    progress: { done: current, total },
  };
}

/** A frase amigável de um log, ou null quando é detalhe técnico. */
export function friendlyText(log: LogEntry): FriendlyText | null {
  const message = log.message.trim();
  for (const [pattern, result] of RULES) {
    const match = message.match(pattern);
    if (!match) continue;
    if (result === null) return null;
    const friendly = typeof result === 'string' ? { text: result } : result(match);
    return friendly && { ...friendly, level: friendly.level ?? log.level };
  }
  return { text: message, level: log.level };
}

/**
 * Logs em linguagem simples: sem os detalhes técnicos, sem frases repetidas em sequência e
 * com o andamento dos contratos numa linha só (a mais recente).
 */
export function friendlyLogs(logs: LogEntry[]): FriendlyLogEntry[] {
  const entries: FriendlyLogEntry[] = [];
  for (const log of logs) {
    const friendly = friendlyText(log);
    if (!friendly) continue;
    const entry: FriendlyLogEntry = {
      timestamp: log.timestamp,
      level: friendly.level ?? log.level,
      text: friendly.text,
      ...(friendly.progress ? { progress: friendly.progress } : {}),
    };
    const last = entries.at(-1);
    if (last && ((last.progress && entry.progress) || last.text === entry.text)) {
      entries[entries.length - 1] = entry;
    } else {
      entries.push(entry);
    }
  }
  return entries;
}

/** Andamento mais recente da conferência dos contratos, se houver. */
export function latestProgress(logs: LogEntry[]): FriendlyProgress | null {
  for (let i = logs.length - 1; i >= 0; i--) {
    const progress = friendlyText(logs[i])?.progress;
    if (progress) return progress;
  }
  return null;
}

export interface FriendlyError {
  title: string;
  explanation: string;
  action: string;
}

const CALL_DEVS =
  'Se acontecer de novo, avise o time de desenvolvimento e envie o registro desta execução (botão "Baixar registro").';
const TRY_AGAIN = 'Tente executar de novo em alguns minutos.';

const ERRORS: Record<string, Omit<FriendlyError, 'title'> & { title?: string }> = {
  'Falha no login do LMS': {
    title: 'Não foi possível entrar no LMS',
    explanation: 'O robô não conseguiu fazer login no portal da LG ou no LMS.',
    action: `${TRY_AGAIN} Se continuar, confira se o usuário e a senha do robô ainda são válidos. ${CALL_DEVS}`,
  },
  'Falha ao baixar o relatório de contratos': {
    title: 'Não foi possível baixar o relatório de contratos',
    explanation: 'O login funcionou, mas o LMS não entregou o relatório de contratos.',
    action: `${TRY_AGAIN} O LMS pode estar lento ou fora do ar. ${CALL_DEVS}`,
  },
  'Falha na extração dos contratos': {
    title: 'Não foi possível ler os contratos no LMS',
    explanation:
      'O relatório foi baixado, mas o robô não conseguiu abrir os detalhes dos contratos.',
    action: `${TRY_AGAIN} ${CALL_DEVS}`,
  },
  'Falha no tratamento da base Ideal': {
    title: 'Não foi possível montar a Base Ideal',
    explanation: 'Os contratos foram lidos, mas a planilha veio num formato diferente do esperado.',
    action: `Avise o time de desenvolvimento: provavelmente o LMS mudou alguma coluna. ${CALL_DEVS}`,
  },
  'Falha ao gravar os contratos no banco': {
    title: 'Os contratos não foram salvos no painel',
    explanation: 'A Base Ideal foi montada, mas o painel recusou ou não recebeu os dados.',
    action: `A planilha ficou salva no servidor do robô. ${CALL_DEVS}`,
  },
  'Falha inesperada no robô': {
    title: 'O robô parou de forma inesperada',
    explanation: 'O programa do robô foi encerrado antes de terminar.',
    action: `${TRY_AGAIN} ${CALL_DEVS}`,
  },
  'Execução interrompida': {
    explanation: 'Alguém parou esta execução pelo painel.',
    action: 'Nada a corrigir. Quando quiser, execute de novo pelo botão "Executar Fluxo Agora".',
  },
  'Robô indisponível': {
    title: 'O robô não respondeu',
    explanation:
      'O pedido foi feito, mas o robô não começou a trabalhar. Ele pode estar desligado.',
    action: `Avise o time de desenvolvimento para verificar o serviço do robô. ${CALL_DEVS}`,
  },
  // Simulador (modo de demonstração)
  'Falha ao iniciar o navegador': {
    title: 'O robô não conseguiu abrir o navegador',
    explanation: 'O navegador que o robô usa não abriu no servidor.',
    action: `${TRY_AGAIN} ${CALL_DEVS}`,
  },
  'Captcha não reconhecido': {
    title: 'O robô não conseguiu ler o captcha',
    explanation:
      'A imagem de verificação do portal da LG não foi reconhecida depois de várias tentativas.',
    action: TRY_AGAIN,
  },
  'Timeout no Elemento SSO': {
    title: 'O portal da LG demorou a responder',
    explanation: 'A tela de login do portal não carregou a tempo.',
    action: `${TRY_AGAIN} O portal pode estar lento.`,
  },
  'Sessão não reconhecida pelo LMS': {
    title: 'O LMS não aceitou o login',
    explanation: 'O login no portal funcionou, mas o LMS pediu para entrar de novo.',
    action: `${TRY_AGAIN} ${CALL_DEVS}`,
  },
  'Tabela de contratos não carregou': {
    title: 'A lista de contratos não carregou',
    explanation: 'O LMS não mostrou os contratos dentro do tempo esperado.',
    action: `${TRY_AGAIN} O LMS pode estar lento.`,
  },
};

/** Erro explicado em linguagem simples, com o que fazer. O texto técnico fica nos detalhes. */
export function friendlyError(error: ExecutionError): FriendlyError {
  const known = ERRORS[error.title];
  if (known)
    return {
      title: known.title ?? error.title,
      explanation: known.explanation,
      action: known.action,
    };
  return {
    title: error.title,
    explanation: 'O robô encontrou um problema e parou antes de terminar.',
    action: `${TRY_AGAIN} ${CALL_DEVS}`,
  };
}
