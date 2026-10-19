# 034 — Roadmap

## Fase 1 — O núcleo passa a dizer quem foi o candidato

`core.matching.match_candidates` devolve, além de `(candidate_pids, reason)`, os **três melhores
candidatos** avaliados (id, `given`, `final`, `jacc`), ordenados por nota. O **comportamento de
aceitação não muda**: mesmos limiares, mesmos pesos, mesma ordem.

Por que três, e não só o melhor: no caso real `*Maria de Fátima Oliveira de Jesus` o melhor
escolhido foi *Angelica Maria De Jesus De Oliveira* (`given` 55) e o candidato plausível era
*Maria de Fátima da Mata Oliveira* (n. 1966), que ficou atrás no ranking. Devolver só o melhor
mostraria a pessoa errada e esconderia a certa — o operador não teria como decidir.

Risco: a função é usada pela análise inteira; a mudança de retorno tem de ser compatível ou o
call site da análise tem de ser atualizado no mesmo passo.

## Fase 2 — A lista dos descartados ganha a coluna

`application.dna_analysis.projetar_analise` leva o candidato ao `DescartadoDaAnalise`; o bloco
`bloco-descartados` mostra nome do candidato + `given`/`final`/`jacc` na mesma linha do motivo.
Linha sem candidato plausível continua como hoje: só o motivo, sem botão.

## Fase 3 — Promover é uma ação do operador

Botão "usar este candidato" envia o pid escolhido; a análise roda de novo aquele kit com o nó
fixado e o cartão nasce completo (parentesco, veredito, janela, árvore sugerida).
Nenhum cartão existente é recalculado.

## Fase 4 — Prova e regressão

Testes de núcleo (retorno do candidato, aceitação intacta), de aplicação (projeção do
descartado) e de tela (coluna, botão, ausência de botão). Suíte completa.

## Ordem de entrega

Fase 1 e 2 juntas: já entregam o valor principal — **ver por que cada nome caiu**. A Fase 3 é a
que converte candidato em cartão, e é a mais cara (mexe no fluxo da análise).
