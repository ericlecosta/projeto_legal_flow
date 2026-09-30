# AUTOMAÇÃO DO PROCESSO DE CONTRATOS JURÍDICOS
## ESPECIFICAÇÃO DE REQUISITOS (PUR)

**DOCUMENTO:** RPA IDEAL RAW — EXTRAÇÃO E ENRIQUECIMENTO DE CONTRATOS DO LMS
**CLIENTE:** LG Electronics do Brasil — Jurídico / Contratos (filial Manaus)

### CONTROLE DO DOCUMENTO

| VERSÃO | DATA | EDIÇÃO | APROVAÇÃO | COMENTÁRIOS |
| :---: | :---: | :---: | :--- | :--- |
| 1.0 | 30/09/2026 | 1 | | Versão de levantamento (pré-MVP) |

### CONTROLE DE VERSÕES

| VERSÃO | DATA | AUTOR(ES) | C.Q. | STATUS | COMENTÁRIOS |
| :---: | :---: | :--- | :---: | :--- | :--- |
| 1.0 | 30/09/2026 | Sannyer Carvalho | | Em aprovação | Versão inicial, baseada no AS-IS, no TO-BE e na Base Ideal |
| 2.0 | | | | Planejada | Revisão pós-MVP (M2) |

---

## ÍNDICE ANALÍTICO

