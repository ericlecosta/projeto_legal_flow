# 5 - RD — Matriz CSD, Matriz de Riscos e User Story Mapping

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)
**Documento complementar a:** `Especificacao_de_Requisitos_RPA_Ideal_Raw.md` (PUR v1.0)

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 1.0 | 30/09/2026 | Sannyer Carvalho | Versão de levantamento |

---

## 1. Matriz CSD (Certezas, Suposições e Dúvidas)

### ✅ Certezas

| # | Certeza | Fonte |
| :---: | :--- | :--- |
| C1 | O processo atual leva de 4 a 5 h por execução, cerca de 2 vezes por semana | AS-IS |
| C2 | Os contratos de Manaus são identificados por "MAO" | AS-IS / TO-BE |
| C3 | O filtro de Subsidiary é "LGESP" | TO-BE |
| C4 | O login exige SSO + OTP temporário com Captcha, e isso já está automatizado | Código (`src/auth/`) |
| C5 | O layout de saída é a aba *Ideal Raw* da Base Ideal, com 23 colunas | Base Ideal.xlsx |
| C6 | As etapas não atingidas ficam nulas; em múltiplas ocorrências vale a última data | TO-BE |
| C7 | Os filtros do LMS usam o componente React Select | Mapeamento de seletores |

### 🟨 Suposições

| # | Suposição | Como validar |
| :---: | :--- | :--- |
| S1 | A conta `legal.manaus` pode ser usada pelo robô de forma agendada | Confirmar com a TI e com a gestora |
| S2 | O relatório exportado traz o marcador MAO em uma coluna identificável (nome do contrato ou departamento) | Analisar um relatório real exportado |
| S3 | O volume diário de contratos MAO permite executar em menos de 40 min | Medir o baseline no MVP |
| S4 | O layout das telas do LMS fica estável durante o projeto | Monitorar a cada sprint |
| S5 | Existe um SMTP ou conta corporativa disponível para o robô enviar e-mail | Confirmar com a TI |
| S6 | O período "Last 10 years" no Request Date cobre todos os contratos de interesse | Validar com a gestora |

### ❓ Dúvidas

| # | Dúvida | Responsável por responder |
| :---: | :--- | :--- |
| D1 | Qual evento do Approval History alimenta as colunas "Request Legal Review" e "Biz-Drop Completed"? | Gestora do Jurídico |
| D2 | A base deve ser **substituída** a cada dia ou **incremental** (mantendo o histórico)? | Gestora do Jurídico |
| D3 | Quem são os destinatários do e-mail (e cópias)? | Gestora do Jurídico |
| D4 | Qual o período de referência do filtro de Request Date? | Gestora do Jurídico |
| D5 | Onde o robô vai rodar em produção (servidor da LG, máquina do Jurídico, nuvem)? | TI / PO |
| D6 | Qual o prazo de retenção dos logs e arquivos gerados (LGPD)? | Gestora / TI |
| D7 | Como separar "Contract type" e "Main Contract Type" na origem? | Gestora do Jurídico |

---

## 2. Matriz de Riscos

**Escala:** Probabilidade (P) e Impacto (I) de 1 a 3 · **Exposição** = P × I (1–2 Baixa · 3–4 Média · 6–9 Alta)

| ID | Risco | P | I | Exposição | Gatilho objetivo | Resposta | Dono |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| R01 | Mudança de layout ou de seletores no LMS ou no SSO | 2 | 3 | **6 – Alta** | Timeout de seletor em 2 execuções seguidas | Seletores centralizados, validação de layout (RF-C03) e alerta por e-mail | Tech Lead |
| R02 | Queda da taxa de acerto do OCR do Captcha | 2 | 3 | **6 – Alta** | Mais de 3 tentativas de Captcha em média por execução | Recarga de imagem, até 5 tentativas; avaliar pré-processamento da imagem | Tech Lead |
| R03 | TI não autoriza o uso da conta pelo robô | 2 | 3 | **6 – Alta** | Negativa formal ou falta de resposta até o fim de M1 | Escalar via patrocinadora; formalizar uma conta de serviço | PO |
| R04 | Bloqueio da conta por tentativas de login falhas | 1 | 3 | **3 – Média** | 2 falhas de login consecutivas | Limitar tentativas de login (RF-S05) e alertar o operador | Tech Lead |
| R05 | Tempo de execução acima de 40 min | 2 | 2 | **4 – Média** | Baseline do MVP acima de 30 min | Otimizar esperas, reaproveitar sessão e paralelizar abas | Dev |
| R06 | Regras de De/Para incompletas ou ambíguas | 2 | 2 | **4 – Média** | Divergência maior que 5% na comparação com a base manual (UAT) | Resolver as dúvidas D1 e D7 com a gestora antes de M2 | Analista de Dados |
| R07 | Vazamento de credenciais ou dados sensíveis | 1 | 3 | **3 – Média** | Credencial/OTP encontrado em log ou commit | `.env` fora do Git, mascaramento nos logs (RF-S03), revisão em PR | Tech Lead |
| R08 | Indisponibilidade de membros do time | 2 | 2 | **4 – Média** | Tarefa sem avanço por mais de 1 sprint | Redistribuir o backlog e registrar no Status Report | PO |
| R09 | Falta de SMTP para envio de e-mail | 2 | 1 | **2 – Baixa** | Envio não configurado até o início da etapa 8 | Arquivo salvo em pasta compartilhada como alternativa (RF-C04) | Tech Lead |

