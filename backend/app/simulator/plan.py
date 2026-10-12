"""
Roteiro de uma execução fictícia do RPA: quais etapas rodam, quanto tempo cada uma leva,
quais logs emitem e onde (se for o caso) a execução falha.

O mesmo roteiro alimenta o seed do histórico (gravado de uma vez, com horários no passado)
e o simulador ao vivo (gravado aos poucos, em tempo real).
"""

import random
from dataclasses import dataclass, field

from app.schemas import ExecutionFlow, LogLevel, StepKey

# Execuções acima deste tempo são marcadas como atípicas (padrão do Control Tower).
ATYPICAL_THRESHOLD_SECONDS = 300

STEPS: list[tuple[StepKey, str]] = [
    ("start_session", "Iniciar Sessão"),
    ("otp_captcha", "Geração OTP e Captcha"),
    ("sso_login", "Login SSO"),
    ("lms_access", "Acesso LMS"),
    ("contract_capture", "Captura de Contratos"),
]
STEP_LABELS: dict[str, str] = dict(STEPS)

# Faixa de duração (segundos) de cada etapa numa execução normal.
STEP_DURATIONS: dict[StepKey, tuple[float, float]] = {
    "start_session": (0.5, 2.0),
    "otp_captcha": (8.0, 20.0),
    "sso_login": (5.0, 15.0),
    "lms_access": (3.0, 8.0),
    "contract_capture": (30.0, 90.0),
}

# Peso de cada etapa no sorteio da etapa que falha (o SSO e o captcha são os pontos mais frágeis).
FAILURE_WEIGHTS: dict[StepKey, int] = {
    "start_session": 5,
    "otp_captcha": 30,
    "sso_login": 40,
    "lms_access": 15,
    "contract_capture": 10,
}

STEP_ERRORS: dict[StepKey, tuple[str, str, str]] = {
    # etapa: (título, mensagem para o usuário, linha de log técnica)
    "start_session": (
        "Falha ao iniciar o navegador",
        "O Chromium não pôde ser iniciado no runner. Verifique a memória compartilhada do contêiner.",
        "BrowserType.launch: Target page, context or browser has been closed",
    ),
    "otp_captcha": (
        "Captcha não reconhecido",
        "O OCR local não atingiu a confiança mínima após 3 tentativas de leitura do captcha.",
        "OTPRetrievalError: confiança do OCR abaixo de 70% após 3 tentativas",
    ),
    "sso_login": (
        "Timeout no Elemento SSO",
        "O seletor de login corporativo #OTPPASSWORD não foi encontrado ou demorou mais de 30 segundos "
        "para responder. O RPA abortou a operação.",
        "TimeoutError: page.wait_for_selector: Timeout 30000ms exceeded.\n"
        "Call log:\n- waiting for locator('#OTPPASSWORD') to be visible",
    ),
    "lms_access": (
        "Sessão não reconhecida pelo LMS",
        "Após o login no SSO, o LMS redirecionou para a tela de login. A sessão autenticada não foi reaproveitada.",
        "LoginError: redirecionado para https://sso.lge.com/ ao acessar o LMS",
    ),
    "contract_capture": (
        "Tabela de contratos não carregou",
        "A grade de busca de contratos não retornou resultados dentro do tempo limite.",
        "ExtractError: grade de contratos vazia após 60s (filtro Subsidiary LGESP)",
    ),
}


@dataclass
class PlannedLog:
    offset: float  # segundos desde o início da etapa
    level: LogLevel
    message: str


@dataclass
class PlannedStep:
    key: StepKey
    label: str
    duration: float
    failed: bool = False
    logs: list[PlannedLog] = field(default_factory=list)


@dataclass
class RunPlan:
    flow: ExecutionFlow
    steps: list[PlannedStep]  # inclui só as etapas que chegam a rodar
    all_steps: list[tuple[StepKey, str]]  # todas as etapas do fluxo, para marcar as puladas
    failed_step: StepKey | None
    records: int | None
    atypical: bool

    @property
    def status(self) -> str:
        if self.failed_step:
            return "failed"
        return "atypical" if self.atypical else "success"

    @property
    def error(self) -> tuple[str, str, str] | None:
        return STEP_ERRORS[self.failed_step] if self.failed_step else None


