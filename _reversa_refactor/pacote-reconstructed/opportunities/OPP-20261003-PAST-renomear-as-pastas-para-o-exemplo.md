---
schema_version: 1
id: OPP-20261003-PAST
display_number: 25
context: pacote-reconstructed
verb: standardize
title: nome das pastas e de dois modulos diverge do exemplo do usuario
target:
  files: [src/reconstructed/parsers/, src/reconstructed/reporting/, src/reconstructed/core/gedcom_state.py, src/reconstructed/core/dna_analysis.py]
  symbol: nomes das pastas criadas pela OPP-20261003-GUE7 e das duas fachadas redistribuidas pela OPP-20261003-RAIZ
smell: o exemplo do usuario usa `parser/` no singular e `generator/` para a pasta de saida, e chama a orquestracao de `analyzer` e o estado de `state`. O pacote ficou com `parsers/`, `reporting/`, `dna_analysis.py` e `gedcom_state.py`
roi:
  confidence: green
  impact: cosmetico, mas nao uniforme. Os dois nomes de pasta custam pouco; os dois nomes de modulo alcancam uma fachada com 18 nomes reexportados e o modulo de estado que o harness importa
  cost: low
  est_return: os nomes do exemplo, em quatro itens
state: proposed
traceability:
  soul:
    - .reversa/soul.md#proposito
  specs:
    - _reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#atualizacao-2026-10-03
---

## Antes observado

Esta oportunidade nasceu com dois itens, e herdou mais dois do lote B da `OPP-20261003-RAIZ`, que o gate recusou misturar com a movimentacao.

| Item hoje | Exemplo do usuario | Superficie |
|---|---|---|
| `parsers/` | `parser/` | duas linhas de import por arquivo que a cita |
| `reporting/` | `generator/` | idem |
| `core/gedcom_state.py` | `core/state.py` | o modulo de estado, importado por seis modulos, cinco testes e o harness, que o chama de `GS` |
| `core/dna_analysis.py` | `core/analyzer.py` | a fachada com 18 nomes em `__all__`, consumida pelo `app.py`, por dois testes e pelo harness, que a chama de `D` |

## Transformacao proposta

Quatro renomeacoes, sem mover nada, com os imports e a arvore do README atualizados. E trabalho de `standardize`: nenhuma fronteira de modulo muda, nenhum conteudo muda, e a prova e a suite mais a paridade mais o AST contra a copia congelada.

## Ordem interna recomendada

Os dois nomes de pasta primeiro, porque nao alcancam codigo de consumidor alem do proprio caminho de import. Depois os dois nomes de modulo, **um por gate**, porque cada um tem um consumidor sensivel: `gedcom_state` e o modulo cujo estado global o harness compara, e `dna_analysis` e a fachada reexportada.

## Ressalva honesta sobre `generator/`

`reporting/` foi escolhido na `GUE7` porque a pasta emite **apresentacao** (um diagrama Mermaid). No exemplo do usuario, `generator/` significa *"Modulo de Saida / Reconstrucao"* e contem `code_generator.py` (que transforma a analise em codigo novo) e `report_factory.py` (que gera relatorios). Nenhum dos dois existe aqui, e o projeto **nao gera codigo**: o unico produto de saida e o diagrama.

Ou seja: adotar `generator/` traz um nome que promete mais do que a pasta entrega. Se o criterio for o nome dizer o que a pasta faz, `reporting/` e mais fiel; se o criterio for espelhar o exemplo, `generator/` ganha. A decisao e do usuario no gate, e por isso os dois itens estao separados aqui.

`parser/` no singular nao tem essa objecao: a pasta guarda dois leitores e os dois sao parsers.

## Dependencia de ordem

Esta oportunidade vem **depois** da `OPP-20261003-FLAT`, e nao antes. O `FLAT` sobe `core/`, `parsers/`, `reporting/` e `utils/` para `src/` e apaga o nivel `reconstructed`; renomear as pastas antes obrigaria a mexer duas vezes nos mesmos imports. Feito depois, o `PAST` renomeia as pastas ja no lugar definitivo.