---

## 3. User Story Mapping (History Map)

**Persona principal:** Gestora do Jurídico – Contratos (Manaus)

### Atividades (backbone)

| 1. Acessar o LMS | 2. Obter a lista de contratos | 3. Enriquecer com o histórico | 4. Consolidar a base | 5. Receber e usar |
| :--- | :--- | :--- | :--- | :--- |

### Histórias por release

| Release | 1. Acessar o LMS | 2. Obter a lista de contratos | 3. Enriquecer com o histórico | 4. Consolidar a base | 5. Receber e usar |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R1 – M1 (Fundação)** ✅ | US01 – Como operador, quero que o robô gere o OTP sozinho, para não precisar fazer isso manualmente ✅<br>US02 – Como operador, quero que o robô faça login no LMS ✅ | — | — | — | — |
| **R2 – M2 (MVP)** | US03 – Como operador, quero que as credenciais nunca apareçam em logs | US04 – Como gestora, quero que o robô aplique LGESP + período e baixe o relatório<br>US05 – Como gestora, quero apenas os contratos MAO | US06 – Como gestora, quero os metadados de cada contrato<br>US07 – Como gestora, quero as datas de cada etapa do Approval History | US08 – Como gestora, quero a Base Ideal no layout que já uso<br>US09 – Como gestora, quero etapas não atingidas vazias e a última data válida | US10 – Como gestora, quero receber a base por e-mail |
| **R3 – M3 (Produção)** | US11 – Como operador, quero retry com backoff no login | US12 – Como operador, quero ser alertado se o layout do relatório mudar | US13 – Como gestora, quero que a falha em um contrato não interrompa os demais | US14 – Como operador, quero log em arquivo e evidências de falha | US15 – Como gestora, quero o robô rodando sozinho todo dia útil de manhã<br>US16 – Como gestora, quero ver no e-mail o resumo e os contratos com falha |
| **Futuro (opcional)** | — | US17 – Como gestora, quero processar outras filiais | US18 – Como gestora, quero o histórico incremental das execuções | US19 – Como gestora, quero guardar os dados em banco | US20 – Como gestora, quero um dashboard de gargalos por etapa |

### Rastreabilidade Histórias ↔ Requisitos

| História | Requisitos |
| :---: | :--- |
| US01–US02 | RF-F02, RF-S02 |
| US03 | RF-S01, RF-S03 |
| US04 | RF-F03, RF-F04, RN-01 |
| US05 | RF-F05, RN-02 |
| US06 | RF-F06, RN-03 |
| US07 | RF-F07, RN-04 |
| US08–US09 | RF-F08, RN-05, RN-06, RN-08, RIHM-04 |
| US10 | RF-F09, RF-F10, RN-07 |
| US11 | RF-C01, RF-S05 |
| US12 | RF-C03 |
| US13 | RF-C02 |
| US14 | RF-L01, RF-L02 |
| US15 | RF-F01 |
| US16 | RF-L03, RIHM-02, RIHM-03 |

---

## 4. Declaração Explícita de Não Escopo

Os itens abaixo **não fazem parte** deste projeto. Qualquer inclusão exige revisão formal do PUR (nova versão) e aprovação da patrocinadora:

1. Criar, editar, aprovar ou reprovar contratos no LMS.
2. Processar contratos de filiais diferentes de Manaus (MAO).
3. Análise ou interpretação do conteúdo jurídico dos contratos.
4. Dashboards, BI ou relatórios analíticos sobre a Base Ideal.
5. Integração por API ou banco de dados com o LMS.
6. Aplicativo móvel ou interface web para usuários finais.
7. Gestão de identidades, criação de contas ou alteração de políticas de acesso da LG.
