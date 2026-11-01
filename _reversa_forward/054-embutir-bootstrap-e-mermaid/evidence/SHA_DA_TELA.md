# Delta do `SHA_DA_TELA` — feature 054

> Medido em `2026-10-31`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária.

## O que mudou

| | Antes | Depois |
|---|---:|---:|
| Bytes de `GET /` | 51.612 | 51.218 |
| Delta | | **−394 bytes** |
| `sha256` | `577a17fd1513b29a1e3704f640bdcdfffbdcdbf373d3da4e148cb44529c87148` | `3487986a8586ab91310d40d79841d22113e99aaeacf8e04b699a1b8fa12123c0` |

## Por que mudou

Só o `<head>`. Saíram três tags de origem externa:

- a folha do Bootstrap em `cdn.jsdelivr.net`;
- os dois `preconnect` (`fonts.googleapis.com` e `fonts.gstatic.com`);
- a folha de fontes do Google.

Entraram duas tags locais:

- `<link href="/bootstrap.css?v=5.3.3" rel="stylesheet">`;
- `<link href="/fontes.css?v=1" rel="stylesheet">`.

As tags do Mermaid e do Bootstrap JS **não mudaram de lugar**: só o endereço passou de
`https://cdn.jsdelivr.net/...` para `/mermaid.js?v=10.9.8` e `/bootstrap.js?v=5.3.3`.

A diferença de 394 bytes é compatível com a troca: cada URL externa longa virou um caminho
curto, e o bloco de comentário Jinja do `<head>` foi reescrito (mais longo, mas comentário
Jinja não sai no documento servido — o que conta são as tags).

## O que **não** mudou

- Nenhum texto visível, classe de CSS, elemento de layout ou atributo de acessibilidade.
- A ordem das folhas: Bootstrap antes de `/app.css`.
- O `mermaid.initialize` e as opções do diagrama.
- A posição dos scripts: Mermaid no `<head>`, Bootstrap JS no fim do `<body>`.

## Onde a declaração vive

- Definitiva: `_reversa_sdd/addenda/054-embutir-bootstrap-e-mermaid.md`, criada pelo
  `/reversa-sync` (canal do projeto).
- Provisória desta rodada: este arquivo, mais o comentário acima de `SHA_DA_TELA` em
  `tests/test_icone_de_atalho.py`.
