# Relatório de Confiança — teste_reversa

> Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração).
> Nível de documentação: **Essencial**. Substitui integralmente o relatório de 2026-08-03.
> Revisão cruzada por engine externa: **não realizada** — o nível `essencial` não a oferece, conforme o Passo 0 do agente.

---

## Resumo Geral

Cobre os **9 arquivos canônicos de unit** (3 units × requirements/design/tasks).

| Nível | Quantidade | Percentual |
|-------|-----------|------------|
| 🟢 CONFIRMADO | 496 | 89,2% |
| 🟡 INFERIDO   | 32 | 5,8% |
| 🔴 LACUNA     | 28 | 5,0% |
| **Total**     | **556** | 100% |

**Confiança geral das specs de unit:** **92,1%** — `(496 + 32×0,5) / 556`

Incluindo também os artefatos transversais (`inventory`, `dependencies`, `code-analysis`, `domain`, `architecture`, `c4-context`):

| Escopo | 🟢 | 🟡 | 🔴 | Total | Confiança |
|--------|----|----|----|-------|-----------|
| 9 arquivos de unit | 496 | 32 | 28 | 556 | **92,1%** |
| Artefatos transversais | 203 | 37 | 30 | 270 | 82,0% |
| **Extração completa** | **699** | **69** | **58** | **826** | **88,8%** |

> **Comparação com a extração anterior:** 211 afirmações com 86,3% 🟢. Agora são **826 afirmações** — quase 4× mais — com 88,8% de confiança. O volume cresceu porque o sistema cresceu: de 887 para 1.201 linhas de Python e de 0 para 7 arquivos de teste.

---

## Por Spec

| Spec | 🟢 | 🟡 | 🔴 | Total | Confiança |
|------|----|----|-----|-------|-----------|
| `upload-gedcom/` (requirements+design+tasks) | 138 | 8 | 12 | 158 | 89,9% |
| `analise-dna/` (requirements+design+tasks) | 176 | 11 | 8 | 195 | 93,1% |
| `busca-caminho/` (requirements+design+tasks) | 182 | 13 | 8 | 203 | 92,9% |

**Artefatos transversais:**

| Artefato | 🟢 | 🟡 | 🔴 | Confiança |
|----------|----|----|-----|-----------|
| `inventory.md` | 24 | 2 | 1 | 92,6% |
| `dependencies.md` | 15 | 4 | 3 | 77,3% |
| `code-analysis.md` | 58 | 12 | 10 | 79,1% |
| `domain.md` | 60 | 5 | 5 | 91,4% |
| `architecture.md` | 31 | 9 | 6 | 76,7% |
| `c4-context.md` | 10 | 1 | 0 | 95,5% |

---

## Verificações de Consistência Executadas

| Verificação | Método | Resultado |
| --- | --- | --- |
| Os 3 arquivos canônicos existem em cada unit | varredura do sistema de arquivos | ✅ 9/9 presentes |
| Units geradas == `surface.json.modules` | comparação de conjuntos | ✅ 3/3; nada faltando nem sobrando |
| Nenhuma afirmação funcional sobre símbolos extintos | varredura de `HARD_MIN`, `GIVEN_MIN`, `process_dna`, `given_index`, `Pyvis` | ✅ as 6 ocorrências são **avisos de "não fazer isso"**, não afirmações de comportamento |
| Globais do nível `essencial` não gerados indevidamente | verificação de existência | ✅ `code-spec-matrix.md`, `spec-impact-matrix.md`, `gaps.md`, `openapi/` e `user-stories/` ausentes — corretos para o nível |
| Valores-contrato coerentes entre units | busca de `MAX_DEPTH`, `MAX_HOPS`, limiares de Jaccard, faixas de cM | ✅ cada constante definida numa única unit e referenciada, nunca redefinida |
| Contagem de RFs confere com o publicado | contagem de linhas `\| RF-nn \|` | ✅ 12 / 13 / 15 |
| Dependências declaradas entre units são reais | confronto com o grafo de imports | ✅ `analise-dna` → `busca-caminho` → `upload-gedcom`; nenhuma dependência circular |

---

## Lacunas Pendentes 🔴

### upload-gedcom

- **`Family`, `GenealogyGraph` e `DNAGroup` nunca são instanciadas** — confirmado por varredura; o *motivo* (abandono ou preparação) não é dedutível do código. Pergunta: `questions.md#pergunta-3`.
- **`GenealogyGraph` documenta `networkx.MultiGraph`, mas o grafo real é `nx.Graph`** — contradição entre comentário e código (`domain.py:77`). É intenção, não comportamento.
- **`"Sem Nome"` é inalcançável a partir de `INDI` reais** — o fato está confirmado; o que é 🔴 é a intenção de manter um literal morto dentro do contrato.
- **`app.secret_key` hardcoded** — preservar por fidelidade ou externalizar? Não dedutível.

### analise-dna

- **Fonte e versão da tabela de faixas de cM** — nenhuma citação no código; e as faixas se sobrepõem de forma atípica. Pergunta: `questions.md#pergunta-5`.
- **Determinismo do desempate de candidatos** — a ordem de iteração de `set` varia com `PYTHONHASHSEED`; não há critério final determinístico. Pergunta: `questions.md#pergunta-4`.
- **Cobertura de exportadores de CSV** — a regex `[A-Z]{2}\d{7}` é específica de um formato; sem prova de generalidade.
- **Base empírica do valor 0,33** no relaxamento de Jaccard — a decisão de *manter* é 🟢; o *número* é 🔴. Pergunta: `questions.md#pergunta-6`.

