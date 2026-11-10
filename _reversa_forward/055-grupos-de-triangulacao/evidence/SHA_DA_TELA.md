# Delta do `SHA_DA_TELA` — feature 055

> Medido em `2026-11-09`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária vazia.

## O que mudou

| | Antes | Depois |
|---|---:|---:|
| Bytes de `GET /` | 51.218 | 52.768 |
| Delta | | **+1.550 bytes** |
| `sha256` | `3487986a8586ab91310d40d79841d22113e99aaeacf8e04b699a1b8fa12123c0` | `82258c2b8bbd1c00a61e768a18048785d9e9e4eb27e7284b1b313743b6e04cb8` |

## Por que mudou

Só o **painel da Fase 3**: entrou o formulário de triangulação, que existe para
rodar **sem árvore** (`RF-18`). Ele ocupa o lugar onde, antes, só havia o estado
vazio "esta fase precisa de uma árvore aberta" — o estado vazio continua lá, e o
formulário vem depois dele.

O bloco de grupos **não** entra em `GET /`: ele só é renderizado quando `grupos`
está preenchido, e a tela de entrada não tem grupos. O que confirma isso é o
próprio hash: +1.550 bytes é o tamanho do formulário, não o do bloco.

## Como conferir

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_icone_de_atalho.py -q
```

A constante vive em `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`), e a
atualização dela é ato declarado, com a data e o motivo no comentário acima da
constante.
