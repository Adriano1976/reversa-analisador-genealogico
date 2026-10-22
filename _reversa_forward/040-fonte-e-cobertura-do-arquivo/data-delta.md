# Data delta: fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/040-fonte-e-cobertura-do-arquivo/requirements.md`
> Modelo extraído: `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit`

## 1. Resumo

A feature **não cria tabela, coluna, porta nem migração**. Ela acrescenta:

1. dois módulos de domínio novos com catálogo e limiares (`core/fontes_de_laboratorio.py`,
   `core/qualidade_da_medida.py`) e um de medida (`core/cobertura_do_arquivo.py`);
2. **três chaves aditivas** no dicionário da evidência (`source_raw`, `source_motivo`, `medida`) e a
   mudança de **conteúdo** de `source` (passa a ser rótulo canônico);
3. **um dicionário** no resultado da aplicação (`cobertura`).

Tudo vive no payload da análise, entre o núcleo e a tela. O histórico (`analysis`, `analysis_person`,
`match_result`, `match_path_node`, `skipped_match`) e a lista de trabalho em CSV não mudam.

## 2. Delta no dicionário da evidência (payload do kit)

O dicionário de `evidencias[nome_normalizado][chave_kit]` (`src/core/genetic_evidence.py`), hoje:

| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `kit` | `str \| None` | Kit em maiúsculas |
| `person_name_csv` | `str` | Nome como veio do CSV |
| `source` | `str \| None` | **Texto cru** da primeira linha não vazia |
| `total_cm` | `float` | Soma dos segmentos |
| `segments` | `list[dict]` | Segmentos |
| `records_used` | `int` | Linhas do CSV no kit |
| `segment_count`, `largest_segment_cm`, `snps_total`, `snps_largest_segment`, `chromosomes`, `method`, `mrca_generations`, `mrca_divergent`, `weak_segment` | — | Como em `data-dictionary.md#51` |

Muda **um** campo e entram **três**:

| Campo | Tipo | Padrão | Conteúdo |
|-------|------|--------|----------|
| `source` | `str \| None` | `None` | **Alterado:** rótulo canônico (`Genera`, `meuDNA`, …, `não declarada`, `outro`) ou `None` quando o CSV não tem coluna de fonte |
| `source_raw` | `str \| None` | `None` | Célula crua que originou o rótulo (o texto de formulário, o haplogrupo, o nome de projeto) |
| `source_motivo` | `str \| None` | `None` | Por que não é laboratório: `texto_de_formulario`, `empresa_nao_confirmada`, `nome_de_projeto`, `haplogrupo`, `nao_reconhecida`; `None` quando é laboratório |
| `medida` | `dict` | sempre presente | Estado da medida — ver §3 |

**Compatibilidade:** `data-dictionary.md#51` descreve `source` como "fonte declarada (empresa/laboratório);
primeira não vazia encontrada". A descrição deixa de valer para o **conteúdo** (passa a ser rótulo), mas o
tipo e a posição continuam. É delta declarado para `/reversa-sync`, não migração.

`evidence_for` (`data-dictionary.md#54`) continua devolvendo `source` do kit principal; o texto padrão
`"fonte não identificada no CSV"` só aparece quando `source` é `None` (CSV sem coluna de fonte). Com coluna e
células vazias, o rótulo é `não declarada`.

## 3. `medida` — estrutura nova dentro do kit

| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `estado` | `str` | `robusta`, `parcial` ou `insuficiente` |
| `rotulo` | `str` | `Medida robusta`, `Medida parcial`, `Medida insuficiente` |
| `motivos` | `tuple[str, ...]` | `bloco_pequeno` (maior < 15,0), `poucos_snps` (< 900), `total_baixo` (< 15,0) |
| `numeros` | `dict` | `total_cm`, `maior_bloco_cm`, `snps` — os mesmos que produziram o estado |

Regra (`core/qualidade_da_medida.py`):

| Condição | Estado |
|----------|--------|
| `total_cm < 15,0` | `insuficiente` (e, por consequência, todo bloco também está abaixo) |
| `total_cm ≥ 15,0` e `largest_segment_cm < 15,0` | `parcial` |
| `total_cm` e `largest_segment_cm` ≥ 15,0 e `snps_total < 900` | `parcial` |
| `total_cm` e `largest_segment_cm` ≥ 15,0 e (`snps_total` ≥ 900 ou ausente) | `robusta` |

