---
schema_version: 1
id: OPP-20261003-PAST
display_number: 25
context: pacote-reconstructed
verb: standardize
title: nome das pastas e de dois modulos diverge do exemplo do usuario
target:
  files: [src/parsers/, src/reporting/, src/core/gedcom_state.py, src/core/dna_analysis.py]
  symbol: nomes das pastas criadas pela OPP-20261003-GUE7 e das duas fachadas redistribuidas pela OPP-20261003-RAIZ
smell: o exemplo do usuario usa `parser/` no singular e `generator/` para a pasta de saida, e chama a orquestracao de `analyzer` e o estado de `state`. O pacote ficou com `parsers/`, `reporting/`, `dna_analysis.py` e `gedcom_state.py`
roi:
  confidence: green
  impact: cosmetico, mas nao uniforme. Os dois nomes de pasta custam pouco; os dois nomes de modulo alcancam uma fachada com 18 nomes reexportados e o modulo de estado que o harness importa
  cost: low
  est_return: os nomes do exemplo, em quatro itens
state: declined
declined_reason: Medicao de 2026-10-06 mostrou alcance de 18 arquivos, perda de precisao nos dois nomes de modulo e quebra de uma sonda de bug congelada, tudo sem ganho funcional. O usuario decidiu nao renomear. Ver a secao "Declinada em 2026-10-06" no fim do arquivo.
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
| `src/parsers/` | `src/parser/` | duas linhas de import por arquivo que a cita |
| `src/reporting/` | `src/generator/` | idem |
| `src/core/gedcom_state.py` | `src/core/state.py` | o modulo de estado, importado por seis modulos, cinco testes e o harness, que o chama de `GS` |
| `src/core/dna_analysis.py` | `src/core/analyzer.py` | a fachada com 18 nomes em `__all__`, consumida pelo `app.py`, por dois testes e pelo harness, que a chama de `D` |

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

## Correcao de alvos em 2026-10-06

O bloco `target` e as quatro linhas da tabela apontavam para `src/reconstructed/...`, caminho que
deixou de existir em 2026-10-03 com a propria `OPP-20261003-FLAT`, da qual esta oportunidade
depende. Os alvos foram reescritos para os caminhos atuais: `src/parsers/`, `src/reporting/`,
`src/core/gedcom_state.py` e `src/core/dna_analysis.py`.

A correcao e de registro: nenhum arquivo do projeto foi tocado, e o trabalho proposto continua
identico em escopo e em risco.

## Independencia em relacao a `OPP-20261006-ESKO`

As duas tocam nomes de modulo e caminhos de import, e por isso a relacao foi verificada:

| | `OPP-20261003-PAST` | `OPP-20261006-ESKO` |
|---|---|---|
| O que move | o nome do arquivo | o nome que o consumidor importa |
| `gedcom_state.py` | passa a se chamar `state.py` | nao e alvo |
| `dna_analysis.py` | passa a se chamar `analyzer.py` | nao e alvo |
| `path_search.py` | nao e alvo | `__all__` reduzido e consumidores migrados |

As superficies sao disjuntas, com uma ressalva de ordem: se as duas forem executadas, `PAST` deve
vir **depois** de `ESKO`, porque renomear `dna_analysis.py` enquanto ainda existem consumidores
importando 18 nomes dele multiplicaria as linhas a reescrever sem necessidade.

## Declinada em 2026-10-06

Esta oportunidade foi marcada `declined` por decisao do usuario, depois de a medicao contradizer a
estimativa de custo `low` registrada em 2026-10-03. A renomeacao **nao foi aplicada**: nenhum
arquivo do projeto foi tocado.

### O alcance real, medido por varredura

| Alvo | Ocorrencias | Arquivos |
|---|---|---|
| `parsers` | 43 | 15, incluindo 12 de teste e uma sonda em `_reversa_bugs/` |
| `gedcom_state` | 26 | 11, incluindo `_reversa_sdd/parity/harness.py` e `_verify_fix_gives_parity.py` |
| `dna_analysis` | 20 | 5, incluindo o harness e a mesma sonda |

Total: **89 ocorrencias em 18 arquivos**, e nao "duas linhas de import por arquivo" como o registro
estimava.

### Os tres motivos da recusa

1. **Os dois nomes de modulo propostos perdem informacao.** `gedcom_state.py` diz QUE estado e o
   estado; `state.py` nao diz. `dna_analysis.py` diz que e a analise de DNA; `analyzer.py` nao diz.
   Os nomes vieram de uma arvore generica de exemplo, e o projeto tem dominio concreto onde o nome
   especifico e melhor. `parser/` no singular era o unico item neutro.

2. **A renomeacao quebraria uma sonda de bug congelada.** `_reversa_bugs/analise-dna/bugs/
   BUG-20261004-EWSJ-.../evidence/probe_reproducao.py` importa `from parsers import gedcom_parser` e
   `from core.dna_analysis import dna_analysis`. Ela e a evidencia de reproducao daquele defeito, e
   `_reversa_bugs/**` nao esta nos `allowedPaths` da config, entao nao poderia ser corrigida.

3. **Nao ha ganho funcional.** Nenhum comportamento muda, nenhuma dependencia diminui, nenhum ciclo
   se fecha. Seria movimento de 18 arquivos por alinhamento a um exemplo, contra a regra do proprio
   time de nao propor transformacao como fim em si.

### O que continua valido

A tabela do exemplo do usuario em `generated/index.md` segue como leitura util: ela mostra que a
arvore proposta **esta de pe** com diferencas de nome. O que muda e que as diferencas deixam de ser
tratadas como pendencia.

Se em algum momento a decisao for renomear, os dois itens de pasta (`parsers/` para `parser/`) sao os
de melhor relacao custo-beneficio, e os dois de modulo exigem liberar `_reversa_bugs/**` na config
antes.

---
*Gerado pelo Reversa-Refactor em 2026-10-03. Alvos corrigidos em 2026-10-06.*
