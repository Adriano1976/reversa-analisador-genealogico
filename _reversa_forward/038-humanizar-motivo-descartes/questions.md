# Perguntas em aberto → premissas assumidas

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Modo: **forward autônomo** ("não parar") — o `/reversa-clarify` foi pulado de propósito, e cada
> `[DÚVIDA]` do `requirements.md` virou premissa explícita no `roadmap.md`.
> **Este arquivo é o que você revisa depois.** Cada item pode ser revertido sem refazer a feature.

## P-01 — Onde ficam os números na tela

**Pergunta original** (`requirements.md` §10, 1ª): o detalhe técnico deve ficar visível também na
tela, ou basta a coluna da planilha?

**Premissa adotada:** o detalhe fica **só** na planilha. A tela mostra a frase e o texto sob o
botão de download diz onde estão os números.

**Por que:** o pedido foi legibilidade na coluna Motivo; quatro números na mesma célula seriam a
mesma fórmula com outro nome. A planilha já é o lugar onde o operador confere o cálculo — é para lá
que a lista vai desde a feature 035.

**Se estiver errada:** o detalhe já viaja no mesmo dicionário do descarte (`motivo_detalhe`), então
reverter é acrescentar um elemento na célula do template, sem tocar no núcleo.

## P-02 — O motivo no histórico da promoção

**Pergunta original** (`requirements.md` §10, 2ª): o motivo guardado no histórico de uma promoção
passa a ser o texto humano, ou continua sendo a fórmula que o sistema deu na hora?

**Premissa adotada:** passa a ser o **texto humano**.

**Por que:** o cartão promovido diz "o sistema havia recusado: …" e repete esse texto. Deixar a
fórmula ali reintroduziria exatamente o que o operador pediu para sair, num lugar onde ele já
decidiu e só precisa lembrar o contexto.

**Se estiver errada:** registros antigos mantêm o texto antigo de qualquer forma; não há migração
nem backfill, e nada lê o motivo por conteúdo.

## P-03 — A redação das cinco frases

**Pergunta original** (`requirements.md` §10, 3ª): a redação final é a proposta, ou o operador quer
revisar palavra por palavra?

**Premissa adotada:** a redação proposta no `requirements.md` §10 / `roadmap.md` `D-03`, revisável
depois.

**Por que:** o processo autônomo não pode parar para escolher palavra. As frases estão numa tabela
única `código → frase` (`core/motivos_do_descarte.py`), para que a revisão seja uma linha por
frase, sem tocar em decisão nem em teste estrutural.

**Se estiver errada:** editar a tabela. Os testes que prendem a frase são de catálogo (por código),
então a revisão atualiza a constante junto.

---

## O que **não** foi assumido

- Nenhum limiar de aceitação foi tocado. `RN-29` e `RF-08` congelam a decisão, e a caracterização
  existente continua valendo.
- Nenhuma coluna de banco foi criada e nenhum dado foi migrado.
- Não foi decidido nada sobre a feature pausada `003`, que continua pausada.
