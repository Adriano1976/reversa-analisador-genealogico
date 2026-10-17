# Adendo: a carga materializa cada registro uma vez e o grafo recebe as famílias

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Cenário: **legado** (âncora em `_reversa_sdd/upload-gedcom/` e `_reversa_sdd/architecture.md#3`)
> **Origem do registro:** escrito no `/reversa-coding` da feature 025. O canal canônico de adendo é o
> `/reversa-sync`; esta linha existe para que a próxima rodada saiba que o arquivo saiu do ciclo, e não
> de uma escrita manual.

## Vigência

Vigente desde 2026-10-17.

Emenda a descrição de `parsers/gedcom_parser.py` em `_reversa_sdd/architecture.md#3` e
`_reversa_sdd/c4-components.md#3` no ponto em que ela descreve a construção do grafo como leitura do
arquivo. **Não** altera nenhuma regra de negócio, nenhum contrato externo e nenhuma estrutura de dados.

Os dois artefatos de destino foram corrigidos em **2026-10-17** (ver “Absorção editorial” ao final);
este adendo permanece como o registro do delta.

## O que mudou

`build_graph_from_parser` deixou de receber o `GedcomReader`:

| | Antes | Depois |
|---|---|---|
| Assinatura | `build_graph_from_parser(people_dict, parser)` | `build_graph_from_parser(people_dict, familias)` |
| Origem das famílias | itera `parser.records0("FAM")` internamente | recebe a lista já materializada |
| Leitura de arquivo | sim | **não** |

`carregar_arvore` passou a materializar `list(parser.records0("FAM"))` **uma vez**, a montar
`families` dessa lista e a entregá-la ao grafo.

## O diagnóstico que a medição corrigiu

O pedido partia de "indexação repetida". **Não havia indexação repetida**: `index0` é propriedade com
cache no `ged4py`, e `_init_index` executou **1 vez** antes e depois. O desperdício era a **segunda
materialização dos registros `FAM`** — `records0("FAM")` chamado 2 vezes, `read_record` 49.321.

| Contador | Antes | Depois |
|---|---:|---:|
| `records0("FAM")` | 2 | **1** |
| `index0` (acesso) | 3 | **2** |
| `_init_index` (execução) | 1 | 1 |
| `read_record` | 49.321 | **42.391** |

## O que continua valendo

- A árvore continua sendo `(people, families, graph, child_to_family)`, com a **mesma ordem de
  inserção** de nós e arestas (`@ordem`) — impressão digital idêntica antes e depois.
- `BR-U-18` (família sem `xref_id` é ignorada; aresta só para nó existente) permanece.
- A porta `CarregadorDeArvores` continua chamando `carregar_arvore(caminho)` e recebendo a mesma tupla.
- O resultado da análise de DNA é idêntico: 93 cartões e 363 descartes, mesmas ordens e valores.
- `ged4py==0.5.5` continua no pin; nenhum parser foi substituído e nenhum cache foi criado.
- `_reversa_sdd/parity/_profile_big.py` e `harness.py` seguem byte a byte.

## Impacto nos artefatos extraídos

| Artefato | Seção | Tipo de impacto | O que muda |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#3` (componentes e pacotes) | `regra-alterada` | A descrição de `parsers/` deixa de atribuir a construção do grafo à leitura do arquivo: ela transforma dado já lido |
| `_reversa_sdd/c4-components.md` | `#3` | `regra-alterada` | Mesma correção na ficha do componente `gedcom_parser.py` |
| `_reversa_sdd/upload-gedcom/requirements.md` | `#5` (`RF-11` a `RF-14`) | **sem alteração** | As regras de parse, grafo e árvore-como-valor seguem idênticas |
| `_reversa_sdd/data-dictionary.md` | `#1` (a árvore) | **sem alteração** | Nenhum campo, tipo ou ordem mudou |
| `_reversa_sdd/reconstruction-report.md` | menção histórica a `build_graph_from_parser` | **sem alteração** | É registro histórico da reconstrução; não descreve contrato vigente |
| `_reversa_sdd/parity/` | `_profile_big.py`, `harness.py` | **sem alteração** | Os dois mantêm o `sha256` |

