# Relatório de Confiança — teste_reversa

> Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração).
> **Atualizado em 2026-09-30** após o processamento de 5 das 6 perguntas de `questions.md`.
> Nível de documentação: **Essencial**. Substitui integralmente o relatório de 2026-08-03.
> Revisão cruzada por engine externa: **não realizada** — o nível `essencial` não a oferece, conforme o Passo 0 do agente.

---

## Resumo Geral

Cobre os **9 arquivos canônicos de unit** (3 units × requirements/design/tasks).

| Nível | Quantidade | Percentual |
|-------|-----------|------------|
| 🟢 CONFIRMADO | 509 | 89,6% |
| 🟡 INFERIDO   | 30 | 5,3% |
| 🔴 LACUNA     | 29 | 5,1% |
| **Total**     | **568** | 100% |

**Confiança geral das specs de unit:** **92,3%** — `(509 + 30×0,5) / 568`

Incluindo também os artefatos transversais (`inventory`, `dependencies`, `code-analysis`, `domain`, `architecture`, `c4-context`):

| Escopo | 🟢 | 🟡 | 🔴 | Total | Confiança |
|--------|----|----|----|-------|-----------|
| 9 arquivos de unit | 509 | 30 | 29 | 568 | **92,3%** |
| Artefatos transversais | 206 | 23 | 22 | 251 | 86,7% |
| **Extração completa** | **715** | **53** | **51** | **819** | **90,5%** |

> **Comparação com a extração anterior:** 211 afirmações com 86,3% 🟢. Agora são **819 afirmações** — quase 4× mais — com **90,5%** de confiança. O volume cresceu porque o sistema cresceu: de 887 para 1.170 linhas de Python e de 0 para 7 arquivos de teste.
>
> **Evolução dentro desta sessão:** o relatório nasceu com 826 afirmações e **88,8%**; o processamento das respostas humanas elevou para **90,5%**, com os 🔴 caindo de 58 para 51.

---

## Por Spec

| Spec | 🟢 | 🟡 | 🔴 | Total | Confiança |
|------|----|----|-----|-------|-----------|
| `upload-gedcom/` (requirements+design+tasks) | 139 | 6 | 12 | 157 | 90,4% |
| `analise-dna/` (requirements+design+tasks) | 186 | 12 | 10 | 208 | 92,3% |
| `busca-caminho/` (requirements+design+tasks) | 184 | 12 | 7 | 203 | 93,6% |

**Artefatos transversais:**

| Artefato | 🟢 | 🟡 | 🔴 | Confiança |
|----------|----|----|-----|-----------|
| `inventory.md` | 24 | 2 | 1 | 92,6% |
| `dependencies.md` | 15 | 4 | 3 | 77,3% |
| `code-analysis.md` | 64 | 6 | 9 | 84,8% |
| `domain.md` | 61 | 5 | 4 | 90,7% |
| `architecture.md` | 32 | 5 | 5 | 82,1% |
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

## Resoluções Humanas Aplicadas em 2026-09-30

Cinco das seis perguntas foram respondidas e **aplicadas às specs**. Cada uma converteu 🔴 em 🟢, 🟡 ou em requisito novo.

| Pergunta | Resposta | O que mudou | Lacuna |
| --- | --- | --- | --- |
| **1** `MAX_DEPTH` | Aceitável — preservar fidelidade | `busca-caminho/design.md` registra o corte silencioso como contrato aceito; **nenhum requisito novo** criado, porque a decisão foi não sinalizar | ✅ L-03 fechada |
| **2** `get_spouses` | Intencional — documentar como contrato | `busca-caminho/design.md` promove a varredura condicional a **contrato explícito**, com aviso de que torná-la complementar muda o resultado | ✅ L-02 fechada |
| **3** Entidades decorativas | Arquitetura abandonada — **remover** | **Mudou o código**, não só a spec: `Family`, `GenealogyGraph` e `DNAGroup` removidas de `domain.py` (115 → 84 linhas); 9 testes removidos; suíte 95 → 86 itens | ✅ L-01 e L-11 fechadas |
| **4** Determinismo | Precisa ser determinístico | Novo `RF-14` + requisito não funcional de Reprodutibilidade + `T-19`. **Única divergência deliberada do legado** | ✅ L-13 fechada |
| **5** Faixas de cM | Escritas à mão — declarar heurística | Novo `RF-10a` + `T-20`. `RF-10` permanece 🟢 na *mecânica*; o que caiu foi a autoridade dos números | ✅ L-07 fechada |
| **6** Valor 0,33 | Calibrado — medição **não fornecida** | Nada alterado; a lacuna permanece aberta aguardando o dado | 🔴 L-14 **aberta** |

