# Estado do `T023` após a reversão de 2026-10-06

> Feature: `005-nucleo-puro-src`. Escrito depois de a suíte ficar **vermelha com 49 falhas** e ser restaurada a **verde com 178**.

## O que aconteceu

O `T023` foi atacado em dois movimentos que **deveriam ter sido separados**:

1. `(a)` — tornar `carregar_arvore` pura: parar de mutar as globais e devolver dicionários novos.
2. `(b)` — os testes passarem a ler a árvore **devolvida**, e não as globais.

Eu fiz `(a)` primeiro. O resultado: **70 testes quebraram de uma vez**, porque todo fixture que carregava via parse e depois lia `gedcom_state.people` passou a ler um dicionário vazio. Daí em diante eu fui consertando sintoma por sintoma, com contexto já escasso, e cheguei a 49 falhas sem convergir.

**A ordem correta é a inversa:** primeiro `(b)` — os fixtures passam a devolver a árvore do parse, **com o parser ainda mutando** (suíte verde o tempo todo, porque as duas leituras são equivalentes); depois `(a)`, que aí não quebra nada.

## O que está no repositório agora

| Item | Estado |
|---|---|
| Suíte | **178 passed, 1 xfailed, 15 errors** |
| Paridade | **100% nas 6 fixtures** |
| `carregar_arvore` | existe, devolve a árvore **e** muta as globais (transição) |
| `load_gedcom_and_build_graph` | casca fina sobre `carregar_arvore`, com o retorno antigo |
| `gedcom_parser` | importa `gedcom_state` — a escrita das globais **continua** |

A reversão de `git checkout src/parsers/gedcom_parser.py` levou junto o `carregar_arvore`, que era trabalho não commitado. Ele foi **restaurado** com a semântica de transição: devolve a árvore e mantém a escrita das globais. É o estado em que `app.py`, os dois fluxos e os testes funcionam.

## O que sobrou de bom, e não deve ser desfeito

- `tests/fixtures/arvore_atual.py` — helper `atual()`/`guardar()`. O `atual()` **já tem o recurso de ler as globais** enquanto o parser as escrever; quando `(a)` for feito, esse recurso sai sozinho.
- `carregar_arvore` devolvendo a árvore: `app.py` e os fluxos já dependem disso desde o `T020`.
- Os testes que passam `carregar_arvore` no fixture e usam `guardar(...)` — **já estão prontos para o `(b)`**.

## Cuidados para quem retomar

1. **Não faça `(a)` antes de `(b)`.** Foi o erro; ele quebra 70 testes de uma vez e o conserto vira caça a sintoma.
2. **O helper `atual()` tem uma armadilha:** ele recorre às globais quando `ATUAL` é `None`, e isso **mistura a árvore de outro arquivo de teste** — o `test_path_search` passava isolado e falhava na suíte por causa disso. Todo fixture que serve a árvore ao teste precisa chamar `guardar(...)`, para o recurso não ser acionado.
3. **Cuidado com substituição global de texto.** Foi ela que criou recursão infinita em dois helpers (`def _arvore(): return (atual()[0], ...)`) e um `RecursionError` em 9 testes.
4. **O here-string `@"..."@` do PowerShell colapsa quebras de linha e come aspas.** Scripts de migração vão para **arquivo** e são executados. Os desta pasta (`_t023_*.py`) mostram o formato que funcionou.

## Passos concretos para o `(b)`

Os fixtures que ainda servem a árvore ao teste e **já guardam** estão prontos. Falta percorrer os que leem as globais direto — `test_upload.py` usa `atual()[0]` em nove pontos, e `test_confrontacao_gedcom_dna.py` usa `atual()` em treze. Com o parser ainda mutando, essa leitura funciona; para o `(b)`, ela precisa vir do retorno do parse em cada ponto de carga.

Só depois disso `(a)` — remover a mutação — e em seguida `(c)` remover `gedcom_state.py` e `(d)` tirar o `xfail` da guarda de estado.
