# busca-caminho, Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=path_search`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui as tasks de 2026-08-03.

## Pré-requisitos

- [ ] Dependências: `networkx` 3.6.1, `Flask` 3.1.3 🟢
- [ ] Unit `upload-gedcom` implementada: `people`, `families`, `child_to_family`, `graph`, `get_name` e `ref_id` disponíveis 🟢
- [ ] A global `graph` precisa ser obtida por **import tardio dentro da função** — um import no topo capturaria `None` para sempre, porque `upload` faz rebind dela 🟢
- [ ] `templates/index.html` renderizando Mermaid com `securityLevel: 'strict'` 🟢
- [ ] **Não aplicável:** schema/migrations de banco 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

### Entrada e resolução de pessoas

- [ ] **T-01**, Validar GEDCOM carregado, existência em disco e re-parse antes da busca
  - Origem no legado: `analisador-genealogico/app.py:36-42`
  - Critério de pronto: sem `gedcom_filename` → `"Erro: Arquivo GEDCOM não encontrado."`; arquivo removido → `"Erro: Arquivo '{nome}' não existe mais."`; caso contrário, árvore recarregada
  - Confiança: 🟢

- [ ] **T-02**, Implementar `find_person_by_name` em duas passadas
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:30-35`
  - Critério de pronto: igualdade `case-insensitive` primeiro; substring só se a igualdade não devolver nada
  - Confiança: 🟢

- [ ] **T-03**, Reportar por pessoa quando o nome não resolve, e usar o primeiro id
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:472-479`
  - Critério de pronto: `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` com `success=False`; caso contrário, `ids[0]`
  - Confiança: 🟢
  - ⚠️ **Não implementar desambiguação de homônimos.** Decisão do usuário (`questions.md#2`).

### Navegação familiar

- [ ] **T-04**, Implementar `get_parents` com `FAMC` preferencial e fallback no índice
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:42-61`
  - Critério de pronto: usa `FAMC` se existir; senão `child_to_family`; coleta todos os `HUSB`/`WIFE` das famílias, sem duplicar
  - Confiança: 🟢

- [ ] **T-05**, Implementar `get_spouses` com o fallback **condicional**
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:64-88`
  - Critério de pronto: caminho por `FAMS`; a varredura global de `families` só roda se `spouse_ids` ficou **vazio**
  - Confiança: 🟢
  - ⚠️ Reproduzir a condicional exatamente. Trocar por "sempre varre" muda o comportamento em árvores com `FAMS` parcial.

- [ ] **T-06**, Implementar `are_spouses`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:91-92`
  - Critério de pronto: `b_id in set(get_spouses(a_id))`
  - Confiança: 🟢

### Conexão direta

- [ ] **T-07**, Implementar o BFS bidirecional por pais (`find_ancestral_path`)
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:144-178`
  - Critério de pronto: duas filas alternando um nível cada; devolve `(path, common_ancestor)` ou `(None, None)`; `start == end` devolve `([id], id)`
  - Confiança: 🟢
  - ⚠️ O teto `MAX_DEPTH = 20` conta **iterações de profundidade**, não gerações. Não reinterpretar.

- [ ] **T-08**, Implementar o teto `MAX_DEPTH = 20` com corte silencioso
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:22`, `:153`, `:178`
  - Critério de pronto: caminho mais fundo que o teto devolve `(None, None)` sem erro nem aviso
  - Confiança: 🟢

### Conexão indireta

- [ ] **T-09**, Implementar `find_indirect_path` com `shortest_path` e compressão
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:126-141`
  - Critério de pronto: `nx.shortest_path` não ponderado; rejeita se `len(path)-1 > MAX_HOPS`; devolve só ids de pessoa; exige ≥ 2
  - Confiança: 🟢
  - ⚠️ O `from .upload import graph` deve ficar **dentro** da função.

