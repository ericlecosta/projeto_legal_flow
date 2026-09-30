# 3 - Documentação do Cliente

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 0.1 | 30/09/2026 | Sannyer Carvalho | Inventário inicial dos insumos do cliente e mapa de stakeholders |

---

## 1. Inventário de Insumos Recebidos

| # | Documento / Insumo | Tipo | Origem | Localização atual | Observações |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | AS-IS – Processo de Contratos | Descrição de processo (PDF) | Jurídico / Equipe | `docs/AS-IS_Processo_Contratos.pdf` | Fluxo manual em 7 etapas; esforço de 4–5 h por execução |
| 2 | TO-BE – Processo de Contratos | Descrição de processo (PDF) | Jurídico / Equipe | `docs/TO-BE_Processo_Contratos.pdf` | Fluxo automatizado em 10 etapas, regras de negócio e exceções |
| 3 | Base Ideal.xlsx | Amostra de dados reais (planilha modelo) | Jurídico | `docs/Base Ideal.xlsx` | Layout de saída que o robô deve reproduzir |
| 4 | Gravação de 26/08/2026 | Vídeo (shadowing / demonstração do processo) | Sessão com o Jurídico | `docs/Recording 2026-08-26 161317.mp4` (fora do Git) | Uso restrito; exige consentimento LGPD (pasta 0) |
| 5 | Telas do LMS e do SSO | Layout de telas do sistema legado | Navegação assistida | `docs/seletores/` | Mapeamento de seletores CSS (MD, CSV e XLSX) |

> **Sugestão de organização:** mover os itens 1–4 para esta pasta (`3 - Documentação do Cliente/`) para manter a rastreabilidade prevista no guia.

---

## 2. Estrutura da Base Ideal (layout de saída)

### 2.1 Aba "Ideal Raw" — colunas e De/Para com o LMS

A segunda linha da planilha ("Espelho sistema") registra o rótulo equivalente no LMS. Ela é a base do **De/Para** que o robô deve aplicar.

| Col. | Campo na Base Ideal | Equivalente no LMS ("Espelho sistema") | Origem |
| :---: | :--- | :--- | :--- |
| B | Contract number | Management Number | Detalhe do contrato |
| C | Counterparty | Counterparty | Detalhe do contrato |
| D | Contract name | Contract Name | Detalhe do contrato |
| E | Main Contract Type | Contract type | Detalhe do contrato |
| F | Contract type | — | Relatório / detalhe *(a confirmar)* |
| G | The person in charge | Requester | Detalhe do contrato |
| H | Department of the person in charge | — | Relatório macro *(a confirmar)* |
| I | Progress State | — | Relatório macro (ver Legenda) |
| J | Start date | Contract Period (início) | Detalhe do contrato |
| K | End date | Contract Period (fim) | Detalhe do contrato |
| L | Request Date | "I request a review of the contract." | Approval History |
| M | Request Legal Review | — | Approval History *(evento a confirmar)* |
| N | Review completed | Review Completed | Approval History |
| O | Agreement request | Legal Team Consent in Progress | Approval History |
| P | Agreement has been completed | Legal Team Consent Completed | Approval History |
| Q | Approval request | Processing Approval for Execution | Approval History |
| R | Approval request completed | Approval Completed | Approval History |
| S | Register the conclusion of contract | Contract Expired / Effective Contract | Approval History |
| T | Biz-Drop Completed | — | Approval History *(evento a confirmar)* |
| U | Reviewer | A person in charge of legal (team) | Detalhe do contrato |
| V | Contract currency | Contract amount (moeda) | Detalhe do contrato |
| W | Amount | Contract amount (valor) | Detalhe do contrato |

> A coluna **A (Nomenclatura)** é de uso interno da planilha. Campos marcados como *(a confirmar)* devem ser validados com a gestora e registrados na Matriz CSD (pasta 5).

### 2.2 Demais abas

| Aba | Conteúdo |
| :--- | :--- |
| Legenda | Tradução dos 11 "Progress State" do LMS para o português |
| Biz-Drop Tela | Referência de tela para contratos em desistência |
| Contract Expired | Referência de tela para contratos expirados |
| Effective Contract | Referência de tela para contratos vigentes |

---

## 3. Registro de Entrevistas e Shadowing

| Data | Tipo | Participantes | Registro | Principais achados |
| :---: | :--- | :--- | :--- | :--- |
| 26/08/2026 | Gravação de demonstração do processo | *[A PREENCHER]* | Vídeo (fora do Git) | Navegação no LMS, filtro por Subsidiary, consulta ao histórico contrato a contrato |
| *[A PREENCHER]* | Entrevista com a gestora | | | |

---

## 4. Mapeamento de Stakeholders

| Stakeholder | Papel | Interesse no projeto | Influência | Expectativa principal |
| :--- | :--- | :--- | :---: | :--- |
| Gestora do Jurídico – Contratos | Patrocinadora e usuária-chave | Alto | Alta | Base confiável e atualizada todo dia útil |
| Analista de Contratos (executa o AS-IS) | Usuária operacional | Alto | Média | Menos trabalho manual e menos retrabalho |
| TI LG Electronics | Gestão de acessos e infraestrutura | Médio | Alta | Segurança das credenciais e conformidade com as políticas |
| Jurídico Corporativo / Matriz (dono do LMS) | Dono do sistema | Baixo | Alta | Uso do LMS sem impacto ou sobrecarga |
| Orientador(a) – Digital Transformation Academy | Acompanhamento acadêmico | Médio | Média | Cumprimento da metodologia e dos marcos |
| Equipe 1 – Legal | Desenvolvimento | Alto | Média | Entregar o MVP e o projeto final aprovado |

### 4.1 Matriz Poder × Interesse

```text
                         INTERESSE
                 Baixo                     Alto
          ┌─────────────────────────┬──────────────────────────┐
   Alto   │  MANTER SATISFEITO      │  GERENCIAR DE PERTO      │
          │  • TI LG Electronics    │  • Gestora do Jurídico   │
 PODER    │  • Dono do LMS (Matriz) │                          │
          ├─────────────────────────┼──────────────────────────┤
   Baixo  │  MONITORAR              │  MANTER INFORMADO        │
          │                         │  • Analista de Contratos │
          │                         │  • Orientador(a)         │
          │                         │  • Equipe 1 – Legal      │
          └─────────────────────────┴──────────────────────────┘
```

---

## 5. POPs, ITs e Manuais Internos

| Documento | Status |
| :--- | :--- |
| Procedimento Operacional Padrão da atualização da Base Ideal | *Não recebido — solicitar à gestora* |
| Manual do LMS (usuário) | *Não recebido — solicitar à gestora* |
| Política de uso de contas de serviço / robôs (TI) | *Não recebido — solicitar à TI* |
