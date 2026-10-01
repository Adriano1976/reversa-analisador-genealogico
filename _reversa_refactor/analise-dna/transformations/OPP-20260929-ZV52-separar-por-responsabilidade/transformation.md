---
schema_version: 1
id: OPP-20260929-ZV52
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/ensaio-divisao.txt
    - safety-net/pytest-after-apply.txt
    - before-after/acoplamento-antes.txt
    - before-after/custo-import-depois.txt
measurement:
  before: "Acoplamento: 5 blocos num arquivo de 402 linhas, grafo em DAG sem ciclo. Para chegar em norm_name era preciso importar dna_analysis, que carrega 1009 modulos em 1093 ms, incluindo pandas, thefuzz, networkx e ged4py"
  after: "4 modulos com responsabilidade unica. norm_name agora exige so name_normalization: 71 modulos em 20 ms e zero dependencia pesada. csv_ingest deixou de puxar networkx e thefuzz; matching deixou de puxar pandas"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/name_normalization.py
    purpose: Novo modulo com o vocabulario de nomes e as 8 funcoes de normalizacao e decomposicao
    diff: CHG-001.diff
  - chg: CHG-002
    kind: code
    artifact: analisador-genealogico/reconstructed/csv_ingest.py
    purpose: Novo modulo com leitura do CSV tolerante a encoding, deteccao de colunas e agregacao por match
    diff: CHG-002.diff
  - chg: CHG-003
    kind: code
    artifact: analisador-genealogico/reconstructed/matching.py
    purpose: Novo modulo com a construcao dos indices do GEDCOM e a decisao de aceitacao de candidatos
    diff: CHG-003.diff
  - chg: CHG-004
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Passa a orquestrar, mantendo a tabela de cM, a traducao de cM em parentesco e a superficie de compatibilidade
    diff: CHG-004.diff
approval:
  by: user
  at: 2026-10-01T04:20:04-03:00
reversible_via: [CHG-001.diff, CHG-002.diff, CHG-003.diff, CHG-004.diff]
---

## Responsabilidades antes

O módulo já estava dividido por banners de seção escritos pelo próprio autor. Não foi preciso
inventar fronteira: ela estava declarada no arquivo. O que existia era um arquivo de 402 linhas com
cinco blocos que não compartilham motivo de mudança.

| Bloco | Linhas | Símbolos | Responsabilidade |
|-------|--------|----------|------------------|
| `head` | 1-25 | 0 | docstring e imports |
| `cm_e_vocabulario` | 26-67 | 8 | faixas de cM e vocabulário de nomes |
| `normalizacao` | 69-145 | 8 | normalização e decomposição de nomes |
| `csv_ingest` | 147-199 | 3 | leitura e agregação do CSV |
| `matching` | 201-341 | 2 | índices e matching difuso |
| `fluxo` | 343-402 | 1 | orquestração e montagem da resposta |

## Acoplamento medido

Medido por AST, com `before-after/analise_blocos.py` e saída em `before-after/acoplamento-antes.txt`.
O grafo entre os blocos é um **DAG, sem ciclo**:

```
normalizacao  -> cm_e_vocabulario
csv_ingest    -> normalizacao
matching      -> cm_e_vocabulario, normalizacao
fluxo         -> cm_e_vocabulario, csv_ingest, matching
```

Sem ciclo, a divisão é movimento de linhas, não reengenharia de dependência.

## A fronteira

| Módulo | Responsabilidade única | Linhas |
|--------|------------------------|--------|
| `name_normalization.py` | transformar e decompor nomes, e o vocabulário que isso usa | 121 |
| `csv_ingest.py` | ler o CSV e reduzir a uma linha por match | 62 |
| `matching.py` | decidir quais candidatos do GEDCOM aceitam cada match | 162 |
| `dna_analysis.py` | orquestrar o fluxo e traduzir cM em parentesco | 136 (eram 402) |

O único ponto que não foi movimento puro de linhas foi o bloco `cm_e_vocabulario`, que misturava dois
donos, como o próprio banner admitia ao dizer "faixas de cM **e** vocabulário". A regra de cM
(`SHARED_CM_DATA` e `get_relationships_by_cm`) é usada só pelo fluxo e ficou com ele. O vocabulário de
nomes é usado pela normalização e pelo matching, e ficou com o módulo que trata nomes, com
`matching.py` importando o que precisa. A alternativa, repartir as constantes por quem as usa, daria
três donos para um vocabulário só.

## Ganho medido

O `est_return` da oportunidade é "cada responsabilidade testável isoladamente". Isso se mede pelo custo
de importar só a parte que interessa. Instrumento em `before-after/custo_import.py`, cada alvo num
processo novo, mínimo de 5 execuções.

| Fronteira | Antes | Depois |
|-----------|-------|--------|
| chegar em `norm_name` | `dna_analysis`: 1009 módulos, 1093 ms, com pandas, thefuzz, networkx e ged4py | `name_normalization`: **71 módulos, 20 ms, zero dependência pesada** |
| ler e agregar CSV | `dna_analysis`: 1009 módulos, 1093 ms | `csv_ingest`: 605 módulos, 709 ms, sem networkx e sem thefuzz |
| decidir candidatos | `dna_analysis`: 1009 módulos, 1093 ms | `matching`: 552 módulos, 498 ms, **sem pandas** |
| orquestrar o fluxo | 1009 módulos, 1093 ms | 1012 módulos, 1149 ms, e agora só quem orquestra paga isso |

