# Spec — Extração de Biz-Drop, Request Date e Qty Review

> **Escopo:** somente o RPA (`ideal_raw_RPA/`). API, front e consolidação da base Ideal Raw ficam fora.
> **Branch:** `hotfix/adicao-colunas`
> **Fonte dos seletores:** `docs/seletores/Mapeamento_Seletores_Formatado.xlsx` (linhas "Request Date", "Qty Review", "Biz-drop status", "Approval History button", "Contract biz drop button", "Biz-Drop Completed").
> **Referência visual:** aba "Biz-Drop Tela" de `docs/Base Ideal.xlsx` (print de um contrato em Biz-Drop, `C2026827791`).

---

## 1. Objetivo

Incluir três dados na planilha gerada pela extração detalhada (`contract_review_management.xlsx`):

| # | Dado | Coluna na saída | Onde está na tela |
|---|------|-----------------|-------------------|
| 1 | Se o contrato está em Biz-Drop e a data/hora em que ele foi concluído | `Biz-Drop Status` (bool) e `Biz-Drop Completed` (texto) | Barra de progresso no topo e a aba **Approval History → Contract Biz Drop** |
| 2 | Data do pedido de revisão | `Request Date` (texto) | Timeline de comentários, no item "I request a review of the contract." |
| 3 | Quantidade de revisões concluídas | `Qty Review` (int) | Card **History of completed review**, no marcador `.Dot` mais recente |

---

## 2. Como o código funciona hoje

Arquivo: `ideal_raw_RPA/src/extract_contract/extract_contract_service.py`.

- **Fluxo por contrato** (um por vez, **sem paralelismo**; ele foi testado e revertido, não reintroduzir):
  1. `_pesquisar_contrato` pesquisa no `elastic_search` e devolve o `href`;
  2. `_abrir_aba_detalhe` abre a aba de detalhe na primeira vez, ou `_navegar_detalhe` só troca a rota do SPA nos seguintes (**a aba de detalhe é reaproveitada**);
  3. `_coletar_dados_contrato` espera a tela ficar pronta (`_aguardar_quietude`) e lê **todos os campos numa única chamada** `page.evaluate(_JS_COLETA, ...)`.
- **Configuração dos campos:** constantes no topo do arquivo. `TABELA_FIELDS` são as células da tabela, `DATE_FIELDS` as datas da timeline e `STATUS_FIELDS` os booleanos por visibilidade. `COLUNAS_FINAIS` define a ordem das colunas da planilha.
- **Esperas:** não existe `time.sleep` fixo. O "tela pronta" é decidido por `_MonitorRede` + `_Quietude`: sem XHR/fetch pendente e com o DOM estável. Depois de qualquer clique que carregue conteúdo, use `_aguardar_quietude(page, monitor, QUIETUDE_DETALHE_MS, ESPERA_MAX_DETALHE_MS)`.
- **Falhas:** exceções dentro de `_coletar_dados_contrato` fazem o contrato ser tentado de novo (até `LMS_TENTATIVAS`, com a aba de detalhe reaberta). Na falha final, um print é salvo em `downloads/erros/`.
- **Hoje já existem:**
  - a coluna `I requested a review of the contract.` em `DATE_FIELDS`, cuja regra é "o `span.Date` mais próximo **antes** do texto". Ela vira `Request Date` (seção 4.2);
  - a coluna `Biz-Drop Completed` em `DATE_FIELDS`, que procura o texto "Status changed to in ‘Biz-Drop Completed’" na timeline. Ela passa a ser preenchida pela regra nova (seção 4.1).

---

## 3. Colunas da planilha (mudanças em `COLUNAS_FINAIS`)

| Mudança | Antes | Depois |
|---------|-------|--------|
| Renomear (mesma posição) | `I requested a review of the contract.` | `Request Date` |
| Mudar a regra (mesma posição e nome) | `Biz-Drop Completed` (texto na timeline) | `Biz-Drop Completed` (aba Approval History) |
| Nova, logo depois de `Biz-Drop Completed` | — | `Qty Review` |
| Nova, junto aos booleanos de `STATUS_FIELDS` (no fim) | — | `Biz-Drop Status` |

- Remover a entrada `"Biz-Drop Completed"` de `DATE_FIELDS`, para a regra antiga não sobrescrever a nova.
- O teste `test_colunas_finais_sem_repeticao` precisa continuar passando: nenhuma coluna repetida.

---

## 4. Regras de extração

### 4.1 Biz-Drop (o mais complexo)

**Passo A — Detectar** (dentro do `_JS_COLETA`, sem cliques):

- Seletor do mapeamento: `#progress_body_id div[id^="Item_Id_"]:has-text("Biz-Drop")`.
- Dentro do `evaluate`, `:has-text` não existe. Faça `document.querySelectorAll('#progress_body_id div[id^="Item_Id_"]')` e procure algum elemento **visível** (use a função `visivel` que já está em `_JS_VISIVEL`) cujo texto normalizado contenha `biz-drop`, sem diferenciar maiúsculas.
- O resultado vai para `Biz-Drop Status` (True/False).

