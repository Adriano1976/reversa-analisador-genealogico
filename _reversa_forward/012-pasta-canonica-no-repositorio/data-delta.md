# Data Delta: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`

## 1. O que a extração descreve, e o que esta feature toca

| Elemento extraído | Onde está descrito | O que muda |
|---|---|---|
| `ARQUIVO_ARMAZENADO` — arquivos imutáveis sob chave derivada do conteúdo | `_reversa_sdd/erd-complete.md`; `_reversa_sdd/upload-gedcom/contracts.md#2.1` | **Nada.** A forma do nome, a chave de conteúdo, a idempotência e a ausência de remoção pelo runtime continuam idênticas |
| Localização do armazenamento | `_reversa_sdd/inventory.md#5`; `_reversa_sdd/c4-containers.md#2` | **A raiz declarada.** Volta a ser `<diretório do app>/uploads`, dentro do repositório |
| `ANALISADOR_UPLOAD_FOLDER` | `_reversa_sdd/data-dictionary.md`; `_reversa_sdd/inventory.md#4` | **O papel.** Volta a ser sobreposição de processo, sobretudo para teste, e não modo de operação |
| Banco de dados relacional (feature 008) | `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | **Nada no schema.** Nenhum campo, tabela ou migração |
| Ciclo de vida do arquivo enviado | `_reversa_sdd/state-machines.md#5` | **Nada no runtime.** O expurgo continua sendo operação de operador, por manifesto, fora do runtime |

## 2. Delta de localização: de quatro diretórios para um

| # | Diretório | Arquivos | Bytes | Destino |
|---|---|---|---|---|
| 1 | `src/uploads` | 36 | 27.932.474 | **fica** — é a pasta canônica |
| 2 | `D:\dados-genealogicos\uploads` | 36 | 27.932.474 | **já removida** em 2026-10-09, por ordem do operador |
| 3 | `_reversa_refactor/…/OPP-20261003-FLAT-achatar-o-nivel-de-pacote/before-after/src-antes/uploads` | 9 | 16.920.784 | sai pelo `RF-09` |
| 4 | `_reversa_refactor/…/OPP-20261003-GUE7-reorganizar-em-subpacotes/before-after/src-antes/uploads` | 9 | 16.920.784 | sai pelo `RF-09` |
| 5 | `_reversa_refactor/…/OPP-20261003-RAIZ-distribuir-modulos-soltos/before-after/src-antes/uploads` | 9 | 16.920.784 | sai pelo `RF-09` |
| — | `_reversa_forward/007-…/evidence/_tmp_e2e/uploads` | 2 | 587 | **fica** — sondas sintéticas, não dado real |

**Total de dado real hoje: 4 diretórios, 78.694.826 bytes.** Depois da feature: **1 diretório,
27.932.474 bytes** — redução de 50.762.352 bytes, sem alterar um byte do dado canônico.

## 3. Inventário do estado de hoje (`src/uploads`)

- **36 arquivos, 27.932.474 bytes, 31 hashes distintos** — ou seja, 5 arquivos são cópias byte a byte
  de outros.
- Por extensão: **16 `.ged`**, **19 `.csv`**, **1 `.xlsx`**.
- **18 arquivos são resíduo de instrumento** (6.631 bytes): 9 `.ged` e 9 `.csv`, com nomes de sonda de
  GEDCOM (`probe.ged` ×6, `arvore.ged`, `basic.ged`, `nomes-inertes.ged`) e de fixture de DNA
  (`utf8.csv`, `latin1.csv`, `duplicated.csv`, `no_intersection.csv`, `generic.csv`,
  `cm_boundaries.csv`, `missing_col.csv`, `matches_dois_kits.csv` ×2).
- **3 arquivos não têm chave de conteúdo no nome** — são do formato anterior à chave derivada:
  `Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged` e `Famílias_Sergipanas.csv`. O agrupamento
  pela chave **não os alcança**: cada um vira item próprio.

### 3.1 Duplicatas: relatadas, nunca removidas

