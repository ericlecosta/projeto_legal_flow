# Notas de trabalho: Atividade de Agentes Inteligentes

Registro do que foi pensado e decidido até agora, para continuar o trabalho em outra máquina.
**Última atualização:** 01/10/2026

---

## 1. Enunciado da atividade (professor)

Cada equipe deve discutir e elaborar uma possível estratégia para uso de agentes inteligentes no projeto. Não é obrigatória nenhuma implementação.

Itens 1 a 3 refletem o projeto atual:

1. Fundamentação do projeto: detalhamento do problema e escopo atual, escrito e com fluxo em diagrama.
2. Objetivos geral e específicos.
3. Artefatos finais do projeto (entregáveis).

A partir do item 4, o que precisaria mudar para usar agentes:

4. Mudanças no escopo que tornariam possível usar agentes no processo. Alterar o diagrama.
5. Tipo de arquitetura de agente para resolver o problema (a partir da leitura dos artigos indicados).
6. Quantos agentes seriam necessários, possíveis modelos LLM offline, objetivo de cada agente, dados requeridos e saída esperada de cada um.

Entrega: **um único arquivo por equipe**, enviado por uma só pessoa, indicando os integrantes.

---

## 2. Arquivos desta pasta

| Arquivo | O que é |
| :--- | :--- |
| `Estrategia_Agentes_Inteligentes.md` | Fonte do documento de entrega (editar aqui) |
| `Estrategia_Agentes_Inteligentes.docx` / `.pdf` | Documento de entrega gerado a partir do `.md` |
| `img/01_fluxo_atual.png` | Item 1: fluxo AS-IS × escopo atual do robô |
| `img/02_fluxo_com_agentes.png` | Item 4: fluxo alterado com agentes |
| `img/03_arquitetura_agentes.png` | Item 5: arquitetura |
| `img/04_agente_validador.png` | Item 6.2: detalhamento do Agente Validador |
| `scripts/diagramas.py` | Gera os 4 diagramas (matplotlib) |
| `scripts/md2docx.py` | Converte o `.md` em `.docx` no padrão visual dos outros documentos do projeto |

### Como regerar

```bash
cd "docs/Atividade - Agentes Inteligentes"
python scripts/diagramas.py img
python scripts/md2docx.py "../1 - Desafio/Desafio.docx" Estrategia_Agentes_Inteligentes.md Estrategia_Agentes_Inteligentes.docx "Estratégia de Agentes Inteligentes"
```

- Dependências: `matplotlib`, `python-docx`, `Pillow`.
- O `Desafio.docx` é usado só como modelo (cabeçalho, rodapé e estilos).
- O PDF foi exportado pelo Word (Salvar como PDF). No Windows, dá para fazer pelo PowerShell com `Word.Application` → `ExportAsFixedFormat(caminho, 17)`.

> **Atenção:** o `.gitignore` do repositório ignora `*.png` (linha 48). Sem uma exceção, as imagens desta pasta **não vão para o Git**. Na outra máquina, basta rodar `scripts/diagramas.py` para recriá-las.

---

## 3. Ideia central da estratégia

O **RPA continua cuidando do que é fixo** (login, filtros, download). Os **agentes entram onde há ambiguidade, texto livre ou decisão**. As etapas do RPA viram *ferramentas* chamadas pelos agentes.

Guardrails: somente leitura no LMS, credenciais no `.env`, **modelos locais e offline** (LGPD e sigilo contratual), o LLM não altera dados sozinho e toda decisão fica em log.

---

## 4. Banco de ideias (brainstorm)

1. **Interpretar o Approval History.** Ler a timeline em texto livre e decidir qual evento vira qual das 8 datas.
2. **Navegação que se adapta (*self-healing*).** Quando um seletor quebra, olhar a tela ou o DOM e achar o elemento certo.
3. **Validar a base.** ✅ *Escolhida para detalhamento (ver seção 6).*
4. **Classificar contratos MAO** nos casos ambíguos.
5. **Resumo executivo no e-mail** (novos, concluídos, rejeitados, parados).
6. **Alertar gargalos** (contrato parado muito tempo em uma etapa).
7. **Perguntas em linguagem natural** da gestora sobre a base.
8. **Orquestrar a execução** (repetir, pular ou escalar).
9. **Diagnosticar falhas** a partir de logs e screenshots.
10. **Ajudar a definir o De/Para** analisando a base manual antiga (dúvidas D1 e D7 da Matriz CSD).
11. **Fila de revisão humana** com justificativa e nível de confiança.
12. **Conferir a LGPD** em logs e saídas.

