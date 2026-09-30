# 0 - Dados da Equipe

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)
**Equipe:** Equipe 1 — Legal
**Cliente:** LG Electronics do Brasil — Jurídico / Contratos (filial Manaus – MAO)
**Programa:** Digital Transformation Academy — Hands-On

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 0.1 | 30/09/2026 | Sannyer Carvalho | Versão inicial (campos marcados como *[A PREENCHER]* devem ser completados pela equipe) |

---

## 1. Composição do Time

| # | Nome | Papel no projeto | Responsabilidades principais | E-mail | Telefone | Alocação (h/semana) |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 1 | Sannyer Carvalho | Desenvolvedor RPA / Tech Lead | Arquitetura do robô, automação do login/OTP, CI/CD e Docker | carvalhosannyer@gmail.com | *[A PREENCHER]* | *[A PREENCHER]* |
| 2 | *[A PREENCHER]* | Product Owner (PO) | Priorização do backlog, interface com a gestora do Jurídico, aceite das entregas | *[A PREENCHER]* | *[A PREENCHER]* | *[A PREENCHER]* |
| 3 | *[A PREENCHER]* | Desenvolvedor(a) | Filtros, exportação e mineração do Approval History | *[A PREENCHER]* | *[A PREENCHER]* | *[A PREENCHER]* |
| 4 | *[A PREENCHER]* | Analista de Dados | Tratamento com Pandas, De/Para e geração da Base Ideal | *[A PREENCHER]* | *[A PREENCHER]* | *[A PREENCHER]* |
| 5 | *[A PREENCHER]* | QA / Testes | Plano de testes, UAT e evidências de homologação | *[A PREENCHER]* | *[A PREENCHER]* | *[A PREENCHER]* |

### 1.1 Contatos externos

| Nome | Organização / Área | Papel | Contato |
| :--- | :--- | :--- | :--- |
| *[A PREENCHER]* | LG Electronics – Jurídico / Contratos | Gestora do processo (usuária-chave e patrocinadora) | *[A PREENCHER]* |
| *[A PREENCHER]* | LG Electronics – Jurídico / Contratos | Colaboradora que executa o processo AS-IS | *[A PREENCHER]* |
| *[A PREENCHER]* | LG Electronics – TI | Responsável por acessos (SSO/LMS) e infraestrutura | *[A PREENCHER]* |
| *[A PREENCHER]* | Digital Transformation Academy | Orientador(a) do projeto | *[A PREENCHER]* |

---

## 2. Matriz RACI

**Legenda:** **R** – Responsável (executa) · **A** – Aprovador (responde pelo resultado; apenas um por linha) · **C** – Consultado · **I** – Informado

| Entregável / Atividade | Tech Lead / Dev RPA | PO | Dev | Analista de Dados | QA | Gestora Jurídico (Cliente) | Orientador |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Levantamento AS-IS / TO-BE | C | R | C | C | I | A | C |
| Especificação de Requisitos (PUR) | C | R | C | C | C | A | C |
| OnePage e KickOff | C | R | I | I | I | A | C |
| Mapeamento de seletores do LMS | R | I | C | I | C | I | I |
| Autenticação SSO + OTP | R | A | C | I | C | I | I |
| Filtros e exportação do relatório | C | A | R | I | C | I | I |
| Mineração do Approval History | C | A | R | C | C | C | I |
| De/Para e geração da Base Ideal | C | A | C | R | C | C | I |
| Notificação por e-mail e logs | R | A | C | I | C | I | I |
| Agendamento (execução diária) | R | A | I | I | C | C | I |
| Plano de testes e UAT | C | A | C | C | R | C | I |
| Status Report semanal | C | R | I | I | I | I | A |
| Manuais e treinamento | C | A | C | C | R | C | I |

> A Matriz RACI deve ser revisada pelo time na próxima cerimônia de planejamento, ajustando os nomes reais aos papéis acima.

---

## 3. Acordos de Trabalho do Time

1. **Rituais:** Planning no início de cada sprint, daily curta (15 min) e Review + Retrospectiva ao final da sprint.
2. **Comunicação:** Canal oficial do time para assuntos do dia a dia; decisões relevantes são registradas por escrito (ata ou issue no GitHub).
3. **Versionamento:** Todo código entra via Pull Request da branch `develop` para `main`; a pipeline de CI deve estar verde antes do merge.
4. **Padrão de commits:** Mensagens no formato `tipo: descrição` (ex.: `feat:`, `fix:`, `docs:`, `ci:`).
5. **Documentação:** Um artefato só é considerado concluído quando arquivado e versionado no diretório correto deste repositório.
6. **Credenciais:** Senhas, OTPs e dados pessoais nunca são commitados; utiliza-se o `.env` local (ignorado pelo Git).
7. **Impedimentos:** Qualquer bloqueio superior a 1 dia útil é comunicado ao PO e registrado no Status Report.

---

## 4. Sigilo, Conduta e LGPD

### 4.1 Termo de Confidencialidade

Os integrantes da equipe comprometem-se a:

- Não divulgar, fora do contexto do projeto, informações de contratos, contrapartes, valores ou dados pessoais obtidos no LMS ou na Base Ideal.
- Utilizar as credenciais institucionais exclusivamente para as finalidades do projeto.
- Não armazenar dados reais de contratos em repositórios públicos, dispositivos pessoais não autorizados ou serviços externos.
- Utilizar dados anonimizados ou amostras autorizadas em apresentações e materiais acadêmicos.

### 4.2 Gravação de Dinâmicas e Entrevistas

- Toda gravação (ex.: `Recording 2026-08-26 161317.mp4`) exige consentimento prévio e expresso dos participantes.
- As gravações são armazenadas fora do Git (arquivos de vídeo estão no `.gitignore`) e em local com acesso restrito à equipe.
- As gravações serão excluídas ao final do projeto, salvo autorização expressa em contrário.

### 4.3 Assinaturas

| Nome | Papel | Data | Assinatura |
| :--- | :--- | :---: | :--- |
| Sannyer Carvalho | Desenvolvedor RPA / Tech Lead | | |
| *[A PREENCHER]* | | | |
| *[A PREENCHER]* | | | |
| *[A PREENCHER]* | | | |
| *[A PREENCHER]* | | | |
