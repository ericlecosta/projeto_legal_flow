# Prompt — Opções de Interface (Front-end) para o Sistema RPA LMS

> Copie tudo abaixo da linha e cole no Gemini. Se possível, anexe também os PDFs `DXi_Design_Guide.pdf` e `DXi_Developer_Guide.pdf`.

---

## PAPEL

Você é um(a) Product Designer sênior especializado(a) em dashboards operacionais e sistemas de monitoramento de automações (RPA), com forte domínio de Angular. Sua tarefa é propor **opções de interface** para um MVP, não escrever o sistema inteiro.

## CONTEXTO DO PRODUTO

Estamos construindo um sistema web que usa um RPA para capturar dados do **LMS (Legal Management System)** da LG Electronics — sistema jurídico corporativo onde ficam, entre outros, os contratos em revisão.

**Arquitetura (4 camadas):**
1. **Front-end:** Angular (v15+), TypeScript.
2. **Back-end:** Django (API REST) — dispara o RPA, guarda o histórico e expõe os indicadores.
3. **RPA:** Python + Playwright. Hoje o fluxo faz:
   - Geração de OTP temporário (navega por popups, resolve captcha por OCR local, intercepta a resposta AJAX).
   - Login no SSO (usuário, senha LDAP, OTP).
   - Acesso ao LMS e, na próxima etapa, captura dos dados (ex.: tela de busca/revisão de contratos).
   - Fluxos disponíveis: "Login completo + captura" e "Somente obtenção do OTP". Pode rodar com navegador visível ou em modo *headless*.
4. **Banco:** PostgreSQL — execuções, logs, etapas, agendamentos e dados capturados.

**Formas de execução do RPA:**
- **Agendada** (ex.: cron diário/horário, configurável).
- **Manual**, disparada pela interface.

**Público:** analistas e desenvolvedores do time de automação (uso interno, desktop em primeiro lugar).

**Escopo do MVP:** um **dashboard de execução e monitoramento**. Não é um sistema de análise dos contratos; o foco é saber se o robô está rodando bem, quando rodou, o que capturou e por que falhou.

## INDICADORES E FUNCIONALIDADES QUE A INTERFACE PRECISA COBRIR

Use como base (pode sugerir ajustes e priorizar):

**KPIs de monitoramento**
- **Status operacional do RPA** no padrão corporativo de 3 níveis:
  - 🟢 Verde: operando normalmente.
  - 🟡 Amarelo: comportamento atípico ou inativo por mais tempo que o esperado → verificar motivo.
  - 🔴 Vermelho: fora de operação → intervenção imediata.
- **Running rate** (taxa de execuções bem-sucedidas). A **meta do setor é > 85%**, então a meta precisa aparecer visualmente.
- Execuções hoje / no período (sucesso × falha × em andamento).
- Duração média e duração da última execução.
- Última execução e **próxima execução agendada**.
- Volume de registros capturados (por execução e no período).
- **Falhas por etapa** (OTP, captcha, login SSO, acesso LMS, captura de dados), para mostrar onde o robô quebra com mais frequência.

**Ações e telas**
- Botão de **executar agora**, com escolha do fluxo e do modo headless, e opção de **interromper** uma execução em andamento.
- **Logs em tempo real** da execução atual (via WebSocket), com níveis de log (info, warning, error, success), busca e mascaramento de credenciais.
- **Linha do tempo das etapas** de uma execução (qual etapa está rodando, quanto tempo levou cada uma, onde falhou).
- **Histórico de execuções** com filtros (período, status, origem: agendada × manual, fluxo).
- **Detalhe de uma execução:** metadados, etapas, logs, erro, screenshot da falha (se houver) e registros capturados.
- **Gestão de agendamentos:** listar, criar, editar, pausar e ativar (expressão cron com pré-visualização das próximas execuções em linguagem humana).
- Visualização simples dos **dados capturados** (tabela com busca e exportação), sem análise avançada.

## DIRETRIZES DE DESIGN (OBRIGATÓRIAS — DXi Design Guide)

**Tema:** dark-first. Superfícies elevadas indicam hierarquia; as cores semânticas comunicam estado.

**Cor de marca (Crimson Red):** primária = `brand-800` `#E7194A`. Use em ações principais, foco, links e ênfase institucional, **sem exagero**: em um dashboard de monitoramento, o vermelho de marca não pode ser confundido com o vermelho de erro. Explique como você resolve esse conflito (o semântico *danger* também é `#E7194A`).
Escala brand: 50 `#FDE7ED` · 100 `#FBC2CF` · 200 `#F799AE` · 300 `#F26F8D` · 400 `#ED4570` · 600 `#D11442` · 700 `#B81039` · 800 `#E7194A` · 900 `#7A0824` · 950 `#4D0517`.

