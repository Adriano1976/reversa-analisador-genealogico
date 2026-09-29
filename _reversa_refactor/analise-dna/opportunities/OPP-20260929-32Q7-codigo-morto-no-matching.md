---
schema_version: 1
id: OPP-20260929-32Q7
display_number: 2
context: analise-dna
verb: prune
title: "Código morto no matching: given_index; e docstring que cita constantes inexistentes"
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: build_ged_indexes, given_index
smell: índice construído e nunca lido; documentação que afirma existir código que não existe
roi:
  confidence: green
  impact: custo de construção pago em toda análise e uma afirmação falsa na documentação do módulo
  cost: low
  est_return: remove cerca de um terço do custo de build_ged_indexes e alinha o docstring ao código
state: applied
labels: [spec-desatualizada]
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs:
    - _reversa_sdd/domain.md#23-regras-de-namespace-de-nome-matching-viral
    - _reversa_sdd/analise-dna/tasks.md
    - _reversa_sdd/migration/topology_decision.md
    - _reversa_sdd/migration/data_migration_plan.md
---

## Roteamento

- Destino: `/reversa-prune OPP-20260929-32Q7`
- Ordem de encadeamento: **3 de 4**.
- Aprovada pelo usuário em 2026-09-29 para roteamento, com execução parando no gate.
- Motivo da posição: depois da `OPP-20260929-AU76`, para não haver dois diffs abertos nas mesmas
  funções. `prune` vem depois de `optimize` na ordem padrão de encadeamento.

## Correção de escopo (2026-09-29, após a varredura de morte)

Esta oportunidade pedia a remoção de três candidatos. A varredura completa mostrou que **dois deles
não existem no código**:

| Candidato | O que a oportunidade dizia | O que a varredura achou |
|-----------|---------------------------|-------------------------|
| `given_index` | construído e nunca lido | confirmado: 3 ocorrências, todas escritas, único leitor é o descarte `_` |
| `HARD_MIN` | "declarado mas não usado" | **não existe**. Só aparece no docstring `dna_analysis.py:11` |
| `GIVEN_MIN` | "declarado mas não usado" | **não existe**. Mesma linha de docstring |

A afirmação original veio do próprio docstring do módulo e de `_reversa_sdd/confidence-report.md`,
que se refere a `app.py:653-654` do **legado**, arquivo que não existe mais na árvore. A reconstrução
copiou a frase para o docstring sem trazer as constantes. O alvo real desta poda passou de 3 para 1,
mais uma correção de documentação.

## Antes observado

1. `build_ged_indexes` constrói e devolve três índices. O único chamador, em `dna_analysis`, escreve
   `ged_index, surname_index, _ = build_ged_indexes()` e descarta o terceiro. O `given_index` tem 23
   chaves no experimento com 3.000 pessoas e **nenhum** ponto do código o lê. `match_candidates`
   recebe apenas dois índices.
2. `dna_analysis.py:11` afirma no docstring que `HARD_MIN`/`GIVEN_MIN` são "declarados porém não
   usados (código morto)". Nenhum dos dois é declarado no módulo reconstruído.
3. O registro de paridade também está inexato: `_reversa_forward/002-integrar-rota-app-modulos/regression-watch.md`
   (OBS-03) e `_reversa_sdd/addenda/002-integrar-rota-app-modulos.md:28` afirmam que as constantes
   "foram preservadas nos módulos reconstruídos". O código não as contém.

## Transformação proposta

- **CHG-001:** remover a construção de `given_index` em `build_ged_indexes` e ajustar o retorno, com o
  desempacotamento do chamador.
- **CHG-002:** remover do docstring a linha que afirma existirem as constantes. Alternativa registrada:
  restaurar `HARD_MIN = 92` e `GIVEN_MIN = 90` para honrar o OBS-03. Decisão do usuário no gate, e a
  recomendação é remover a linha, porque `_reversa_sdd/migration/topology_decision.md:166` já decidiu
  que elas são removidas e "não entram no alvo", e `data_migration_plan.md:54` registra "não migrar".

## Rede de segurança exigida

`prune` só fecha com `preservation.method: death-proof` e prova anexada. A prova está em
`../transformations/OPP-20260929-32Q7-podar-given-index/before-after/death-proof.txt`, com varredura
completa dos 6 arquivos Python do projeto, classificação de cada ocorrência e busca por entrada
dinâmica. Resultado: as duas condições de morte cumpridas para `given_index`, e nenhuma ocorrência de
declaração para as duas constantes.

Nenhum teste referencia qualquer deles, então a suíte permanece em 50.

## Estado do gate

Especialista acionado em 2026-09-29 em `control_mode: gated`. Plano, prova de morte e confirmação
estão em `../transformations/OPP-20260929-32Q7-podar-given-index/`.

| Rede | Resultado |
|------|-----------|
| Suíte completa contra a sombra (AU76 + 32Q7) | 50 passed |
| Equivalência de saída, 2.206 comparações | 0 divergências |
| Prova de morte, varredura completa | anexada |

O patch é **empilhado**: aplica-se ao estado pós-AU76, não ao estado atual do projeto, porque as duas
transformações tocam `build_ged_indexes`. A aplicação está bloqueada por
`.reversa/reversa-config.json` em `allowLegacyEdits: false`.

## Risco

Baixo no código, com duas ressalvas de registro.

1. **Ressalva de spec.** `_reversa_sdd/analise-dna/tasks.md` T-07 define o critério de pronto como
   "`ged_index`, `surname_index`, `given_index` populados". Remover o índice desvia desse critério.
   Não é regra de negócio, então não cai na trava dura da alma, mas o desvio precisa de adendo de spec
   (`kind: specification`) aprovado pelo usuário.
2. **Divergência entre spec e código.** O OBS-03 e o adendo 002 afirmam que as constantes foram
   preservadas; o código não as tem. Ou o registro está errado, ou a reconstrução as perdeu. A decisão
   sobre `HARD_MIN`/`GIVEN_MIN` resolve isso em um sentido ou no outro.
