<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-06 a partir de 4 oportunidades -->

# Índice de qualidade de código · arquitetura-src

> Gerado em `2026-10-06`. Fonte de verdade: `../opportunities/*.md`.
> Auditoria das quatro configurações pedidas pelo usuário (orientação a objeto, padrão de
> projeto, alta coesão, baixo acoplamento) sobre `src/`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #32 | `OPP-20261006-4KMB` | restructure | green | duas cópias das mesmas guardas de entrada, na superfície de contrato de erro do sistema | low | **applied** | uma autoridade única para resolver a árvore pedida, com as duas mensagens preservadas ao pé da letra |
| #28 | `OPP-20261006-ULVW` | decouple | green | ciclo de pacote `core/` ↔ `reporting/`: o renderizador navegava o domínio por importação | medium | **applied** | ciclo extinto por injeção do resolvedor, com a string Mermaid idêntica |
| #29 | `OPP-20261006-LIGH` | decouple | green | ciclo de pacote `core/` ↔ `parsers/`: a camada de leitura grava o estado do domínio | medium | **partially-applied** | aresta do `csv_ingest` resolvida; a do `gedcom_parser` está bloqueada por spec |
| #27 | `OPP-20261006-3WR5` | decouple | green | nove módulos acoplados por variável global mutável, e a raiz da corrida entre threads (L2) | high | **declined** | nenhum: o comportamento está fixado pela spec, a mitigação no legado nunca foi autorizada, e a Onda 3 da migração já descarta o mecanismo |

## Transformações

| OPP | Estado | Plano | Diferenças aplicadas | Rede de segurança |
|-----|--------|-------|----------------------|-------------------|
| `OPP-20261006-4KMB` | **aplicada em 2026-10-06** | - | 1 arquivo, 28 inserções e 6 remoções | suíte na linha de base e `pyrefly` em 27 erros |
| `OPP-20261006-ULVW` | **aplicada em 2026-10-06** | `plan.html` | 4 arquivos, 1 novo e cerca de 25 linhas de costura | 39 testes de caracterização Mermaid, suíte na linha de base e `pyrefly` em 27 erros |
| `OPP-20261006-LIGH` | **aplicada em parte em 2026-10-06** | - | 3 arquivos, 1 novo | rede de caracterização, suíte na linha de base e prova de identidade de `norm_name` nos três endereços |

### Efeito da `OPP-20261006-LIGH` (parcial, por decisão)

O ciclo tinha **duas arestas** e só uma é refactor puro:

| Aresta | Situação |
|---|---|
| `parsers/csv_ingest.py:42` → `core.name_normalization` | **resolvida:** `norm_name` foi para `src/utils/name_keys.py` e o `core` reexporta, preservando os três endereços |
| `parsers/gedcom_parser.py:15-16` → `core.gedcom_state` | **bloqueada por spec:** `upload-gedcom/design.md:33` exige que `load_gedcom_and_build_graph` substitua o estado, e `requirements.md:148` a fixa em `parsers/` |

| Aresta | Antes | Depois |
|---|---|---|
| `parsers` → `core` | 3 | **2** |
| Ciclo `core/` ↔ `parsers/` | presente | **presente** |

**Encaminhamento da aresta bloqueada:** `/reversa-forward`, com atualização da spec de
`upload-gedcom`. Mudá-la exige que o parser deixe de instalar estado, o que altera comportamento
observável e sai do verbo `decouple`. A migração já aloca essa correção ao alvo
(`topology_decision.md` divide o bloco em `core/tree` mais `application/upload_tree.py`).

### Efeito da `OPP-20261006-ULVW`

| Aresta | Antes | Depois |
|---|---|---|
| `reporting` → `core` | 3 | **0** |
| `core` → `reporting` | 2 | 2 (direção legítima, inalterada) |
| Ciclo `core/` ↔ `reporting/` | presente | **EXTINTO** |
| Ciclo `core/` ↔ `parsers/` | presente | presente (é a `OPP-20261006-LIGH`) |

A costura foi **injeção do resolvedor de domínio**, não movimentação do layout: `architecture.md` §3
proíbe tirar a decisão de desenho de `reporting/`. Os 21 pontos de chamada continuam lá, agora
satisfeitos por parâmetro.

**Pendência de documentação criada por esta transformação:** `_reversa_sdd/architecture.md` §3 e
`c4-components.md` afirmam que `reporting/mermaid_render.py` importa `core.family_navigation`,
`core.path_finding` e `core.gedcom_state`. Isso passou a ser falso e os dois artefatos precisam de
adendo.

## Ordem de encadeamento sugerida

| Ordem | Oportunidade | Por quê nesta posição |
|---|---|---|
| ~~1~~ | ~~`OPP-20261006-4KMB`~~ | **aplicada em 2026-10-06.** Sem dependências, `app.py` apenas |
| ~~2~~ | ~~`OPP-20261006-ULVW`~~ | **aplicada em 2026-10-06.** Ciclo `core/` ↔ `reporting/` extinto |
| 3 | `OPP-20261006-LIGH` | fecha o segundo ciclo de pacote; o passo 1 devolve valor e é o de menor risco |
| 4 | `OPP-20261006-ESKO` | usa a mesma classe de prova, e vem antes da `PAST` |
| não rotear ainda | `OPP-20261006-3WR5` | custo alto e oito arquivos de teste leem as globais; a migração já tem esta correção especificada para a borda |

## O que esta auditoria NÃO registra como refactor

| Item pedido | Situação | Encaminhamento |
|---|---|---|
| Orientação a objeto no núcleo | Ausente por decisão: `paradigm_decision.md` escolheu Híbrido e manda "não introduzir aggregates com estado no núcleo de cálculo" | `_reversa_sdd/migration/` (alvo) ou `/reversa-requirements` |
| Padrão de projeto | Ausente; o único padrão presente é o singleton de estado global, que é o item #27 | `/reversa-requirements` |
| Alta coesão no nível de dado | Registrado como `OPP-20261006-YTSH`, no contexto `contrato-de-dados-src` | `/reversa-requirements` |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-06.*
