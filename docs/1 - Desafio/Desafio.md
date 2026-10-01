# 1 - Desafio

**Projeto:** Automação do Processo de Contratos Jurídicos — RPA Ideal Raw (LMS)
**Área demandante:** Jurídico – Contratos (LG Electronics, filial Manaus)

| Versão | Data | Autor | Comentários |
| :---: | :---: | :--- | :--- |
| 0.1 | 30/09/2026 | Sannyer Carvalho | Versão inicial baseada no documento AS-IS e na Base Ideal |

---

## 1. Enunciado do Desafio

> *Como garantir que a área Jurídica de Manaus tenha acesso frequente, confiável e padronizado às datas de cada etapa do ciclo de vida dos seus contratos, sem que a equipe precise dedicar horas semanais à coleta e transcrição manual dessas informações?*

O enunciado descreve a dor — e não a solução. A definição de que a resposta será um robô RPA acontece somente na etapa de KickOff (pasta `2 - KickOff - OnePage`).

---

## 2. Contexto

A área de Contratos do Jurídico usa o **LMS – Legal Management System** para gerenciar os contratos da LG Electronics. O relatório padrão exportado pelo LMS é **macro**: ele não traz as datas em que cada contrato passou pelas etapas de revisão, consenso e aprovação.

Para acompanhar essas etapas, a área mantém a planilha **Base Ideal.xlsx (aba "Ideal Raw")**. Ela reúne 23 colunas de informação por contrato, e 8 delas são datas de etapas que só existem no histórico individual de cada contrato ("Approval History").

---

## 3. Evidências do Problema (Cenário Atual Medido)

| Indicador | Valor observado | Fonte |
| :--- | :--- | :--- |
| Esforço por execução | 4 a 5 horas | Documento AS-IS |
| Frequência de atualização | Cerca de 2 vezes por semana, sob demanda | Documento AS-IS |
| Esforço semanal estimado | 8 a 10 horas por semana | Cálculo: 4–5 h × 2 execuções |
| Esforço mensal estimado | Cerca de 35 a 43 horas por mês | Cálculo: 8–10 h × 4,33 semanas |
| Consulta ao LMS | Manual, um contrato por vez | Documento AS-IS |
| Colunas de datas transcritas manualmente | 8 (da solicitação de revisão até a conclusão do contrato) | Base Ideal.xlsx – aba Ideal Raw |
| Estados possíveis do contrato ("Progress State") | 11 | Base Ideal.xlsx – aba Legenda |

**Dores relatadas:**

- Atividade repetitiva, que depende de navegação manual tela a tela.
- Risco de erros de digitação, omissões e inconsistências na base.
- Base atualizada com pouca frequência, o que atrasa a análise e o acompanhamento de desvios.
- Tempo de uma profissional qualificada gasto em coleta, e não em análise.

> **A levantar com o cliente:** volume médio de contratos de Manaus por execução, taxa de erros de transcrição já identificados e custo-hora da colaboradora. Esses dados são necessários para calcular o ROI na entrega M3.

---

## 4. Análise de Causa-Raiz

> As análises abaixo são uma **proposta inicial** construída a partir do AS-IS. Elas precisam ser validadas em dinâmica com o time e com a gestora do Jurídico.

### 4.1 5 Porquês

| # | Pergunta | Resposta |
| :---: | :--- | :--- |
| 1 | Por que a Base Ideal é atualizada com pouca frequência e está sujeita a erros? | Porque cada atualização leva de 4 a 5 horas de trabalho manual. |
| 2 | Por que a atualização leva tanto tempo? | Porque é preciso abrir cada contrato de Manaus no LMS e copiar as datas do "Approval History" uma a uma. |
| 3 | Por que é preciso abrir contrato por contrato? | Porque o relatório macro exportado pelo LMS não traz as datas das etapas de aprovação. |
| 4 | Por que não se usa outra fonte com esses dados? | Porque não existe integração, API ou relatório customizado do LMS disponível para a área. |
| 5 | Por que a área não tem esse relatório? | Porque o LMS é um sistema corporativo global e a filial não controla sua evolução. **Causa-raiz:** o dado existe no sistema, mas só é acessível pela interface, contrato a contrato. |

