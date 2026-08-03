# Análise Técnica de Código — analisador-genealogico

> Gerado pelo **Archaeologist** em 2026-08-03
> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO (Extraído diretamente do código fonte `app.py`)

---

## 1. Visão Geral do Código Fonte

O sistema é composto por uma aplicação monolítica Python (`app.py`, ~888 linhas) estruturada em torno do framework Flask, com responsabilidades integradas de:
1. Parsing de arquivos GEDCOM (.ged) via biblioteca `ged4py`.
2. Leitura, tratamento e agregação de relatórios de segmentos de DNA em CSV via `pandas`.
3. Normalização de caracteres (mojibake/UTF-8/Latin-1) e matching difuso de nomes via `thefuzz`.
4. Algoritmos de grafos para cálculo de caminho genealógico direto e indireto via `networkx`.
5. Tradução de cM em relações de parentesco prováveis e renderização de diagramas Mermaid.js e Pyvis.

---

## 2. Estrutura e Modaridade do Sistema

Como o sistema é monolítico (`app.py`), a arquitetura lógica é dividida nos seguintes blocos funcionais internos:

```
[Entrada HTTP: Flask Routes]
        │
        ├── Action: "process_dna"
        │     ├── GEDCOM Parser & Graph Builder (ged4py, networkx)
        │     ├── CSV DNA Data Aggregator (pandas)
        │     ├── Fuzzy Name Matcher & Scoring (thefuzz, unidecode, Jaccard)
        │     ├── Ancestral Path Finder (networkx BFS / Ancestor Search)
        │     └── Relationship & Mermaid Predictor
        │
        └── Action: "path_search"
              ├── Name Index Search
              ├── Direct Ancestral Path Search
              └── Indirect Affinity Bridge Search (Marriage / Hops BFS)
```

---

## 3. Fluxo de Controle e Funções Principais

### `load_gedcom_and_build_graph(file_path)` 🟢 CONFIRMADO
- **Parâmetros:** `file_path: str`
- **Retorno:** `all_names: list[str]`
- **Fluxo:** Instancia `GedcomReader`, extrai registros `INDI` em `people` (dicionário `xref_id -> person`) e `FAM` em `families`. Invoca `build_graph_from_parser` para alimentar o grafo NetworkX bidirecional. Retorna lista ordenada de todos os nomes formatados.

### `build_graph_from_parser(people_dict, parser)` 🟢 CONFIRMADO
- **Parâmetros:** `people_dict: dict`, `parser: GedcomReader`
- **Retorno:** `(g: nx.Graph, c2f: dict)`
- **Fluxo:** Cria nós para cada indivíduo e cada família no grafo NetworkX. Conecta cônjuges (`HUSB`, `WIFE`) e filhos (`CHIL`) aos nós das famílias. Mapeia também o índice bidirecional `child_to_family`.

### `process_dna_action` (bloco em `app.py`) 🟢 CONFIRMADO
- **Parâmetros:** `request.files['gedcom_file']`, `request.files['dna_file']`, `request.form['root_person']`
- **Fluxo:**
  1. Carrega GEDCOM e constrói o grafo de pessoas.
  2. Lê CSV de DNA (tentativa em UTF-8, fallback para Latin-1).
  3. Identifica colunas (`Name`, `cM`, ID/Email).
  4. Agrupa segmentos duplicados pela chave `_group_key` e soma a coluna de cM (`groupby.agg`).
  5. Para cada pessoa do CSV, executa busca fuzzy contra o índice GEDCOM (com regras anti-falso-positivo e scoring).
  6. Para cada match localizado, calcula o menor caminho genealógico (`find_ancestral_path`) até a pessoa raiz.
  7. Ordena resultados por cM decrescente e renderiza `templates/index.html`.

### `find_ancestral_path(start_id, end_id, max_depth=20)` 🟢 CONFIRMADO
- **Parâmetros:** `start_id: str`, `end_id: str`, `max_depth: int`
- **Retorno:** `(path: list[str], common_ancestor_id: str)` ou `(None, None)`
- **Fluxo:** Executa busca em largura (BFS bidirecional) subindo exclusivamente pelas conexões de pais (`get_parents`) até encontrar o ancestral comum de menor profundidade (MRCA). Concatena o ramo ascendente com o ramo descendente.

