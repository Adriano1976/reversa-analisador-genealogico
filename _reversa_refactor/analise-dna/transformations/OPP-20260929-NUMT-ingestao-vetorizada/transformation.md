---
schema_version: 1
id: OPP-20260929-NUMT
verb: optimize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/equivalencia-antes-depois.txt
    - before-after/ganho-candidato.txt
    - safety-net/pytest-after-apply.txt
measurement:
  before: "3000 linhas (arvore de 1023): detect_columns 20,87 ms, aggregate_matches 196,62 ms, fluxo 920,44 ms. Complexidade O(k*n) e O(n) chamadas Python com uma Series alocada por linha"
  after: "3000 linhas: detect_columns 10,70 ms, aggregate_matches 43,02 ms, fluxo 709,32 ms. Complexidade O(j*n) com j = primeira coluna que casa, e O(u) chamadas Python com u = nomes distintos"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Para a varredura de colunas na primeira que casa, e troca df.apply(axis=1) por chave montada em coluna com normalizacao por nome distinto
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-10-01T03:58:09-03:00
reversible_via: [CHG-001.diff]
---

## Gargalo atacado

Dois trechos da ingestão de CSV faziam trabalho por linha em Python puro onde a biblioteca opera em
coluna. O alvo é a ingestão, que cresce com o **tamanho do arquivo**, e não com o número de
candidatos do GEDCOM.

| Símbolo | Antes | Depois |
|---------|-------|--------|
| `detect_columns` | montava a lista completa das colunas que casam a regex, para depois pegar `[0]` | `next(...)`, parando na primeira que casa |
| `aggregate_matches` | `df.apply(build_group_key, axis=1)`, com uma `Series` por linha e uma normalização por linha | chave montada por coluna, com normalização uma vez por **nome distinto** |

## Complexidade declarada

| Fase | Antes | Depois |
|------|-------|--------|
| `detect_columns` | O(k · n), k = todas as colunas, sempre | O(j · n), j = índice da primeira coluna que casa, j ≤ k |
| `aggregate_matches` | O(n) chamadas Python, cada uma alocando uma `Series` | O(u) chamadas Python, u = nomes distintos |

Espaço: O(n) nos dois casos. A versão nova acrescenta um dicionário de u entradas, do tamanho da
coluna que já existia.

## Medição

Mesmo instrumento antes e depois: `before-after/bench_ingest.py`, com GEDCOM sintético de 1023
pessoas, CSV de 8 colunas, 15 repetições por fase e 5 por fluxo, aquecimento e medições intercaladas
entre os tamanhos. Saídas cruas em `before-after/baseline.txt` e `before-after/depois.txt`.

| Linhas no CSV | Fase | Antes | Depois | Ganho |
|---------------|------|-------|--------|-------|
| 300 | `detect_columns` | 4,60 ms | 2,70 ms | −41,3% |
| 300 | `aggregate_matches` | 22,38 ms | 16,54 ms | −26,1% |
| 300 | fluxo completo | 275,99 ms | 236,64 ms | **−14,3%** |
| 1000 | `detect_columns` | 7,63 ms | 4,60 ms | −39,7% |
| 1000 | `aggregate_matches` | 66,06 ms | 29,47 ms | −55,4% |
| 1000 | fluxo completo | 418,13 ms | 355,47 ms | **−15,0%** |
| 3000 | `detect_columns` | 20,87 ms | 10,70 ms | −48,7% |
| 3000 | `aggregate_matches` | 196,62 ms | 43,02 ms | −78,1% |
| 3000 | fluxo completo | 920,44 ms | 709,32 ms | **−22,9%** |

A fatia de `aggregate_matches` no fluxo caiu de 21,4% para 6,1% em 3000 linhas. O ganho cresce com o
tamanho do arquivo, que era o argumento estrutural da oportunidade.

### Validação do baseline

Antes de otimizar, o baseline reproduziu o número registrado na própria oportunidade: na escala de 300
linhas, a OPP anotou `aggregate_matches` em 0,027 s = 8,2% do fluxo, e a medição independente deu
22,4 ms = 8,1%. Duas medições com quase dois meses de distância e instrumentos diferentes.

## Prova de equivalência

Duas frentes, ambas com igualdade exata.

**Igualdade da função isolada** (`before-after/ganho-candidato.txt`): a chave de agrupamento nova foi
comparada com a antiga por `DataFrame.equals` em 16 entradas, as 7 fixtures de DNA do harness de
paridade e 9 casos de borda. Zero divergências.

