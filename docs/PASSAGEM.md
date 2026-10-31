# Passagem do projeto – LMS RPA Monitor (Equipe 1 Legal)

Estado em 30/10/2026, para quem continua a entrega ao jurídico da LGESP (Dydra Andrade, Legal Supervisor).
Comandos, variáveis e rotas estão no [README](../README.md); aqui fica o que é preciso saber para continuar.

## 1. O que o sistema faz hoje

```text
LMS (lms.lge.com) ──► robô (ideal_raw_RPA) ──► API (backend) ──► painel (frontend)
                       1. login (OTP + SSO)       PostgreSQL       Visão geral
                       2. relatório de contratos                   Contratos (+ Exportar)
                       3. detalhe de cada contrato do depto. MAO   Execuções (passo a passo)
                       4. tratamento → Base Ideal (base_ideal.xlsx)
                       5. envio dos contratos para o banco
```

| Parte | Situação |
| :--- | :--- |
| Extração no LMS | Pronta e testada pelo time no LMS real. Coleta status, datas, Biz-Drop (status e data), Request Date (pedido de revisão mais recente) e quantidade de reviews (`Qty Review`). |
| Extração incremental | Pronta. Só reabre no LMS os contratos que mudaram de status; os demais vêm do banco. `LMS_EXTRACAO_COMPLETA=true` força tudo. |
| Tratamento (Base Ideal) | Pronto. Regras da aba Legenda: Biz-Holding e Signed Contract Registered ficam de fora; status amarelos ficam sem datas. 23 colunas (as 22 do modelo + `Qty Review`). |
| Painel | Visão geral, histórico de execuções, página da execução em linguagem simples, tela Contratos com as colunas e os valores da planilha e exportação em xlsx, xls, csv e pdf. |
| Disparo | Botão **Executar Fluxo Agora** (modo real, via `rpa-worker`) ou `docker compose run --rm rpa` (dá para agendar no cron: ver README). |
| Testes / CI | pytest + black (robô e API), Jest + Babel (front), build Docker. Tudo roda no GitHub Actions a cada PR para `develop`/`main`. |

## 2. Pendências da entrega (e-mail da Dydra de 29/10)

Em ordem de prioridade:

1. **Planilha para auditoria do jurídico.** Rodar uma extração completa no LMS real e enviar a `base_ideal.xlsx`
   (ou exportar pela tela Contratos). O jurídico vai conferir a extração e a data do "assigner" (Request Date).
2. **Execução diária no primeiro horário.** O agendamento por cron já funciona (README → "Execução diária").
   Falta escolher o servidor e decidir como a planilha chega até eles:
   - pelo painel (Contratos → Exportar): já funciona;
   - por e-mail ou pasta do SharePoint: **não feito**. Depende da TI da LG liberar uma conta de envio (SMTP)
     ou o acesso à pasta (Microsoft Graph).
3. **Hospedagem e acesso.** O sistema precisa rodar num servidor dentro da rede da LG (o robô precisa alcançar
   o LMS). O painel **ainda não tem login**: definir com a LG se será usuário/senha por perfil
   (jurídico, diretoria, administrador) ou o login corporativo.
4. **Dashboards piloto (7).** **Não feitos.** Os dados já existem na tabela `contracts` (colunas da planilha em
   `raw`/`baseIdeal`). A ideia é uma tela nova no front, alimentada por uma rota nova na API (ex.: `/api/contracts/indicators/`).

   | # | Indicador | Colunas | Pendente de definição |
   | :-: | :--- | :--- | :--- |
   | 1 | Contratos criados por mês/ano | `Request Date` | Contratos sem Request Date |
   | 2 | Contratos registrados por mês/ano | `Progress State` ∈ {Effective Contract, Signed Contract Registered, Contract Expired} + data de registro | Ver perguntas A e B |
   | 3 | Biz-Drop por mês/ano | `Progress State` = Biz-Drop + `Biz-Drop Completed` | — |
   | 4 | Em andamento por status | `Progress State` fora de Biz-Drop e dos registrados | — |
   | 5 | Reviews dos contratos em andamento | `Qty Review` (mesmo filtro do 4) | — |
   | 6 | Tendência em andamento por tipo + valor | `Contract type`, `Amount`, `Contract currency` | Ver pergunta C |
   | 7 | Tempo médio de confecção dos registrados | data de registro − `Request Date` | Ver perguntas B e D |