**Passo B — Data de conclusão** (só se `Biz-Drop Status` for True, **depois** do `_JS_COLETA`):

1. Clicar na aba **Approval History**: `.nav-tabs .nav-link:has-text("Approval History")`.
2. Esperar: `_aguardar_quietude(...)`.
3. Clicar na sub-aba **Contract Biz Drop**: `a.nav-link:has-text("Contract Biz Drop")`.
4. Esperar: `_aguardar_quietude(...)` e então esperar a tabela da sub-aba ter ao menos uma linha, usando o mesmo `timeout` da coleta.
5. Ler a tabela inteira **numa única chamada `evaluate`**, devolvendo uma lista de linhas, cada uma uma lista com o texto das células: `[["Requester", "Draft", "SIMEIA BATALHA", "2026-08-25 23:41", ""], ["Approver", "Approval", "LAERTE SOUZA", "2026-08-26 02:40", "Confirmed."]]`.
6. Escolher a data em Python, numa **função pura** `escolher_data_biz_drop(linhas) -> str` (testável sem navegador). Regra **confirmada** (seção 7):
   - pegar a **última linha cujo Status é "Approver"** e que tenha `Processing Date` preenchida;
   - se nenhuma linha for de Approver, devolver `""`;
   - localizar a coluna `Processing Date` pelo **cabeçalho** da tabela, e não por posição fixa;
   - devolver o texto de data e hora exatamente como aparece na tela (ex.: `2026-08-26 02:40`), sem converter, como as demais datas da planilha.
7. **Voltar para a aba Comment:** `.nav-tabs .nav-link:has-text("Comment")`. Isso é obrigatório (ver o primeiro risco abaixo).

**Riscos que a implementação precisa tratar:**

- **Aba de detalhe reaproveitada:** se o SPA lembrar a aba selecionada, o próximo contrato abriria em "Approval History". A timeline (aba Comment) ficaria escondida, e todos os `STATUS_FIELDS`, que dependem de visibilidade, e as datas sairiam errados. Por isso:
  - o Passo B roda **depois** do `_JS_COLETA`;
  - ao final, o robô volta para a aba Comment, inclusive em caso de erro (`try/finally`).
- **Seletor da data não confirmado:** o seletor `span.IncidentName_Txt` do mapeamento devolve o texto da **coluna Status** ("Requester"), não a data. O próprio exemplo da planilha diz isso. **Antes de codar, inspecione a tabela real no DevTools** e defina os seletores do cabeçalho e das células. Registre o que encontrar na planilha de mapeamento.
- **Falha só no Biz-Drop:** se o Passo B falhar (aba não aparece ou tabela vazia), **não descartar o contrato inteiro**:
  - tentar o Passo B mais uma vez;
  - se falhar de novo, deixar `Biz-Drop Completed` vazio, registrar `logger.warning` e salvar um print com `_salvar_diagnostico(page, pasta_erros, f"bizdrop_{contrato}")`;
  - no fim da execução, listar no log os contratos Biz-Drop sem data, como já é feito com os `falhas`.
- **Sub-aba "Contract Review Complete":** o exemplo do mapeamento também clica nela. Não é necessário para a data do Biz-Drop; não clicar.

### 4.2 Request Date

- Seletor do mapeamento: `.CommentTimeline_Body:has-text("I request a review of the contract.") .Date`.
- **Regra confirmada:** se o contrato teve mais de um pedido de revisão, vale o **mais recente**.
- No `_JS_COLETA`: achar **todos** os `.CommentTimeline_Body` cujo texto normalizado contenha `I request a review of the contract.`. De cada um, pegar o `innerText.trim()` do primeiro `.Date` e devolver a **lista** dessas datas.
- Escolher em Python com uma **função pura** `escolher_request_date(datas) -> str`, que **não depende da ordem da timeline** (não sabemos se o LMS mostra do mais novo para o mais antigo):
  - interpretar cada texto como data/hora, tolerando `AAAA-MM-DD`, `AAAA-MM-DD HH:MM` e `AAAA-MM-DD HH:MM:SS`;
  - devolver o texto **original**, sem converter, da maior data/hora;
  - se nenhum texto puder ser interpretado, devolver o último texto não vazio da lista e registrar `logger.warning`;
  - com a lista vazia, devolver `""`.
- Substitui a regra antiga dessa coluna ("`span.Date` anterior ao texto"). Remover essa entrada de `DATE_FIELDS` e preencher `Request Date` pela função nova.
- Formato: o texto como aparece na tela, sem converter (decisão confirmada).

### 4.3 Qty Review

- Seletor do mapeamento: `.card:has-text("History of completed review") .Dot >> nth=0`. O mais recente é o primeiro.
- No `_JS_COLETA`: achar o `.card` cujo texto contenha `History of completed review` e pegar o `innerText.trim()` do primeiro `.Dot` dentro dele (ex.: `"1st"`, `"2nd"`).
- Converter em Python com uma **função pura** `parse_qty_review(texto) -> int`:

