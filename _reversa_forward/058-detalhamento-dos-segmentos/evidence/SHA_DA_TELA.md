# Delta do `SHA_DA_TELA` — feature 058

> Medido em `2026-11-11`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária vazia.

## Veredito: o hash não mudou

| | Antes (057) | Depois (058) |
|---|---:|---:|
| Bytes de `GET /` | 52.497 | 52.497 |
| `sha256` | `0b926895…` | `0b926895…` |

## O susto, e o que ele ensinou

A primeira versão do `<script>` da tabela ficou **fora** do `{% if segmentos %}`. A tabela em si
nunca aparece sem resultado, mas o script aparecia sempre — e o hash da tela de entrada mudou.

O teste `test_a_tela_nao_mudou_sem_mudanca_declarada` acusou na hora. A correção foi envolver o
bloco inteiro (comentário + script) no `{% if segmentos %}`, com as tags Jinja em linhas próprias,
de modo que o ramo falso não emita **nem o espaço em branco**. Medido: o hash voltou a `0b926895…`.

Regra que fica para as próximas features: **comentário e script também contam bytes** — tudo o que
nasce por causa do bloco de resultado precisa nascer dentro da condição do bloco.

## Como conferir

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_icone_de_atalho.py -q
```
