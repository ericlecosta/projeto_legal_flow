# 4 - Desenvolvimento — Relatório do Estado Atual

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)
**Repositório:** `github.com/Sannyer3232/hands-on-equipe1-legal`
**Data de referência:** 30/09/2026 · **Branch analisada:** `main` (commit `c6eea5b`)

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 1.0 | 30/09/2026 | Sannyer Carvalho | Primeiro relatório do estado do desenvolvimento |

---

## 1. Resumo Executivo

O projeto concluiu a **fundação técnica** do robô:

- autenticação automática no SSO da LG, incluindo a geração do OTP temporário com leitura do Captcha por OCR;
- conteinerização com Docker;
- pipeline de CI/CD no GitHub Actions, que publica a imagem no GHCR;
- mapeamento dos seletores das telas do LMS que serão automatizadas em seguida.

Das **10 etapas do processo TO-BE**, **1 está implementada** (Autenticação). Outras **3 estão mapeadas**, com seletores documentados, mas ainda sem código: Filtro, Exportação e Mineração. As demais ainda não começaram.

| Indicador | Situação |
| :--- | :--- |
| Etapas TO-BE implementadas | 1 de 10 (Autenticação) |
| Etapas TO-BE com seletores mapeados | 3 de 10 (Filtro, Exportação, Mineração) |
| Infraestrutura (Docker, CI/CD) | ✅ Concluída |
| Testes automatizados | ❌ Nenhum teste unitário ou de integração (apenas smoke test de dependências na CI) |
| Marco atual | M1 — Protótipo de login no LMS funcional |

---

## 2. Histórico de Entregas (Git)

| Data | Commit | Descrição |
| :---: | :---: | :--- |
| 18/09/2026 | `e7768be` | Início do projeto: módulo `ideal_raw_RPA` com automação do login de acesso ao LMS (OTP + SSO) e mapeamento de seletores |
| 21/09/2026 | `cbe4305` | CI/CD com GitHub Actions, Dockerfile e `docker-compose.yml` |
| 21/09/2026 | `c6eea5b` | Merge do PR #1 (`develop` → `main`) |

---

## 3. Progresso por Etapa do Processo TO-BE

| # | Etapa TO-BE | Status | Evidência / Observação |
| :---: | :--- | :---: | :--- |
| 1 | Agendamento (dias úteis, manhã) | ⬜ Não iniciado | Não há agendador (cron, Task Scheduler ou outro orquestrador) |
| 2 | Autenticação no LMS | ✅ Concluído | `src/auth/otp_service.py` e `src/auth/login_service.py` |
| 3 | Filtro (Subsidiary `LGESP` + período) | 🟨 Mapeado | Seletores e helper de React Select documentados em `docs/seletores/Mapeamento_Seletores_LMS.md` §4 |
| 4 | Exportação do relatório macro | 🟨 Mapeado | Botão `Download` e `expect_download` documentados (§4) |
| 5 | Filtragem MAO (Pandas) | ⬜ Não iniciado | Pandas ainda não está no `requirements.txt` |
| 6 | Mineração do Approval History | 🟨 Mapeado | Seletores de metadados (§5) e da timeline de status (§6) documentados |
| 7 | Consolidação / De/Para → Base Ideal.xlsx | ⬜ Não iniciado | De/Para identificado na linha "Espelho sistema" da Base Ideal (ver pasta 3) |
| 8 | Notificação por e-mail | ⬜ Não iniciado | — |
| 9 | Validação humana | — | Atividade do Jurídico; depende das etapas 7–8 |
| 10 | Log de execução e ocorrências | 🟨 Parcial | Logging existe apenas no console (`logging.basicConfig`); não há arquivo de log nem evidências (screenshots) de falha |

---

## 4. O que está implementado

### 4.1 Arquitetura atual do repositório

```text
hands-on-equipe1-legal/
├── .github/workflows/ci-cd.yml     # Pipeline CI/CD
├── ideal_raw_RPA/
│   ├── src/auth/
│   │   ├── otp_service.py          # Geração do OTP temporário (autoatendimento + Captcha)
│   │   └── login_service.py        # Login SSO e navegação para o LMS
│   ├── obter_otp.py                # CLI de teste do OTP
│   ├── login.py                    # CLI de teste do login completo
│   ├── requirements.txt
│   └── Dockerfile
├── docs/seletores/                 # Mapeamento de seletores (MD, CSV, XLSX)
└── docker-compose.yml              # Serviço "rpa" + blocos comentados para api/frontend/db
```