| `sha256` (16 primeiros) | Cópias | Nomes |
|---|---|---|
| `080e7943572d2652` | **3** | `080e7943572d2652__080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged`, `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged`, `Arvore_Unificada_Oficial_V1_2.ged` |
| `94e2402671702cac` | **3** | `94e2402671702cac__Famílias_Sergipanas.csv`, `94e2402671702cac__Famílias_Sergipanas.csv.ged`, `Famílias_Sergipanas.csv` |
| `b3211a52a933fdd0` | **2** | `Adriano_Santos.ged`, `b3211a52a933fdd0__Adriano_Santos.ged` |

A `D-06` da 010 continua valendo: **duplicata é relatada e preservada**. Nenhuma das três sai por esta
feature. Note que o primeiro grupo contém um nome **com chave dupla** — um envio cujo nome visível já
era um nome com chave — e que o segundo grupo mistura `.csv` e `.csv.ged`, o que faz os dois caírem em
**abas diferentes** da feature 011.

## 4. As três cópias de arrasto

Cada uma tem **9 arquivos e 16.920.784 bytes**, com **7 hashes distintos** — as três são idênticas entre
si. Conteúdo:

| Nome | Bytes | Presente em `src/uploads`? |
|---|---|---|
| `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` | 5.332.198 | sim |
| `Arvore_Unificada_Oficial_V1_2.ged` | 5.332.198 | sim |
| `b3211a52a933fdd0__Adriano_Santos.ged` | 3.063.082 | sim |
| `Adriano_Santos.ged` | 3.063.082 | sim |
| `7d693792453770c9__DNA_Nordestino.csv` | 36.714 | sim |
| `94e2402671702cac__Famílias_Sergipanas.csv` | 30.968 | sim |
| `94e2402671702cac__Famílias_Sergipanas.csv.ged` | 30.968 | sim |
| `Famílias_Sergipanas.csv` | 30.968 | sim |
| `20a046eb06150ccd__nomes-inertes.ged` | 606 | sim |

**Órfãos: 0.** Todo `sha256` das três cópias ocorre em `src/uploads`, e é isso que o `RF-09` confere
antes de remover — qualquer órfão cancelaria a remoção daquele diretório. O critério é sobre **conteúdo**
e não sobre nome, precisamente porque a cópia carrega os três nomes do formato anterior à chave.

## 5. Estado final previsto

Depois do `RF-09` (arrastos) e do `RF-10` (resíduo):

- **18 arquivos, 27.925.843 bytes.**
- Por extensão: **7 `.ged`**, **10 `.csv`**, **1 `.xlsx`**.
- **Um diretório** com dado real.

| Arquivo | Aba |
|---|---|
| `080e7943572d2652__080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` | árvore |
| `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` | árvore |
| `94e2402671702cac__Famílias_Sergipanas.csv.ged` | árvore |
| `Adriano_Santos.ged` | árvore |
| `Arvore_Unificada_Oficial_V1_2.ged` | árvore |
| `b3211a52a933fdd0__Adriano_Santos.ged` | árvore |
| `c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged` | árvore |
| `0e85a4f3052e19e3__Genealogia_Mineira.csv` | DNA |
| `442e5bb013a121f6__Projetos_Genealogicos_Unificados.csv` | DNA |
| `50a3dd36fea8f8bb__Famílias_Sergipanas.csv` | DNA |
| `555c9871570e8044__Best_of_British_DNA_Gedmatch_Project.csv` | DNA |
| `7d693792453770c9__DNA_Nordestino.csv` | DNA |
| `877d18ad9c6ac1e6__African_Brazilian_Genealogy_and_Genetics.csv` | DNA |
| `94e2402671702cac__Famílias_Sergipanas.csv` | DNA |
| `c7bf4be4bf7c4201__Italian_Ancestors.csv` | DNA |
| `d8cdd388e5b6f432__Genealogia_Paulistana.csv` | DNA |
| `Famílias_Sergipanas.csv` | DNA |
| `b70889273a505a5d__Familias Sergipanas.xlsx` | **nenhuma** |