| Entrada | Saída |
|---------|-------|
| `"1st"` | 1 |
| `"2nd"` | 2 |
| `"3rd"` | 3 |
| `"11th"` | 11 |
| `" 2nd "` | 2 |
| sem card ou sem `.Dot` | 0 (decisão confirmada) |
| texto sem número | 0, com `logger.warning` |

---

## 5. Onde mexer

| Arquivo | Mudança |
|---------|---------|
| `src/extract_contract/extract_contract_service.py` | Constantes dos seletores novos; `_JS_COLETA_CORPO` passa a devolver `bizdrop`, `request_date` e `qty_review_texto`; `DATE_FIELDS` e `COLUNAS_FINAIS` (seção 3); funções puras `parse_qty_review`, `escolher_request_date` e `escolher_data_biz_drop`; nova função `_coletar_biz_drop(page, monitor, timeout) -> str` com o Passo B; `_coletar_dados_contrato` chama `_coletar_biz_drop` quando `Biz-Drop Status` for True |
| `src/extract_contract/__init__.py` | Exportar `parse_qty_review`, `escolher_request_date` e `escolher_data_biz_drop` (os testes importam daqui) |
| `tests/unit/test_extract_contract.py` | Testes da seção 6 |
| `main.py` (opcional, recomendado) | Variável `LMS_SOMENTE_CONTRATOS` (números separados por vírgula) que filtra a planilha antes da coleta, para validar no LMS real com poucos contratos (seção 6) |

Para o `_JS_COLETA` não ficar ilegível, separe as partes novas em funções JS auxiliares dentro do mesmo corpo. **Mantenha uma única chamada `evaluate` para tudo o que não precisa de clique.**

---

## 6. Testes e validação

**Testes unitários** (rodam no CI, sem navegador):

- `parse_qty_review`: todos os casos da tabela da seção 4.3.
- `escolher_request_date`:
  - um pedido só: devolve a data dele;
  - dois pedidos, **em qualquer ordem na lista**: devolve o mais recente;
  - formatos misturados (`2026-04-17` e `2026-05-20 10:35:35`): compara certo e devolve o texto original;
  - lista vazia: devolve `""`;
  - textos que não são data: devolve o último não vazio.
- `escolher_data_biz_drop`:
  - com a tabela do print (Requester + Approver), devolve `2026-08-26 02:40`;
  - com dois Approvers, devolve o do último;
  - sem Approver, devolve `""`;
  - com as colunas em outra ordem, ainda acha `Processing Date` pelo cabeçalho;
  - com tabela vazia, devolve `""`.
- `COLUNAS_FINAIS`:
  - contém `Request Date`, `Qty Review`, `Biz-Drop Status` e `Biz-Drop Completed`;
  - **não** contém mais `I requested a review of the contract.`;
  - não tem colunas repetidas;
  - continua começando por `Contract Number` e `Department of the person in charge`.

**Validação no LMS real** (só dá para fazer na rede da empresa), com `LMS_SOMENTE_CONTRATOS`:

| Contrato | O que conferir |
|----------|----------------|
| `C2026827791` (Biz-Drop, do print) | `Biz-Drop Status=True`; `Biz-Drop Completed` igual à `Processing Date` da linha Approver na aba Contract Biz Drop; `Qty Review=1` |
| Um contrato com "2nd" ou mais no card de reviews | `Qty Review` correto e `Request Date` igual ao pedido de revisão **mais recente** da timeline |
| Um contrato comum, sem Biz-Drop | `Biz-Drop Status=False`; `Biz-Drop Completed` vazio |
| **Na mesma execução:** um contrato comum logo **depois** do Biz-Drop | Os `STATUS_FIELDS` e as datas desse contrato saem iguais aos de uma execução dele sozinho. Isso prova que a volta para a aba Comment funciona |

**Antes do commit:**

```bash
cd ideal_raw_RPA
black --check .   # black==26.10.1, line-length 120 (fixado no requirements-dev.txt)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
pytest -v
```

---

## 7. Decisões (confirmadas pelo Sannyer)

| # | Pergunta | Decisão |
|---|----------|---------|
| 1 | Qual data é o Biz-Drop Completed? | A `Processing Date` da linha **Approver**, na aba Contract Biz Drop |
| 2 | Request Date com mais de um pedido de revisão | O **mais recente** (escolhido pela data, não pela ordem da timeline) |
| 3 | Qty Review sem o card "History of completed review" | `0` |
| 4 | Formato das datas novas | O texto como aparece na tela, sem converter, igual às demais datas da planilha |

## 8. Restrições

- Não reintroduzir paralelismo nem esperas fixas (`time.sleep`, `wait_for_timeout` com tempo fixo). Use `_aguardar_quietude` e esperas por condição.
- Respeitar `timeout` / `LMS_TIMEOUT_MS` em toda espera nova. Nada de `timeout=0`.
- Manter os nomes e comentários em português, no estilo atual do arquivo.
- Não alterar a API (`backend/`), o front nem a consolidação.
  - **Aviso para a frente da consolidação:** `ContractIn` na API tem `biz_drop_completed_at` e `review_requested_at` como `date`, mas o RPA vai entregar data **e hora** em texto.
