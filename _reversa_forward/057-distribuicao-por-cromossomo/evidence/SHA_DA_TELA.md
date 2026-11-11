# Delta do `SHA_DA_TELA` — feature 057

> Medido em `2026-11-10`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária vazia.

## Veredito: o hash não mudou

| | Antes (056) | Depois (057) |
|---|---:|---:|
| Bytes de `GET /` | 52.497 | 52.497 |
| `sha256` | `0b926895…` | `0b926895…` |

## Por que não mudou

A feature só acrescenta marcação **dentro do bloco de resultado**: o sub-bloco do gráfico vive no
cartão "Regiões compartilhadas", que só é renderizado quando existe região. A tela de entrada
(`GET /` sem resultado) não ganhou byte nenhum, e a folha de estilo é servida por `GET /app.css`,
que não entra no hash.

A byte-igualdade é deduzida pela igualdade do `sha256`: se o hash de 52.497 bytes bate, o conteúdo
é o mesmo, byte a byte.

## Como conferir

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_icone_de_atalho.py -q
```

O teste prende o valor **e** reclama quando ele muda sem delta declarado aqui.
