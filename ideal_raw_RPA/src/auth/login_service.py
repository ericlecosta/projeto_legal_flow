"""
Módulo responsável pelo fluxo de login completo no portal SSO da LGE
e redirecionamento para o sistema LMS (Legal Management System).
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from src.auth.otp_service import obter_otp_temporario, OTPRetrievalError

logger = logging.getLogger("rpa_lms.login")


class LoginError(Exception):
    """Exceção disparada quando ocorre falha no fluxo de login."""
    pass


def _carregar_variaveis_ambiente():
    """Busca o arquivo .env no diretório de execução, na pasta atual ou pastas pai."""
    candidatos = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    for p in candidatos:
        if p.exists():
            load_dotenv(p)
            return
    load_dotenv()


def _setup_dialog_handler(page_or_context):
    """Manipulador para aceitar alertas do navegador de forma silenciosa e resiliente."""
    def _on_dialog(dialog):
        try:
            logger.info(f"[Alerta do Navegador] {dialog.message}")
            dialog.accept()
        except Exception:
            pass

    page_or_context.on("dialog", _on_dialog)


def fazer_login_lms(
    user_id: Optional[str] = None,
    password: Optional[str] = None,
    otp: Optional[str] = None,
    employee_number: Optional[str] = None,
    personal_identification_code: Optional[str] = None,
    login_address: Optional[str] = None,
    lms_index: Optional[str] = None,
    headless: Optional[bool] = None,
    page: Optional[Page] = None,
    timeout: int = 30000,
) -> Page:
    """
    Realiza o login no portal SSO da LG Electronics utilizando as credenciais e o OTP temporário,
    navegando em seguida diretamente para a página inicial do LMS (LMS_INDEX).

    Args:
        user_id: Usuário corporativo LGE. Se None, obtém de USER_ID do .env.
        password: Senha corporativa LGE. Se None, obtém de PASSWORD do .env.
        otp: Código OTP temporário já gerado. Se None, a função gera automaticamente.
        employee_number: Matrícula do funcionário (usado na geração do OTP).
        personal_identification_code: Código pessoal (usado na geração do OTP).
        login_address: URL do SSO LGE. Padrão: 'https://sso.lge.com/'.
        lms_index: URL da página inicial do LMS. Padrão: 'https://lms.lge.com/#/app/dashboard'.
        headless: Executar o navegador em segundo plano (True) ou visível (False). Se None, lê HEADLESS do .env.
        page: Instância opcional de Page do Playwright para reaproveitar sessão existente.
        timeout: Timeout máximo em milissegundos para os seletores e navegações.

    Returns:
        Page: Objeto de página do Playwright autenticado e posicionado na página LMS_INDEX.
    """
    _carregar_variaveis_ambiente()

    if headless is None:
        headless = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

    user_id = user_id or os.getenv("USER_ID")
    password = password or os.getenv("PASSWORD")
    login_address = login_address or os.getenv("LOGIN_ADDRESS", "https://sso.lge.com/")
    lms_index = lms_index or os.getenv("LMS_INDEX", "https://lms.lge.com/#/app/dashboard")

    if not user_id or not password:
        raise ValueError("USER_ID e PASSWORD são obrigatórios para efetuar o login.")

    # 1. Gera o OTP automaticamente se não foi informado
    if not otp:
        logger.info("Nenhum OTP prévio informado. Iniciando geração de OTP temporário...")
        otp = obter_otp_temporario(
            user_id=user_id,
            password=password,
            employee_number=employee_number,
            personal_identification_code=personal_identification_code,
            login_address=login_address,
            headless=headless,
            timeout=timeout,
        )
        logger.info("OTP temporário obtido para login.")

    # 2. Inicializa o navegador caso uma Page não tenha sido fornecida
    playwright_instance = None
    if page is None:
        logger.info("Iniciando nova instância do navegador Playwright...")
        playwright_instance = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ]
        channel = os.getenv("BROWSER_CHANNEL", "chrome" if not headless else None)
        if channel in ("", "none", "None"):
            channel = None

        try:
            browser: Browser = playwright_instance.chromium.launch(
                headless=headless,
                channel=channel,
                args=launch_args,
            )
        except Exception as err:
            if channel is not None:
                logger.warning(
                    f"Falha ao iniciar com canal '{channel}' ({err}). "
                    "Tentando com o Chromium padrão do Playwright..."
                )
                browser = playwright_instance.chromium.launch(
                    headless=headless,
                    channel=None,
                    args=launch_args,
                )
            else:
                raise

        context: BrowserContext = browser.new_context(ignore_https_errors=True)
        context.on("page", _setup_dialog_handler)

        page = context.new_page()
        _setup_dialog_handler(page)

        page._playwright_instance = playwright_instance
        page._browser_instance = browser

    try:
        # 3. Acessa o portal SSO
        logger.info(f"Navegando para o portal de login: {login_address}")
        page.goto(login_address, wait_until="domcontentloaded", timeout=timeout)

        # 4. Preenche credenciais e aciona o campo de OTP
        logger.info("Preenchendo User ID e Senha corporativa...")
        page.wait_for_selector("#USER", state="visible", timeout=timeout)
        page.fill("#USER", user_id)
        page.fill("#LDAPPASSWORD", password)

        page.locator("#USER").press("Tab")
        time.sleep(0.5)

        # 5. Preenche o OTP temporário
        logger.info("Aguardando campo #OTPPASSWORD e preenchendo token...")
        page.wait_for_selector("#OTPPASSWORD", state="visible", timeout=timeout)
        page.fill("#OTPPASSWORD", otp)

        # 6. Submete a autenticação
        logger.info("Clicando no botão de login (#loginSsobtn)...")
        page.click("#loginSsobtn")

        # Pausa para submissão do formulário e gravação dos cookies de sessão
        time.sleep(3)

        # 7. Navega diretamente para a URL inicial do LMS
        logger.info(f"Navegando para a página do LMS: {lms_index}")
        page.goto(lms_index, wait_until="domcontentloaded", timeout=timeout)

        time.sleep(3)
        logger.info(f"Página posicionada com sucesso em: {page.url}")

        return page

    except Exception as exc:
        logger.error(f"Erro durante o processo de login no LMS: {exc}")
        raise LoginError(f"Falha ao realizar login no LMS: {exc}") from exc


def fechar_sessao_lms(page: Page):
    """Fecha a página, navegador e driver do Playwright de forma segura."""
    try:
        if hasattr(page, "_browser_instance") and page._browser_instance:
            page._browser_instance.close()
        elif page.context and page.context.browser:
            page.context.browser.close()
    except Exception:
        pass

    try:
        if hasattr(page, "_playwright_instance") and page._playwright_instance:
            page._playwright_instance.stop()
    except Exception:
        pass