**Arquiteturas consideradas:** Supervisor (orquestrador–trabalhadores), ReAct, Avaliador–Otimizador e híbrido RPA + agente. → **Escolhida:** Orquestrador–Trabalhadores com ReAct, Avaliador–Otimizador (Validador ↔ Extrator) e Human-in-the-Loop.

**Modelos offline considerados:**
- Texto e ferramentas: Qwen2.5 7B/14B, Llama 3.1 8B, Mistral 7B.
- Visão: Qwen2.5-VL 7B.
- Leves: Phi-4-mini, Llama 3.2 3B.
- Servir os modelos: Ollama ou vLLM. Orquestrar: LangGraph ou CrewAI (escolhido: LangGraph).

---

## 5. Os 5 agentes propostos

| Agente | Papel | Modelo |
| :--- | :--- | :--- |
| 1. Orquestrador | Planeja, delega, decide retry ou escalonamento | Qwen2.5 7B / Llama 3.1 8B |
| 2. Navegador | Navega no LMS com *self-healing* de seletores | Qwen2.5-VL 7B |
| 3. Extrator | Converte a timeline nas 8 datas + Progress State (JSON) | Qwen2.5 7B / Mistral 7B |
| 4. Validador | Regras + comparação + LLM; separa exceções | Pandas + Phi-4-mini / Llama 3.2 3B |
| 5. Analista | Resumo, alertas e perguntas da gestora | Qwen2.5 14B / Llama 3.1 8B |

---

## 6. Detalhamento da ideia 3: Agente Validador

**Motivação:** com o robô, o risco deixa de ser o erro de digitação e passa a ser o **erro silencioso** (mudança no LMS, De/Para errado, timeline incompleta).

**Exemplos reais na `Base Ideal.xlsx` (linha de exemplo da aba Ideal Raw):**
- `Biz-Drop Completed = "Data"` (texto no lugar de data);
- `Amount = "9.240.61"` (valor mal formatado);
- `End date` (18/04/2026) anterior às datas de revisão (maio/junho).

**3 camadas:**
1. **Regras (Pandas):** formato, obrigatórios, domínio (11 estados), ordem cronológica das 8 datas, coerência estado × datas, duplicidade, marcador MAO.
2. **Comparação com a base anterior:** datas antigas que mudaram, regressão de estado, contratos que sumiram, volume anormal, nulos em massa.
3. **LLM:** explica em português, classifica a gravidade (🔴 bloqueia · 🟡 alerta · 🟢 informativo) e investiga com ReAct (logs, screenshots).

**Ordem das 8 datas (para a regra cronológica):** Request Date ≤ Request Legal Review ≤ Review completed ≤ Agreement request ≤ Agreement has been completed ≤ Approval request ≤ Approval request completed ≤ Register the conclusion of contract.

**Saídas:** base aprovada ou bloqueada, relatório de qualidade no e-mail, fila de exceções em JSON ou na aba "Exceções" e score de confiança da base.

**Métricas:** % de contratos para revisão humana (meta: abaixo de 5%), taxa de falsos positivos, erros pegos antes da gestora e tempo da analista.

**Riscos:** excesso de alertas (calibrar com a analista), alucinação do LLM (sempre citar a regra e o valor) e LGPD (prompt sem nomes de pessoas).

---

## 7. Pendências

- [ ] **Artigos indicados pelo orientador:** a seção 5 e as Referências do documento estão marcadas com **[A ajustar]**. Hoje elas citam ReAct (Yao et al., 2023), *Building Effective Agents* (Anthropic, 2024), AutoGen (Wu et al., 2023) e LangGraph.
- [ ] Confirmar a lista de integrantes. Hoje estão Sannyer Carvalho, Kauã Sales, Ericle Luna e Daniele Greice. Na tabela de `0 - Dados da Equipe` falta o integrante nº 2.
- [ ] Revisar com a equipe se mantém os 5 agentes ou reduz (por exemplo, Analista como opcional).
- [ ] Validar a ordem cronológica das datas e a matriz de transições de estado com a gestora.
- [ ] Decidir se as imagens de `docs/` devem entrar no Git (exceção no `.gitignore`, como `!docs/**/*.png`).

### Pendências de outras pastas (fora desta atividade)

- [ ] `3 - Documentação do Cliente/Documentacao_do_Cliente.docx`: trocar o bloco ASCII da seção **4.1 Matriz Poder × Interesse** pela imagem `matriz_poder_interesse.png` e reexportar o PDF. O `.md` já foi atualizado; o `.docx` estava aberto no Word e não pôde ser alterado.
- [x] `1 - Desafio`: diagrama de Ishikawa (6M) substituído por espinha de peixe (`ishikawa_6m.png`), com `.docx` e `.pdf` atualizados.
