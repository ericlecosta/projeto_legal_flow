# Sugestões para acelerar a extração de contratos

Opções para reduzir o tempo da etapa **Extração dos contratos** do robô
(`ideal_raw_RPA/src/extract_contract/extract_contract_service.py`).

## Como funciona hoje

Para cada contrato filtrado do relatório (`relatorio_contratos.xlsx`), o robô:

1. Pesquisa o contrato no `elastic_search` do LMS.
2. Abre a tela de detalhe (a mesma aba é reaproveitada entre contratos) e espera ela terminar de carregar.
3. Lê todos os campos numa única chamada ao navegador.
4. Se o contrato estiver em Biz-Drop, abre também as abas **Approval History** e **Contract Biz Drop** para ler a data de conclusão.

Tudo isso roda **um contrato por vez**.

As esperas já estão otimizadas: não há `sleep` fixo. A tela é considerada pronta quando não há requisições pendentes e a página parou de mudar. Por isso, o ganho grande agora vem de **fazer menos trabalho** ou de **fazer em paralelo**.

## Resumo

| # | Opção | Ganho esperado | Esforço | Precisa de acesso ao LMS para desenvolver? |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Extração incremental (só o que mudou) | Alto a partir da 2ª execução | Médio | Não |
| 2 | Paralelismo (várias abas) | 2× a 4× | Médio | Não (mas precisa medir no LMS) |
| 3 | Ir direto ao detalhe, sem a busca | 30% a 50% por contrato | Baixo a médio | Sim (DevTools) |
| 4 | Ler pela API interna do LMS | 5× a 20× | Alto | Sim (DevTools) |
| 5 | Ajustes finos | 10% a 20% | Baixo | Não |

---

## 1. Extração incremental: só buscar o que mudou

O relatório baixado na etapa 2 já traz o **`Progress State` de cada contrato**. O banco do monitor também guarda o status da última execução. Se os dois forem iguais, o contrato não mudou, e o robô pode reaproveitar os dados do banco em vez de abrir a tela dele.

- **Ganho:** contratos em status final (Effective Contract, Contract Expired, Biz-Drop com data) quase nunca mudam. Depois da primeira execução, o robô pode passar a abrir só uma fração dos contratos.
- **Esforço:** médio. O robô passa a ler o último estado pela API, e a rota `GET /api/contracts/` já existe.
- **Risco:** se o LMS mudar uma data sem mudar o status, a base fica desatualizada.
- **Como mitigar:** fazer uma execução completa periódica (por exemplo, semanal) ou criar uma variável de ambiente como `LMS_EXTRACAO_COMPLETA=true` para forçar a leitura de todos.

## 2. Paralelismo: várias abas ao mesmo tempo

As abas compartilham o login, então não é preciso refazer SSO nem OTP. Seria configurável por uma variável como `LMS_ABAS_PARALELAS` (padrão 2 ou 3), com a lista de contratos dividida entre as abas.

- **Ganho:** perto de N vezes com N abas, limitado pela velocidade do LMS e pela CPU do servidor.
- **Esforço:** médio. O código já monitora a rede por aba (`_MonitorRede`), mas usa a API síncrona do Playwright, que roda em uma única thread. Seria preciso alternar entre as abas no mesmo laço ou migrar para a versão assíncrona.
- **Risco:** o LMS pode limitar acessos simultâneos ou derrubar a sessão.
- **Como mitigar:** começar com 2 abas, medir e só então aumentar.

## 3. Pular a busca e ir direto ao detalhe

A busca só serve para descobrir o `id` da URL `/app/contract/save?id=...`. Esse `id` vem de uma requisição JSON da própria busca, e é provável que a resposta traga o id de vários contratos de uma vez. Com isso, cada contrato passa a carregar uma tela, em vez de duas.

- **Ganho:** de 30% a 50% do tempo por contrato.
- **Esforço:** baixo a médio.
- **Pré-requisito:** alguém com acesso ao LMS precisa abrir o DevTools (aba Rede), fazer uma busca e identificar a requisição que devolve o `id`.

## 4. Ler os dados pela API interna do LMS, sem desenhar a tela

A tela de detalhe é preenchida por requisições JSON. O robô pode chamá-las diretamente com a sessão já logada (`page.request`), sem esperar a página carregar.

- **Ganho:** de 5 a 20 vezes. Cada contrato vira algumas requisições de milissegundos.
- **Esforço:** alto. É preciso mapear as requisições da tela de detalhe, da linha do tempo e do Biz-Drop.
- **Risco:** quebra se o LMS mudar essa API interna, assim como os seletores de tela quebram hoje.
- **Pré-requisito:** o mesmo da opção 3 (captura das requisições no DevTools).

## 5. Ajustes finos

- **Bloquear imagens, fontes e vídeos** com `page.route`. CSS e scripts precisam ficar, porque a coleta verifica a visibilidade dos elementos.
- **Usar os dados que o relatório já traz:** Counterparty, Main Contract Type, Contract type, responsável, `Request Date`, `Effective Date` e `Contract Expiration Date`. A tela de detalhe ficaria só para a linha do tempo, os flags e o Biz-Drop.
- **Ajustar as esperas:** hoje cada tela fica 500 ms "quieta" antes da leitura (`QUIETUDE_DETALHE_MS`), e o Biz-Drop repete essa espera três vezes. Dá para medir e reduzir com segurança.

---

## Recomendação

1. **Primeiro, medir:** registrar nos logs da execução o tempo médio por contrato e por fase (busca, detalhe, Biz-Drop). Assim dá para comparar o ganho de cada mudança no LMS real.
2. **Depois, implementar 1 + 2:** a opção 1 reduz o volume e a 2 acelera o que sobra. As duas podem ser desenvolvidas e testadas sem acesso ao LMS. Com o paralelismo começando em 2 abas, uma execução de rotina deve ficar várias vezes mais rápida.
3. **Por último, 3 e 4:** quando for possível capturar as requisições do LMS no DevTools. São as opções de maior ganho por contrato.