### 5.1 O efeito na lista da feature 011, nas duas unidades

As duas contagens são diferentes e as duas importam — a lista agrupa pela chave do nome:

| Aba | Hoje | Depois |
|---|---|---|
| Árvore (`.ged`) | 16 arquivos → **15 itens** | 7 arquivos → **6 itens** |
| DNA (`.csv`) | 19 arquivos → **19 itens** | 10 arquivos → **10 itens** |

A aba de árvore não chega a 7 itens porque dois arquivos compartilham a chave `080e7943572d2652`.
O `.xlsx` continua sem aba, porque a `RN-03` da 011 só lista `.ged` e `.csv`.

## 6. Banco de dados

**Nenhuma mudança de schema.** Nenhum campo novo, nenhum removido, nenhuma migração. As seis tabelas da
feature 008 (`dna_analysis`, `analysis_person`, `match_result`, `match_kit`, `match_path_node`,
`skipped_match`) ficam como estão.

**Continuidade das referências por nome.** `tree_ref` e `match_file_ref` guardam o **nome** do arquivo
armazenado, e nenhum nome em `src/uploads` é renomeado por esta feature. O resíduo que o `RF-10` remove
não é referenciado por nenhuma linha: as duas únicas linhas de `dna_analysis` apontam para
`sonda_t014.ged`, que **não** está no manifesto.

**Referências já quebradas, medidas em 2026-10-09** — declaradas aqui, não corrigidas (`D-13`):

| `tree_ref` | Linha do histórico | Arquivo existe? |
|---|---|---|
| `0646f8431ba58cca__sonda_t014.ged` | registrada em 2026-10-09T14:54:04Z | **não** |
| `dbc25ecc1cb17db3__sonda_t014.ged` | registrada em 2026-10-09T14:54:40Z | **não** |
| `match_file_ref` = `641b786ce546bff6__sonda_t014.csv` | idem | **não** |

Nenhum arquivo com `sonda` no nome existe em lugar nenhum do projeto (varredura completa do
repositório). As duas linhas vêm das sondas do `T016` da 010, executadas pelo contêiner. Como a
varredura de `src/` mostra **zero `SELECT`**, nada no runtime lê esse histórico: o impacto é latente.
Os artefatos da 010 afirmam o contrário do que se mede hoje (`onboarding.md` §16 e `regression-watch.md`
dizem que 4 arquivos sintéticos ficaram no destino), e isso está registrado em `investigation.md` §8.

## 7. Migrações necessárias

**Nenhuma migração de dados.** Nada é movido, renomeado ou convertido. O que existe é retirada:

| Passo | Operação | Volume |
|---|---|---|
| `RF-04` | remoção da cópia externa | **já executada**, 36 arquivos conferidos por `sha256` antes e depois |
| `RF-09` | remoção de três diretórios de arrasto | 27 arquivos, 50.762.352 bytes, com conferência de órfãos |
| `RF-10` | expurgo do resíduo por manifesto | 18 arquivos, 6.631 bytes, com simulação antes |

Nenhum passo toca arquivo do operador. A prova de que nenhum conteúdo único se perde é a medição de
órfãos de §4 — **0** — e ela é refeita pelo instrumento no momento da remoção, não presumida.

## 8. Registro de rastreabilidade

| Unidade do `_reversa_sdd/` | Como fica |
|---|---|
| `upload-gedcom` | Sem mudança de comportamento. Os nomes em disco e a forma fechada continuam os mesmos |
| `analise-dna` | Sem mudança. `match_file_ref` continua resolvendo, porque o resíduo removido não é referenciado |
| `busca-caminho` | Sem mudança |
| Persistência (feature 008) | Sem mudança de schema; o volume do banco não é tocado (`D-11`: nunca `down -v`) |
| Instrumento de paridade (`_reversa_sdd/parity/`) | Sem mudança; segue isolado pelo invólucro `tests/rodar_paridade.py` |
| `_reversa_refactor/` | **Perde** os três `src-antes/uploads`; os `.py` irmãos de `src-antes/` ficam intactos |