### 4.2 Diagrama de Ishikawa (6M)

**Efeito:** Base Ideal desatualizada, trabalhosa de manter e sujeita a erros.

![Diagrama de Ishikawa (6M)](ishikawa_6m.png)

### 4.3 Pareto de Esforço (estimativa por etapa do AS-IS)

> Estimativa qualitativa. Deve ser substituída pela medição cronometrada de uma execução real (baseline) na pasta `7 - QA_Testes`.

| Etapa AS-IS | Esforço estimado | % acumulado |
| :--- | :---: | :---: |
| 3–4. Consulta individual e Approval History | ≈ 55% | 55% |
| 5. Transcrição manual das datas | ≈ 25% | 80% |
| 6. Consolidação na Base Ideal | ≈ 10% | 90% |
| 2. Seleção dos contratos MAO | ≈ 5% | 95% |
| 1. Extração do relatório macro | ≈ 5% | 100% |

**Leitura:** consulta e transcrição somam cerca de 80% do esforço. É nelas que a automação traz mais ganho.

### 4.4 Matriz GUT

**Escala:** 1 (baixo) a 5 (alto). **Prioridade** = G × U × T.

| Problema | Gravidade | Urgência | Tendência | Prioridade |
| :--- | :---: | :---: | :---: | :---: |
| Consulta manual contrato a contrato no Approval History | 5 | 4 | 4 | **80** |
| Erros de transcrição e inconsistência na base | 5 | 4 | 3 | **60** |
| Baixa frequência de atualização da base | 4 | 4 | 3 | **48** |
| Dependência de uma única pessoa para o processo | 4 | 3 | 3 | **36** |
| Falta de rastreabilidade (sem logs das atualizações) | 3 | 3 | 3 | **27** |

---

## 5. Estudo Preliminar de Domínio

### 5.1 Ciclo de vida do contrato no LMS

Os estados ("Progress State") catalogados na aba *Legenda* da Base Ideal são:

| Progress State | Significado |
| :--- | :--- |
| Legal Review in Progress | Solicitação de revisão do Jurídico |
| Legal Comments Provided | Comentários emitidos pelo Jurídico |
| Legal Team Consent in Progress | Solicitação de consenso do Jurídico |
| Legal Team Consent Completed | Consenso do Jurídico concluído |
| Approval Completed | Aprovação concluída |
| Approval Rejected | Aprovação rejeitada |
| Approval for the Biz-Drop | Aprovação da desistência do contrato |
| Biz-Drop | Desistência do contrato |
| Biz-Holding | Suspensão do contrato |
| Effective Contract | Contrato finalizado com vigência válida |
| Contract Expired | Contrato finalizado com vigência expirada |

### 5.2 Identificação dos contratos de Manaus

- **Subsidiary:** `LGESP` (filtro aplicado no LMS antes da exportação).
- **Filial Manaus:** identificada pelo marcador `MAO`, que aparece no nome do contrato ou no departamento do responsável (ex.: *"LGESP GA Support Part - MAO"*).

### 5.3 Regulamentações e referências aplicáveis

| Referência | Aplicação no projeto |
| :--- | :--- |
| **LGPD – Lei nº 13.709/2018** | A Base Ideal contém nomes de pessoas físicas (contrapartes, solicitantes e revisores). O tratamento desses dados deve seguir os princípios de finalidade, necessidade e segurança. |
| **Políticas de Segurança da Informação da LG** | O uso das credenciais SSO/OTP pelo robô precisa ser autorizado pela TI. Credenciais não podem ser expostas em código ou logs. |
| **Sigilo contratual** | Valores, contrapartes e objetos dos contratos são informações confidenciais da empresa. |
| **Documentos de processo** | `docs/AS-IS_Processo_Contratos.pdf` e `docs/TO-BE_Processo_Contratos.pdf` |
