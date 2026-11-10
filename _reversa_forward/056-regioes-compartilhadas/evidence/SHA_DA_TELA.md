# Delta do `SHA_DA_TELA` — feature 056

> Medido em `2026-11-09`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária vazia.

## O que mudou

| | Antes (055) | Depois (056) |
|---|---:|---:|
| Bytes de `GET /` | 52.768 | 51.218 |
| Delta | | **−1.550 bytes** |
| `sha256` | `82258c2b8bbd1c00a61e768a18048785d9e9e4eb27e7284b1b313743b6e04cb8` | `3487986a8586ab91310d40d79841d22113e99aaeacf8e04b699a1b8fa12123c0` |

## Por que mudou

A 055 havia acrescentado o formulário de triangulação na Fase 3 (+1.550 bytes). A 056
**removeu o arquivo de triangulação** e, com ele, o formulário e o campo opcional. O bloco
de regiões nasce do CSV de matches, e só aparece quando há resultado — logo, nada novo
entra em `GET /`.

## A prova de que a remoção foi completa

O hash voltou **exatamente** ao valor de 2026-10-31 (`3487986a…`, 51.218 bytes), anterior
à 055. Não é "parecido": é idêntico, byte a byte. Se algum resquício do formulário tivesse
ficado, o hash seria outro.

## Como conferir

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_icone_de_atalho.py -q
```