## Ganho medido, e o que ele não é

O custo da leitura removida foi medido na árvore real: **mediana de 1,59 s** por carga (1,35 / 1,59 /
2,77 s em três execuções), coerente com os 1,80 s medidos na fase isolada antes da mudança.

Isso é **~5 % da carga e ~1,4 % de uma requisição completa**. As medianas de ponta a ponta **não** são
prova de ganho: a rodada "antes" variou 83 % e a "depois", 6 %. O que a feature entrega é remoção de
trabalho redundante com saída idêntica — não uma melhora perceptível.

## Evidência

`_reversa_forward/025-desempenho-carga-arvore/evidence/RELATORIO.md`, com os arquivos brutos em
`evidence/antes/` e `evidence/depois/`. Nenhum deles contém dado pessoal: só contagens, tempos e hashes.

## Atualização 2026-10-17 (execução do `/reversa-sync`)

Esta seção é **aditiva**: o delta acima foi escrito na mesma sessão pelo `/reversa-coding` (`T020`), e
nada dele foi reescrito. O que entra aqui é o que faltava para a leitura pela pipeline reversa: o
resumo da entrega, a tabela canônica de impacto e os apontadores de vigilância.

### Resumo da entrega

A feature removeu a **segunda materialização dos registros `FAM`** na carga da árvore: `carregar_arvore`
passa a ler a lista uma vez e a entregar a `build_graph_from_parser`, que deixou de receber o
`GedcomReader`. **20 de 20 ações concluídas**; suíte de 1.046 para 1.048 testes, zero falhas; árvore e
resultado de DNA idênticos por impressão digital. O ganho atribuível é de ~1,5 s por carga — remoção de
trabalho redundante, não melhoria perceptível.

### Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#3` Componentes e estrutura de pacotes | `regra-alterada` | A descrição de `parsers/` não deve mais atribuir a construção do grafo à leitura do arquivo: ela transforma dado já lido |
| `_reversa_sdd/c4-components.md` | `#3` Componentes | `regra-alterada` | Mesma correção na ficha do componente `gedcom_parser.py`, que passa a receber as famílias e não o leitor |

Nenhum outro artefato da extração muda: `upload-gedcom/requirements.md#5` (`RF-11` a `RF-14`),
`data-dictionary.md#1` e `code-analysis.md` descrevem contratos que continuam válidos. Os dois
instrumentos novos (`_reversa_sdd/parity/_perfil_da_carga.py` e o script de impressão digital em
`evidence/`) são de desenvolvimento e não fazem parte do sistema em execução, portanto não entram na
extração.

### Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008` —
ver `_reversa_forward/025-desempenho-carga-arvore/regression-watch.md`.

### Fontes

- `_reversa_forward/025-desempenho-carga-arvore/legacy-impact.md`
- `_reversa_forward/025-desempenho-carga-arvore/regression-watch.md`
- `_reversa_forward/025-desempenho-carga-arvore/requirements.md`
- `_reversa_forward/025-desempenho-carga-arvore/progress.jsonl`
- `_reversa_forward/025-desempenho-carga-arvore/evidence/RELATORIO.md`

### Absorção editorial nos artefatos (2026-10-17)

Os dois artefatos da tabela de impacto foram corrigidos nesta data, **sem re-extração e sem tocar
código**:

- `_reversa_sdd/architecture.md#3` — a linha de `parsers/` e a nota “A construção do grafo não lê o
  arquivo” registram que `build_graph_from_parser(people, familias)` recebe as famílias já
  materializadas, e não o `GedcomReader`.
- `_reversa_sdd/c4-components.md` (nível 3) — a ficha de `gedcom_parser.py` foi atualizada com a mesma
  assinatura, a contagem de linhas úteis e a referência a este adendo.

A absorção é **documental**: nenhum arquivo de `src/`, `tests/` ou `requirements.txt` foi alterado por
ela. A feature 025 segue sendo a única origem da mudança de código.
