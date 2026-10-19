# 034 — Ações

## Fase 1+2 — a lista passa a mostrar quem a árvore oferecia

| # | Ação | Status | Arquivos |
|---|------|--------|----------|
| T001 | `avaliar_candidatos` devolve os três melhores, sem mudar a aceitação; `match_candidates` mantém o contrato de dois valores | [X] | `src/core/matching.py` |
| T002 | A análise passa a chamar a avaliação e leva os candidatos ao descarte (com ano de nascimento) | [X] | `src/core/dna_analysis.py` |
| T003 | `CandidatoDoDescarte` na porta e na projeção | [X] | `src/ports/__init__.py`, `src/application/dna_analysis.py` |
| T004 | Coluna "Candidatos na árvore" no bloco dos descartados, com contagem no cabeçalho | [X] | `src/templates/index.html` |
| T005 | Compatível (prenome + sobrenome) separado de "melhor avaliado" fraco | [X] | `src/core/matching.py`, `src/templates/index.html` |
| T006 | Ordem dos candidatos pela utilidade do operador, e não pela ordem da decisão | [X] | `src/core/matching.py` |
| T007 | Testes de núcleo, projeção e tela | [X] | `tests/test_candidatos_do_descarte.py` |
| T008 | Contrato congelado da caracterização atualizado com a chave nova | [X] | `tests/test_characterization_matching.py` |

## Fase 3 — promover um candidato a cartão

| # | Ação | Status | Arquivos |
|---|------|--------|----------|
| T009 | Botão "usar este candidato" (formulário próprio, com o que a análise original usou) | [X] | `src/templates/index.html` |
| T010 | `candidatos_fixos` no núcleo: a escolha do operador substitui o casamento para aquele nome | [X] | `src/core/dna_analysis.py`, `src/application/dna_analysis.py` |
| T011 | Rota: lê `promover` (nome\|pid\|motivo), inclusive as promoções anteriores, e passa ao caso de uso | [X] | `src/app.py` |
| T012 | Cartão promovido registra a promoção e o motivo original como observação | [X] | `src/core/dna_analysis.py` |
| T013 | Testes da promoção (um cartão a mais, nenhum existente alterado) | [X] | `tests/test_promocao_de_descarte.py` |
| T014 | Suíte completa, reinício do servidor e adendo | [X] | `_reversa_sdd/addenda/034-revisao-dos-descartes.md` |

## Nota de execução

A T014 exigiu corrigir antes o ambiente da suíte: a raiz temporária vivia em `tests/.tmp/`, e
o sandbox de escrita recusa criar subdiretório no workspace — 408 testes morriam no preparo.
Com a raiz em `%TEMP%/reversa-analisador-testes`, a suíte inteira rodou: **1233 passam, 11
pulados, 0 falham**. Na primeira execução completa apareceu uma regressão **pré-existente** que
o ambiente mascarava: o bloco `observacoes-do-arquivo` estava sem `open`, contrariando o adendo
`017`. Corrigido no mesmo passo.

## Notas de execução

Fase 1+2, medido no GEDCOM real (`..._V1_2_Tratado.ged` + CSV ativo, 2026-10-19): **366**
descartes, **281** com algum candidato avaliado e **76** com candidato compatível. A diferença
entre 281 e 76 é o motivo da T005.

A ordem da T006 nasceu da medição: ordenando pela regra de decisão (interseção de sobrenomes
primeiro), só **50** descartes mostravam um compatível; pela ordem do operador, **76**.

Fase 3, validada de ponta a ponta no mesmo GEDCOM:
- promover `Maria José de Souza Santos` → `Mariza Souza Santos`: **90 → 91** cartões, **366 →
  365** descartes; o cartão nasce com a observação da promoção e sem caminho.
- promover `Sheila Costa Bonates` → `Sheila Moreira Costa`: **com caminho 6 → 7**, com caminho
  documental de **10 pessoas** e veredito `ERRO CRONICO / QUEBRA DE LINHA`.

A promoção **não garante** caminho: o primeiro caso não tem, o segundo tem. É o operador quem
decide, e o resultado passa por todo o fluxo normal.
