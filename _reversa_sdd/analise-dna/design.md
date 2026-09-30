# analise-dna, Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=dna_analysis`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui o design de 2026-08-03.

## Interface

### Endpoint HTTP (formulário multipart)

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/` | `action=dna_analysis`, `gedcom_filename`, `root_name`, arquivo no campo `matches_csv` | `index.html` com `dna_results`, `skipped_matches`, `message`, `success` | 200 sempre — o erro vira mensagem na tela 🟢 |

### Símbolos do núcleo

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `dna_analysis` | `(csv_path: str, root_name: str)` | `(results_sorted, skipped, message)` | **Lança exceção** em raiz ausente ou colunas faltantes 🟢 |
| `match_candidates` | `(match_name, cm_value, ged_index, surname_index, features)` | `(candidate_pids, reason)` | Coração do scoring e da aceitação 🟢 |
| `build_ged_indexes` | `()` | `(ged_index, surname_index, features)` | Lê as globais `people`; cacheia atributos normalizados 🟢 |
| `aggregate_matches` | `(df, name_col, cm_col, match_id_col, match_email_col)` | `DataFrame` | Agrupa por `_group_key` e **soma** cM 🟢 |
| `detect_columns` | `(df)` | `(name_col, cm_col, match_id_col, match_email_col)` | Heurística tolerante 🟢 |
| `read_csv_with_fallback` | `(path)` | `DataFrame` | `utf-8` → `latin-1`; `strip()` nos nomes de coluna 🟢 |
| `get_relationships_by_cm` | `(cm_value)` | `list[str]` | Contrato de **lista** 🟢 |
| `norm_name` | `(s)` | `str` | NFKD, sem diacríticos, minúsculas, espaços colapsados 🟢 |
| `split_name_pt` | `(s)` | `(given, surnames, suffixes)` | Decomposição pt-BR 🟢 |
| `soft_prefix_jaccard` | `(a, b, min_pref=4, min_len=2)` | `float` | Trunca **os dois lados** em 4 quando há token curto 🟢 |
| `drop_short_tokens` | `(S, n=3)` | `set` | Mantém `sa` e `sá` por `SHORT_KEEP` 🟢 |
| `token_prefixes` | `(tokens, min_len=3)` | `set` | Prefixos usados no resgate de abreviações 🟢 |

### Contrato de retorno do fluxo

| Saída | Estrutura |
|-------|-----------|
| item de resultado | `{match_name, cm, text_path, mermaid_data, relationships, csv_name}` 🟢 |
| item de descarte | `{csv_name, motivo}` 🟢 |
| mensagem | `"{n} conexões encontradas. {m} descartadas."` 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:44-63`)

1. `app.py:36-42` — fora do ramo de `action`: recupera `gedcom_filename`, valida presença (`"Erro: Arquivo GEDCOM não encontrado."`) e existência em disco (`"Erro: Arquivo '{nome}' não existe mais."`); **re-parseia** o GEDCOM. 🟢
2. `app.py:46-47` — se `matches_csv` ausente ou com nome vazio → `"Por favor, carregue o arquivo CSV de matches."` com `all_names` preservados. 🟢
3. `app.py:48-50` — salva o CSV em `uploads/<nome>`. 🟢
4. `app.py:52` — chama `dna_analysis_flow(matches_path, root_name)`. 🟢
5. `app.py:53-61` — renderiza com `dna_results`, `skipped_matches`, `message`, `success=True`. 🟢
6. `app.py:62-63` — exceção → `"Ocorreu um erro: {e}"`, `success=False`. 🟢

### Núcleo (`dna_analysis.py:340-395`)

