<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-06 a partir de 32 oportunidades -->
<!-- Atualizado a mao em 2026-10-01: OPP-20260929-5XGJ, OPP-20260929-NUMT, OPP-20260929-ZV52, OPP-20260929-UXEF e OPP-20260929-H2YY passaram a applied. O gerador nao foi reexecutado. -->
<!-- Atualizado em 2026-10-06 pela auditoria das quatro configuracoes pedidas pelo usuario: 6 oportunidades novas (#27 a #32), contexto arquitetura-src e contrato-de-dados-src. -->
<!-- Reconciliado em 2026-10-06: OPP-20260929-EHNZ marcada declined (alvos mortos e conteudo duplicado por OPP-20261006-3WR5) e alvos da OPP-20261003-PAST corrigidos. -->

# Registro de qualidade de código · visão global

> Gerado em `2026-10-06`. Ordenado por retorno estimado, não por estética.

Contextos: analise-dna, arquitetura-src, busca-caminho, contrato-de-dados-src, documentacao-sdd, pacote-reconstructed, upload-gedcom, verificacao-de-tipos. Total: **33 oportunidades**, sendo **26 aplicadas**, **1 aplicada em parte** (`OPP-20261006-LIGH`), **3 declined**, e **3 que permanecem `proposed` por não serem roteáveis**: `OPP-20261003-INIT` contradiz a RN-01, `OPP-20261006-YTSH` não é refactor, e `OPP-20261006-W4KD` está em caminho não liberado pela config.

> **Leitura do estado:** não sobrou nenhuma oportunidade de refactor puro em código. As três
> `proposed` e a `partially-applied` são bloqueios estruturais, cada um com a decisão que o sustenta:
> a `OPP-20261003-INIT` contradiz a RN-01; a `OPP-20261006-YTSH` muda a forma dos dados de modo
> observável para o template; a aresta restante da `OPP-20261006-LIGH` está fixada pela spec de
> `upload-gedcom`; e a `OPP-20261006-W4KD` depende de o usuário liberar `_reversa_sdd/**`.

## Reconciliação de 2026-10-06

O levantamento das oportunidades em aberto encontrou duas desatualizações de registro, ambas
corrigidas sem tocar em código do projeto:

| Oportunidade | Problema | Ação |
|---|---|---|
| `OPP-20260929-EHNZ` (#10) | Alvos em `analisador-genealogico/reconstructed/*.py`, raiz extinta em 2026-10-03; conteúdo duplicado pela `OPP-20261006-3WR5` | Marcada `declined` com `superseded_by`, preservando o registro e o encaminhamento ao Forward |
| `OPP-20261003-PAST` (#25) | Alvos em `src/reconstructed/...`, nível de pacote apagado pela `OPP-20261003-FLAT` | Alvos reescritos para `src/parsers/`, `src/reporting/`, `src/core/gedcom_state.py` e `src/core/dna_analysis.py` |

Nenhuma das duas mudanças altera escopo, custo ou risco do trabalho proposto.

## Auditoria de 2026-10-06: as quatro configurações pedidas

Diagnóstico sobre `src/` (22 módulos, 3.473 linhas), com evidência medida:

| Configuração | Situação | Evidência |
|---|---|---|
| Orientação a objeto | ❌ ausente por decisão | zero `class` e zero `@dataclass` em `src/` |
| Padrão de projeto | ❌ ausente | nenhuma fábrica, repositório, estratégia ou injeção; o único padrão é o singleton de estado global |
| Alta coesão | 🟡 parcial | excelente por pacote e módulo, ausente no nível de dado |
| Baixo acoplamento | 🔴 ausente | 2 ciclos de import em nível de pacote e estado global importado por 9 módulos |

As seis oportunidades novas:

| # | ID | Contexto | Verbo | Custo | Estado | O que resolve |
|---|----|----------|-------|-------|--------|---------------|
| #32 | `OPP-20261006-4KMB` | arquitetura-src | restructure | low | **applied** | guarda de leitura do GEDCOM duplicada em `app.py` |
| #28 | `OPP-20261006-ULVW` | arquitetura-src | decouple | medium | **applied** | ciclo `core/` ↔ `reporting/`, extinto por injeção do resolvedor |
| #27 | `OPP-20261006-3WR5` | arquitetura-src | decouple | high | **declined** | estado global mutável: spec fixa o comportamento, mitigação não autorizada, e a Onda 3 já descarta o mecanismo |
| #29 | `OPP-20261006-LIGH` | arquitetura-src | decouple | medium | **partially-applied** | ciclo `core/` ↔ `parsers/`: aresta do `csv_ingest` resolvida, a do `gedcom_parser` bloqueada por spec |
| #30 | `OPP-20261006-ESKO` | contrato-de-dados-src | standardize | medium | **applied** | superfície de compatibilidade de `path_search` reduzida de 18 nomes para 1 |
| #31 | `OPP-20261006-YTSH` | contrato-de-dados-src | modularize | high | proposed | contrato dos dicionários de domínio vive só no documento |
| #33 | `OPP-20261006-W4KD` | documentacao-sdd | standardize | low | proposed | specs afirmam que `reporting/` importa `core`, e os dois módulos novos não existem em artefato algum |

## Itens que NÃO devem ser roteados como refactor

| ID | Destino correto | Motivo |
|----|-----------------|--------|
| `OPP-20260929-EHNZ` | **declined** em 2026-10-06 | Alvos mortos e conteúdo duplicado por `OPP-20261006-3WR5`; o encaminhamento ao Forward foi transportado para lá |
| `OPP-20261006-3WR5` | **declined** em 2026-10-06 | Comportamento fixado por `upload-gedcom/requirements.md:23` e `design.md:33`; mitigação no legado nunca autorizada (`questions.md:262-264`); a Onda 3 já descarta o mecanismo (`discard_log.md` BR-DESCARTAR-001) |
| `OPP-20261003-PAST` | **declined** em 2026-10-06 | Alcance medido de 89 ocorrências em 18 arquivos, perda de precisão nos dois nomes de módulo e quebra de uma sonda de bug em `_reversa_bugs/`, sem ganho funcional |
| `OPP-20260929-DW3U` (opção A) | Decisão humana antes | Remover as entidades derruba testes de `tests/test_domain.py`: mesmo dilema de linha de base |
| `OPP-20260929-DW3U` (opção C) | Forward | Dar consumidor às entidades reescreve `upload.py`: mudança de comportamento |
| poda do pool por `given_index` | Forward | Muda qual candidato vence: mudança de comportamento |
| `OPP-20261006-YTSH` | `/reversa-requirements` | Eliminar a variação de chaves entre ramos muda a forma dos dados de modo observável para o template |
| orientação a objeto e padrões de projeto | `/reversa-requirements` ou `_reversa_sdd/migration/` | `paradigm_decision.md` escolheu Híbrido e proíbe aggregates com estado no núcleo de cálculo |
| `OPP-20261003-INIT` | Decisão humana antes | Contradiz a RN-01 |

## Ordem sugerida de ataque (auditoria de 2026-10-06)

| Ordem | ID | Verbo | Custo | Comando |
|-------|----|-------|-------|---------|
| ~~1~~ | ~~`OPP-20261006-4KMB`~~ | restructure | low | **aplicada em 2026-10-06** |
| ~~2~~ | ~~`OPP-20261006-ULVW`~~ | decouple | medium | **aplicada em 2026-10-06** |
| ~~3~~ | ~~`OPP-20261006-LIGH`~~ | decouple | medium | **aplicada em parte em 2026-10-06**; a aresta restante vai ao Forward |
| ~~4~~ | ~~`OPP-20261006-ESKO`~~ | standardize | medium | **aplicada em 2026-10-06** |
| 5 | `OPP-20261006-3WR5` | decouple | high | `/reversa-decouple OPP-20261006-3WR5` (só depois de decisão humana) |
| 6 | `OPP-20261006-YTSH` | modularize | high | `/reversa-requirements` (não é refactor) |

## Por contexto

| Contexto | Oportunidades | Caminho |
|----------|---------------|---------|
| `analise-dna` | 8 | `_reversa_refactor/analise-dna/` |
| `arquitetura-src` | 4 | `_reversa_refactor/arquitetura-src/` |
| `busca-caminho` | 4 | `_reversa_refactor/busca-caminho/` |
| `contrato-de-dados-src` | 2 | `_reversa_refactor/contrato-de-dados-src/` |
| `documentacao-sdd` | 1 | `_reversa_refactor/documentacao-sdd/` |
| `pacote-reconstructed` | 9 | `_reversa_refactor/pacote-reconstructed/` |
| `upload-gedcom` | 3 (1 declined) | `_reversa_refactor/upload-gedcom/` |
| `verificacao-de-tipos` | 1 | `_reversa_refactor/verificacao-de-tipos/` |

## Roteamento aprovado em 2026-09-29

Ordem de encadeamento definida pelo usuário. As 11 primeiras foram aplicadas sob o gate de edição do legado liberado; as demais seguem a mesma ordem e param no gate até serem autorizadas.

| Ordem | ID | Comando |
|-------|----|---------|
| 1 | `OPP-20260929-TPSH` | `/reversa-restructure OPP-20260929-TPSH` |
| 2 | `OPP-20260929-AU76` | `/reversa-optimize OPP-20260929-AU76` |
| 3 | `OPP-20260929-32Q7` | `/reversa-prune OPP-20260929-32Q7` |
| 4 | `OPP-20260929-SEQO` | `/reversa-prune OPP-20260929-SEQO` |

## Linha de base medida em 2026-10-06

| Verificação | Resultado |
|---|---|
| Suíte (`py -3.14 -m pytest -q`) | 164 passam, 15 erros de ambiente (`PermissionError` do sandbox em `tmp_path`) |
| Verificação de tipos (`py -3.14 -m pyrefly check src`) | 27 erros |

---
*Gerado pelo Reversa-Refactor em 2026-10-06.*