def _step_logs(rng: random.Random, key: StepKey, duration: float, records: int | None) -> list[PlannedLog]:
    """Logs no estilo dos módulos src/auth e src/extraction do RPA, distribuídos ao longo da etapa."""

    def at(fraction: float, level: LogLevel, message: str) -> PlannedLog:
        return PlannedLog(round(duration * fraction, 2), level, message)

    if key == "start_session":
        return [
            at(0.0, "info", "Iniciando navegador Chromium (headless: true)..."),
            at(0.8, "info", "Contexto do navegador criado."),
        ]
    if key == "otp_captcha":
        confidence = rng.randint(82, 99)
        suffix = "".join(rng.choices("0123456789ABCDEF", k=3))
        return [
            at(0.0, "info", "Acessando o autoatendimento LGE para gerar o OTP temporário."),
            at(0.2, "info", "Captcha detectado. Inicializando OCR local (ddddocr)."),
            at(0.7, "info", f"Captcha resolvido com {confidence}% de confiança."),
            at(0.95, "success", f"OTP temporário gerado: ***{suffix}"),
        ]
    if key == "sso_login":
        return [
            at(0.0, "info", "Navegando para https://sso.lge.com/"),
            at(0.3, "info", "Preenchendo User ID e senha LDAP."),
            at(0.6, "info", "Campo #OTPPASSWORD renderizado. Inserindo OTP e enviando login."),
        ]
    if key == "lms_access":
        return [
            at(0.0, "info", "Redirecionando para o LMS (https://lms.lge.com/#/app/dashboard)."),
            at(0.8, "info", "Sessão autenticada reaproveitada no LMS."),
        ]
    # contract_capture
    logs = [
        at(0.0, "info", "Aplicando filtro Subsidiary LGESP e período de 3 meses."),
        at(0.1, "info", "Baixando relatório de contratos (relatorio_contratos.xlsx)."),
    ]
    if records:
        logs.append(at(0.2, "info", f"Filtro departamento MAO: {records} contratos encontrados."))
        for fraction in (0.45, 0.7, 0.9):
            done = int(records * (fraction - 0.2) / 0.75)
            logs.append(at(fraction, "info", f"Extraindo Approval History: {done}/{records} contratos..."))
    return logs


def build_plan(
    rng: random.Random,
    flow: ExecutionFlow = "login_capture",
    failure_rate: float = 0.12,
    atypical_rate: float = 0.06,
) -> RunPlan:
    all_steps = STEPS[:2] if flow == "otp_only" else STEPS
    keys = [key for key, _ in all_steps]

    failed_step: StepKey | None = None
    if rng.random() < failure_rate:
        weights = [FAILURE_WEIGHTS[key] for key in keys]
        failed_step = rng.choices(keys, weights=weights)[0]

    atypical = failed_step is None and rng.random() < atypical_rate
    records = rng.randint(400, 1200) if flow == "login_capture" and failed_step is None else None

    steps: list[PlannedStep] = []
    for key, label in all_steps:
        low, high = STEP_DURATIONS[key]
        duration = round(rng.uniform(low, high), 1)
        if atypical and key == keys[-1]:
            # Etapa lenta o suficiente para estourar o limite de 5 minutos
            duration = round(rng.uniform(320, 420), 1)
        if key == failed_step and key == "sso_login":
            duration = 30.0 + round(rng.uniform(0, 2), 1)  # timeout do wait_for_selector

        step = PlannedStep(key, label, duration, logs=_step_logs(rng, key, duration, records))
        if key == failed_step:
            step.failed = True
            title, _, technical = STEP_ERRORS[key]
            # Mantém só os logs da primeira metade da etapa e encerra com o erro
            step.logs = [log for log in step.logs if log.offset < duration * 0.5]
            step.logs += [
                PlannedLog(duration, "error", technical),
                PlannedLog(duration, "info", "Screenshot da falha salvo em /dumps/."),
                PlannedLog(duration, "info", "Fechando contexto do navegador. Processo encerrado com código 1."),
            ]
            steps.append(step)
            break

        steps.append(step)

    if failed_step is None:
        last = steps[-1]
        if atypical:
            last.logs.append(
                PlannedLog(last.duration, "warning", "Execução acima do tempo esperado (limite: 05m 00s).")
            )
        message = f"{records} registros capturados." if records is not None else "Fluxo concluído."
        last.logs.append(PlannedLog(last.duration, "success", message))

    return RunPlan(flow, steps, list(all_steps), failed_step, records, atypical)
