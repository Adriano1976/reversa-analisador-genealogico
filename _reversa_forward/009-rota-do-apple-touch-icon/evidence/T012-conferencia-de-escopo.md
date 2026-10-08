# T012 — Conferência de escopo por `diff`

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T012` · Data: `2026-10-08`

## O que esta conferência prova

Que a feature **acrescentou** em vez de alterar. É a conferência que sustenta a `RN-01`, a
`RN-02` e o `RF-05` sem pedir confiança: o `diff` é a prova, e não a afirmação de quem
implementou.

## O que **não** foi tocado

```
$ git diff --stat -- src/templates
(vazio)

$ git diff --stat -- src/core src/parsers src/reporting src/utils
(vazio)
```

| Área | Estado | Significado |
|---|---|---|
| `src/templates/` | **intocado** | As 8 telas literais mantêm diff textual zero. O ícone de atalho é descoberto por caminho convencional, sem declaração no documento (`RN-02`) |
| `src/core/` | **intocado** | Nenhuma regra de negócio criada, alterada ou removida (`RN-01`) |
| `src/parsers/` | **intocado** | — |
| `src/reporting/` | **intocado** | — |
| `src/utils/` | **intocado** | — |

É por isso que a paridade em 100 % do `T010` era esperada **por construção** — e medi-la
continua valendo, porque é o instrumento que distingue "não toquei" de "não percebi que
toquei".

## O que foi tocado, e quanto

```
$ git diff --stat -- src/app.py
 src/app.py | 48 +++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 47 insertions(+), 1 deletion(-)
```

**47 inserções e 1 única remoção.** A remoção é esta:

```
-from flask import Flask, render_template, request
```

Ela não é remoção de comportamento: é a **mesma** linha reescrita para trazer `send_file`.
Nos termos do projeto, o `src/app.py` mudou **em dois pontos**: um import e um bloco novo.

## O bloco novo, em uma linha

Uma constante com o caminho da arte derivada de `__file__` (nunca de entrada do cliente,
`D-06`), a chave correspondente em `app.config` — para que o caso de ausência seja testável
sem tocar no repositório — e uma rota `GET` que devolve o arquivo ou `404`.

**Nenhuma linha de `index()` foi tocada.** As três linhas do contrato HTTP existentes
continuam exatamente como estavam; a quarta entrou ao lado.

## Conferência cruzada com o contrato congelado

| Item vigiado | Origem | Estado |
|---|---|---|
| Literais de tela ao caractere | `W005` (006) | ✅ template intocado |
| `index()` sem passo de domínio | `W010` (006) | ✅ `index()` intocado |
| Assinatura de retorno do núcleo congelada | `W016` (006) | ✅ núcleo intocado |
| Nenhum teste removido ou desabilitado | `W017` (006) | ✅ 20 acrescentados, 0 removidos |
| Paridade em 100 % | `W018` (006) | ✅ medida, exit 0 |
| O dono não entra na chave nem no caminho | `W020` (007) | ✅ nada de armazenamento foi tocado |
| `src/static/` continua ausente | `W004` (003) | ✅ ausente no host e na imagem |

## Veredito

**APROVADO.** A entrega é acréscimo: uma rota, uma constante, um import reescrito e um
binário de arte. Todo o resto do sistema tem `diff` vazio.

## Fontes

- Saída de `git diff --stat` e `git diff`, executadas em 2026-10-08
- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (`RN-01`, `RN-02`, `RF-05`)
- `_reversa_forward/00{3,6,7}-*/regression-watch.md` (os itens vigiados herdados)
