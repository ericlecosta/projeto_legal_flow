# 🏛️ Projeto de Automação LMS - Equipe 1 Legal

Repositório corporativo para o ecossistema de automação do **LMS (Legal Management System)** da LG Electronics.
A estrutura é modular, projetada para acomodar o robô (RPA), bem como futuras APIs de serviço e interfaces Web (Frontend).

---

## 🗂️ Arquitetura do Repositório

```text
hands-on-equipe1-legal/
├── ideal_raw_RPA/           # Módulo principal do RPA (Playwright + OCR)
│   ├── src/
│   │   ├── __init__.py
│   │   └── auth/
│   │       ├── __init__.py      # Exportações do módulo de autenticação
│   │       ├── otp_service.py   # Extração do OTP via autoatendimento e Captcha
│   │       └── login_service.py # Login SSO e redirecionamento para o LMS
│   ├── obter_otp.py             # Script CLI para gerar/testar o OTP
│   ├── login.py                 # Script CLI para validar o login completo
│   ├── requirements.txt         # Dependências isoladas do RPA
│   ├── .env.example             # Modelo de variáveis de ambiente do RPA
│   └── README.md                # Documentação detalhada do RPA
│
├── docs/                        # Mapeamentos de seletores e documentações de apoio
│   ├── seletores/
│   │   ├── Mapeamento_Seletores_Formatado.csv
│   │   ├── Mapeamento_Seletores_Formatado.xlsx
│   │   └── Mapeamento_Seletores_LMS.md
│   └── videos/                  # Vídeos de demonstração (ignorados pelo git por tamanho)
│
├── .env.example                 # Modelo global de variáveis de ambiente
├── .gitignore                   # Regras para proteção de senhas, venv e arquivos pesados
└── README.md                    # Documentação do projeto
```

---

## 🚀 Como Executar o RPA

### 1. Pré-requisitos
- Python 3.10+
- Google Chrome instalado

### 2. Ativação do Ambiente
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ideal_raw_RPA/requirements.txt
playwright install chromium
```

### 3. Configuração do `.env`
Preencha suas credenciais no arquivo `.env` na raiz ou dentro de `ideal_raw_RPA/`:
```dotenv
USER_ID="legal.manaus"
PASSWORD="sua_senha"
EMPLOYEE_NUMBER="YSPxxxxxx"
PERSONAL_IDENTIFICATION_CODE="YYYYMMDD"
LOGIN_ADDRESS="https://sso.lge.com/"
LMS_INDEX="https://lms.lge.com/#/app/dashboard"
LMS_CONTRACT_REVIEW_MANAGEMENT="https://lms.lge.com/#/app/contract/search"
```

### 4. Execuções Rápidas

- **Para testar apenas a obtenção do OTP**:
  ```powershell
  python ideal_raw_RPA/obter_otp.py
  ```

- **Para testar o login completo no LMS**:
  ```powershell
  python ideal_raw_RPA/login.py
  ```

---

## 🔒 Segurança e Boas Práticas do Git

- O arquivo `.gitignore` já está configurado para:
  - **Nunca enviar senhas**: O arquivo `.env` com suas credenciais corporativas está protegido e bloqueado do Git.
  - **Vídeos pesados**: Os arquivos `.mp4` com mais de 100MB da pasta `docs/videos/` estão ignorados para evitar que o GitHub rejeite os seus commits.
  - **Ambientes virtuais**: A pasta `.venv/` e caches `__pycache__` estão ignorados.
