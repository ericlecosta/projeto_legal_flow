# 🏛️ Projeto de Automação LMS - Equipe 1 Legal

Repositório corporativo para o ecossistema de automação do **LMS (Legal Management System)** da LG Electronics.
A estrutura é modular, projetada para acomodar o robô (RPA), bem como futuras APIs de serviço e interfaces Web (Frontend).

---

## 🗂️ Arquitetura do Repositório

```text
hands-on-equipe1-legal/
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # Pipeline de CI/CD (GitHub Actions)
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
│   ├── Dockerfile               # Definição do contêiner Docker para o RPA
│   ├── .dockerignore            # Regras de exclusão do build Docker do RPA
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
├── docker-compose.yml           # Orquestrador de serviços (RPA e serviços futuros)
├── .dockerignore                # Regras de exclusão do build Docker na raiz
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

## 🐳 Execução via Docker e Docker Compose

O projeto conta com conteinerização completa para execução isolada do RPA e suporte à orquestração de múltiplos serviços.

### 1. Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/) (versão v2+)

### 2. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo para `.env` na raiz do projeto e preencha suas credenciais:
```bash
cp .env.example .env
```

### 3. Construir e Executar o RPA com Docker Compose
Para subir e executar o fluxo de login do RPA:
```bash
docker compose up --build rpa
```

Esse comando executa login, baixa o relatório do LMS, extrai os detalhes dos contratos e
gera `ideal_raw_RPA/downloads/Base Ideal preenchida.xlsx`. Os relatórios intermediários
também ficam nessa pasta. A execução usa, por padrão, subsidiária `LGESP`, período `3`
e departamento contendo `mao`; configure `LMS_SUBSIDIARY_CODE`, `LMS_PERIODO` e
`LMS_FILTRO_DEPARTAMENTO` no `.env` para alterar esses filtros. A execução substitui
os arquivos de saída anteriores. Caso falhe, uma planilha de execução anterior pode
continuar na pasta; confira a mensagem de sucesso e a data do arquivo.
Contratos cujo link não apareça no prazo são omitidos da Base Ideal e registrados em
`ideal_raw_RPA/downloads/Pendencias contratos.xlsx` para verificação no LMS. O arquivo
de pendências é recriado a cada execução concluída, inclusive quando não há pendências.
Um prazo esgotado não confirma, por si só, que o contrato não existe. Outras falhas
interrompem o processo.

### 4. Executar Comandos Específicos do RPA via Contêiner

- **Obter apenas o OTP Temporário**:
  ```bash
  docker compose run --rm rpa python obter_otp.py
  ```

- **Executar o Login Completo**:
  ```bash
  docker compose run --rm rpa python login.py
  ```

- **Acessar o terminal interativo do contêiner**:
  ```bash
  docker compose run --rm rpa bash
  ```

### 5. Adicionando Novos Serviços (Backend, Frontend, Banco de Dados)
O arquivo `docker-compose.yml` já está estruturado com a rede `lms_network` e blocos de modelo comentados para:
- **Backend API** (FastAPI / Flask / Express)
- **Frontend Web** (React / Next.js / Vue)
- **Banco de Dados** (PostgreSQL)

Para adicionar um novo serviço, basta criar a pasta correspondente (ex: `api/`), descomentar e ajustar o bloco no `docker-compose.yml`. Todos os serviços se comunicarão automaticamente através da rede `lms_network`.

---

## 🔄 Pipeline de CI/CD (GitHub Actions)

O repositório possui uma esteira automatizada configurada em [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) que é disparada a cada `push` ou `pull_request` nas branches `main` e `develop` (ou manualmente via `workflow_dispatch`).

### Etapas da Esteira:

1. **Code Quality & Syntax Check (CI)**:
   - Valida a integridade sintática de todos os arquivos Python (`py_compile`).
   - Executa análise estática via `flake8` para detectar erros críticos de sintaxe e escopo.
2. **Docker Build & Validation (CI)**:
   - Valida a sintaxe do [docker-compose.yml](docker-compose.yml) (`docker compose config`).
   - Constrói a imagem Docker do RPA com cache inteligente do GitHub Actions.
   - Executa um **Smoke Test** no contêiner para validar se todas as dependências nativas (Playwright, OpenCV, ONNX, OCR) funcionam em runtime Linux sem erros de bibliotecas compartilhadas.
3. **Continuous Delivery (CD - GHCR)**:
   - Em commits integrados nas branches `main` e `develop`, a imagem é versionada e publicada automaticamente no **GitHub Container Registry (`ghcr.io`)** com tags correspondentes (`latest`, `develop`, `sha-<commit>`), pronta para uso pela equipe.

---

## 🔒 Segurança e Boas Práticas do Git

- O arquivo `.gitignore` já está configurado para:
  - **Nunca enviar senhas**: O arquivo `.env` com suas credenciais corporativas está protegido e bloqueado do Git.
  - **Vídeos pesados**: Os arquivos `.mp4` com mais de 100MB da pasta `docs/videos/` estão ignorados para evitar que o GitHub rejeite os seus commits.
  - **Ambientes virtuais**: A pasta `.venv/` e caches `__pycache__` estão ignorados.
