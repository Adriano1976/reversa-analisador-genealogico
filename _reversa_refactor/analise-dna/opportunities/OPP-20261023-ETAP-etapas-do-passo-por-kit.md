---
schema_version: 1
id: OPP-20261023-ETAP
display_number: 49
context: analise-dna
verb: restructure
title: Passo por kit com 368 linhas: catorze etapas ainda sem nome dentro de _cartao_do_kit
target:
  files: [src/core/dna_analysis.py]
  symbol: _cartao_do_kit
smell: >
  A `OPP-20261023-ORQA` deu nome e assinatura ao passo por kit, mas o corpo continua
  sendo a concatenação de catorze etapas: mitigação de endogamia, casamento de nome,
  promoção, recusa, parentesco documental, endogamia estrutural, identidade, janela
  de vida, regra do operador, confronto, profundidade, anotação do diagrama, rótulo
  efetivo, validação, árvore sugerida e montagem do cartão. São 368 linhas, 8
  condicionais e 2 retornos, sem nenhuma fronteira interna.
roi:
  confidence: green
  impact: >
    É o trecho onde toda feature de análise de DNA encosta: as últimas doze entregas
    acrescentaram um bloco cada uma nesse mesmo corpo. Depois da ORQA, cada etapa
    custa apenas 3 a 5 parâmetros para ser extraída, porque o estado compartilhado já
    está no contexto; antes dela, cada extração precisaria carregar os 18 nomes. A
    janela de custo baixo está aberta agora.
  cost: medium
  est_return: >
    `_cartao_do_kit` com cerca de 224 linhas e seis etapas nomeadas (recusa,
    parentesco, endogamia, confronto, profundidade e rótulo), cada uma com 2 a 5
    parâmetros.
state: applied
traceability:
  soul: [.reversa/soul.md#3-decisoes-fundadoras]
  specs:
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/analise-dna/requirements.md
    - _reversa_sdd/adrs/24-nucleo-puro-arvore-por-parametro.md
---

## Antes observado

Medido no arquivo depois da `OPP-20261023-ORQA`, nesta sessão:

| Medida | Valor |
|---|---|
| linhas de `_cartao_do_kit` | **368** (590-957) |
| condicionais | 8 |
| retornos | 2 (`cartão` e `descarte`) |
| etapas encadeadas no corpo | 14 |

As catorze etapas, na ordem em que aparecem:

1. mitigação de endogamia do kit (`analisador.avaliar_segmentos`)
2. casamento de nome e cM (`avaliar_candidatos`)
3. promoção manual do descarte (`candidatos_fixos`)
4. recusa e montagem do descarte
5. escolha do parentesco documental entre candidatos
6. diagnóstico de endogamia estrutural
7. nomes resolvidos das reconvergências
8. identidade do match
9. janela de vida
10. regra do operador para idade impossível
11. confronto e rótulo efetivo
12. profundidade do caminho e anotação do diagrama
13. veredito de validação
14. árvore sugerida e montagem do cartão

## Por que agora, e não antes

A `ORQA` deixou o estado compartilhado em `_ContextoDaAnalise`. Com isso, extrair a
etapa 6, por exemplo, custa uma assinatura de três parâmetros:

```python
def _endogamia_do_par(contexto, pid, documentary):
    ...
    return diagnostico, arvore_da_endogamia, tem_caminho, selo
```

Sem o contexto, a mesma extração precisaria de `arvore`, `root_id`, `analisador` e
mais três nomes, que é o mesmo data clump um nível abaixo.

## Transformação proposta

Cinco extrações, na ordem em que o corpo as executa. Cada uma devolve tuplas ou
dicionários já montados, sem efeito fora de `contexto`:

| Etapa extraída | Parâmetros | Devolve |
|---|---|---|
| `_parentesco_do_kit` | contexto, kit, candidate_pids | pid, documentary, homonimos |
| `_endogamia_do_par` | contexto, pid, documentary | diagnostico, arvore_da_endogamia, tem_caminho, selo |
| `_janela_do_match` | contexto, kit, pid, documentary | documental apresentado, janela, identidade, avisos |
| `_confronto_e_profundidade` | contexto, por_kit, chave_kit, avisos, documentary | evidence, hypotheses, comparison, profundidade, anotacao |
| `_validacao_e_sugestao` | contexto, documento, comparacao, kit, identidade, janela | validacao, resumo, desenho |

O que fica dentro de `_cartao_do_kit`: as duas primeiras etapas (endogamia do kit e
casamento, que produzem o `descarte`), a recusa, o encadeamento e o dicionário de 40
chaves. Estimativa: cerca de 150 linhas.

## Fronteira de comportamento

Movimentação pura, sem reordenar efeito. As extrações preservam a ordem em que as
etapas rodam hoje, e nenhuma delas escreve fora do contexto e do `kit` que recebe.

## Rede de segurança

A mesma da `ORQA`, que continua disponível e vale para este corte:

- suíte completa, medida em **1625 passed, 9 skipped** depois da fase 1;
- `safety-net/equivalencia.py`, digest idêntico em três cenários
  (`b8d186c8…b570b5dd`).

O gate repete as duas provas antes e depois.

## Resultado da aplicação

Aplicada em 2026-10-23, sob gate de plano e de diff aprovados.

| Medida | Antes | Depois |
|---|---|---|
| `_cartao_do_kit` | 368 linhas, 8 condicionais | **224 linhas, 5 condicionais** |
| etapas nomeadas | 0 | 6 |
| módulo | 1.181 | 1.258 |

As seis extrações: `_recusa_do_kit`, `_parentesco_do_kit`, `_endogamia_estrutural`,
`_confronto_do_kit`, `_profundidade_do_caminho` e `_rotulo_do_confronto`.

A estimativa de 150 linhas não se confirmou: o piso é o dicionário de 40 chaves, que
são 96 linhas de dado e não de lógica. O registro completo está em
`../transformations/OPP-20261023-ETAP-etapas-do-passo-por-kit/transformation.md`.

Suíte: **1625 passed, 9 skipped** antes (108,78 s) e depois (95,87 s). Digest de
equivalência idêntico nos três cenários.

---
*Gerado pelo Reversa-Refactor em 2026-10-23, como fase 2 da OPP-20261023-ORQA. Aplicada no mesmo dia.*