1. [Objetivo](#1-objetivo)
2. [Abrangência](#2-abrangência)
3. [Descrição dos Termos Utilizados](#3-descrição-dos-termos-utilizados)
4. [Informações Preliminares](#4-informações-preliminares)
   - 4.1 Critério Obrigatório · 4.2 Critério Opcional · 4.3 Limitações
5. [Área de Operação](#5-área-de-operação)
   - 5.1 Usuários · 5.2 Condições de Operação
6. [Ambiente](#6-ambiente)
   - 6.1 Software · 6.2 Hardware · 6.3 Mecânica · 6.4 Interfaces do Sistema
7. [Requisitos Funcionais](#7-requisitos-funcionais)
8. [Requisitos Não Funcionais](#8-requisitos-não-funcionais)
9. [Requisitos da IHM](#9-requisitos-da-ihm)
10. [Requisitos de Qualidade](#10-requisitos-de-qualidade)
11. [Ambiente de Testes](#11-ambiente-de-testes)
12. [Ambiente de Desenvolvimento](#12-ambiente-de-desenvolvimento)
13. [Apêndice](#13-apêndice)

---

## 1. Objetivo

Este documento define, estrutura e organiza os requisitos do robô **RPA Ideal Raw**. O robô automatiza a extração, a filtragem, a mineração e a consolidação dos dados de contratos jurídicos registrados no **LMS – Legal Management System** da LG Electronics.

Hoje a área de Contratos do Jurídico de Manaus mantém a planilha **Base Ideal.xlsx** manualmente. Ela exporta um relatório macro do LMS, abre contrato por contrato e copia as datas do "Approval History". Cada execução leva de 4 a 5 horas e acontece cerca de duas vezes por semana.

O robô deve executar esse processo sozinho, em todos os dias úteis pela manhã, e entregar a base padronizada por e-mail. Assim, a participação humana fica concentrada na validação de exceções e na análise dos contratos (*Human-in-the-Loop*).

Este plano dá uma visão clara e objetiva da solução, para que a equipe técnica, a área cliente e o orientador do projeto tenham o mesmo entendimento.

## 2. Abrangência

A solução atende a área **Jurídico – Contratos** da LG Electronics do Brasil. O escopo são os contratos da subsidiária **LGESP** identificados como da **filial Manaus (MAO)**.

O robô é desenvolvido no programa *Digital Transformation Academy* (Hands-On, Equipe 1 – Legal). Seu código fica versionado em repositório Git e é distribuído como imagem Docker. A arquitetura é modular, o que permite estendê-lo no futuro a outras filiais ou somar uma API e um frontend (já previstos no `docker-compose.yml`).

## 3. Descrição dos Termos Utilizados

| Termo | Definição |
| :--- | :--- |
| **LMS** | Legal Management System — sistema corporativo da LG de gestão de contratos jurídicos |
| **SSO** | Single Sign-On — portal de autenticação corporativa da LG (`sso.lge.com`) |
| **OTP** | One-Time Password — senha temporária de uso único exigida no login |
| **Captcha** | Imagem com caracteres usada para validar que quem acessa é humano; neste projeto é lida por OCR |
| **OCR** | Optical Character Recognition — reconhecimento de caracteres em imagem (biblioteca `ddddocr`) |
| **RPA** | Robotic Process Automation — automação de tarefas repetitivas por software |
| **Base Ideal / Ideal Raw** | Planilha Excel de saída com as informações detalhadas dos contratos |
| **Approval History** | Histórico de aprovações/timeline do contrato no LMS, fonte das datas de cada etapa |
| **LGESP** | Código da subsidiária LG Electronics do Brasil usado no filtro do LMS |
| **MAO** | Identificador dos contratos da filial Manaus |
| **De/Para** | Correspondência entre os eventos do Approval History e as colunas da Base Ideal |
| **Progress State** | Estado atual do contrato no LMS (ex.: *Approval Completed*, *Biz-Drop*) |
| **Biz-Drop** | Desistência do contrato |
| **Human-in-the-Loop** | Modelo em que o humano valida exceções e resultados da automação |
| **CI/CD** | Integração e Entrega Contínuas (GitHub Actions) |
| **GHCR** | GitHub Container Registry, onde a imagem Docker do robô é publicada |
| **LGPD** | Lei Geral de Proteção de Dados (Lei nº 13.709/2018) |

## 4. Informações Preliminares

As especificações foram elaboradas a partir destas fontes:

- documentos de processo **AS-IS** e **TO-BE** do Processo de Contratos;
- a planilha modelo **Base Ideal.xlsx**, com as abas *Ideal Raw* e *Legenda*;
- a gravação de demonstração do processo feita com a área cliente em 26/08/2026;
- a navegação assistida no SSO e no LMS, registrada no mapeamento de seletores (`docs/seletores/`).

### 4.1 Critério Obrigatório

Os critérios obrigatórios abaixo vêm do cenário TO-BE acordado com a área cliente. Sem eles, a solução não cumpre seu objetivo.

1. O robô deve autenticar-se no SSO da LG com credenciais institucionais, gerando automaticamente o OTP temporário.
2. O robô deve aplicar o filtro de Subsidiary **LGESP** e o período de referência antes de exportar o relatório.
3. Somente contratos identificados como **MAO** devem ser processados.
4. As datas das etapas devem ser extraídas do **Approval History** de cada contrato, seguindo as regras de De/Para.
5. A saída deve ser a **Base Ideal.xlsx**, no mesmo layout de colunas usado hoje pela área.
6. A base deve ser enviada por **e-mail** ao final de cada execução.
7. A falha em um contrato **não** deve interromper o processamento dos demais.
8. Toda execução deve gerar **log** com as ocorrências e as falhas.
9. Credenciais, senhas e OTPs nunca podem ser gravados no código-fonte, no repositório ou nos logs.
10. O robô deve operar em **modo somente leitura** no LMS, sem alterar nenhum dado.

### 4.2 Critério Opcional

Os critérios a seguir agregam valor, mas não são essenciais ao MVP. Serão implementados conforme a viabilidade técnica e o tempo disponível.

- **Dashboard de acompanhamento:** painel (ex.: Power BI ou web) com indicadores de prazo por etapa e gargalos dos contratos.
- **Histórico incremental:** manter as execuções anteriores para comparar a evolução dos contratos entre dias.
- **Notificação de desvios:** destacar no e-mail os contratos parados há mais de N dias em uma mesma etapa.
- **Execução sob demanda via API:** endpoint (serviço `api` do compose) para disparar o robô manualmente.
- **Extensão a outras filiais:** parametrizar o identificador da filial (hoje fixo em MAO).
- **Armazenamento em banco de dados:** persistir os dados em PostgreSQL (serviço `db` já previsto no compose).
- **Cofre de credenciais:** integração com um gerenciador de segredos corporativo em vez de `.env`.

### 4.3 Limitações

A seguir estão os aspectos que o robô não vai atender, em funcionalidades e em compatibilidade.

**1. Funcionalidades não atendidas**
- O robô não cria, edita, aprova ou reprova contratos no LMS.
- O robô não interpreta o conteúdo jurídico dos contratos (cláusulas, riscos, pareceres).
- O robô não processa contratos de outras filiais além de Manaus na versão inicial.

**2. Restrições de hardware**
- O robô não roda em dispositivos móveis.
- A execução exige máquina ou servidor capaz de rodar um navegador Chromium (ver 6.2).

**3. Restrições de software**
- A automação depende da interface web do LMS e do SSO. Mudanças de layout nesses sistemas podem exigir manutenção dos seletores.
- O LMS não oferece API disponível para a área; a extração é feita pela interface.

**4. Restrições de integração**
- Não há integração direta com o banco de dados do LMS.
- O envio de e-mail depende de um servidor SMTP ou conta corporativa liberada pela TI.

**5. Restrições ambientais e de uso**
- O robô precisa de acesso à rede corporativa ou à internet com alcance ao `sso.lge.com` e ao `lms.lge.com`.
- O uso é restrito às finalidades do Jurídico da LG Electronics, conforme a LGPD e o sigilo contratual.

## 5. Área de Operação

### 5.1 Usuários

O robô não tem interface interativa para o usuário final. Os perfis abaixo interagem com suas entradas e saídas:

**Gestora do Jurídico – Contratos**
- Recebe a Base Ideal por e-mail em todos os dias úteis.
- Valida exceções e acompanha desvios dos contratos.
- Aprova mudanças de regra (De/Para, filtros, destinatários).

**Analista de Contratos**
- Consulta a Base Ideal para acompanhar os contratos.
- Trata os contratos com falha de extração indicados no resumo da execução.

**Operador / Sustentação (TI ou equipe técnica)**
- Configura as credenciais e as variáveis de ambiente.
- Monitora logs, reexecuta o robô sob demanda e mantém os seletores.

### 5.2 Condições de Operação

**Infraestrutura e ambiente**
- Execução agendada de segunda a sexta-feira, no período da manhã.
- Execução em contêiner Docker (Linux, modo *headless*) ou localmente (Windows/Linux, com ou sem interface gráfica).
- Conectividade estável com o SSO e o LMS durante toda a execução.

**Segurança e acesso**
- Acesso somente com a conta institucional autorizada (ex.: `legal.manaus`).
- Credenciais fornecidas por variáveis de ambiente (`.env`, fora do Git) ou por um cofre de segredos.
- Arquivos de saída e logs guardados em diretório com acesso restrito.

## 6. Ambiente

### 6.1 Software

- Python 3.10 ou superior (imagem Docker: Python 3.11).
- Playwright com Chromium (ou Google Chrome, canal `chrome`, em execução local).
- Bibliotecas: `ddddocr`, `onnxruntime`, `opencv-python-headless`, `pillow`, `python-dotenv`, `pandas` e `openpyxl` (as duas últimas previstas).
- Docker 24+ e Docker Compose v2 para execução conteinerizada.
- Sistemas operacionais suportados: Windows 10/11 e Linux (Ubuntu 20.04 ou superior).

### 6.2 Hardware

- Mínimo recomendado: 4 GB de RAM, CPU com 2 núcleos e 2 GB livres em disco.
- 1 GB de memória compartilhada (`shm_size`) para o Chromium no contêiner.

### 6.3 Mecânica

Não se aplica. A solução é exclusivamente de software e não tem componentes mecânicos.

### 6.4 Interfaces do Sistema

| Interface | Tipo | Descrição |
| :--- | :--- | :--- |
| SSO LGE (`sso.lge.com`) | Web (entrada) | Login com usuário, senha LDAP e OTP |
| Autoatendimento de OTP | Web (entrada) | Geração da senha temporária com matrícula, código pessoal e Captcha |
| LMS (`lms.lge.com`) | Web (entrada) | Busca de contratos, download do relatório, detalhes e Approval History |
| Base Ideal.xlsx | Arquivo (saída) | Planilha consolidada no layout *Ideal Raw* |
| E-mail corporativo | SMTP (saída) | Envio da base e do resumo da execução |
| Logs | Arquivo (saída) | Registro de execução, ocorrências e evidências |

## 7. Requisitos Funcionais

Estes são os requisitos funcionais do robô, agrupados por classes para facilitar a leitura:

### 7.1 Requisitos de Confiabilidade

- **RF-C01:** O robô deve repetir operações críticas (login, download, consulta de contrato) até **3 vezes**, com intervalos progressivos entre as tentativas.
- **RF-C02:** A falha no processamento de um contrato não deve interromper os demais. O contrato com falha deve aparecer no log e no resumo da execução.
- **RF-C03:** O robô deve validar o layout (colunas esperadas) do relatório exportado antes de processá-lo e abortar com alerta se o layout tiver mudado.
- **RF-C04:** O arquivo final da Base Ideal deve ficar disponível em disco mesmo se o envio do e-mail falhar.
- **RF-C05:** O robô deve poder ser reexecutado no mesmo dia sem gerar dados duplicados ou corrompidos.

### 7.2 Requisitos de Segurança

- **RF-S01:** As credenciais devem ser lidas exclusivamente de variáveis de ambiente ou de um cofre de segredos, nunca do código-fonte.
- **RF-S02:** O robô deve gerar o OTP temporário automaticamente, resolvendo o Captcha por OCR local, sem enviar imagens a serviços externos.
- **RF-S03:** Senhas e OTPs não devem aparecer em texto claro nos logs nem na saída do console.
- **RF-S04:** O robô deve operar em modo somente leitura no LMS.
- **RF-S05:** O robô deve limitar as tentativas de login no SSO para evitar o bloqueio da conta institucional.

### 7.3 Requisitos de Logs e Relatórios

- **RF-L01:** Cada execução deve gerar um arquivo de log com data e hora, etapas executadas, duração e ocorrências.
- **RF-L02:** Em caso de falha em uma tela, o robô deve salvar uma evidência (captura de tela) associada ao log.
- **RF-L03:** Ao final, o robô deve produzir um resumo da execução: total de contratos exportados, contratos MAO, processados com sucesso, com falha e duração total.

### 7.4 Requisitos Funcionais — Funcionalidades

- **RF-F01:** O robô deve iniciar automaticamente nos dias úteis, no período da manhã, e também permitir execução manual sob demanda.
- **RF-F02:** O robô deve autenticar-se no SSO e navegar até o LMS com a sessão autenticada.
- **RF-F03:** O robô deve acessar o *Contract Review Management* e aplicar os filtros **Subsidiary Code = LGESP** e **Request Date** (período de referência configurável).
- **RF-F04:** O robô deve exportar (Download) o relatório macro de contratos filtrados.
- **RF-F05:** O robô deve carregar o relatório com Pandas e manter somente os contratos identificados como **MAO**.
- **RF-F06:** Para cada contrato MAO, o robô deve abrir o detalhe no LMS pelo identificador (Management Number) e extrair os metadados: Counterparty, Contract Name, Contract type, Requester, Contract Period, Contract amount e *A person in charge of legal (team)*.
- **RF-F07:** Para cada contrato MAO, o robô deve extrair do **Approval History** as datas das etapas mapeadas no De/Para (RN-04).
- **RF-F08:** O robô deve consolidar os dados na **Base Ideal.xlsx**, com as colunas e a ordem da aba *Ideal Raw*.
- **RF-F09:** O robô deve enviar por e-mail a Base Ideal gerada, com o resumo da execução (RF-L03) no corpo da mensagem.
- **RF-F10:** Sem contratos MAO no período, o robô deve encerrar com sucesso e enviar um e-mail com aviso específico.
- **RF-F11:** Os destinatários do e-mail, o período de referência e o identificador da filial devem ser configuráveis sem alterar o código.

### 7.5 Regras de Negócio

- **RN-01:** O filtro **Subsidiary = "LGESP"** deve ser aplicado antes da exportação.
- **RN-02:** São mantidos apenas os contratos da filial Manaus, identificados pelo marcador **"MAO"**.
- **RN-03:** A consulta individual usa o identificador do contrato (*Management Number* / *Contract number*).
- **RN-04 (De/Para):** As datas são atribuídas às colunas da Base Ideal conforme a correspondência abaixo:

| Coluna na Base Ideal | Evento no Approval History / LMS |
| :--- | :--- |
| Request Date | "I request a review of the contract." |
| Review completed | "Review Completed" / "Completion of contract review" |
| Agreement request | "Legal Team Consent in Progress" |
| Agreement has been completed | "Legal Team Consent Completed" |
| Approval request | "Processing Approval for Execution" / "Status changed to in Processing Approval" |
| Approval request completed | "Approval Completed" / "Status changed to in Approval Completed" |
| Register the conclusion of contract | "Contract Expired" / "Effective Contract" |
| Request Legal Review · Biz-Drop Completed | *A confirmar com a área cliente (ver Matriz CSD)* |

- **RN-05:** Etapas que o contrato ainda não atingiu ficam **nulas** (célula vazia).
- **RN-06:** Se um evento ocorrer mais de uma vez, vale a **última data válida**.
- **RN-07:** Sem contratos MAO no período, a execução é considerada **bem-sucedida** e gera aviso específico (RF-F10).
- **RN-08:** As datas são gravadas no formato **AAAA-MM-DD**, como na Base Ideal atual.

## 8. Requisitos Não Funcionais

Estes são os requisitos não funcionais do robô:

- **RNF01:** A execução completa deve levar **menos de 40 minutos** para a carga média de contratos.
- **RNF02:** O robô deve rodar em modo *headless* dentro de um contêiner Docker Linux, sem depender de interface gráfica.
- **RNF03:** O robô também deve rodar localmente em Windows 10/11 e Linux, com o navegador visível para depuração.
- **RNF04:** Toda a configuração (URLs, credenciais, filtros, destinatários, modo *headless*) deve vir de variáveis de ambiente.
- **RNF05:** O código deve passar pela pipeline de CI (compilação, `flake8` e build Docker) antes de ser integrado à `main`.
- **RNF06:** A imagem Docker deve ser versionada e publicada no GHCR a cada integração em `main` ou `develop`.
- **RNF07:** A Base Ideal gerada deve abrir sem erros no Microsoft Excel (formato `.xlsx`).
- **RNF08:** O tratamento dos dados pessoais presentes na base deve seguir a **LGPD**: finalidade restrita ao Jurídico, acesso restrito e nenhum compartilhamento com terceiros.
- **RNF09:** Os logs de execução devem ser mantidos por pelo menos **90 dias** *(prazo a validar com a área cliente)*.
- **RNF10:** Os seletores das telas devem ficar centralizados e documentados, para facilitar a manutenção quando o layout mudar.
- **RNF11:** O código deve ser modular (autenticação, extração, transformação, notificação), permitindo reutilizar e testar cada módulo separadamente.
- **RNF12:** O OCR do Captcha deve rodar localmente, sem dependência de serviços pagos ou externos.

## 9. Requisitos da IHM

O robô não tem telas próprias. A interação humana acontece pelo **e-mail**, pela **planilha** e pela **linha de comando** do operador.

- **RIHM-01:** O e-mail deve ter um assunto padronizado com a data da execução (ex.: *"[RPA Ideal Raw] Base Ideal – 30/09/2026"*).
- **RIHM-02:** O corpo do e-mail deve mostrar o resumo da execução (RF-L03) em uma tabela simples e legível.
- **RIHM-03:** Quando houver falhas, o e-mail deve listar os contratos afetados e o motivo resumido.
- **RIHM-04:** A Base Ideal deve manter o cabeçalho, a ordem das colunas e os nomes da planilha atual, para que a usuária não precise se adaptar.
- **RIHM-05:** As colunas de data devem estar formatadas como data no Excel, e os valores como número.
- **RIHM-06:** A saída de linha de comando deve informar ao operador a etapa em andamento, o sucesso ou a falha e a localização do arquivo gerado e do log.
- **RIHM-07:** Mensagens de erro devem ser claras e indicar a ação sugerida (ex.: *"Credencial USER_ID ausente no .env"*).

## 10. Requisitos de Qualidade

Estes são os requisitos de qualidade do robô:

- **RQ1 – Funcionalidade (Alto):** O robô deve reproduzir fielmente o processo manual e gerar a mesma informação que a área obtém hoje, com todas as etapas do TO-BE operacionais.
- **RQ2 – Confiabilidade (Alto):** O robô deve executar de forma estável, com retry, isolamento de falhas e alertas, gerando a base em todos os dias úteis.
- **RQ3 – Usabilidade (Normal):** A saída (e-mail e planilha) deve ser fácil de entender e usar, sem exigir treinamento da usuária final.
- **RQ4 – Flexibilidade (Alto):** Mudanças de filtros, De/Para, destinatários ou layout das telas devem ser absorvidas com mínimo impacto no código.
- **RQ5 – Portabilidade (Alto):** O robô deve rodar em contêiner Docker e localmente em Windows ou Linux, com o mesmo comportamento.
- **RQ6 – Escalabilidade (Normal):** O robô deve suportar o aumento do volume de contratos sem ultrapassar o tempo máximo de execução (RNF01).
- **RQ7 – Segurança (Alto):** Credenciais e dados de contratos devem ser protegidos, sem exposição em código, repositório ou logs, conforme a LGPD.
- **RQ8 – Robustez (Alto):** O robô deve tolerar instabilidades do LMS e do SSO (lentidão, falhas pontuais, Captcha ilegível) e se recuperar sem intervenção manual.

O quadro abaixo mostra o nível de relevância de cada característica de qualidade.

| Item | Características | Alto | Normal | Baixo | Irrelevante |
| :---: | :--- | :---: | :---: | :---: | :---: |
| RQ1 | Funcionalidade | X | | | |
| RQ2 | Confiabilidade | X | | | |
| RQ3 | Usabilidade | | X | | |
| RQ4 | Flexibilidade | X | | | |
| RQ5 | Portabilidade | X | | | |
| RQ6 | Escalabilidade | | X | | |
| RQ7 | Segurança | X | | | |
| RQ8 | Robustez | X | | | |

## 11. Ambiente de Testes

- **Testes unitários:** `pytest` com mocks do Playwright para a lógica de parsing, De/Para e regras de negócio (RN-04 a RN-08).
- **Testes de integração:** execução real contra o SSO e o LMS com a conta institucional, em modo visível e *headless*.
- **Smoke test (CI):** validação das dependências nativas no contêiner (já implementada no GitHub Actions).
- **Homologação (UAT):** comparação da Base Ideal gerada pelo robô com a base manual para uma mesma amostra de contratos, junto com a gestora do Jurídico.
- Os roteiros e evidências de teste ficam na pasta `7 - QA_Testes`.

## 12. Ambiente de Desenvolvimento

### Software
- Python 3.11;
- Playwright (Chromium / Google Chrome);
- ddddocr, ONNX Runtime, OpenCV, Pillow, python-dotenv;
- Pandas e openpyxl (previstos);
- Docker e Docker Compose v2;
- Git e GitHub (GitHub Actions e GHCR);
- VS Code *(ou IDE de preferência de cada integrante)*.

### Hardware
- Computadores pessoais dos integrantes da equipe *[especificação a preencher]*;
- Runners `ubuntu-latest` do GitHub Actions para CI/CD;
- Rede com acesso ao SSO e ao LMS da LG Electronics.

## 13. Apêndice

Conceitos para os requisitos de qualidade (item 10).

| Requisito | Conceito | Perguntas-chave | Aplicação no RPA Ideal Raw |
| :--- | :--- | :--- | :--- |
| **Funcionalidade (RQ1)** | Capacidade do produto de cumprir as funções que lhe cabem, com resultados corretos e completos. | Faz o que é apropriado? Faz de forma correta? Interage com os sistemas especificados? | **Exemplo:** a Base Ideal gerada deve ter as mesmas datas que a transcrição manual para os mesmos contratos. **Integrações:** SSO, LMS e e-mail. |
| **Confiabilidade (RQ2)** | Capacidade de manter o desempenho sob as condições estabelecidas, sem falhas inesperadas. | É imune a falhas? Faz o que é proposto o tempo todo? Como se comporta em indisponibilidade parcial? | **Exemplo:** se um contrato não carregar, os demais continuam sendo processados. **Retry:** até 3 tentativas com intervalo progressivo. |
| **Usabilidade (RQ3)** | Esforço necessário para aprender, entender e usar o produto. | Que usuários vão interagir? É fácil de operar? É fácil de aprender? | **Exemplo:** a gestora recebe a planilha no layout que já conhece, com um resumo claro no e-mail. |
| **Flexibilidade (RQ4)** | Esforço necessário para modificar o produto por mudança de requisitos ou de escopo. | É possível modificar sem grande esforço? É fácil adicionar funções? | **Exemplo:** mudar o período do filtro ou os destinatários só por configuração. **Aderência:** seletores centralizados e módulos separados. |
| **Portabilidade (RQ5)** | Capacidade de ser transferido de um ambiente para outro. | Posso usá-lo em outra máquina? Posso instalá-lo em outro ambiente com facilidade? | **Exemplo:** a mesma imagem Docker roda no servidor e na máquina do desenvolvedor. **Virtualização:** imagem publicada no GHCR. |
| **Escalabilidade (RQ6)** | Esforço necessário para suportar crescimento de volume sem perda de desempenho. | Aguenta mais dados sem lentidão ou falhas? | **Exemplo:** o dobro de contratos MAO não deve ultrapassar o limite de 40 minutos (RNF01). |
| **Segurança (RQ7)** | Capacidade de manter a integridade e a confidencialidade dos dados, em conformidade com as normas. | Controla o acesso a dados? É seguro? Está de acordo com as normas? | **Exemplo:** OTP e senhas nunca aparecem em logs. **LGPD:** dados de contrapartes com acesso restrito. |
| **Robustez (RQ8)** | Capacidade de manter as funções sob falhas ou perturbações e se recuperar sem perdas. | A queda de um sistema externo inutiliza o produto? Há recuperação automática? | **Exemplo:** Captcha lido errado leva a nova tentativa com recarga da imagem (até 5 vezes). **Tolerância:** o arquivo final é preservado mesmo se o e-mail falhar. |
