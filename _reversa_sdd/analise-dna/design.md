# Análise de DNA, Design Técnico

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

Para o endpoint HTTP (formulário multipart):

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/` | `action=dna_analysis`, `gedcom_filename`, `root_name`, `matches_csv: File` | `index.html` com `dna_results`, `skipped_matches` ou erro | 200 (sempre) |

Para funções:

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `load_gedcom_and_build_graph` | `(file_path: str)` | `all_names: list[str]` | Re-parse do GEDCOM a cada POST |
| `demojibake` | `(s: str)` | `str` | Corrige encoding via `encode("latin1").decode("utf-8")` |
| `norm_name` | `(s)` -> `str` | Normaliza (NFKD, sem acentos, minúsculas) |
| `split_name_pt` | `(name)` -> `(given, surnames, suffixes)` | Decompõe nome pt-BR |
| `surnames_set` | `(name)` -> `set[str]` | Sobrenomes deduplicados |
| `find_ancestral_path` | `(start_id, end_id, max_depth=20)` | `(path, common_ancestor)` ou `(None, None)` | BFS bidirecional pelos pais |
| `get_relationships_by_cm` | `(cm_value)` -> `list[str]` | Relações prováveis por faixa |
| `generate_mermaid_graph` | `(path, p1_id, p2_id, common_ancestor_id)` -> `str` | Diagrama Mermaid da conexão |

## Fluxo Principal
1. Valida GEDCOM carregado e re-parseia (`app.py:576-582`). 🟢
2. Valida arquivo `matches_csv` presente; ausente → "Por favor, carregue o arquivo CSV de matches." (`app.py:586-587`). 🟢
3. Salva CSV em `uploads/` (`app.py:589`). 🟢
4. Localiza a raiz por nome; não encontrada → erro (`app.py:592-594`). 🟢
5. Lê CSV com fallback UTF-8/Latin-1 (`app.py:598-601`). 🟢
6. Identifica colunas de Nome, cM, ID/Email (`app.py:606-615`). 🟢
7. Monta `_group_key` por match (nome + ID/email) (`app.py:617-625`). 🟢
8. Agrega segmentos somando cM (`groupby.agg`) (`app.py:627-635`). 🟢
9. Constrói índices GEDCOM (nome, sobrenome, given) (`app.py:639-651`). 🟢
10. Para cada match, busca candidato no GEDCOM via fuzzy (bloco de scoring). 🟢
11. Para cada candidato aceito, calcula `find_ancestral_path` até a raiz e monta resultado (`app.py:803-820`). 🟢
12. Ordena por cM decrescente e renderiza, com `skipped_matches` para auditoria (`app.py:824-833`). 🟢
13. Exceções → erro amigável (`app.py:835-836`). 🟢

### Detalhe do matching (bloco de scoring)
1. `match_name = demojibake(csv)`, `key = norm_name(match_name)`. 🟢
2. Busca exata normalizada em `ged_index` (`app.py:667`). 🟢
3. Se não há exact, restringe por sobrenome via `surname_index` (`app.py:672-681`). 🟢
4. Fallback por prefixos de sobrenome (`token_prefixes`) (`app.py:684-688`). 🟢
5. Para candidatos no pool, calcula `s_given`, `s_token`, `s_part`, `inter_bonus` (`app.py:700-718`). 🟢
6. Desempate por interseção > given > score (`app.py:721-724`). 🟢
7. Regras de aceitação (A/B/C/D) decidem `candidate_pids` (`app.py:726-793`). 🟢

## Fluxos Alternativos
- **Sem arquivo CSV:** erro claro (`app.py:586-587`). 🟢
- **Raiz não encontrada:** erro com o nome (`app.py:592-594`). 🟢
- **Match sem candidato:** entra em `skipped_matches` com motivo (`app.py:799-801`). 🟢
- **Candidato sem caminho ancestral:** entra em `skipped_matches` (`app.py:821-822`). 🟢
- **Encoding inválido:** fallback para Latin-1 (`app.py:600-601`). 🟢

## Dependências
- **pandas** — leitura e agregação do CSV (`read_csv`, `groupby.agg`, `merge`). 🟢
- **thefuzz** — `ratio`, `token_sort_ratio`, `partial_ratio`. 🟢
- **networkx** — grafo (não usado aqui diretamente, mas base do `find_ancestral_path`). 🟢
- **ged4py + Flask** — infraestrutura herdada do GEDCOM. 🟢

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Agregação em memória com `groupby` + `merge` | `app.py:627-635` | 🟢 |
| Heurísticas de matching com limiares literais (92, 90, 86, 100 etc.) nas regras A/B/C/D | `app.py:759,764,769,773,775,782,790` | 🟢 |
| Constantes `HARD_MIN=92` e `GIVEN_MIN=90` declaradas mas **nunca usadas** (código morto) | `app.py:653-654` | 🟡 |
| Fallback de encoding CSV | `app.py:598-601` | 🟢 |
| Chave de match = nome + ID/email (ocorrência) | `app.py:617-623` | 🟢 |

## Estado Interno
- Usa os globals `people`, `families`, `graph`, `child_to_family` (produzidos pelo upload). 🟢
- `dna_matches_df` é local à requisição (DataFrame). 🟢
- `results_list` e `skipped_matches` são locais à requisição e renderizados. 🟢
- Sem persistência de resultados entre requisições. 🟢

## Observabilidade
- Nenhum log estruturado. 🔴
- `skipped_matches` retorna motivos de descarte na UI (auditoria). 🟢

## Riscos e Lacunas
- 🔴 Complexidade das regras A/B/C/D de aceitação — difícil de validar sem dados reais/amostra.
- 🔴 Sem testes; regressões de matching não são detectadas.
- 🟡 Requisito de cM alto relaxa threshold de Jaccard (0.5→0.33) — pode gerar falsos positivos.
- 🟢 Dependência de ordem/posição das colunas do CSV (heurística, pode variar entre exportadores).