### busca-caminho

- **`MAX_DEPTH = 20` conta iterações, não gerações** — o fato é 🟢; 🔴 é o efeito prático do corte e a ausência de sinalização ao usuário. Pergunta: `questions.md#pergunta-1`.
- **`get_spouses` só faz a varredura global se nenhum `FAMS` resolveu** — intencional ou acidente? Pergunta: `questions.md#pergunta-2`.
- **Famílias adotivas não são representáveis** como laço parental; nenhum tratamento dedicado no legado.
- **`success=True` com `path_result=None`** — a distinção "sem conexão" × "erro" depende do template, não do contrato do handler.
- **O fuzz do `BUG-20260929-J6PQ` não é teste permanente** — as evidências de 288 payloads e 30.000 nomes vivem em arquivo de adendo, fora da suíte.

---

## Histórico de Reclassificações

### Contra a extração anterior — correções aplicadas nesta re-extração

| De | Para | Afirmação | Evidência |
|----|------|-----------|-----------|
| 🟢 | 🔴 | `HARD_MIN=92` / `GIVEN_MIN=90` existem como código morto "em `app.py:653-654`" | **Não existem** em nenhum arquivo de `analisador-genealogico/` — varredura: 0 ocorrências. Eram código morto do **monolito original** (`oracle/app_legacy_e43ca22.py:653-654`) e a reconstrução nunca os implementou. |
| 🟢 | 🔴 | "cM ≤ 0 ou não numérico retorna 'Relação distante ou indeterminada'" | Falso. `dna_analysis.py:62-64` devolve **lista vazia**. O literal só aparece com valor positivo fora de todas as faixas. Correção herdada de `migration/ambiguity_log.md#AMB-023`. |
| 🟢 | 🔴 | A `action` de análise de DNA é `process_dna` | Falso. `app.py:44` usa `dna_analysis`. `process_dna` não existe no código. |
| 🟢 | 🟡 | `given_index` é um índice a construir | Removido por prova de morte em `OPP-20260929-32Q7` — nenhum ponto do código o lia. Hoje existe o cache `features`. |
| 🟢 | 🟡 | "Profundidade máxima de 20 **níveis**" | `MAX_DEPTH` conta **iterações de profundidade** do BFS bidirecional, não gerações. |
| 🔴 | 🟢 | "Não há repositório Git — ADRs retrospectivos impossíveis" | O repositório tem **66 commits**. 8 ADRs reconstruídos em `domain.md §7`. |
| 🔴 | 🟢 | "Sem cobertura de testes do matching" | Existem `test_characterization_matching.py` (3 testes) e `test_characterization_mermaid.py` (2). |
| 🟢 | 🟢 | Referências de linha das specs | **Todas** estavam obsoletas — apontavam para `app.py:653-654`, `:853`, `:297-318`, que deixaram de existir quando o núcleo migrou para `reconstructed/` (ADR-02). Reescritas e reconferidas. |

### Upgrades internos desta re-extração

| De | Para | Afirmação | Evidência |
|----|------|-----------|-----------|
| 🟡 | 🟢 | Contrato de escape do rótulo Mermaid — lista branca, entidades **depois** do filtro | `path_search.py:201-214`; `tests/test_mermaid_escape.py` (6 testes); commit `c709ea0` |
| 🟡 | 🟢 | `COMMON_SURNAMES` tem `"souza"` duplicado | Contagem por AST: 16 itens, 15 únicos |
| 🟡 | 🟢 | `Family`, `GenealogyGraph` e `DNAGroup` não são instanciadas em produção | Varredura de referências: aparecem apenas nas próprias definições |
| 🟢 | 🟢 | Mapa de mojibake de `strip_bad_utf` tem 18 pares | Contagem por AST (a própria re-extração havia escrito 13 por erro, corrigido durante a análise) |

---

## Recomendações

- [ ] **Responder `questions.md`** — são 6 perguntas, mas apenas **3 bloqueiam** a reimplementação fiel: a **#1** (corte silencioso do `MAX_DEPTH`), a **#2** (`get_spouses` condicional) e a **#3** (entidades decorativas). As #4, #5 e #6 são de qualidade, não de bloqueio.
- [ ] **Fixar as versões das dependências antes de qualquer reimplementação.** `thefuzz` delega a `RapidFuzz`/`python-Levenshtein`; trocar versão **altera o resultado do matching sem mudar uma linha de código** (`RISK-006`). É a mitigação de maior retorno e menor custo do projeto.
- [ ] **Promover o fuzz do `BUG-20260929-J6PQ` a teste permanente.** Hoje a evidência de 288 payloads combinados e 30.000 nomes está em arquivo de adendo; se o adendo sair do radar, o contrato de escape fica sem rede de proteção.
- [ ] **`analise-dna` é a unit de maior risco.** 25 regras, 6 ramos de aceitação interdependentes, e a única unit em que uma diferença de biblioteca muda o resultado. Priorizar a revisão humana nela.
- [ ] **As 4 decisões de 2026-08-03 não são pendências** — foram verificadas contra o código atual e continuam válidas (`questions.md`, seção final).
- [ ] **A lacuna do Git está fechada.** `_reversa_docs/` e `.reversa/chronicle.md` podem agora referenciar `domain.md §7` como fonte de ADRs retroativos.
- [ ] **Atualizar o `README.md` de `analisador-genealogico/`** — ainda anuncia `Pyvis`, removida do projeto (`code-analysis.md` §6, dívida #8).

---

*Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração).*