### `find_indirect_path(start_id, end_id, max_hops=40)` 🟢 CONFIRMADO
- **Parâmetros:** `start_id: str`, `end_id: str`, `max_hops: int`
- **Retorno:** `person_path: list[str]` ou `None`
- **Fluxo:** Fallback executado quando não há ancestral comum direto. Usa `networkx.shortest_path` no grafo geral comprimindo nós de família para localizar conexões por afinidade (ex: casamentos, cunhados).

---

## 4. Algoritmos e Regras de Negócio Relevantes

### 4.1. Limpeza de Mojibake (`strip_bad_utf` & `demojibake`) 🟢 CONFIRMADO
* **Problema:** Nomes em português lidos como Latin-1 em UTF-8 geram caracteres corrompidos (`A`, `Ã§`, `JoAo`).
* **Solução:** Substituição de padrões conhecidos de mojibake e re-encoding tentado em `demojibake` (`s.encode("latin1").decode("utf-8")`).

### 4.2. Algoritmo de Pontuação de Matching Difuso (Fuzzy Matching Score) 🟢 CONFIRMADO
* **Fórmula de Score:**
  $$\text{Score} = 0.55 \times S_{\text{token}} + 0.25 \times S_{\text{part}} + 0.20 \times S_{\text{given}} + \text{InterBonus}$$
  * $S_{\text{token}}$: `fuzz.token_sort_ratio(name_csv, name_ged)`
  * $S_{\text{part}}$: `fuzz.partial_ratio(name_csv, name_ged)`
  * $S_{\text{given}}$: `fuzz.ratio` entre o primeiro nome do CSV e candidatos de primeiro nome do GEDCOM.
  * $\text{InterBonus} = 8.0 \times |\text{Interseção Surnames}| - 4.0 \times |\text{Sobrenomes Comuns (Silva, Santos, etc.)}|$

### 4.3. Filtros Anti-Falso-Positivo 🟢 CONFIRMADO
* Se ambos os nomes contêm sobrenomes e a interseção de sobrenomes for 0 (sem bater sufixos de salvamento como 'filho', 'neto'), o candidato é **rejeitado**.
* Se o primeiro nome for genérico (ex: "Maria", "José", "João") e houver 2+ sobrenomes no CSV, a interseção mínima exigida é de pelo menos 2 sobrenomes.

### 4.4. Predição de Parentesco por Tabela de cM (`SHARED_CM_DATA`) 🟢 CONFIRMADO
Traduz o valor de cM total acumulado para relações prováveis:

| Faixa de cM | Relação Prevista |
| --- | --- |
| 3300 - 3720 cM | Pai/Mãe ↔ Filho(a) |
| 2200 - 3400 cM | Irmãos completos |
| 1317 - 2312 cM | Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos |
| 553 - 1330 cM | Primos de 1º grau |
| 200 - 850 cM | Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos |
| 46 - 515 cM | Primos de 2º grau |
| 30 - 350 cM | Primos de 2º grau (1× removido), Primos de 3º grau |
| 10 - 220 cM | Primos de 3º grau (1× removido), Primos de 4º grau |
| 0 - 110 cM | Primos de 4º/5º grau ou mais distantes |

---

## 5. Dicionário de Dados Resumido 🟢 CONFIRMADO

| Entidade / Modelo | Campo | Tipo | Obrigatoriedade | Descrição |
| --- | --- | --- | --- | --- |
| **Person (INDI)** | `xref_id` | String | Sim | Identificador único GEDCOM (ex: `@I0001@`). |
| | `name` | String / Object | Sim | Nome completo em formato GEDCOM. |
| | `sub_records` | List | Sim | Sub-registros de eventos, `FAMC` (família como filho) e `FAMS` (família como cônjuge). |
| **Family (FAM)** | `xref_id` | String | Sim | Identificador único da família (ex: `@F0001@`). |
| | `HUSB` | String | Não | Referência `xref_id` do marido. |
| | `WIFE` | String | Não | Referência `xref_id` da esposa. |
| | `CHIL` | List[String] | Não | Lista de referências `xref_id` dos filhos. |
| **DnaMatchRecord** | `_group_key` | String | Sim | Chave única (Nome normalizado + ID/Email). |
| | `cM` | Float/Int | Sim | Soma de centiMorgans dos segmentos do match. |
| | `matched_name` | String | Sim | Nome original do parente no relatório CSV. |
