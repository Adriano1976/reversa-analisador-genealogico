# ADR-07 — Autoridade única para a limpeza de nome

- **Status:** Aceito e vigente (o **local** mudou; a decisão não)
- **Data da decisão:** 2026-09-29
- **Commit(s):** `9318864` — "refactor: unifica a limpeza de nome em domain.py (`OPP-B5F2` opção B)"
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Existiam **duas** implementações de limpeza de nome (correção de mojibake): uma em `domain.py` e uma cópia em `dna_analysis.py`. Elas **divergiam em 5 de 9 casos** — e a de `domain.py`, que era a mais correta, **não era consumida por nenhum caminho de produção**. Ou seja: o sistema usava a pior das duas, e a boa existia como código decorativo.

## Decisão

Mover os dois corpos de limpeza para um único módulo e fazer `dna_analysis` **importar de lá**, deixando **uma só implementação**.

## Evidência

- `9318864` e o adendo `_reversa_sdd/addenda/003-refactor-code-quality.md`.
- Hoje a autoridade é `src/utils/text_cleaning.py` (`strip_bad_utf`, `demojibake`) — o módulo foi **movido** de `domain.py` na reorganização em pacotes (ADR-11), sem alteração de comportamento.
- `src/core/documentary_relationship.py:150-161` — a comparação de nomes **depende** dessa autoridade: aplica a correção de mojibake antes de comparar, e é isso que faz um CSV sem acento encontrar o registro GEDCOM com acento.

## Justificativa

Duas cópias de uma regra de normalização produzem **dois resultados diferentes para a mesma entrada**, e o usuário não tem como saber qual deles gerou o resultado que está vendo. A divergência de 5 em 9 casos já era grande o suficiente para mudar quem casa com quem no matching — ou seja, mudava resultado de negócio.

## Consequências

- 🟢 **Passou a haver um único ponto de correção** para o problema mais recorrente dos dados reais: nomes portugueses exportados com encoding corrompido.
- 🟡 **Mapa de mojibake com dois defeitos cosméticos medidos por AST:** **18 entradas, mas 17 chaves efetivas** (a chave `"A�"` aparece duas vezes, e a segunda prevalece) e um **mapeamento identidade** (`"Ã": "Ã"`, um no-op). Inofensivo hoje por serem ambos `dict`, mas é imprecisão para quem contar as linhas.
- 🟢 **A faixa `Á-ú` na expressão de limpeza é redundante — e isso é bom.** Verificado por execução: `\w` é *Unicode-aware* no Python 3, então `ñ`, `Ñ`, `ý`, `ÿ`, `ö`, `ç` e `ã` sobrevivem por `\w` independentemente da faixa. O que a substituição remove é pontuação e símbolo.
- ⚠️ **`demojibake` prefere o original a um palpite pior:** só tenta o *round-trip* `latin1 → utf-8` quando há indício de mojibake, e **descarta o resultado** se ele ainda contiver caractere de substituição, `Ã` ou `A�`. Essa escolha é o que impede a limpeza de **criar** corrupção onde não havia.

## Alternativas consideradas

O nome do commit registra "**opção B**", o que implica que houve ao menos uma opção A avaliada no ciclo do `reversa-refactor`. **O conteúdo das alternativas não foi localizado nos artefatos disponíveis** — fica registrado como 🔴 lacuna de rastreabilidade, e não como ausência de análise.