Nenhum desses valores é ganho de runtime da aplicação: o import acontece uma vez por processo. O ganho
é de testabilidade e de tempo de ciclo de quem mexe nessas funções, e ele foi medido, não estimado. A
projeção do plano (`≈ 68 módulos`, `≈ 15 ms` para a normalização) ficou próxima do medido (71 e 20 ms).

## O que a alma e a spec exigiram preservar

| Decisão | Exigência | Como foi honrada |
|---------|-----------|------------------|
| #3 Predição por faixas de cM | `SHARED_CM_DATA` é a autoridade única | A tabela e `get_relationships_by_cm` ficaram juntos e intactos |
| #4 Matching viral e defensivo | Score difuso, bônus de sobrenome, rejeição de suspeito | `match_candidates` e `build_ged_indexes` moveram sem uma linha alterada no corpo |
| #6 Mojibake embutido | Uma autoridade só, em `domain.py` | Nenhuma cópia nova. O harness de paridade registra que duas funções com esse nome geravam **falso positivo de divergência** |
| #1 Tudo em memória | `people` mutado in place | `matching.py` importa `get_name` e `people` do topo, seguro pela mesma regra documentada na 5XGJ |

A alma não declara `dna_analysis.py` como módulo coeso: lista três decisões distintas (#3, #4, #6) que
conviviam num arquivo. E o `analise-dna/design.md` § Interface declara os 12 símbolos do núcleo como um
contrato **da unit**, não de um arquivo.

## Superfície de compatibilidade

A oportunidade avisa que os testes importam de `reconstructed.dna_analysis`. A varredura mostrou que o
risco é **maior do que ela registrou**: o harness de paridade também importa dez nomes por essa
superfície, e ele é a rede de segurança mais forte do projeto.

| Consumidor | Nomes usados |
|------------|--------------|
| `app.py` | `dna_analysis` |
| `tests/test_dna_analysis.py` | `aggregate_matches`, `detect_columns`, `dna_analysis`, `get_relationships_by_cm`, `read_csv_with_fallback` |
| `tests/test_characterization_matching.py` | `build_ged_indexes`, `dna_analysis`, `match_candidates` |
| `_reversa_sdd/parity/harness.py` | `norm_name`, `strip_bad_utf`, `demojibake`, `split_name_pt`, `surnames_set`, `top_given_tokens`, `token_prefixes`, `drop_short_tokens`, `surname_core_tokens`, `get_relationships_by_cm` |

`dna_analysis.py` mantém um bloco de reexportação com `__all__` e comentário explicando por que ele
existe. Ele **não foi removido** nesta transformação: migrar os consumidores mexeria nos arquivos de
teste que são justamente a rede de segurança. Fica como passo futuro.

## Prova de equivalência

**Ensaio antes de aplicar.** `before-after/ensaio_equivalencia.py` copia o pacote para
`.pytest-tmp/zv52-ensaio/`, sobrepõe os quatro arquivos gerados e roda o mesmo runner em dois processos:
um apontando para o pacote real, outro para o espelho. Saída em `before-after/ensaio-divisao.txt`.

| Frente | Extensão | Resultado |
|--------|----------|-----------|
| Superfície de compatibilidade | 18 nomes | 0 divergentes |
| Funções puras do núcleo | 7 amostras × 9 funções | idênticas |
| Faixas de cM | 9 valores de fronteira | idênticas |
| `soft_prefix_jaccard` | 3 pares | idêntico |
| Fluxo completo | 11 casos na árvore dos testes | 0 divergentes |
| Fluxo completo | 3 casos na árvore de 1023 pessoas | 0 divergentes |

**Depois de aplicar**, os quatro arquivos gravados na árvore foram conferidos por SHA-256 contra o
espelho ensaiado: **byte a byte idênticos**. Isso faz a prova do ensaio valer para a árvore aplicada,
sem depender de reprodutibilidade do gerador.

**Suíte completa**: 85 passed, 1 error, idêntico ao estado anterior. O erro é o `PermissionError` de
sandbox em `test_ensure_dirs_creates_uploads`.

**Harness de paridade diferencial**: reexecutado depois da divisão, **PARIDADE 100%, zero divergência**
nas 6 fixtures GEDCOM. Sem a superfície de compatibilidade, este harness teria quebrado no import.

## Um erro meu, que vale registrar

A primeira versão do gerador da divisão tinha um off-by-one em `texto_de`: o texto de cada símbolo
começava uma linha antes, então cada constante multilinha levava o prefixo da vizinha e o fecha-chaves
ia parar no lugar errado. A minha conferência de "verbatim" não pegou, porque era **tautológica**:
comparava o texto errado com o arquivo que continha aquele mesmo texto errado. Quem pegou foi o
`compile()`. Corrigi o índice e substituí a conferência por uma que verifica se o texto começa pelo
próprio nome do símbolo, que é exatamente o que teria pegado esse erro.

## Estado dos arquivos

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/dna_analysis.py` | 402 linhas | 136 linhas |
| `reconstructed/name_normalization.py` | não existia | 121 linhas |
| `reconstructed/csv_ingest.py` | não existia | 62 linhas |
| `reconstructed/matching.py` | não existia | 162 linhas |

## Reversão

Por `git apply -R` de cada diff, na ordem inversa (CHG-004, CHG-003, CHG-002, CHG-001). Os quatro são
reversíveis de forma independente, verificado com `git apply --check --reverse`. Para reverter o
conjunto:

```
git checkout -- analisador-genealogico/reconstructed/dna_analysis.py
rm analisador-genealogico/reconstructed/{name_normalization,csv_ingest,matching}.py
```

---
*Gerado pelo Reversa-Modularize em 2026-10-01.*