**Neutros:** n-0 `#FFFFFF` · n-50 `#F5F5F5` · n-100 `#E0E0E0` · n-200 `#BDBDBD` · n-300 `#9E9E9E` · n-400 `#757575` · n-500 `#616161` · n-600 `#424242` · n-700 `#303030` · n-750 `#252525` · n-800 `#1E1E1E` · n-850 `#181818` · n-900 `#141414` · n-950 `#0D0D0D`.
Papéis: `--bg`, `--surface`, `--surface-elevated`, `--border-soft`.

**Semânticas:** Success `#22C55E` · Warning `#F59E0B` · Danger `#E7194A` · Info `#3B82F6`.

**Tipografia:**
- **Inter** para toda a interface. H1 Semibold 48/52 (-0.025em) · H2 Semibold 36/40 · H3 Semibold 24/32 · Body Regular 16/24 · Eyebrow Semibold 12, uppercase, tracking 0.1em.
- **JetBrains Mono** para números, KPIs, IDs, durações, timestamps, logs e código.

**Raios:** xs 2 · sm 4 · md 6 · lg 8 · xl 12 · 2xl 16 · 3xl 24 (px).
**Sombras:** shadow-sm, md, lg, xl e shadow-glow (use o glow com parcimônia, ex.: execução ao vivo).
**Motion:** fast 100ms (micro-interações) · normal 200ms (hover/focus) · slow 300ms (painéis/modais). Easing: ease-out `cubic-bezier(0,0,0.2,1)` e ease-in-out `cubic-bezier(0.4,0,0.2,1)`.
Todos os tokens existem como CSS custom properties, ex.: `color: var(--color-brand-800);`.

## DIRETRIZES DE ENGENHARIA DO FRONT-END (DXi Developer Guide)

- Estrutura: `src/app/core` (guards, interceptors, serviços globais) · `modules/` (um módulo por feature/página) · `layouts/` (ex.: `LoginLayoutComponent`, `MainLayoutComponent`) · `shared/` (components, models, utils) · `assets/` · `environments/` · `fonts/`.
- Padrões: modularização por feature, injeção de dependência, serviços singleton no core, RxJS (Observer) para comunicação reativa, componentes pequenos e reutilizáveis, com a lógica nos services.
- Tempo real via WebSocket (logs e status de execução).

## O QUE EU QUERO QUE VOCÊ ENTREGUE

Proponha **3 opções de interface conceitualmente diferentes**, por exemplo (fique à vontade para propor outras):
- **A) "Control Tower":** visão geral densa, com tudo numa tela e foco em status e KPIs.
- **B) "Execution-centric":** a execução ao vivo é a protagonista (console, timeline e logs), e os KPIs ficam em segundo plano.
- **C) "Workflow / navegação por abas":** telas separadas e mais limpas (Dashboard, Execuções, Agendamentos, Dados).

**Para cada opção, entregue:**
1. **Conceito e cenário ideal de uso** (2–3 frases).
2. **Mapa de navegação** (sidebar/topbar, rotas Angular sugeridas).
3. **Wireframe em ASCII** da tela principal (dashboard) e de **mais uma tela-chave** (detalhe da execução ou execução ao vivo).
4. **Hierarquia visual:** o que o usuário vê nos primeiros 3 segundos e como os tokens (cores, superfícies, tipografia) reforçam isso.
5. **Componentes de visualização** de cada KPI (ex.: gauge × número grande × sparkline × barra empilhada), com justificativa de cada escolha.
6. **Estados:** vazio (nenhuma execução ainda), carregando, execução em andamento, erro/RPA vermelho e WebSocket desconectado.
7. **Árvore de componentes Angular** (módulos de feature + componentes `shared` reutilizáveis).
8. **Prós e contras** e **esforço estimado** para um MVP (baixo/médio/alto).

**Depois das 3 opções:**
- Uma **tabela comparativa** (clareza do status, velocidade de diagnóstico de falhas, esforço de implementação, escalabilidade para mais RPAs no futuro).
- Sua **recomendação** para o MVP, com justificativa, e o que deixar para a v2.
- Uma lista dos **endpoints REST e eventos WebSocket** que o front-end vai precisar do back-end Django (nome, método e payload resumido), para alinharmos o contrato da API.
- Sugestão de **biblioteca de componentes e de gráficos** compatível com Angular que respeite os tokens acima sem brigar com o tema (ex.: Angular Material com tema customizado, PrimeNG, ngx-charts, ECharts, Chart.js). Justifique.

## RESTRIÇÕES

- Respeite estritamente a paleta e a tipografia acima. Não invente cores fora dos tokens (pode usar opacidades das cores existentes).
- Status nunca pode depender só de cor: use também ícone e texto, por acessibilidade (WCAG AA de contraste).
- Desktop-first (≥1280px), mas indique como o layout se comporta em telas menores.
- É um MVP: priorize clareza e poucas telas bem resolvidas em vez de muitas funcionalidades.
- Responda em **português do Brasil**.