5. **SingleX.** Verificar se aceita upload da planilha (xlsx/csv já são exportados) e quem dá acesso.

### Perguntas em aberto para o jurídico

- **A.** *Signed Contract Registered* entra nos contratos registrados? Na Legenda ele estava marcado como não usado e,
  por isso, **o tratamento hoje o tira da base** (`STATUS_PROGRESS_STATE` em `ideal_raw_RPA/src/base_ideal/preencher.py`, valor 2).
  Se entrar, mude para 0 ou 1 e confira os testes.
- **B.** Qual é a "data de registro"? Hoje `Register the conclusion of contract` traz a data de Effective Contract ou o
  texto "Expirado" (sem data) para Contract Expired.
- **C.** Valores em BRL e USD: converter para uma moeda (o LMS mostra o equivalente em USD) ou mostrar separado?
- **D.** Contrato sem `Request Date`: usar `Request Legal Review` ou deixar fora do tempo médio?
- **E.** Vigência em texto livre ("4 anos a partir da assinatura") vira `DATA INVÁLIDA` na planilha. Está bom assim?

## 3. Onde mexer

| Quero mudar… | Arquivo |
| :--- | :--- |
| Seletores / leitura da tela do LMS | `ideal_raw_RPA/src/extract_contract/extract_contract_service.py` (mapa em `docs/seletores/`) |
| Regras da Base Ideal (status, datas, colunas) | `ideal_raw_RPA/src/base_ideal/preencher.py` e o modelo `src/base_ideal/modelo/Base_Ideal_padrao.xlsx` |
| Quando reaproveitar um contrato do banco | `contrato_mudou()` no mesmo arquivo da extração |
| Etapas do fluxo do robô | `ideal_raw_RPA/src/pipeline.py` |
| Colunas da tela Contratos e da exportação | `backend/app/services/base_ideal.py` e `frontend/src/app/shared/models/contract.model.ts` (manter as duas listas iguais) |
| Formatos exportados | `backend/app/services/contract_export.py` |
| Frases da página da execução | `frontend/src/app/shared/utils/friendly-log.ts` (mensagem nova do robô sem regra aparece como veio) |

Se mudar uma coluna da Base Ideal, mude nos três lugares (tratamento, API e front) e rode os testes:
`backend/tests/unit/test_base_ideal_export.py` confere se a API segue o modelo do robô.

## 4. Pontos de atenção

- **O LMS pode mudar.** Se a tela mudar, a extração falha na etapa "Extração dos contratos" e a página da execução
  mostra o erro. O print da tela fica em `ideal_raw_RPA/downloads/erros/`.
- **Extração incremental** não percebe mudanças que não alteram o status. Por isso, a extração completa semanal no cron.
- **Contratos gravados antes da coluna `Qty Review`** são lidos de novo no LMS na primeira execução (por isso ela demora mais).
- **Dados reais no repositório:** `db_init/01_seed.sql` e as planilhas em `docs/planilha_de_dados/`. O repositório é
  privado; não copiar para fora. Os códigos OTP que estavam nos logs do dump foram removidos, e o robô não grava mais o OTP.
- **Trocar do modo simulado para o real** num banco com dados fictícios exige `docker compose down -v` (apaga o volume).
- Uma execução por vez: o botão do painel recusa um pedido enquanto houver outra execução em andamento.

## 5. Primeiros passos para quem chega

1. Copie `.env.example` para `.env`, preencha as credenciais LGE, `RPA_MODE=real` e um `RPA_API_TOKEN`.
2. `docker compose up -d --build` e abra o painel (porta 8080).
3. Clique em **Executar Fluxo Agora** e acompanhe em Execuções.
4. Confira a tela Contratos e exporte a planilha.
5. Antes de abrir um PR: `black --check . && pytest` em `ideal_raw_RPA/` e `backend/`, e `npx jest` em `frontend/`.
