# Correção — rótulo de parentesco com palavra inventada (`bisbisavô`)

**Data:** 2026-10-14
**Tipo:** defeito de **ortografia/formatação** no rótulo de parentesco. Não altera decisão de
matching, caminho, cM nem confronto.
**Arquivos alterados:** `src/core/documentary_relationship.py`,
`src/core/relationship_hypotheses.py`
**Teste novo:** `tests/test_rotulos_de_parentesco.py`

## O que o operador viu

No cartão **"Análise de conexão com Margarida"**, a coluna do parentesco exibia:

```
Tio/Tia-bisbisbisbisbisbisbisbisavô/avó ↔ Sobrinho(a)-bisbisbisbisbisbisbisbisneto(a)
```

**`bisbisbisbisbisbisbisbisavô` não existe em português.**

## A causa

`documentary_label` montava a palavra repetindo `"bis"`, em dois pontos:

```python
bis = "bis" * (acima - 2)                       # linha direta
f"Tio/Tia-{'bis' * (removidos - 1)}avô/avó …"   # colateral
```

A repetição só vale para o **segundo** grau acima dos pais. Do terceiro em diante a série
portuguesa troca o prefixo: `avô → bisavô → trisavô → tetravô → pentavô → hexavô → heptavô →
octavô → nonavô`.

## O alcance, medido

A varredura de `(0,0)` a `(12,12)` mostrou que o defeito **não era do grau da Margarida** —
atingia **todo grau a partir do quarto**:

| Grau | Antes | Agora |
|---|---|---|
| 3 gerações | `bisavô/avó ↔ bisneto(a)` | `bisavô/avó ↔ bisneto(a)` *(já correto)* |
| 4 | `bisbisavô/avó ↔ bisbisneto(a)` | **`trisavô/avó ↔ trisneto(a)`** |
| 5 | `bisbisbisavô/avó ↔ bisbisbisneto(a)` | **`tetravô/avó ↔ tetraneto(a)`** |
| 6 | `bisbisbisbisavô/…` | **`pentavô/avó ↔ pentaneto(a)`** |
| 9 | 8× `bis` | **`octavô/avó ↔ octaneto(a)`** |

Nos 62 cartões da análise real, **1** exibia o defeito (o da Margarida, grau 9 removido). Mas
o defeito estava na **regra de formação**, e não num grau específico: um teste só no caso da
Margarida teria fechado 1 e deixado os outros abertos. Por isso o teste novo cobre a série
inteira.

## O mesmo defeito em outro lugar

`relationship_hypotheses.SCP40_NOT_PUBLISHED` rotulava as relações não publicadas na 4.0 como
`2º bisavô/avó` e `3º bisavô/avó` — nomenclatura que não é a corrente. Alinhado para
**`trisavô/avó`** e **`tetravô/avó`**.

## O erro que eu introduzi ao corrigir, e como ele foi pego

A primeira versão da correção concatenava prefixo + radical:

```python
_PREFIXOS_DE_GERACAO = {5: "tetra", 6: "penta", …}
f"{prefixo}avô/avó"      # -> "tetraavô", "pentaavô"
```

`tetra-` e `penta-` **já terminam em vogal**, e o radical começa com outra — a forma correta
contrai (`tetravô`, `pentavô`), não alonga. A varredura pegou na hora.

A correção passou a guardar as **palavras prontas** numa tabela, eliminando a classe inteira
desse erro. Está registrado no docstring e há teste para cada grau, justamente porque
concatenar ali é tentador.

## Dois enganos meus no detector

Vale registrar, porque o detector é o instrumento de medição — se ele mente, a medição mente:

1. A primeira versão marcava `avô/avó ↔ bisneto(a)` como malformado. **`bisneto` é palavra
   correta** — o detector procurava a forma legítima.
2. A segunda marcava `10º avô`, porque `0º avô` casa **dentro** dele. Resolvido com `\b` à
   esquerda.

E, no teste, caí na mesma armadilha do `10º`: escrevi `assert "0º" not in nome_do_grau(graus)`
e isso reprovou `10º avô/avó`, que está certo. A checagem passou a ser na abertura da string.

## O que mudou na tela

| | Antes | Agora |
|---|---|---|
| Cartão da Margarida | 85 caracteres, palavra inventada | **44 caracteres**: `Tio/Tia-nonavô/avó ↔ Sobrinho(a)-nonaneto(a)` |
| Cartões com rótulo malformado | 1 de 62 | **0 de 62** |
| Rótulos de primo, irmão e tio/tia | — | **inalterados** |

## Acima de `nonavô`

A série para em `nonavô` (10 graus). Acima disso o rótulo usa **ordinal**: `9º avô`, `10º avô`.
`undecavô` é forma que quase ninguém reconhece, e um rótulo que o operador não entende é pior
que um numerado — a mesma razão pela qual o projeto já usa `N× remoção` nos primos.

O ordinal conta a partir de **`1º avô`**, e não do bisavô: 11 gerações são `9º avô`. Também
está fixado em teste, com o comentário do engano, porque eu mesmo marquei essa forma como
defeito ao revisar.

## Verificação

- **841 testes, zero falhas** (788 → 841; 53 novos no arquivo de rótulos).
- Os testes que já existiam para `(3,0)`, `(1,2)`, `(1,3)` e `(1,4)` passaram **sem edição** —
  a correção não tocou nos graus que já estavam certos.
- O caso real, pelo caminho de produção, medido no HTML renderizado.
