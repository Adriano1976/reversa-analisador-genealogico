<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-modularize em 2026-10-03 a partir de 5 oportunidades e 2 transformacoes -->

# Índice de qualidade de código · pacote-reconstructed

> Gerado em `2026-10-03`. Fonte de verdade: `../opportunities/*.md`.
> Duas transformações aplicadas neste contexto.

## Oportunidades

Ordenadas por retorno estimado, não pela ordem da árvore proposta.

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #19 | `OPP-20261003-TWNT` | modularize | green | acoplamento: seis módulos importavam as globais de `upload.py` | low | **applied** | estado separado do carregamento, e o split em `parsers/` deixa de esconder o estado dentro do parser |
| #20 | `OPP-20261003-DWJC` | decouple | green | acoplamento estrutural: um módulo interno importa pela fachada | low | **applied** | a fachada volta a existir só para consumidores externos, liberando a reorganização e a aposentadoria futura dela |
| #21 | `OPP-20261003-RGKA` | modularize | green | coesão e auditabilidade: heurística de domínio presa no fluxo | low | **applied** | heurística de cM isolada e auditável, com a origem declarada que o princípio V exige |
| #22 | `OPP-20261003-LMAY` | standardize | green | clareza: nomes que descrevem o que os módulos já não fazem | low | proposed | nomes alinhados ao papel real, incluindo os docstrings que induzem a erro |
| #18 | `OPP-20261003-GUE7` | modularize | green | clareza: 12 módulos planos, cinco papéis, nenhuma fronteira visível | high | proposed | fronteiras explícitas entre parsing, núcleo, apresentação e validação |

## Transformações

| OPP | Estado | Plano | Diferenças aplicadas | Rede de segurança |
|-----|--------|-------|----------------------|-------------------|
| `OPP-20261003-TWNT` | **aplicada em 2026-10-03** | `plan.html` | 20 arquivos (3 estruturais, 17 de migração) | suíte na linha de base e paridade em 100 por cento; ver `transformation.md` |
| `OPP-20261003-DWJC` | **aplicada em 2026-10-03** | `plan.html` | 1 arquivo, 1 linha trocada por 2 | suíte na linha de base e paridade em 100 por cento; fan-in interno da fachada de 1 para 0 |
| `OPP-20261003-RGKA` | **aplicada em 2026-10-03** | `plan.html` | 2 arquivos novos (`core/` e `core/cm_estimator.py`) e 1 arquivo reduzido de 137 para 122 linhas | suíte na linha de base, paridade em 100 por cento e equivalência direta da costura em 51 sondagens |
| `OPP-20261003-GUE7` | não iniciada | - | não | não iniciada |
| `OPP-20261003-LMAY` | não iniciada | - | não | não iniciada |

### Efeito da `OPP-20261003-TWNT`

`src/reconstructed/upload.py` deixou de existir. Em seu lugar:

| Módulo | Responsabilidade única | Linhas |
|--------|------------------------|--------|
| `gedcom_state.py` | registro do estado do processo e acesso aos registros | 45 |
| `gedcom_parser.py` | leitura do GEDCOM e construção do grafo | 67 |

A transformação ficou vermelha na primeira aplicação (suíte com 60 erros) e foi revertida pelo diff antes de ser corrigida e reaplicada. O ciclo completo está registrado em `transformations/OPP-20261003-TWNT-separar-estado-do-parser/transformation.md`.

### Efeito da `OPP-20261003-RGKA`

`dna_analysis.py` deixou de definir o conhecimento de cM. Em seu lugar:

| Módulo | Responsabilidade única | Linhas | Fan-out interno |
|--------|------------------------|--------|-----------------|
| `core/cm_estimator.py` | traduzir um valor de cM nas relações prováveis daquela faixa | 57 | **0** |

Efeito medido: `dna_analysis.py` de 137 para 122 linhas e de 4 para 2 definições de topo; a fachada continua expondo os mesmos 18 nomes de `__all__`, na mesma ordem. A tabela foi movida byte a byte, conferido por comparação de texto. O princípio V **continua formalmente aberto**: a transformação declara a ausência de fonte no próprio módulo, e não fecha a lacuna, porque a referência não existe no repositório.

## Fora do escopo do time Code Quality

Itens da árvore proposta que **não são refactor**, por alterarem comportamento observável ou introduzirem capacidade inexistente. Cada um é candidato a `/reversa-requirements`.

| Item proposto | Motivo | Encaminhamento |
|---|---|---|
| `models/person.py` | reintroduz modelo de classes removido deliberadamente em 2026-09-30 | `/reversa-requirements` |
| `models/relationship.py` (aresta tipada) | muda comportamento: implementa o princípio IV, ainda não implementado | `/reversa-requirements` |
| `utils/logger.py` | o projeto não tem logging algum | `/reversa-requirements` |
| `utils/file_handler.py` com limpeza de temporários | a limpeza não existe; e mover `validate.py` renomearia módulo que carrega contrato vigente | `/reversa-requirements` |
| `reporting/report_factory.py` | não existe fábrica de relatório, e abstração sem consumidor foi o que produziu as entidades removidas | `/reversa-requirements` |
| `src/__init__.py` | conflita com RN-01: `src` é raiz de caminho, não pacote | descartado |

## Pendências de registro, conhecidas

Nenhuma delas é código, e nenhuma foi introduzida por uma transformação:

| Onde | O que está desatualizado |
|---|---|
| `OPP-20261003-LMAY` | o registro ainda lista `src/reconstructed/upload.py` como alvo, e esse arquivo deixou de existir na `TWNT`. Sobrou `domain.py` para virar `text_cleaning.py` |
| `OPP-20261003-GUE7` | o inventário diz 12 arquivos e 1363 linhas; o pacote tem 15 arquivos e 1419 linhas, e o `core/` já existe com um módulo |
| `README.md` deste registro | diz que o harness de paridade "não pode mais rodar"; ele roda e dá 100 por cento nas 6 fixtures |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-03.*
