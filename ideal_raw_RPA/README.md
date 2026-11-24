# 🤖 RPA LMS - LG Electronics (LGE)

Módulo de automação robótica de processos (RPA) para o sistema corporativo **LMS (Legal Management System)** da LG Electronics, construído em **Python** com **Playwright**.

---

## 🎯 Funcionalidades

- **Autoatendimento e Geração de OTP Temporário**:
  - Navega automaticamente pela sequência de popups corporativos da LG.
  - Reconhecimento de Captcha em imagem via rede neural OCR local (`ddddocr`), sem necessidade de dependências externas como o Tesseract no Windows.
  - Correção automática de inconsistências de validação de idioma (`eng`/`kor`) da página legada.
  - Interceptação direta da resposta AJAX para captura imediata do OTP.
- **Login Automatizado no SSO e LMS**:
  - Preenchimento do User ID e Senha LDAP.
  - Disparo de evento `Tab` para renderização dinâmica do campo `#OTPPASSWORD`.
  - Inserção do OTP temporário gerado e submissão do login.
  - Navegação direta para a tela inicial do LMS (`LMS_INDEX`) reaproveitando a sessão autenticada.

---

## 📂 Estrutura de Arquivos

```text
ideal_raw_RPA/
├── src/
│   ├── __init__.py
│   └── auth/
│       ├── __init__.py          # Exporta fazer_login_lms, obter_otp_temporario
│       ├── otp_service.py       # Fluxo completo de geração e extração do OTP
│       └── login_service.py     # Fluxo de autenticação SSO e acesso ao LMS
├── obter_otp.py                 # CLI para execução/teste da extração do OTP
├── login.py                     # CLI para execução/teste do login completo
├── gui.py                       # Interface gráfica para executar os fluxos e acompanhar os logs
├── requirements.txt             # Dependências do RPA
├── Dockerfile                   # Definição do contêiner Docker para o RPA
├── .dockerignore                # Arquivos ignorados na geração da imagem Docker
├── .env.example                 # Exemplo de configuração de credenciais
└── README.md                    # Este arquivo
```

---

## 🚀 Instalação e Configuração

### 1. Criar e Ativar o Ambiente Virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar as Dependências

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 3. Configurar as Credenciais

Copie o arquivo `.env.example` para `.env` (na raiz ou dentro de `ideal_raw_RPA/`):

```dotenv
USER_ID="seu_usuario_lge"
PASSWORD="sua_senha_ldap"
EMPLOYEE_NUMBER="xxxxxx"
PERSONAL_IDENTIFICATION_CODE="YYYYMMDD"
LOGIN_ADDRESS="https://sso.lge.com/"
LMS_INDEX="https://lms.lge.com/#/app/dashboard"
LMS_CONTRACT_REVIEW_MANAGEMENT="https://lms.lge.com/#/app/contract/search"
```

---

## 💻 Como Usar

O fluxo de extração fecha avisos do dashboard e registra contratos cujo link não
apareceu no prazo em `downloads/Pendencias contratos.xlsx`. A lista é recriada a
cada extração concluída; se houver pendências, o monitor registra a execução
como atípica. Confirme cada contrato no LMS, pois o prazo esgotado não comprova
que ele não existe. Outros erros interrompem a extração.

### 1. Apenas obter o OTP Temporário:
```powershell
python ideal_raw_RPA/obter_otp.py
```

### 2. Executar o Login Completo no LMS:
```powershell
python ideal_raw_RPA/login.py
```

### 3. Executar pela Interface Gráfica (CustomTkinter):
```powershell
python ideal_raw_RPA/gui.py
```
Permite escolher o fluxo (login completo ou somente OTP), ativar/desativar o modo headless,
acompanhar os logs coloridos em tempo real, interromper a execução e salvar os logs em arquivo.
Por padrão as credenciais do `.env` são mascaradas nos logs.

### 4. Importar como Módulo em Outros Scripts / APIs:
```python
from src.auth import fazer_login_lms, fechar_sessao_lms

# Inicia o navegador, realiza o login e retorna a página no LMS
page = fazer_login_lms(headless=False)

# Utilize a instância de 'page' do Playwright para os próximos passos
# ex: page.goto("https://lms.lge.com/#/app/contract/search")

# Ao final:
fechar_sessao_lms(page)
```

---

## 🐳 Executando com Docker

Você pode construir a imagem e executar o RPA diretamente com o Docker:

### 1. Construir a Imagem Docker
```bash
docker build -t lms_rpa -f ideal_raw_RPA/Dockerfile ideal_raw_RPA/
```

### 2. Executar o Login Completo via Contêiner
```bash
docker run --rm --env-file .env lms_rpa
```

### 3. Executar Apenas a Obtenção do OTP
```bash
docker run --rm --env-file .env lms_rpa python obter_otp.py
```
*(Para orquestração completa e adição de múltiplos serviços, consulte o arquivo `docker-compose.yml` na raiz do projeto).*

