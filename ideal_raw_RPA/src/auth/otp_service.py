"""
Módulo responsável pela obtenção automatizada do OTP temporário
no portal de autoatendimento da LG Electronics (LGE).
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import ddddocr
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

logger = logging.getLogger("rpa_lms.otp")


class OTPRetrievalError(Exception):
    """Exceção disparada quando não é possível recuperar o OTP temporário."""

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
    """Manipulador resiliente de diálogos nativos do navegador."""

    def _on_dialog(dialog):
        try:
            logger.info(f"[Alerta do Navegador] {dialog.message}")
            dialog.accept()
        except Exception:
            pass

    page_or_context.on("dialog", _on_dialog)


def obter_otp_temporario(
    user_id: Optional[str] = None,
    password: Optional[str] = None,
    employee_number: Optional[str] = None,
    personal_identification_code: Optional[str] = None,
    login_address: Optional[str] = None,
    headless: Optional[bool] = None,
    max_captcha_retries: int = 5,
    timeout: int = 20000,
) -> str:
    """
    Executa o fluxo completo de autoatendimento de OTP da LGE e retorna o código OTP temporário.

    Args:
        user_id: Usuário de rede LGE. Se None, lê de USER_ID no .env.
        password: Senha de rede LGE. Se None, lê de PASSWORD no .env.
        employee_number: Matrícula do colaborador. Se None, lê de EMPLOYEE_NUMBER no .env.
        personal_identification_code: Código pessoal (YYYYMMDD). Se None, lê de PERSONAL_IDENTIFICATION_CODE no .env.
        login_address: URL inicial do SSO LGE. Padrão: 'https://sso.lge.com/'.
        headless: Executar navegador em segundo plano (True) ou visível (False). Se None, lê HEADLESS do .env.
        max_captcha_retries: Quantidade máxima de tentativas para quebra do Captcha.
        timeout: Timeout máximo em milissegundos para operações de rede/seletor.

    Returns:
        str: Código OTP temporário gerado (ex: '8966881p').
    """
    _carregar_variaveis_ambiente()

    if headless is None:
        headless = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

    user_id = user_id or os.getenv("USER_ID")
    password = password or os.getenv("PASSWORD")
    employee_number = employee_number or os.getenv("EMPLOYEE_NUMBER")
    personal_identification_code = personal_identification_code or os.getenv("PERSONAL_IDENTIFICATION_CODE")
    login_address = login_address or os.getenv("LOGIN_ADDRESS", "https://sso.lge.com/")

    faltantes = []
    if not user_id:
        faltantes.append("USER_ID")
    if not password:
        faltantes.append("PASSWORD")
    if not employee_number:
        faltantes.append("EMPLOYEE_NUMBER")
    if not personal_identification_code:
        faltantes.append("PERSONAL_IDENTIFICATION_CODE")

    if faltantes:
        raise ValueError(
            f"As seguintes credenciais obrigatórias não foram informadas nem encontradas no .env: {', '.join(faltantes)}"
        )

    logger.info(f"Iniciando obtenção de OTP para o usuário: {user_id}")
    ocr = ddddocr.DdddOcr(show_ad=False)

    with sync_playwright() as p:
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
            browser: Browser = p.chromium.launch(
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
                browser = p.chromium.launch(
                    headless=headless,
                    channel=None,
                    args=launch_args,
                )
            else:
                raise
        context: BrowserContext = browser.new_context(ignore_https_errors=True)
        context.on("page", _setup_dialog_handler)

        try:
            page: Page = context.new_page()
            _setup_dialog_handler(page)

            logger.info(f"1. Acessando página SSO: {login_address}")
            page.goto(login_address, wait_until="domcontentloaded", timeout=timeout)

            page.wait_for_selector("#USER", state="visible", timeout=timeout)
            page.fill("#USER", user_id)
            page.fill("#LDAPPASSWORD", password)
            page.locator("#USER").press("Tab")
            time.sleep(0.5)

            logger.info("2. Clicando em Self-service OTP (#OTP)...")
            with context.expect_page(timeout=timeout) as p1_info:
                page.click("#OTP")

            auth_page: Page = p1_info.value
            auth_page.wait_for_load_state("domcontentloaded", timeout=timeout)

            logger.info("3. Preenchendo senha e submetendo autenticação (#myButton)...")
            auth_page.wait_for_selector("#pw", state="visible", timeout=timeout)
            auth_page.fill("#pw", password)

            with context.expect_page(timeout=timeout) as p2_info:
                auth_page.click("#myButton")

            services_page: Page = p2_info.value
            services_page.wait_for_load_state("domcontentloaded", timeout=timeout)

            logger.info("4. Clicando em OTP temporário (.tempPw)...")
            services_page.wait_for_selector(".tempPw", state="visible", timeout=timeout)
            with context.expect_page(timeout=timeout) as p3_info:
                services_page.click(".tempPw")

            req_page: Page = p3_info.value
            req_page.wait_for_load_state("domcontentloaded", timeout=timeout)

            req_page.evaluate("() => { window.langSetting = 'eng'; }")
            req_page.wait_for_selector("#photo_imageE:visible, #photo_imageK:visible", state="visible", timeout=timeout)
            captcha_img_element = req_page.locator("#photo_imageE:visible, #photo_imageK:visible").first

            otp_code: Optional[str] = None

            for tentativa in range(1, max_captcha_retries + 1):
                logger.info(f"5. Tentativa {tentativa}/{max_captcha_retries} de validação do formulário...")

                req_page.wait_for_function(
                    """() => {
                        const imgs = [document.querySelector('#photo_imageE'), document.querySelector('#photo_imageK')];
                        const visibleImg = imgs.find(img => img && img.offsetParent !== null && img.complete && img.naturalWidth > 0);
                        return !!visibleImg;
                    }""",
                    timeout=timeout,
                )
                time.sleep(0.4)

                img_bytes = captcha_img_element.screenshot()
                captcha_texto = ocr.classification(img_bytes).strip()
                logger.info(f"Captcha reconhecido: '{captcha_texto}'")

                if len(captcha_texto) < 4:
                    logger.warning("Texto de Captcha insuficiente, solicitando recarga da imagem...")
                    reload_btn = req_page.locator('img[src*="captcha_reload"]:visible').first
                    if reload_btn.is_visible():
                        reload_btn.click()
                    time.sleep(1)
                    continue

                req_page.evaluate(
                    """(args) => {
                        window.langSetting = 'eng';
                        const [bizid, pcode, captcha] = args;
                        for (const prefix of ['E', 'K']) {
                            const b = document.getElementById('bizid' + prefix);
                            if (b) b.value = bizid;
                            const p = document.getElementById('pcode' + prefix);
                            if (p) p.value = pcode;
                            const a = document.getElementById('answer' + prefix);
                            if (a) a.value = captcha;
                        }
                    }""",
                    [employee_number, personal_identification_code, captcha_texto],
                )

                if req_page.locator("#bizidE").is_visible():
                    req_page.fill("#bizidE", employee_number)
                    req_page.fill("#pcodeE", personal_identification_code)
                    req_page.fill("#answerE", captcha_texto)
                elif req_page.locator("#bizidK").is_visible():
                    req_page.fill("#bizidK", employee_number)
                    req_page.fill("#pcodeK", personal_identification_code)
                    req_page.fill("#answerK", captcha_texto)

                logger.info("Submetendo requisição e aguardando resposta da API...")
                try:
                    with req_page.expect_response(
                        lambda res: "TempPasswordResultPcode" in res.url, timeout=timeout
                    ) as resp_info:
                        req_page.locator('input[type="button"][value="Ok"]:visible').click()

                    resp = resp_info.value
                    resp_text = resp.text().strip()
                    logger.info(f"Resposta do serviço: {resp_text}")

                    partes = resp_text.split("#")
                    result_code = partes[0] if len(partes) > 0 else ""
                    result_msg = partes[1] if len(partes) > 1 else ""

                    if result_code == "0" and len(partes) >= 3:
                        otp_code = partes[2].strip()
                        logger.info(f"OTP obtido com sucesso: {otp_code}")
                        break
                    else:
                        logger.warning(
                            f"Falha na validação do Captcha/Dados ({result_code}): {result_msg}. Tentando novamente..."
                        )
                        time.sleep(1.2)
                except Exception as exc:
                    logger.warning(f"Exceção durante submissão da tentativa {tentativa}: {exc}")
                    time.sleep(1)

            if not otp_code:
                raise OTPRetrievalError(
                    f"Não foi possível obter o OTP temporário após {max_captcha_retries} tentativas."
                )

            return otp_code

        finally:
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("=== Testando Obtenção de OTP ===")
    codigo = obter_otp_temporario(headless=False)
    print(f"\nOTP: {codigo}\n")
