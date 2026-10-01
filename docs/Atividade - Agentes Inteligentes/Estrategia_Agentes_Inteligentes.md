# Estratégia de Agentes Inteligentes

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)
**Equipe:** Equipe 1 — Legal
**Integrantes:** Sannyer Carvalho · Kauã Sales · Ericle Luna · Daniele Greice
**Cliente:** LG Electronics do Brasil — Jurídico / Contratos (filial Manaus – MAO)
**Programa:** Digital Transformation Academy — Hands-On

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 0.1 | 01/10/2026 | Sannyer Carvalho | Versão inicial da estratégia de uso de agentes inteligentes |

> Este documento apresenta uma **proposta de estratégia**. Não há implementação de agentes neste trabalho. Os itens 1 a 3 refletem o projeto atual em desenvolvimento; a partir do item 4, descreve-se o que precisaria mudar para o uso de agentes.

---

## 1. Fundamentação do Projeto

### 1.1 Problema

A área de Contratos do Jurídico da LG Electronics em Manaus usa o **LMS – Legal Management System** para gerenciar os contratos. O relatório padrão exportado pelo LMS é **macro**: ele não traz as datas em que cada contrato passou pelas etapas de revisão, consenso e aprovação.

Para acompanhar essas etapas, a área mantém manualmente a planilha **Base Ideal.xlsx (aba "Ideal Raw")**, com 23 colunas por contrato. Oito dessas colunas são datas que só existem no histórico individual de cada contrato (**"Approval History"**). Hoje uma colaboradora precisa abrir contrato por contrato no LMS e copiar essas datas à mão.

| Indicador | Valor observado |
| :--- | :--- |
| Esforço por execução | 4 a 5 horas |
| Frequência de atualização | Cerca de 2 vezes por semana |
| Esforço semanal | 8 a 10 horas |
| Colunas de datas transcritas à mão | 8 |
| Estados possíveis do contrato ("Progress State") | 11 |

**Consequências:** base desatualizada na maior parte da semana, risco de erros de digitação e omissões, e tempo de uma profissional qualificada gasto em coleta, e não em análise.

**Causa-raiz:** o dado existe no sistema, mas só é acessível pela interface, contrato a contrato. Não há API, integração ou relatório customizado do LMS disponível para a filial.

### 1.2 Escopo atual

O projeto desenvolve um robô **RPA em Python (Playwright)** que executa o processo sozinho, todo dia útil pela manhã:

- login automático no SSO da LG, com geração do OTP temporário e leitura do Captcha por OCR local (`ddddocr`);
- aplicação dos filtros no LMS (Subsidiary `LGESP` e período) e exportação do relatório macro;
- filtragem dos contratos de Manaus (`MAO`) com Pandas;
- consulta individual de cada contrato e extração das datas do Approval History;
- aplicação do De/Para por regras fixas e geração da Base Ideal.xlsx no layout atual;
- envio da base por e-mail, com resumo e logs da execução.

**Fora do escopo:** alterar, aprovar ou criar contratos (o robô apenas lê o LMS), outras filiais, dashboards e análises de BI, integração via API e qualquer decisão jurídica.

**Estado atual:** autenticação (SSO + OTP + Captcha), Docker e CI/CD concluídos. Filtro, exportação e mineração estão com os seletores mapeados. As demais etapas estão a desenvolver.

### 1.3 Fluxo do processo

![Fluxo do processo AS-IS e escopo atual](img/01_fluxo_atual.png)

---

## 2. Objetivos

### 2.1 Objetivo geral

Automatizar a geração da Base Ideal dos contratos de Manaus a partir do LMS, para entregar à área Jurídica dados confiáveis e atualizados todo dia útil, sem trabalho manual de coleta.

### 2.2 Objetivos específicos

- Automatizar o login no SSO da LG, incluindo a geração do OTP temporário e a leitura do Captcha.
- Aplicar os filtros no LMS e exportar o relatório macro dos contratos `LGESP`.
- Filtrar os contratos da filial Manaus (`MAO`).
- Extrair as 8 datas de etapa do Approval History de cada contrato.
- Padronizar os dados com o De/Para no layout da aba *Ideal Raw*.
- Enviar a base por e-mail, com resumo e logs de cada execução.
- Executar o processo em menos de 40 minutos.
- Aumentar a frequência de atualização de 2 para 5 vezes por semana.

---

## 3. Artefatos Finais (Entregáveis)

