<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-06 a partir de 1 oportunidade -->

# Índice de qualidade de código · contrato-de-dados-src

> Gerado em `2026-10-06`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #30 | `OPP-20261006-ESKO` | standardize | green | 18 nomes em `__all__`, dos quais 12 nunca usados pelo módulo, e 4 consumidores importando pelo caminho errado | medium | **applied** | `__all__` reduzido ao que o módulo define, e cada consumidor no módulo canônico |
| #31 | `OPP-20261006-YTSH` | modularize | green | 27 estruturas de domínio sem tipo, com contrato declarado só em Markdown, e chaves variáveis por ramo | high | proposed | tipos nomeados com origem única e verificação estática sobre as fronteiras que hoje são só string |

## Transformações

| OPP | Estado | Diferenças aplicadas | Rede de segurança |
|-----|--------|----------------------|-------------------|
| `OPP-20261006-ESKO` | **aplicada em 2026-10-06** | 4 arquivos em 2 lotes | suíte na linha de base, 39 testes de caracterização Mermaid e o **harness de paridade em 100 por cento rodado depois de editado** |

### Efeito da `OPP-20261006-ESKO`

| Item | Antes | Depois |
|---|---|---|
| `__all__` de `core/path_search.py` | 18 entradas, 17 reexportadas | **1**, o que o módulo define |
| Imports que existiam só para reexportar | 13 | **0** |
| Consumidores importando pelo caminho errado | 4 (2 testes e o harness) | **0** |
| Docstring com lista de consumidores inventada | sim | substituído pelo registro medido |

Dois achados do docstring eram **falsos**: `app.py` importa apenas `path_search`, e
`core/dna_analysis.py` não importa nada de `core.path_search`. A superfície existia para servir
consumidores que não existiam, além dos três reais.

## Rota descartada nesta auditoria, com medição

A rota barata (declarar `TypedDict` e anotar as assinaturas, sem tocar em lógica) foi **testada e
reprovada** com `pyrefly 1.3.2`: o `TypedDict` exige correspondência exata de chaves, chave a mais
é erro e chave obrigatória ausente é erro, e os ramos deste domínio montam dicionários com
conjuntos de chaves diferentes. Declarar tudo como `total=False` foi descartado porque anularia o
único ganho real da rota.

## Fora do escopo do time Code Quality

| Item | Motivo | Encaminhamento |
|---|---|---|
| Eliminar a variação de chaves entre o ramo de sucesso e o de não encontrado | A variação é observável para o template | `/reversa-requirements` |
| Introduzir classes de domínio no núcleo de cálculo | `paradigm_decision.md` proíbe aggregates com estado no núcleo e aloca os tipos ao alvo | `_reversa_sdd/migration/` |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-06.*
