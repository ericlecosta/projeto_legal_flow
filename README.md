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
├── backend/                     # API FastAPI (dashboard de monitoramento)
│   ├── app/
│   │   ├── api/routes/          # /api/overview/, /api/executions/, /api/health/
│   │   ├── core/config.py       # Configurações via variáveis de ambiente
│   │   ├── db/session.py        # Engine, sessão e Base do SQLAlchemy (PostgreSQL)
│   │   ├── models/              # Modelos ORM (execuções, etapas, logs)
│   │   ├── schemas/             # Schemas Pydantic (JSON em camelCase)
│   │   ├── repositories/        # Consultas ao banco (listagem, detalhe, indicadores)
│   │   ├── simulator/           # Seed do histórico fictício + simulador ao vivo do RPA
│   │   └── main.py              # App FastAPI, CORS e rotas
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                    # Dashboard Angular (servido pelo Nginx no Docker)
│   ├── src/
│   ├── nginx.conf               # SPA fallback + proxy de /api para o FastAPI
│   └── Dockerfile               # Multi-stage: Node (build) → Nginx
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

> O serviço `rpa` está no profile `rpa`, então **não** sobe com um `docker compose up` simples (ele exige as credenciais LGE).
> Para subir tudo junto, use `docker compose --profile rpa up --build`.

---

## 📊 Dashboard de Monitoramento (Angular + FastAPI + PostgreSQL)

```bash
cp .env.example .env        # se ainda não existir
docker compose up --build
```

| Serviço    | Contêiner          | URL                                   |
| :--------- | :----------------- | :------------------------------------ |
| `frontend` | `lms_frontend_web` | http://localhost:8080                 |
| `api`      | `lms_backend_api`  | http://localhost:8000/api/docs (Swagger) |
| `db`       | `lms_postgres`     | `localhost:5432` (usuário/senha do `.env`) |

O Nginx do front repassa `/api/*` para o contêiner `api`, então o navegador fala só com `localhost:8080`.

### Dados fictícios e simulador do RPA

Enquanto o RPA real não grava no banco, a API usa um simulador (`backend/app/simulator/`):

- **Histórico:** na primeira subida, com o banco vazio, são criados ~30 dias de execuções fictícias
  (agendadas às 08h, 12h e 18h, mais algumas manuais), com etapas, logs e falhas.
- **Execução ao vivo:** o botão **Executar Fluxo Agora** (`POST /api/executions/`) roda um roteiro em tempo real,
  gravando etapas e logs no banco. A tela de detalhe atualiza a cada 2 s, e **Interromper**
  (`POST /api/executions/{id}/stop/`) cancela. Só uma execução roda por vez (`409` se já houver uma).
- **Agenda:** com a API no ar, execuções "agendadas" são disparadas nos horários de `SIMULATOR_SCHEDULE`.

Comandos úteis:

```bash
# Recriar o histórico do zero (ex.: 60 dias, com outra semente aleatória)
docker compose exec api python -m app.simulator.seed --reset --days 60 --seed 7

# Execuções ao vivo 5x mais rápidas
SIMULATOR_SPEED=5 docker compose up -d api
```

As variáveis do simulador estão documentadas no `.env.example`.

### Desenvolvimento local sem Docker

```bash
# API (porta 8000)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

# Front (porta 4200), em outro terminal
cd frontend
npm ci
npm start
```

O `ng serve` usa `environment.development.ts`, que aponta para `http://localhost:8000/api` (o CORS libera `localhost:4200`).
Para trabalhar no front sem a API, mude `useMocks` para `true` nesse arquivo.

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