### Impacto no código (fora das specs)

A resposta 3 exigiu edição do legado, autorizada por `reversa-config.json` (`allowedPaths` cobre `analisador-genealogico/**` e `tests/**`):

| Arquivo | Mudança | Verificação |
| --- | --- | --- |
| `analisador-genealogico/reconstructed/domain.py` | 3 classes removidas + 2 comentários de registro; imports `dataclass`/`field` removidos | 115 → 84 linhas; só `strip_bad_utf` e `demojibake` permanecem |
| `tests/test_domain.py` | 9 testes das classes extintas removidos; docstring documenta a remoção | `pytest --collect-only`: 86 itens (eram 95); **85 passam** |
| — | O único erro de coleta é `PermissionError` do sandbox ao escanear diretórios temporários, reproduzível em qualquer `--basetemp` | restrição de ambiente, **não regressão** |

---

## Lacunas Pendentes 🔴

### upload-gedcom

- **`"Sem Nome"` é inalcançável a partir de `INDI` reais** — o fato está confirmado (0 ocorrências em 55.523 nomes medidos); o que é 🔴 é a intenção de manter um literal morto dentro do contrato.
- **`app.secret_key` hardcoded** — preservar por fidelidade ou externalizar? Não dedutível do código. (Irrelevante em comportamento hoje: não há sessão.)

### analise-dna

- **Origem empírica do valor 0,33** no relaxamento de Jaccard — o usuário indicou ter a medição de calibração, mas ela **ainda não foi fornecida**. A decisão de *manter* o relaxamento é 🟢; o *número* segue 🔴. Pergunta: `questions.md#pergunta-6`.
- **Cobertura de exportadores de CSV** — a regex `[A-Z]{2}\d{7}` é específica de um formato; sem prova de generalidade.

### busca-caminho

- **Famílias adotivas não são representáveis** como laço parental; nenhum tratamento dedicado no legado — cai para a busca indireta, que pode achar afinidade sem significado genealógico.
- **`success=True` com `path_result=None`** — a distinção "sem conexão" × "erro" depende do template, não do contrato do handler.
- **O fuzz do `BUG-20260929-J6PQ` não é teste permanente** — as evidências de 288 payloads e 30.000 nomes vivem em arquivo de adendo, fora da suíte.

> **Fechadas nesta rodada:** L-01, L-02, L-03, L-07, L-11 e L-13. As lacunas 🔴 caíram de 58 para 51 na extração completa.

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

- [ ] **Fornecer a medição de calibração do 0,33** — é a **única pergunta ainda em aberto** (`questions.md#pergunta-6`). Tudo o mais que dependia de decisão humana já foi respondido e aplicado. É um dado que só você tem; sem ele a lacuna `L-14` não fecha.
- [ ] **Fixar as versões das dependências antes de qualquer reimplementação.** `thefuzz` delega a `RapidFuzz`/`python-Levenshtein`; trocar versão **altera o resultado do matching sem mudar uma linha de código** (`RISK-006`). É a mitigação de maior retorno e menor custo do projeto.
- [ ] **Promover o fuzz do `BUG-20260929-J6PQ` a teste permanente.** Hoje a evidência de 288 payloads combinados e 30.000 nomes está em arquivo de adendo; se o adendo sair do radar, o contrato de escape fica sem rede de proteção.
- [ ] **`analise-dna` é a unit de maior risco.** 25 regras, 6 ramos de aceitação interdependentes, e a única unit em que uma diferença de biblioteca muda o resultado. Priorizar a revisão humana nela.
- [ ] **Atenção à `T-19` (determinismo).** É a **única tarefa que diverge de propósito do legado**. Quem reimplementar deve saber que ali não se preserva comportamento — se corrige um defeito.
- [ ] **Conferir o estado do repositório antes de commitar.** Esta rodada editou código do legado (`domain.py`, `test_domain.py`) por decisão sua. A suíte tem 86 itens e 85 passam; o erro restante é do sandbox, não do código.
- [ ] **A lacuna do Git está fechada.** `_reversa_docs/` e `.reversa/chronicle.md` podem agora referenciar `domain.md §7` como fonte de ADRs retroativos.
- [ ] **Atualizar o `README.md` de `analisador-genealogico/`** — ainda anuncia `Pyvis`, removida do projeto (`code-analysis.md` §6, dívida #8).

---

*Gerado pelo Reversa-Reviewer em 2026-09-30 (re-extração).*