- [ ] **T-10**, Implementar o teto `MAX_HOPS = 40`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:23`, `:136-137`
  - Critério de pronto: caminho com mais de 40 arestas é rejeitado
  - Confiança: 🟢

- [ ] **T-11**, Tratar `NetworkXNoPath` e `NodeNotFound` como ausência de caminho
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:140-141`
  - Critério de pronto: exceções do networkx devolvem `None`, nunca propagam
  - Confiança: 🟢

### Ponte matrimonial

- [ ] **T-12**, Implementar `split_path_by_marriage`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:95-103`
  - Critério de pronto: devolve `(left, right, (a, b))` no **primeiro** par adjacente de cônjuges; `(None, None, None)` se não houver
  - Confiança: 🟢

- [ ] **T-13**, Implementar `pick_spouse_for_couple` e `exclude_tail`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:106-119`
  - Critério de pronto: prefere cônjuge presente em `candidate_path`; senão o primeiro; `exclude_tail` devolve `[]` quando `len(seq) <= n`
  - Confiança: 🟢

### Renderização Mermaid

- [ ] **T-14**, Implementar `_mermaid_sid`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:185-190`
  - Critério de pronto: coleção → primeiro elemento; remove `@`; `+` → `_`; remove tudo fora de `[a-zA-Z0-9_]`; prefixa `N_`
  - Confiança: 🟢

- [ ] **T-15**, Implementar `_mermaid_label` com **lista branca** e a ordem correta
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:201-214`
  - Critério de pronto: NFC → normaliza NBSP/travessões/aspas curvas → `"` vira `'` → achata quebras de linha → **lista branca** → **depois** `&`,`<`,`>` como entidades
  - Confiança: 🟢
  - ⚠️ **A ordem é o contrato.** Filtro antes das entidades. Inverter reintroduz o `BUG-20260929-J6PQ`.

- [ ] **T-16**, Emitir o diagrama da conexão direta (`generate_mermaid_graph`)
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:217-263`
  - Critério de pronto: `flowchart BT`; nó "casal" quando o ancestral não é extremidade; arestas na direção correta conforme `ac_idx`; `style` de P1 (verde), P2 (vermelho) e ancestral (amarelo)
  - Confiança: 🟢

- [ ] **T-17**, Emitir o diagrama de ponte (`generate_mermaid_graph_indirect_bridge`)
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:266-456`
  - Critério de pronto: dois ramos em subgrafos de colunas; âncoras transparentes; aresta `--- |Casamento| ---`; `style` de A e B; **três delegações** para `generate_mermaid_graph` quando faltar pré-requisito (`:281`, `:290`, `:376`)
  - Confiança: 🟢

### Fluxo e saída

