# Busca de Caminho, Design Técnico

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

Para o endpoint HTTP (formulário):

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/` | `action=path_search`, `gedcom_filename`, `person1_name`, `person2_name` | `index.html` com `path_result` ou mensagem | 200 (sempre) |

Para funções:

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `find_person_by_name` | `(name_query: str)` | `list[str]` | Exact match, depois substring |
| `find_ancestral_path` | `(start_id, end_id, max_depth=20)` | `(path, common_ancestor)` ou `(None, None)` | BFS bidirecional pelos pais |
| `find_indirect_path` | `(start_id, end_id, max_hops=40)` | `person_path: list[str]` ou `None` | `nx.shortest_path` com compressão de famílias |
| `generate_mermaid_graph` | `(path, p1_id, p2_id, common_ancestor_id)` -> `str` | Mermaid para conexão direta |
| `generate_mermaid_graph_indirect_bridge` | `(p1_id, p2_id, person_path)` -> `str` | Mermaid para conexão indireta |
| `split_path_by_marriage` | `(person_path)` | `(left, right, spouses)` | 1º par de cônjuges adjacentes |
| `are_spouses` | `(a_id, b_id)` -> `bool` | Verifica casamento |

## Fluxo Principal
1. Valida GEDCOM carregado e re-parseia (`app.py:576-582`). 🟢
2. Lê `person1_name` e `person2_name` (strip) (`app.py:840`). 🟢
3. Localiza IDs; inexistente → erro específico por pessoa (`app.py:843-850`). 🟢
4. Usa o primeiro ID de cada lista (`app.py:853`). 🟢
5. Tenta `find_ancestral_path(p1, p2)` (`app.py:856`). 🟢
6. Se achou: monta nomes, `generate_mermaid_graph`, msg direta (`app.py:857-860`). 🟢
7. Senão: tenta `find_indirect_path(p1, p2, max_hops=40)` (`app.py:863`). 🟢
8. Sem caminho → "Nenhuma conexão encontrada..." (`app.py:864-867`). 🟢
9. Com caminho: `generate_mermaid_graph_indirect_bridge`, msg indireta (`app.py:868-870`). 🟢
10. Monta `path_result` e renderiza (`app.py:872-879`). 🟢
11. Exceções → erro amigável (`app.py:880-882`). 🟢

### Detalhe da conexão direta (`find_ancestral_path`)
1. Duas filas BFS, uma de cada extremo, subindo por `get_parents`. 🟢
2. Intercalando expansão de `q1` e `q2`; ao encontrar interseção, monta caminho (`app.py:298-317`). 🟢
3. `start_id == end_id` → caminho trivial (`app.py:300`). 🟢
4. Limite de `max_depth` iterações; estoura → `(None, None)` (`app.py:301`, `318`). 🟢

### Detalhe da conexão indireta (`find_indirect_path`)
1. Verifica nós presentes no grafo (`app.py:284`). 🟢
2. `nx.shortest_path(graph, source, target)` — BFS não ponderado (`app.py:287`). 🟢
3. `len(path)-1 > max_hops` → `None` (`app.py:288-289`). 🟢
4. Comprime o caminho mantendo só nós de pessoa (`app.py:291`). 🟢
5. Menos de 2 pessoas → `None` (`app.py:292`). 🟢

## Fluxos Alternativos
- **Pessoa 1 não encontrada:** "Pessoa 1 'X' não encontrada." (`app.py:845-847`). 🟢
- **Pessoa 2 não encontrada:** "Pessoa 2 'X' não encontrada." (`app.py:848-850`). 🟢
- **Sem conexão direta nem indireta:** mensagem de nenhuma conexão (`app.py:864-867`). 🟢
- **Sem cônjuges no caminho indireto:** fallback para `generate_mermaid_graph` simples (`app.py:408`). 🟢

## Dependências
- **networkx** — `shortest_path` e grafo de relacionamento. 🟢
- **ged4py + Flask** — infraestrutura herdada do GEDCOM. 🟢

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Busca direta primeiro, indireta como fallback | `app.py:856-870` | 🟢 |
| BFS bidirecional manual para MRCA (não usa `nx.lowest_common_ancestor`) | `app.py:297-318` | 🟢 |
| Compressão de nós de família no caminho indireto | `app.py:291` | 🟢 |
| Âncoras transparentes `--- |Casamento| ---` no Mermaid indireto | `app.py:534` | 🟢 |
| Uso do 1º ID encontrado por nome (ambiguidade ignorada) | `app.py:853` | 🟢 |

## Estado Interno
- Usa os globals `people`, `families`, `graph`, `child_to_family` (produzidos pelo upload). 🟢
- `path_result` é local à requisição e renderizado. 🟢
- Sem persistência. 🟢

## Observabilidade
- Nenhum log estruturado. 🔴
- Mensagens de resultado/erro são passadas ao template. 🟢

## Riscos e Lacunas
- 🔴 Uso do 1º ID em caso de homônimos — pode conectar a pessoa errada.
- 🔴 `find_ancestral_path` assume caminho pelos pais; famílias adotivas/complexas podem não ser cobertas.
- 🟡 `split_path_by_marriage` detecta só o 1º par de cônjuges — caminhos com múltiplas afinidades podem renderizar de forma simplificada.
- 🟡 Sem testes automatizados.