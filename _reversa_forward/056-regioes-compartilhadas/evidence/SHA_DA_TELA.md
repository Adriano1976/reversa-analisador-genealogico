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

## Atualização 2026-11-10 — relógio da análise

O indicador de carregamento passou a dizer **o que** está acontecendo ("Cruzando os matches com a
árvore…") e a **contar os segundos**. O delta é só o `<script>`:

| | Antes | Depois |
|---|---:|---:|
| Bytes de `GET /` | 51.218 | 52.497 |
| Delta | | **+1.279 bytes** |
| `sha256` | `3487986a…` | `0b926895…` |

Não há markup novo: o texto é reescrito pelo próprio script no `submit`. A mensagem fixa "Isso
pode levar alguns segundos" foi substituída por relógio + expectativa declarada ("a primeira
análise de uma árvore grande pode levar até 1 minuto").

## Atualização 2026-11-10 — cartão do hover não é mais recortado

O cartão que abre no hover das faixas do ideograma perdia o topo nas duas primeiras linhas do
mapa (cromossomos 1 e 2), como o operador reportou. A causa é de CSS e não de markup: o cartão
abre **acima** da faixa e o `overflow:hidden` de `details.card` recorta no raio da borda. O
conserto é do bloco das regiões — `details.card.regioes-compartilhadas{overflow:visible}` e o
raio migra para o cabeçalho, que é quem precisa dele.

| | Antes | Depois |
|---|---:|---:|
| Bytes de `GET /` | 52.497 | 52.497 |
| `sha256` | `0b926895…` | `0b926895…` |

**Nada mudou no hash, e isso é o esperado**: `app.css` é servido por `GET /app.css` e não
entra no hash da tela; e o bloco de regiões continua fechado em `GET /` (só renderiza com
resultado). A prova de que a folha mudou é a nova `test_o_cartao_do_hover_nao_e_recortado_pelo_card`.

### O que foi medido, e onde

Harness estático (o mesmo markup do bloco + `app.css` + `bootstrap`, Chrome headless,
janela de 1114 px), cartão aberto, hover forçado na faixa da linha 1:

| Medida | Valor |
|---|---:|
| Cartão do hover | 280 × 219 px (título + 4 linhas + 5 membros) |
| Espaço entre o topo do card e o trilho da linha 1 | 133 px |
| Recorte | **86 px** — 4 linhas (título, posição, tamanho e SNPs) |
| Espaço acima das linhas 1–4 (133 / 157 / 181 / 205 px) | **todas menores que 219 px** |

A última linha da tabela é o que decidiu o conserto: abrir o cartão para baixo nas primeiras
linhas exigiria inverter **quatro** linhas de nove, e o número muda com o zoom e com a
quantidade de membros. Liberar o recorte resolve para qualquer linha e para qualquer altura.

Na tela do operador o recorte foi de duas linhas (título e posição), e não de quatro: a altura
do cartão depende da largura do texto e do número de membros da faixa.

Antes e depois, os dois do mesmo harness e da mesma faixa da linha 1: `dica-antes.png` (cartão
começando em "Desfecho:") e `dica-depois.png` (cartão inteiro, começando no título).