**Igualdade do fluxo completo** (`before-after/equivalencia-antes-depois.txt`): a versão anterior foi
recuperada de `HEAD` e carregada lado a lado com a atual no mesmo processo, e as duas rodaram
`dna_analysis(csv, raiz)` sobre 14 entradas. Veredito: **equivalente em todo o corpus**.

| Grupo | Entradas | Resultado |
|-------|----------|-----------|
| Fixtures do harness de paridade | 7 | idêntico, incluindo o `ValueError` de `missing_col.csv` |
| CSVs do teste de caracterização | 4 | idêntico, com o caso de **537 cM** somado preservado |
| Corpus sintético do benchmark | 3 | idêntico, até 3000 linhas |

Uma observação honesta sobre as fixtures de paridade: elas usam o nome `Ana Silva`, cujo único token
não-genérico é o sobrenome. Esse é o achado caracterizado e deliberadamente não corrigido que está
documentado no topo de `tests/test_characterization_matching.py`: `split_name_pt` lê o sobrenome como
prenome, o pool de candidatos fica vazio e a linha é descartada. Por isso elas **não** exercitam o
caminho de aceitação, e foi preciso acrescentar os CSVs do teste para que o caso de 537 cM fosse
coberto pela prova. Sem essa segunda passada, a prova teria sido mais fraca do que parecia.

## O que a sonda pegou antes de virar código

A primeira versão da deduplicação usava `.astype(str)`, que é o reflexo natural em pandas. Em coluna
de objeto, o `astype(str)` **preserva `NaN` como float** em vez de virar a string `'nan'`, enquanto a
versão antiga convertia com `str(...)` por elemento. O `demojibake` então recebia um float e estourava
com `TypeError`. É exatamente o risco que a oportunidade registrou em prosa. A sonda só pegou porque
incluía um caso de borda com `None` na coluna de nome. O código aplicado usa `.map(str)`, e o motivo
está comentado no próprio módulo.

## Duas medições que eu corrigi no meio do caminho

- A primeira versão do instrumento media cada tamanho em bloco, e uma lentidão momentânea da máquina
  contaminava um tamanho só: `detect_columns` saiu mais rápido com 1000 linhas do que com 300, o que é
  impossível. Passou a intercalar as medições.
- A primeira versão cronometrava o `df.copy()` junto com a função alvo. As cópias passaram a ser
  criadas fora da região medida.

## Uma hipótese que caiu

Suspeitei que `apply(axis=1)` também encarecesse com o número de colunas, já que monta uma `Series`
por linha com todas elas. Medi um CSV de 3 colunas contra o de 8, nas mesmas contagens de linha: a
razão ficou entre 1,03x e 1,21x, ou seja, ruído. A hipótese não foi usada para justificar nada.

## O que esta otimização não resolve

O custo continua proporcional ao número de **nomes distintos**, e cada um paga `norm_name`, que a
docstring do módulo estima em 41 µs. O coeficiente ajustado nos dados medidos dá ≈ 40 µs por nome
distinto, o que confirma a estimativa. `norm_name` é normalização customizada (NFKD, combinação,
pontuação, mojibake) e não vira operação vetorizada de pandas sem reescrever a regra, o que sairia do
escopo desta oportunidade e tocaria uma função usada por todo o matching.

## Nota de estilo do módulo

Ao contrário de `path_search.py`, os comentários e docstrings de `dna_analysis.py` são escritos em
ASCII, sem acento (`Constroi os indices`, `nao altera nenhuma decisao`), enquanto as mensagens de
interface usam acento. Os comentários acrescentados seguem a convenção local.

## Estado do arquivo

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/dna_analysis.py` | 395 linhas | 402 linhas |
| Ocorrências de `.apply(` no módulo | 1 | 0 |

## Rede de segurança

Suíte completa verde antes e depois: **85 passed, 1 error** nas duas execuções. O erro é o
`PermissionError` do sandbox em `test_ensure_dirs_creates_uploads`, que reproduz em qualquer
`--basetemp` e não tem relação com esta transformação. `tests/test_characterization_matching.py`
roda sozinho com **21 passed**.

## Reversão

Por `git apply -R CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/dna_analysis.py`.

---
*Gerado pelo Reversa-Optimize em 2026-10-01.*
