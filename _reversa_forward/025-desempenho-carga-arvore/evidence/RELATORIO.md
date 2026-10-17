# Relatório de medição — feature 025

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Árvore: `0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged` — 5.508.014 bytes,
> `sha256` `0fa3699e…acba6b`, 35.460 pessoas, 6.930 famílias
> CSV: `54f4887e89705735__Famílias_Sergipanas.csv` — `sha256` `d7cbb84a…37ce31`
> Raiz: `Adriano Santos`
> Ambiente: `.venv` Python 3.14.6, `ged4py` 0.5.5, `networkx` 3.7, `DATABASE_URL` ausente,
> HEAD `c946b6c`

## 1. O que mudou

`carregar_arvore` materializa a lista de registros `FAM` **uma vez** e a entrega a
`build_graph_from_parser`, que deixou de receber o `GedcomReader` e de chamar
`records0("FAM")`. A mudança são 37 linhas em um arquivo de produção
(`src/parsers/gedcom_parser.py`), mais a adaptação de dois testes e um teste novo.

## 2. Contagem de chamadas ao parser

| Contador | Antes | Depois | Leitura |
|---|---:|---:|---|
| `records0("INDI")` | 1 | 1 | já era única |
| `records0("FAM")` | **2** | **1** | a leitura repetida |
| `index0` (acesso à propriedade) | 3 | **2** | um acesso por iteração de tag |
| `_init_index` (execução) | **1** | **1** | a indexação **nunca** se repetiu |
| `read_record` | **49.321** | **42.391** | −6.930 = exatamente uma passada `FAM` |

A aritmética fecha: `read_record` = 1 (`HEAD`) + 35.460 (`INDI`) + N × 6.930 (`FAM`).
Antes, N = 2; depois, N = 1. A queda de `index0` de 3 para 2 confirma o diagnóstico:
o índice é cacheado e era apenas **reiterado**, nunca reconstruído.

## 3. Tempo por etapa

Protocolo: aquecimento descartado + 3 repetições, **cada uma em processo próprio**,
mediana e dispersão.

| | Antes (T006) | Depois (T014) |
|---|---:|---:|
| Aquecimento (descartado) | 28,80 s | 24,73 s |
| Carga — repetições | 34,47 / 45,96 / 25,09 s | 23,44 / 24,85 / 23,72 s |
| **Carga — mediana** | **34,47 s** | **23,72 s** |
| Carga — dispersão | **83 %** | 6 % |
| Análise de DNA (1 execução) | 22,40 s | 29,37 s |
| Total estimado (mediana + DNA) | 56,87 s | 53,09 s |

## 4. O ganho atribuível — e por que não é o da tabela acima

A diferença de medianas da carga (34,47 → 23,72 s) **não pode ser atribuída à
mudança**: a rodada "antes" variou 83 % (25,09 a 45,96 s) e a "depois", 6 %. A
máquina estava visivelmente mais calma na segunda rodada, e o `min` das duas fica
próximo (25,09 s e 23,44 s).

O ganho atribuível é medido onde ele acontece: **no custo da materialização que foi
removida**, medido 3 vezes na árvore real depois da mudança.

| Medição do custo removido | Tempo |
|---|---:|
| 1ª leitura extra de `FAM` (6.930 registros) | 2,77 s |
| 2ª | 1,35 s |
| 3ª | 1,59 s |
| **Mediana** | **1,59 s** |

Nas medições de fase feitas antes da mudança, a mesma leitura custou **1,80 s**, e a
diferença entre `build_graph_from_parser` com e sem a releitura foi de **1,49 s**.

**Conclusão honesta:** o ganho atribuível é de **~1,5 s a ~1,8 s por carga**, ou
**5 % a 6 % da carga** e **~1,4 % de uma requisição completa de ~105 s**. É remoção
de trabalho redundante, com saída idêntica. **Não** é ganho perceptível ao operador,
e este relatório não o apresenta como tal. Os custos dominantes continuam sendo a
passada `INDI` (~19 s medidos antes da mudança) e a análise de DNA (~22 a 54 s,
conforme o estado de cache da máquina).

## 5. Identidade da saída (comparação exata, sem tolerância)

Impressão digital `sha256` de uma serialização canônica que preserva ordem
(pessoas, famílias, nós com `label`/`type`, arestas, `child_to_family`, e a projeção
do resultado de DNA). Nenhum dado pessoal entra na evidência.

| Impressão | Antes (T007) | Depois (T013) | Resultado |
|---|---|---|---|
| Árvore | `8bf55afb8fa93ee414240afe8698eee1b419fd073fb67f446467c7f37cc1d925` | idêntica | **IGUAL** |
| Resultado de DNA | `d369611f03a30f448849a3885a3e4f3b4adf4cf4ad73ae877f27283b585c5163` | idêntica | **IGUAL** |

Estrutura: 35.460 pessoas, 6.930 famílias, 42.390 nós, 36.807 arestas — igual nas
duas pontas. Resultado: 93 cartões e 363 descartes — igual nas duas pontas.

## 6. Paridade contra o oráculo congelado

| | Antes (T005) | Depois (T012) |
|---|---|---|
| `affinity.ged` | 0 divergências | 0 divergências |
| `basic.ged` | 8 | 8 |
| `deep25.ged` | 6 | 6 |
| `mojibake_latin1.ged` | 4 | 4 |
| `no_name.ged` | 2 | 2 |
| `variants.ged` | 4 | 4 |
| **Total** | **24** | **24** |

Comparação **linha a linha** dos dois arquivos de saída: **0 linhas diferentes**.
Nenhuma divergência nova; nenhuma fixture nova divergente. As 24 são a linha de
base registrada antes da mudança e são **anteriores** a esta feature (commits de
matching e janela de vida posteriores a 2026-10-13).

## 7. Suíte e escopo

| | Antes (T004) | Depois (T011) |
|---|---|---|
| Suíte | 1.046 passed, 9 skipped, 0 falhas | **1.048 passed, 9 skipped, 0 falhas** |

Os dois testes a mais são os de `tests/test_carga_da_arvore.py`; **nenhum teste foi
removido**.

Escopo fechado (`T015`):

```text
git diff --stat
 src/parsers/gedcom_parser.py      | 37 ++++++++++++++++++++++++-----
 tests/test_upload.py              |  4 ++--
 (+ tests/test_carga_da_arvore.py, novo e nao rastreado)
```

`requirements.txt` sem diff (`ged4py==0.5.5` intacto). `_reversa_sdd/parity/_profile_big.py`
e `harness.py` com o **mesmo `sha256`** de antes (`50c27b09…`, `33e45b05…`).

## 8. Como reproduzir

Ver `onboarding.md` §3. Os arquivos brutos de cada passo estão em `evidence/antes/` e
`evidence/depois/`.
