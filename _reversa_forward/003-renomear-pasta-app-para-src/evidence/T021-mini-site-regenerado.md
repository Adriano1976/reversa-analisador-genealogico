# Evidência da T021 — mini-site regenerado

> Data: `2026-10-08`
> Ação: `T021` — Regenerar o mini-site de documentação para refletir a árvore nova
> Executado por: pipeline de documentação (`/reversa-docs`), com `reversa-extract-soul` antes.

## Por que não pelo ciclo de codificação

As rodadas 2 (2026-10-03) e 3 (2026-10-07) do `/reversa-coding` registraram `blocked` com a mesma
conclusão: não há ação de código nesta tarefa. Ela pertence ao pipeline de documentação. O `[ ]`
foi mantido nas duas rodadas em vez de ser marcado sem execução.

## O que mudou no mini-site

| Medida | Antes (2026-10-06) | Depois (2026-10-08) |
| --- | --- | --- |
| Módulos | 37 | 61 |
| Linhas não vazias | 5 966 | 9 972 |
| Pastas de código | 8 | 10 |
| Pacotes de import | 6 | 8 |
| Arestas de pacote | 13 | 20 |
| Ciclos de pacote | 2 | 0 |
| Eventos de timeline | 86 | 96 |
| Conceitos de glossário | 24 | 44 |

## Comandos de verificação e resultado

```text
node .reversa/_docs_render_check.js
  -> data.js x assets/data/: 6/6 chaves iguais; nav com 10 itens resolvendo no disco;
     script inline das 10 páginas compila. RESULTADO: tudo verde

.venv/Scripts/python.exe .reversa/_docs_smoke_test.py
  -> páginas verificadas no servidor: 10/10
     assets locais verificados por GET: 28
     erros do smoke test: 0
     links quebrados: 0
```

## Achado registrado neste fechamento

O mini-site marcava **2 ciclos de pacote** em vermelho; o código atual é **acíclico**. A quebra veio
de dois **commits diretos**, fora de qualquer feature do ciclo forward:

- `2443273` — `refactor(utils): move norm_name para utils e quebra o ciclo core-parsers`
- `87bcea5` — `refactor(reporting): injeta o resolvedor de diagrama e quebra o ciclo core-reporting`

Ambos de 2026-10-06, entre o encerramento da feature 004 e a abertura da 005. Por isso os adendos das
features 005, 006 e 007 registram a dívida #5 como **inalterada por elas**: quando a 005 começou, os
ciclos já não existiam. Nenhum artefato do `_reversa_sdd/` declara a quebra.

## Passivo que permanece, declarado e não corrigido aqui

As páginas de feature descrevem a extração de 2026-10-05 e algumas citações de arquivo e linha
morreram depois dela: `src/core/gedcom_state.py` foi apagado pela feature 005, e `_guardar_upload` e
`_resolver_caminho_armazenado` não existem mais em `src/app.py`. Cada página recebeu um bloco de
delta apontando os adendos vigentes, e as citações **não** foram reescritas, porque elas são o
registro daquela extração.