### 4.2 Módulo de OTP — `otp_service.obter_otp_temporario()`

1. Acessa o SSO, preenche o usuário e a senha e abre o **Self-service OTP** (`#OTP`).
2. Autentica no autoatendimento (`#pw` / `#myButton`) e abre **OTP temporário** (`.tempPw`).
3. Força o idioma `eng` na página legada e localiza a imagem do Captcha (`#photo_imageE` ou `#photo_imageK`).
4. Lê o Captcha com **OCR local (`ddddocr`)**, sem depender de Tesseract ou de serviços externos.
5. Preenche a matrícula, o código pessoal e o Captcha, submete e **intercepta a resposta AJAX** (`TempPasswordResultPcode`) para extrair o OTP.
6. Faz até **5 tentativas** (`max_captcha_retries`) e recarrega o Captcha quando o texto lido tem menos de 4 caracteres.
7. Lança `OTPRetrievalError` se as tentativas se esgotarem.

### 4.3 Módulo de Login — `login_service.fazer_login_lms()`

1. Gera o OTP automaticamente, se ele não for informado.
2. Inicia o Chromium (canal `chrome` com fallback para o Chromium do Playwright) ou reaproveita uma `Page` recebida.
3. Preenche `#USER`, `#LDAPPASSWORD`, aciona o `Tab` para exibir `#OTPPASSWORD`, preenche o OTP e envia o login (`#loginSsobtn`).
4. Navega até `LMS_INDEX` e retorna a `Page` autenticada para as próximas etapas.
5. `fechar_sessao_lms()` encerra o navegador e o Playwright com segurança.

### 4.4 Configuração

Tudo é configurado por variáveis de ambiente (`.env`, ignorado pelo Git): `USER_ID`, `PASSWORD`, `EMPLOYEE_NUMBER`, `PERSONAL_IDENTIFICATION_CODE`, `LOGIN_ADDRESS`, `LMS_INDEX`, `LMS_CONTRACT_REVIEW_MANAGEMENT`, `HEADLESS` e `BROWSER_CHANNEL`.

### 4.5 Infraestrutura e DevOps

| Item | Descrição |
| :--- | :--- |
| **Dockerfile** | `python:3.11-slim` + Chromium do Playwright (`--with-deps`) + libs de OpenCV/ONNX; `HEADLESS=true` por padrão |
| **docker-compose** | Serviço `rpa` com `shm_size: 1gb`, rede `lms_network` e blocos comentados para API, frontend e PostgreSQL |
| **CI — Code Quality** | `py_compile` em todos os `.py` e `flake8` bloqueante para erros críticos (E9, F63, F7, F82) |
| **CI — Docker** | Valida o compose, faz o build com cache do GitHub Actions e roda um smoke test de import (Playwright, ddddocr, cv2, PIL, onnxruntime) |
| **CD** | Publica a imagem no `ghcr.io/<repo>/rpa` com as tags `latest`, `develop` e `sha-<commit>` em pushes para `main` e `develop` |

### 4.6 Documentação técnica

- `README.md` (raiz) e `ideal_raw_RPA/README.md`: instalação, execução local, Docker e CI/CD.
- `docs/seletores/Mapeamento_Seletores_LMS.md`: fluxo geral em Mermaid e seletores do login, do OTP, do Portal EP, da busca de contratos, dos metadados do contrato e da timeline de status, com exemplos em Playwright.

---

## 5. Débitos Técnicos e Pontos de Atenção

