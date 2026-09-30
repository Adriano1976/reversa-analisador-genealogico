# busca-caminho, Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=path_search`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui o design de 2026-08-03.

## Interface

### Endpoint HTTP (formulário)

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/` | `action=path_search`, `gedcom_filename`, `person1_name`, `person2_name` | `index.html` com `path_result` ou `message` | 200 sempre 🟢 |

### Símbolos do núcleo

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `path_search` | `(person1_name: str, person2_name: str)` | `(path_result \| None, msg, success)` | Fluxo completo 🟢 |
| `find_person_by_name` | `(name_query)` | `list[str]` | Passada exata, depois substring 🟢 |
| `find_ancestral_path` | `(start_id, end_id, max_depth=20)` | `(path, common_ancestor)` ou `(None, None)` | BFS bidirecional por pais 🟢 |
| `find_indirect_path` | `(start_id, end_id, max_hops=40)` | `list[str]` ou `None` | `nx.shortest_path` com compressão 🟢 |
| `get_parents` | `(person_id)` | `list[str]` | `FAMC` preferencial, fallback `child_to_family` 🟢 |
| `get_spouses` | `(person_id)` | `list[str]` | `FAMS`; varredura global só se `spouse_ids` ficou **vazio** — contrato explícito, ver nota 🟢 |
| `are_spouses` | `(a_id, b_id)` | `bool` | `b in set(get_spouses(a))` 🟢 |
| `split_path_by_marriage` | `(person_path)` | `(left, right, (a,b))` ou `(None, None, None)` | Primeiro par adjacente 🟢 |
| `pick_spouse_for_couple` | `(person_id, candidate_path=None)` | `str \| None` | Prefere cônjuge já no caminho 🟢 |
| `exclude_tail` | `(seq, n=1)` | `list` | Evita duplicar o ancestral na ponta 🟢 |
| `_mermaid_sid` | `(raw)` | `str` | Id de nó seguro, prefixo `N_` 🟢 |
| `_mermaid_label` | `(txt)` | `str` | Rótulo com lista branca + entidades HTML 🟢 |
| `generate_mermaid_graph` | `(path, p1_id, p2_id, common_ancestor_id)` | `str` | Diagrama da conexão direta 🟢 |
| `generate_mermaid_graph_indirect_bridge` | `(p1_id, p2_id, person_path)` | `str` | Diagrama de ponte 🟢 |

### Contrato de retorno

| Campo de `path_result` | Conteúdo |
|------------------------|----------|
| `person1_name` / `person2_name` | Nomes já com `strip()` 🟢 |
| `text_path` | Nomes unidos por `" → "` 🟢 |
| `mermaid_data` | Texto do diagrama Mermaid 🟢 |

### Constantes

| Constante | Valor | Papel |
|-----------|-------|-------|
| `MAX_DEPTH` | `20` | Iterações de profundidade do BFS bidirecional 🟢 |
| `MAX_HOPS` | `40` | Arestas máximas do caminho indireto 🟢 |
| `_LABEL_SEGURO` | `[^0-9A-Za-zÀ-ÖØ-öø-ÿ .,'()&<>:;/\[\]!?-]` | Regex de **lista branca** 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:65-78`)

1. `app.py:36-42` — herdado: valida `gedcom_filename`, existência em disco e **re-parseia** a árvore. 🟢
2. `app.py:67-68` — lê `person1_name` e `person2_name` com `strip()`. 🟢
3. `app.py:70` — chama `path_search_flow(person1_name, person2_name)`. 🟢
4. `app.py:71-73` — se `not success and path_result is None` → renderiza com a mensagem, `success=False`. 🟢
5. `app.py:74-75` — caso contrário, renderiza com `path_result` e `success=True`. 🟢
6. `app.py:76-78` — exceção → `"Ocorreu um erro: {e}"`, `success=False`. 🟢

### Núcleo (`path_search.py:463-502`)

1. `:469-470` — `strip()` nos dois nomes. 🟢
2. `:472-473` — resolve as duas listas de ids. 🟢
3. `:474-477` — lista vazia → `(None, "Pessoa N '{nome}' não encontrada.", False)`. 🟢
4. `:479` — `p1_id, p2_id = p1_ids[0], p2_ids[0]` — **primeiro id, homônimos ignorados**. 🟢
5. `:481` — `find_ancestral_path(p1_id, p2_id)`. 🟢
6. `:482-485` — sucesso → nomes, `generate_mermaid_graph`, `"Conexão direta encontrada (ancestral comum)."` 🟢
7. `:486-491` — senão, `find_indirect_path`; sem caminho → `(None, "Nenhuma conexão encontrada entre ...", True)`. 🟢
8. `:492-494` — com caminho → `generate_mermaid_graph_indirect_bridge`, `"Conexão indireta encontrada (via casamento/afinidade)."` 🟢
9. `:496-502` — monta `path_result` com `text_path` unido por `" → "` e devolve. 🟢

### BFS bidirecional (`find_ancestral_path`, `:144-178`)

1. `:149-150` — duas filas `deque([(id, [id])])` e dois mapas `visited` com o caminho até cada nó. 🟢
2. `:151-152` — `start_id == end_id` → `([start_id], start_id)`. 🟢
3. `:153-165` — **primeiro turno:** expande um nível de `q1`; se um nó já está em `visited2`, concatena `path + visited2[curr][::-1][1:]` e devolve com o ancestral. 🟢
4. `:166-177` — **segundo turno:** mesma lógica do lado de `q2`, concatenando `visited1[curr] + path[::-1][1:]`. 🟢
5. `:178` — teto atingido sem interseção → `(None, None)`. 🟢

### Caminho indireto (`find_indirect_path`, `:126-141`)

1. `:131` — `from .upload import graph` **dentro da função** — capta o rebind da global. 🟢
2. `:132-133` — grafo ausente ou nó inexistente → `None`. 🟢
3. `:135` — `nx.shortest_path(graph, source, target)` — BFS não ponderado. 🟢
4. `:136-137` — `len(path) - 1 > max_hops` → `None`. 🟢
5. `:138-139` — comprime para só pessoas; menos de 2 → `None`. 🟢
6. `:140-141` — `NetworkXNoPath` / `NodeNotFound` → `None`. 🟢

### Escape do rótulo (`:185-214`)

1. `:185-190` — `_mermaid_sid`: se receber coleção, pega o primeiro elemento; remove `@`; troca `+` por `_`; remove tudo fora de `[a-zA-Z0-9_]`; prefixa `N_`. 🟢
2. `:206` — `unicodedata.normalize("NFC", ...)`. 🟢
3. `:207-210` — substitui NBSP por espaço; `–` e `—` por `-`; aspas curvas (`“`, `”`, `’`) por `'`. 🟢
4. `:211` — `"` vira `'`. 🟢
5. `:212` — quebras de linha viram espaço. 🟢
6. `:213` — `_LABEL_SEGURO.sub('', s)` — **lista branca**: remove tudo que não consta. 🟢
7. `:214` — **por último**, `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`. 🟢

> ⚠️ A ordem dos passos 6 e 7 é a **invariante** que sustenta a correção do `BUG-20260929-J6PQ`. Se a conversão em entidades vier antes do filtro, o `&` de `&amp;` pode ser reavaliado. Não reordenar.

## Fluxos Alternativos

- **Pessoa 1 não encontrada:** `"Pessoa 1 '{nome}' não encontrada."` com `success=False`. 🟢
- **Pessoa 2 não encontrada:** idem para Pessoa 2. 🟢
- **Sem conexão direta nem indireta:** `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com **`success=True`** e `path_result=None`. 🟡 Ver Riscos.
- **Sem cônjuges no caminho indireto:** `generate_mermaid_graph_indirect_bridge` delega para `generate_mermaid_graph(person_path, p1_id, p2_id, None)` (`:281-282`). 🟢
- **`find_ancestral_path` não achou o ancestral de P1:** mesma delegação (`:290-291`). 🟢
- **`find_ancestral_path` não achou o ancestral de P2:** mesma delegação (`:376-377`). 🟢
- **GEDCOM re-parseado antes da busca:** o grafo é reconstruído a cada POST, garantindo que a busca use a árvore do arquivo `gedcom_filename` informado. 🟢
- **Exceção inesperada:** `"Ocorreu um erro: {e}"` com `success=False`. 🟢

## Dependências

| Dependência | Versão | Como usa |
|-------------|--------|----------|
| **networkx** | 3.6.1 | `nx.Graph`, `nx.shortest_path`, `NetworkXNoPath`, `NodeNotFound` 🟢 |
| **unit `upload-gedcom`** | — | `people`, `families`, `child_to_family`, `get_name`, `ref_id`, e a global mutável `graph` 🟢 |
| **Flask** | 3.1.3 | Rota, `request.form`, `render_template` 🟢 |
| **`templates/index.html`** | — | Renderiza o diagrama; Mermaid inicializado com `securityLevel: 'strict'` 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Busca direta primeiro, indireta como fallback — nunca as duas | `path_search.py:481-494` | 🟢 |
| BFS bidirecional **manual**, em vez de `nx.lowest_common_ancestor` — porque a subida é restrita às arestas de paternidade, não ao grafo todo | `path_search.py:144-178` | 🟢 |
| Compressão dos nós de família no caminho indireto | `path_search.py:138` | 🟢 |
| Âncoras transparentes com aresta rotulada `Casamento` para o diagrama indireto | `path_search.py:424-434` | 🟢 |
| Uso do 1º id por nome; ambiguidade ignorada por decisão do usuário | `path_search.py:479`; `questions.md#2` | 🟢 |
| `import` da global `graph` **dentro** da função, para captar o rebind | `path_search.py:131` | 🟢 |
| **`&`/`<`/`>` escapados depois do filtro**, não antes — invariante do contrato | `path_search.py:213-214` | 🟢 |
| **Lista branca** em vez de negra — a negra era furada pela crase | `path_search.py:193-201` (comentário) | 🟢 |
| `_mermaid_sid` tolera receber coleção (pega o primeiro elemento) | `path_search.py:187-188` | 🟢 |

## Estado Interno

| Estado | Escopo | Observação |
|--------|--------|------------|
| `people`, `families`, `graph`, `child_to_family` | global do processo | Produzidos pelo upload; **lidos** aqui 🟢 |
| `path_result` | local da requisição | Renderizado e descartado 🟢 |

> Nada é persistido. Sem sessão: a busca sempre opera sobre a última árvore carregada no processo. 🟢

## Observabilidade

- Nenhum `logging`, métrica ou trace. 🔴
- As mensagens de resultado e erro são o único sinal ao usuário. 🟢
- O contrato de escape tem **evidência própria** fora da aplicação: `tests/test_mermaid_escape.py` (6 testes), o fuzz de 288 payloads combinados e a varredura de 30.000 nomes, registrados no adendo `bug-BUG-20260929-J6PQ-v001.md`. 🟢

## Riscos e Lacunas

- 🔴 **Homônimos:** o primeiro ID é escolhido sem desempate nem aviso. Decisão do usuário (`questions.md#2`), mas o risco de conectar a pessoa errada permanece. Não é bug; é contrato.
- 🔴 **Famílias adotivas/complexas:** `find_ancestral_path` só sobe por `HUSB`/`WIFE`, então adoção não é representável como laço parental. Cai para a busca indireta, que pode achar um caminho por afinidade sem significado genealógico.
- 🟡 **`success=True` com `path_result=None`** (`:488-491`): "sem conexão" e "erro" chegam ao template com a mesma forma de `path_result`, distinguidos apenas por `success`. A tela depende de o template tratar os dois casos. (`L-06`)
- 🟡 **`split_path_by_marriage` acha só o primeiro par de cônjuges.** Caminhos com múltiplas afinidades renderizam de forma simplificada.
- 🟢 **RESOLVIDO em 2026-09-30 — contrato de `get_spouses` confirmado como intencional.** A varredura global de `families` **é fallback total, não complemento**: ela só roda quando `spouse_ids` ficou vazio (`:79-80`). Decisão do usuário (`questions.md#pergunta-2`), confirmada como economia deliberada de varredura.
  - **Consequência que a reimplementação deve preservar:** com `FAMS` parcialmente resolvidos, cônjuges legítimos podem faltar, e o fallback **não** roda para corrigir. Quem reimplementar e "melhorar" isso para varredura complementar **muda o resultado** da busca indireta e das pontes matrimoniais. Não melhorar.
  - Registrado aqui como contrato, não como lacuna.
- 🟢 **RESOLVIDO em 2026-09-30 — corte silencioso do `MAX_DEPTH` aceito como está.** Decisão do usuário (`questions.md#pergunta-1`): **preservar a fidelidade ao legado**, sem sinalização ao usuário. O teto continua contando **iterações de profundidade** do BFS bidirecional (não gerações), e o corte continua indistinguível de "não existe caminho" no retorno `(None, None)`.
  - **Consequência aceita:** uma árvore com mais de ~20 níveis de ascendência faz a conexão direta falhar em silêncio e cair para a busca indireta, que pode achar um laço por afinidade sem significado genealógico.
  - **A reimplementação não deve acrescentar aviso nem distinguir os dois casos.** Se quiser melhorar isso no alvo, é decisão de produto, não de migração.
- 🟡 **`soft_prefix_jaccard` é da unit `analise-dna`**, mas a mesma família de heurísticas de nome atravessa as duas units — qualquer mudança de normalização afeta ambas.
- 🟢 **Resolvido no legado:** o vazamento de gramática Mermaid por aspa dupla + crase (`BUG-20260929-J6PQ`), com 19 testes e fuzz independente.

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