| Artefato | Descrição |
| :--- | :--- |
| Robô RPA Ideal Raw | Código Python versionado no GitHub, distribuído como imagem Docker no GHCR, com pipeline de CI/CD |
| Base Ideal.xlsx | Planilha gerada automaticamente no layout da aba *Ideal Raw* |
| E-mail diário | Envio da base com resumo da execução |
| Logs e evidências | Registro de cada execução e das falhas por contrato |
| Documentação | Especificação de requisitos (PUR), mapeamento de seletores, manuais de operação e de sustentação |
| Termos de aceite | Aceite intermediário (MVP – M2) e definitivo (M3) |
| Cálculo de ROI | Comparação entre o esforço manual e o automatizado |

---

## 4. Mudanças no Escopo para o Uso de Agentes

No escopo atual, o robô segue regras fixas. Ele funciona bem nas etapas previsíveis, mas tem limites justamente onde o processo é ambíguo. A proposta é **manter o RPA nas etapas determinísticas** (login, filtros, exportação) e **introduzir agentes onde há texto livre, mudança ou decisão**.

| Escopo atual (regra fixa) | Escopo com agentes | Problema que resolve |
| :--- | :--- | :--- |
| De/Para por regras fixas | Agente **interpreta** a timeline em texto livre e classifica os eventos nas 8 datas | Ambiguidade de eventos no Approval History (histórico em texto livre) |
| Seletor quebrado interrompe o robô | Agente **se adapta** à mudança de layout do LMS (*self-healing*) | Risco de mudança de layout do LMS (exposição alta na matriz de riscos) |
| Validação humana de toda a base | Agente **valida** a base e envia ao humano apenas as exceções | Erros de transcrição e inconsistências |
| Dashboards e análises fora do escopo | Agente **resume** a base e aponta gargalos (contratos parados há X dias) | A gestora precisa acompanhar desvios |
| E-mail com conteúdo fixo | A gestora pode **perguntar** em linguagem natural sobre a base | Foco da área em análise, não em coleta |
| Retry fixo em caso de falha | Agente **orquestrador** decide repetir, pular ou escalar | Robustez da execução |

**Itens que entram no escopo:** interpretação da timeline, adaptação a mudanças de layout, validação automática com fila de exceções, resumo executivo, alertas de gargalo e consulta em linguagem natural.

**Guardrails que permanecem:**

- o robô continua **somente lendo** o LMS;
- credenciais continuam no `.env`, nunca no prompt ou nos logs;
- os modelos rodam **localmente (offline)**: nenhum dado de contrato sai da LG (LGPD e sigilo contratual);
- o LLM **não altera dados sozinho**: as exceções são decididas pela analista (*Human-in-the-Loop*);
- toda decisão de um agente fica registrada em log.

### 4.1 Fluxo alterado

![Fluxo proposto com agentes inteligentes](img/02_fluxo_com_agentes.png)

---

## 5. Arquitetura de Agentes

> **[A ajustar]** Relacionar esta seção aos artigos indicados pelo orientador.

A arquitetura proposta é **multiagente hierárquica, no padrão Orquestrador–Trabalhadores (Supervisor)**, combinada com três padrões complementares:

| Padrão | Onde é usado | Por quê |
| :--- | :--- | :--- |
| **Orquestrador–Trabalhadores** | Agente Orquestrador coordena os agentes trabalhadores | O processo tem etapas bem separadas e sequenciais; um supervisor delega, acompanha o estado e decide o próximo passo |
| **ReAct** (raciocinar + agir) | Dentro de cada agente trabalhador | O agente alterna raciocínio e uso de ferramentas (Playwright, Pandas, leitura de logs), observando o resultado de cada ação |
| **Avaliador–Otimizador** | Entre o Agente Validador e o Agente Extrator | O validador avalia a saída do extrator e devolve os casos inconsistentes para reprocessamento |
| **Human-in-the-Loop** | Exceções graves e consultas da gestora | Decisões sobre dados jurídicos continuam com pessoas |

**Princípio de projeto:** as etapas determinísticas do RPA atual viram **ferramentas** chamadas pelos agentes. O LLM só é usado onde agrega valor (interpretação, adaptação e explicação), o que reduz custo, latência e risco de erro.

![Arquitetura de agentes](img/03_arquitetura_agentes.png)

---

## 6. Agentes, Modelos, Dados e Saídas

### 6.1 Visão geral

São propostos **5 agentes**:

| Agente | Objetivo | Modelo offline sugerido | Dados requeridos | Saída esperada |
| :--- | :--- | :--- | :--- | :--- |
| **1. Orquestrador** | Planejar a execução, acionar os demais agentes e decidir entre repetir, pular ou escalar | Qwen2.5 7B Instruct ou Llama 3.1 8B Instruct (bom suporte a chamada de ferramentas) | Agenda, estado da execução, logs, regras de retry | Plano da execução, status final e log estruturado |
| **2. Navegador** | Navegar no LMS e se recuperar quando um seletor deixa de funcionar | Qwen2.5-VL 7B (multimodal: lê screenshot e DOM) | Mapeamento de seletores, screenshots e DOM das telas do LMS | Relatório exportado e conteúdo bruto da timeline de cada contrato |
| **3. Extrator** | Converter a timeline em texto livre nas 8 datas e no Progress State | Qwen2.5 7B ou Mistral 7B, com saída em JSON Schema | Aba *Legenda* (11 estados), linha "Espelho sistema" (De/Para), exemplos rotulados da base manual | JSON por contrato com estado, datas e nível de confiança |
| **4. Validador** | Checar a consistência da base e separar as exceções | Regras em Pandas + LLM leve (Phi-4-mini ou Llama 3.2 3B) | Base do dia anterior, regras de negócio, matriz de transições de estado | Base aprovada, relatório de qualidade e fila de exceções |
| **5. Analista** | Gerar o resumo executivo, alertar gargalos e responder perguntas da gestora | Qwen2.5 14B ou Llama 3.1 8B, com consulta à base via Pandas | Base Ideal consolidada e histórico das bases | Resumo no e-mail, alertas e respostas em linguagem natural |

**Infraestrutura offline proposta:**

- **Ollama** (ou vLLM) para servir os modelos localmente, com quantização de 4 bits: um modelo de 7B ocupa cerca de 5 a 6 GB de memória de vídeo;
- **LangGraph** para a orquestração dos agentes, com estado explícito e pontos de interrupção para revisão humana;
- reaproveitamento do RPA atual (Playwright, `ddddocr`, Pandas) como ferramentas.

### 6.2 Detalhamento: Agente Validador

O Agente Validador é o "segundo par de olhos" automático da base. Com o robô, o risco deixa de ser o erro de digitação e passa a ser o **erro silencioso**: uma mudança no LMS, um evento mapeado errado no De/Para ou uma timeline incompleta. O validador detecta esses casos e só chama o humano quando necessário.

A própria Base Ideal atual já mostra problemas que ele detectaria: texto no lugar de data (`Biz-Drop Completed = "Data"`), valor mal formatado (`Amount = "9.240.61"`) e data de término anterior às datas de revisão.

**Validação em 3 camadas:**

| Camada | Técnica | Checagens |
| :--- | :--- | :--- |
| **1. Regras** | Pandas, sem LLM | Formato (datas válidas, valor numérico, moeda ISO), campos obrigatórios, Progress State entre os 11 estados, ordem cronológica das 8 datas, coerência entre estado e datas, duplicidade, marcador MAO |
| **2. Comparação** | Pandas, com a base do dia anterior | Datas antigas que mudaram, regressão de estado, contratos que sumiram, volume anormal, campos que ficaram nulos em massa |
| **3. Interpretação** | LLM local | Explica a anomalia em português, classifica a gravidade e investiga a causa provável consultando logs e screenshots (ReAct) |

**Gravidade:** 🔴 bloqueia o envio e vai para a analista · 🟡 envia com alerta · 🟢 apenas informativo.

**Exemplo de exceção gerada:**

```json
{"contrato": "C2026814234", "campo": "Biz-Drop Completed", "valor": "Data",
 "regra": "formato_data", "gravidade": "vermelho",
 "explicacao": "O campo contém o texto 'Data' em vez de uma data. Provável erro no De/Para.",
 "acao_sugerida": "Verificar o evento correspondente no Approval History"}
```

**Métricas:** percentual de contratos enviados para revisão humana (meta: abaixo de 5%), taxa de falsos positivos, erros detectados antes de chegar à gestora e tempo da analista na validação.

![Agente Validador](img/04_agente_validador.png)

### 6.3 Riscos e cuidados

| Risco | Mitigação |
| :--- | :--- |
| O LLM "alucina" uma data ou explicação | Saída em JSON Schema, toda explicação cita a regra e o valor que dispararam o alerta, e o LLM não altera dados |
| Excesso de alertas (ruído) | Começar com poucas regras e calibrar com a analista; registrar falsos positivos |
| Exposição de dados pessoais | Modelos locais; o prompt recebe apenas número do contrato e campos necessários |
| Hardware insuficiente | Modelos de 3B a 8B quantizados; o Analista (14B) é opcional |
| Comportamento imprevisível do agente navegador | Ele só atua quando um seletor falha, e apenas em modo de leitura |

---

## 7. Referências

> **[A ajustar]** Substituir ou complementar com os artigos indicados pelo orientador.

- YAO, S. et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR, 2023.
- ANTHROPIC. *Building Effective Agents*. 2024.
- WU, Q. et al. *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*. 2023.
- LANGCHAIN. *LangGraph: Multi-agent Systems* (documentação).
- BRASIL. *Lei nº 13.709/2018 – Lei Geral de Proteção de Dados Pessoais (LGPD)*.