1. `:346-349` — resolve a raiz por substring case-insensitive; sem match → `raise ValueError(...)`. Usa `root_person_ids[0]`. 🟢
2. `:351` — `read_csv_with_fallback`. 🟢
3. `:352-354` — `detect_columns`; faltando nome ou cM → `raise ValueError(...)`. 🟢
4. `:355` — `aggregate_matches`. 🟢
5. `:357` — `build_ged_indexes`. 🟢
6. `:362-367` — itera os matches agregados; `demojibake` no nome; chama `match_candidates`. 🟢
7. `:369-371` — sem candidatos → descarte com `reason`. 🟢
8. `:374-389` — para o primeiro candidato com caminho ancestral até a raiz: monta nomes, relações e Mermaid; `break`. 🟢
9. `:390-391` — nenhum candidato tinha caminho → descarte `"sem caminho subindo por pais (pais ausentes no GED?)"`. 🟢
10. `:393-395` — ordena por `cm` desc e monta a mensagem. 🟢

### Detalhe do scoring (`match_candidates`, `:233-333`)

1. `:235-236` — `key = norm_name(match_name)`; busca **exata** em `ged_index`. Se achou, `reason = None` e retorna. 🟢
2. `:240-242` — decompõe o nome do CSV e calcula o conjunto de sobrenomes (sem tokens curtos). 🟢
3. `:244-252` — monta o `pool` de candidatos por `surname_index`; se vazio, tenta por **prefixos** de sobrenome. 🟢
4. `:254-255` — pool vazio → `reason = "sem candidatos por sobrenome (abreviação/corrupção?)"`. 🟢
5. `:262-277` — para cada candidato: `s_given`, `s_token`, `s_part`, interseção de sobrenomes e `common_penalty`; calcula o score e aplica o desempate triplo. 🟢
6. `:279-283` — recalcula a interseção do **melhor** candidato. 🟢
7. `:285-289` — filtro anti-falso-positivo. 🟢
8. `:291-301` — `required_intersection` adaptativo e limiar de Jaccard (0.5 ou 0.33). 🟢
9. `:303-320` — seis ramos de aceitação. 🟢
10. `:322-326` — rebaixamento por conflito de nome do meio. 🟢
11. `:328-331` — `candidate_pids = [best_pid] if ACCEPT else []`, com `reason` detalhado contendo `given`, `final`, `inter` e `jacc`. 🟢

## Fluxos Alternativos

- **Sem GEDCOM carregado:** erro antes de qualquer análise. 🟢
- **Arquivo GEDCOM apagado do disco:** `"Erro: Arquivo '{nome}' não existe mais."` 🟢
- **Sem CSV:** `"Por favor, carregue o arquivo CSV de matches."`, preservando a lista de nomes na tela. 🟢
- **Raiz não encontrada:** `ValueError` → `"Ocorreu um erro: Seu nome 'X' não foi encontrado no GEDCOM."` 🟢
- **Colunas ausentes:** `ValueError` → `"Ocorreu um erro: Colunas de Nome e cM não encontradas no CSV."` 🟢
- **CSV não-UTF-8:** fallback para `latin-1` apenas em `UnicodeDecodeError`. 🟢
- **Match sem candidato:** descarte com um dos motivos catalogados. 🟢
- **Candidato aceito sem caminho ancestral:** descarte `"sem caminho subindo por pais (pais ausentes no GED?)"`. 🟢
- **`cM` não numérico na coluna:** `get_relationships_by_cm` protege com `isinstance` e devolve lista vazia; o `sorted` usa `.get("cm", 0)`. 🟡

## Dependências