- [ ] **T-18**, Implementar `path_search` orquestrando direta → indireta
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:463-502`
  - Critério de pronto: direta tem precedência; indireta só se a direta falhar; mensagens exatas; `text_path` unido por `" → "`
  - Confiança: 🟢

- [ ] **T-19**, Distinguir ausência de conexão de erro de entrada via `success`
  - Origem no legado: `analisador-genealogico/reconstructed/path_search.py:488-491` e `app.py:71-73`
  - Critério de pronto: sem conexão → `(None, msg, True)`; pessoa não encontrada → `(None, msg, False)`
  - Confiança: 🟡

- [ ] **T-20**, Tratar exceções com erro amigável na rota
  - Origem no legado: `analisador-genealogico/app.py:76-78`
  - Critério de pronto: exceção → `"Ocorreu um erro: {e}"` com `success=False`
  - Confiança: 🟢

## Tarefas de Teste

O legado **já tem** estes testes:

- [ ] **TT-01**, Resolução de pessoa por nome (`test_person_lookup`) 🟢
- [ ] **TT-02**, Conexão direta trivial e com ancestral comum (`test_direct_connection_trivial`, `test_direct_connection_common_ancestor`) 🟢
- [ ] **TT-03**, Fluxo completo da busca direta (`test_path_search_direct`) 🟢
- [ ] **TT-04**, Conexão indireta via casamento (`test_indirect_connection_via_marriage`) 🟢
- [ ] **TT-05**, `find_indirect_path` isoladamente (`test_indirect_path_function`) 🟢
- [ ] **TT-06**, Pessoa não encontrada (`test_person_not_found`) 🟢
- [ ] **TT-07**, Sem conexão (`test_no_connection`) 🟢
- [ ] **TT-08**, Pessoas idênticas (`test_identical_persons`) 🟢
- [ ] **TT-09**, **Escape do rótulo: crase neutralizada** (`test_rotulo_neutraliza_crase`) 🟢
- [ ] **TT-10**, **Nenhum caractere que quebra a gramática sobrevive** (`test_diagrama_nao_carrega_caractere_que_quebra_a_gramatica`) 🟢
- [ ] **TT-11**, **Entidades HTML preservadas** (`test_entidades_html_preservadas`) 🟢
- [ ] **TT-12**, **Caracteres legítimos sobrevivem** (`test_caracteres_legitimos_sobrevivem`) 🟢
- [ ] **TT-13**, Neutralizações pré-existentes e rótulo vazio (`test_neutralizacoes_que_ja_existiam`, `test_rotulo_vazio_continua_vazio`) 🟢
- [ ] **TT-14**, Caracterização da saída Mermaid (`test_saida_mermaid_caracterizada`, `test_rotulo_com_caracteres_de_escape`) 🟢
- [ ] **TT-15**, Fuzz de rótulo com payloads hostis combinados e varredura de 30.000 nomes — **reproduzir como teste de regressão** (hoje vive como evidência do adendo `bug-J6PQ`, não como teste permanente) 🟡
- [ ] **TT-16**, Teste do teto de `MAX_DEPTH` e de `MAX_HOPS` (não existe no legado — criar) 🟡

## Tarefas de Migração de Dados

**Não aplicável** — sem banco de dados, sem volume a migrar. 🟢

## Ordem Sugerida

1. **T-04, T-05, T-06 (navegação familiar) primeiro.** São a base do BFS e das pontes; não dependem de grafo, só dos dicionários.
2. **T-02, T-03 (resolução de pessoas).** Independentes, testáveis isoladamente.
3. **T-07, T-08 (conexão direta).** Dependem de T-04.
4. **T-09, T-10, T-11 (conexão indireta).** Dependem da global `graph` e de T-13.
5. **T-12, T-13 (ponte matrimonial).** T-12 depende de T-06.
6. **T-14, T-15 (escape do rótulo).** Podem ser feitos em paralelo a qualquer momento — são funções puras. Devem ser feitos **antes** de T-16/T-17.
7. **T-16, T-17 (diagramas).** Dependem de T-14, T-15 e T-13.
8. **T-18, T-19, T-20 (fluxo e rota) por último.**
9. **Bloqueios:** nada aqui funciona sem a unit `upload-gedcom`. A unit `analise-dna` depende de T-07 e T-16 desta unit.

## Lacunas Pendentes (🔴)

- **L-02:** `get_spouses` só faz varredura global se nenhum `FAMS` resolveu — intencional ou acidente?
- **L-06:** `success=True` com `path_result=None` — o template distingue "sem conexão" de "erro"?
- **L-03:** o teto de 20 conta iterações, não gerações; o efeito prático do corte não está documentado.
- **L-15:** política de homônimos — aceita pelo usuário, mas não há desambiguação nem aviso ao usuário de que uma pessoa diferente poderia ter sido escolhida.
- **L-16:** `TT-15` e `TT-16` não existem como testes permanentes; as evidências de fuzz do `bug-J6PQ` estão em arquivo de adendo, não na suíte.
- **Já decididas, não são pendências:** homônimos usam o 1º ID (`questions.md#2`); famílias adotivas não têm tratamento dedicado (limitação conhecida do legado).

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