`largest_segment_cm` ausente conta como abaixo do piso; `snps_total` ausente **não** penaliza (o arquivo
não declarou SNPs, e ausência de dado não é dado ruim).

## 4. Delta no resultado da aplicação

`ResultadoDeAnalise` (`src/application/dna_analysis.py`) ganha um campo por último:

| Campo | Tipo | Padrão | Conteúdo |
|-------|------|--------|----------|
| `cobertura` | `dict \| None` | `None` | Medida do arquivo, ou `None` quando o núcleo não a preencheu |

O dicionário `cobertura` é produzido por `core.cobertura_do_arquivo.medir(evidencias, linhas)`:

| Chave | Tipo | Conteúdo |
|-------|------|----------|
| `linhas` | `int` | Linhas do CSV lido |
| `evidencias` | `int` | Quantidade de pares (nome, kit) |
| `kits` | `int` | Kits distintos |
| `quantidade_de_laboratorios` | `int` | Rótulos do catálogo distintos (fora `não declarada` e `outro`) |
| `laboratorios` | `tuple[(str, int), ...]` | Rótulos com contagem, ordem decrescente e alfabética no empate |
| `grafias` | `int` | Valores distintos de fonte no arquivo (inclui vazio) |
| `cromossomos` | `int` | Cromossomos distintos vistos |
| `mediana_cm` | `float` | Mediana do total de cM por evidência |
| `segmentos` | `int` | Segmentos somados |
| `segmentos_abaixo_do_piso` | `int` | Segmentos com cM < 10,0 |
| `percentual_abaixo_do_piso` | `int` | Percentual inteiro desses segmentos (74 no arquivo real) |
| `evidencias_sem_bloco` | `int` | Evidências com maior bloco < 15,0 |
| `percentual_sem_bloco` | `int` | Percentual inteiro dessas evidências (88 no arquivo real) |
| `evidencias_snps_baixo` | `int` | Evidências com SNPs somados < 900 |
| `total_acima_com_bloco_abaixo` | `int` | Evidências com total ≥ 15,0 e maior bloco < 15,0 |
| `total_acima` | `int` | Evidências com total ≥ 15,0 |
| `sem_laboratorio` | `tuple[(str, int), ...]` | Texto do motivo com contagem, ordem decrescente e alfabética — texto pronto, para o template não traduzir código |
| `sem_laboratorio_total` | `int` | Soma das células sem laboratório (59 no arquivo real) |
| `tem_coluna_de_fonte` | `bool` | Se o CSV trouxe coluna de fonte reconhecida |

Nenhum campo é persistido. `projetar_analise` (payload da porta de histórico) **não** inclui `cobertura`
nem `medida`: não há coluna para elas e o histórico é registro, não tela.

## 5. Constantes de domínio novas

| Constante | Valor | Módulo | Natureza |
|-----------|-------|--------|----------|
| `LABORATORIOS` | 11 rótulos | `core/fontes_de_laboratorio.py` | Catálogo declarado pelo projeto |
| `PISO_TOTAL_CM` | `15.0` | `core/qualidade_da_medida.py` | Critério do projeto (`LIMITE_SEGMENTO_FRACO`) |
| `PISO_MAIOR_BLOCO_CM` | `15.0` | `core/qualidade_da_medida.py` | Critério do projeto; dono único do número |
| `PISO_SNPS` | `900` | `core/qualidade_da_medida.py` | **Corte de triagem declarado**, como o de 20,0 cM da feature 039 |
| `CM_MINIMO_SEGMENTO` | `10.0` | `core/endogamia.py` (reaproveitada) | Critério do projeto já existente |

`LIMITE_SEGMENTO_FRACO` (`core/genetic_evidence.py`) passa a referenciar `PISO_MAIOR_BLOCO_CM`, mantendo o
valor `15.0`. `_reversa_sdd/code-analysis.md#46` descreve a constante com esse valor — a linha continua
verdadeira e ganha, no `/reversa-sync`, a nota de que o dono do número mudou de módulo.

## 6. Nada muda no banco

`init.sql` fica como está: seis tabelas, sem coluna nova. Consequências explícitas:

- O histórico não guarda `cobertura` nem `medida`; reabrir uma análise antiga não reconstrói o painel.
- O `match_result` continua com o que decide parentesco; a fonte nunca foi persistida.
- Não há backfill, índice novo ou migração de esquema.