| Dependência | Versão | Como usa |
|-------------|--------|----------|
| **pandas** | 3.0.3 | `read_csv`, `groupby().agg()`, `merge`, `apply` 🟢 |
| **thefuzz** | 0.22.1 | `fuzz.ratio`, `fuzz.token_sort_ratio`, `fuzz.partial_ratio` 🟢 |
| **RapidFuzz** | 3.14.5 | Backend real do `thefuzz` (transitiva) 🟢 |
| **python-Levenshtein** | 0.27.3 | Aceleração C do cálculo (transitiva) 🟢 |
| **unit `upload-gedcom`** | — | Consome as globais `people` e o grafo 🟢 |
| **unit `busca-caminho`** | — | Reusa `find_ancestral_path` e `generate_mermaid_graph` 🟢 |
| **`domain`** | — | `demojibake`, `strip_bad_utf` 🟢 |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Agregação em memória com `groupby` + `merge` sobre a chave composta | `dna_analysis.py:183-190` | 🟢 |
| Limiares literais dentro dos ramos de aceitação, **sem constantes nomeadas** | `dna_analysis.py:305-320` | 🟢 |
| **Não implementar** `HARD_MIN`/`GIVEN_MIN` — eram código morto no monolito original | `migration/data_migration_plan.md`; ADR-08 | 🟢 |
| Cache de atributos normalizados para evitar renormalização no laço de candidatos | `dna_analysis.py:198-230` | 🟢 |
| Fallback de encoding apenas em `UnicodeDecodeError` (não em qualquer erro de parse) | `dna_analysis.py:151-157` | 🟢 |
| Chave de match = nome normalizado + ID **ou** e-mail, com ID tendo precedência | `dna_analysis.py:174-180` | 🟢 |
| Usar o **primeiro** candidato com caminho, em vez de avaliar todos | `dna_analysis.py:374-389` | 🟢 |
| Limpeza de nome delegada a `domain.py` (autoridade única) | ADR-07; `dna_analysis.py:22` | 🟢 |

## Estado Interno

| Estado | Escopo | Observação |
|--------|--------|------------|
| `people`, `graph` | global do processo | Produzidos pelo upload; **lidos**, não escritos 🟢 |
| `ged_index`, `surname_index`, `features` | local da requisição | Reconstruídos a cada análise 🟢 |
| `df`, `aggregated` | local da requisição | DataFrames transitórios 🟢 |
| `results_list`, `skipped_matches` | local da requisição | Renderizados e descartados 🟢 |

> **Nenhum resultado é persistido.** Repetir a análise com o mesmo CSV recalcula tudo do zero. 🟢

## Observabilidade

- Nenhum `logging`, métrica ou trace. 🔴
- `skipped_matches` funciona como **auditoria funcional** — é a única visibilidade do motivo de um match não aparecer. 🟢
- A instrumentação de paridade (harness diferencial, fixtures, oráculo) vive em `_reversa_sdd/` e **não faz parte da aplicação**. 🟢

## Riscos e Lacunas

- 🔴 **L-08:** a cobertura dos 6 ramos de aceitação é conhecida apenas pelos testes de caracterização, que congelam o comportamento **atual**. Não há prova de que cobrem exportadores diferentes — a detecção de ID é específica do padrão `[A-Z]{2}\d{7}`.
- 🔴 **L-13:** o teto de precisão do score é `round(..., 2)`. Empates exatos no terceiro critério de desempate são resolvidos pela ordem de iteração de um `set`, que **não é determinística entre processos**. Risco de resultado não reprodutível em casos-limite. 🟡
- 🔴 **Dependência de versão de biblioteca:** `thefuzz` → `RapidFuzz`/`python-Levenshtein`. Trocar versão muda o resultado sem mudar o projeto (`RISK-006`). Fixar as versões é mitigação obrigatória numa reimplementação.
- 🟡 **Justificativa do relaxamento de Jaccard:** a decisão é intencional (`questions.md#4`), confirmada pelo usuário, mas a **base empírica** para 0,33 (e não 0,35 ou 0,30) não está documentada em lugar nenhum.
- 🟡 **Fonte da tabela de cM:** as 9 faixas não citam origem nem versão; e o fato de se **sobreporem** é atípico para uma tabela derivada de percentis do Shared cM Project (`L-07`).
- 🟡 **`COMMON_SURNAMES` contém `"souza"` duas vezes** (`:50`) — inofensivo para um `set`, mas indica curadoria descuidada da lista.
- 🟡 **`soft_prefix_jaccard` trunca os dois lados em 4 caracteres** quando algum token é curto, o que pode aproximar sobrenomes de mesmo prefixo (`L-04`).

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