| # | Ponto | Impacto | Recomendação |
| :---: | :--- | :---: | :--- |
| D1 | **O OTP é registrado em log em texto claro** (`logger.info` em `otp_service.py` e `login_service.py`) | Alto (segurança) | Mascarar o OTP nos logs antes de gravar logs em arquivo |
| D2 | **Não há testes automatizados** (unitários ou de integração); a CI só valida imports | Alto | Criar testes com `pytest` e mocks do Playwright para a lógica de parsing (ex.: resposta `0#msg#OTP`) |
| D3 | O fluxo abre **dois navegadores**: um para o OTP (fechado ao final) e outro para o login | Médio (tempo) | Reaproveitar o mesmo contexto do navegador para o OTP e para o login |
| D4 | Uso de **esperas fixas** (`time.sleep` de 0,5 a 3 s) | Médio (robustez) | Trocar por esperas explícitas (`wait_for_url`, `wait_for_selector`, `wait_for_load_state`) |
| D5 | **Código duplicado** entre os módulos: `_carregar_variaveis_ambiente`, `_setup_dialog_handler` e a inicialização do navegador | Baixo | Extrair para um módulo comum (ex.: `src/core/browser.py` e `src/core/config.py`) |
| D6 | Atributos privados injetados na `Page` (`page._playwright_instance`, `page._browser_instance`) | Baixo | Encapsular a sessão em uma classe (ex.: `SessaoLMS`) com context manager |
| D7 | `ignore_https_errors=True` no contexto do navegador | Médio (segurança) | Confirmar com a TI se é necessário; se não for, remover |
| D8 | Não há validação de sucesso do login (a URL ou um elemento do LMS não é verificado) | Médio | Confirmar um elemento da dashboard antes de retornar a `Page` |
| D9 | Não há retry com intervalo progressivo nas operações críticas (exigido no TO-BE: 3 tentativas) | Médio | Criar um decorator de retry com backoff |
| D10 | `LMS_CONTRACT_REVIEW_MANAGEMENT` está configurada, mas ainda não é usada | — | Será usada na etapa de filtro e exportação |

---

## 6. Riscos Técnicos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
| :--- | :---: | :---: | :--- |
| Mudança de layout ou de seletores no LMS ou no SSO | Média | Alto | Seletores centralizados, validação do layout do relatório antes de processar, alertas |
| Queda da taxa de acerto do OCR do Captcha | Média | Alto | 5 tentativas com recarga; monitorar a taxa de acerto nos logs |
| Bloqueio da conta por tentativas de login mal-sucedidas | Baixa | Alto | Limitar tentativas de login (diferente das tentativas de Captcha); alertar em caso de falha |
| Restrição da TI ao uso de robô com credencial pessoal | Média | Alto | Formalizar o uso de conta institucional (`legal.manaus`) com a TI |
| Execução em volume alto passar de 40 min | Média | Médio | Medir o baseline no MVP; paralelizar abas se necessário |

---

## 7. Próximos Passos (Backlog Priorizado)

| Prioridade | Item | Etapa TO-BE | Requisito (pasta 5) |
| :---: | :--- | :---: | :--- |
| 1 | Mascarar o OTP nos logs e criar log em arquivo com rotação | 10 | RF-S03, RF-L01 |
| 2 | Implementar os filtros (Subsidiary `LGESP` + Request Date) e o download do relatório | 3–4 | RF-F03, RF-F04 |
| 3 | Adicionar Pandas e filtrar os contratos `MAO` | 5 | RF-F05 |
| 4 | Implementar a extração de metadados e do Approval History por contrato | 6 | RF-F06, RF-F07 |
| 5 | Aplicar o De/Para e gerar a Base Ideal.xlsx no layout atual | 7 | RF-F08, RN-01 a RN-06 |
| 6 | Retry com backoff e isolamento de falhas por contrato | 6, 10 | RF-C01, RF-C02 |
| 7 | Envio de e-mail com anexo e resumo | 8 | RF-F09, RF-F10 |
| 8 | Agendamento em dias úteis | 1 | RF-F01 |
| 9 | Testes automatizados (pytest) na CI | — | RQ2, RQ7 |
| 10 | Refatoração dos débitos D3–D6 | — | RQ4 |

---

## 8. Como reproduzir o estado atual

```bash
# Local
pip install -r ideal_raw_RPA/requirements.txt && playwright install chromium
python ideal_raw_RPA/obter_otp.py   # valida somente o OTP
python ideal_raw_RPA/login.py       # valida o login completo no LMS

# Docker
docker compose up --build rpa
```
