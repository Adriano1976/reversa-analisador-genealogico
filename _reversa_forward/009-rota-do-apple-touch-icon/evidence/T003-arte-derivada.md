# T003 — A arte derivada, medida por sonda independente

> Feature: `009-rota-do-apple-touch-icon` · Ação: `T003` · Data: `2026-10-08`
> Sonda: `evidence/_t003_sonda_arte.py` · Exit code: **0 (APROVADO)**

## Por que a sonda é independente

A arte foi produzida por `tests/icone_de_atalho.py`, que usa a biblioteca de imagem. Se
esta conferência usasse a **mesma** biblioteca e o **mesmo** caminho de leitura, provaria
pouco: um erro de leitura passaria nos dois lados.

Então a prova principal é **estrutural, com a biblioteca padrão apenas**. O formato PNG
declara no próprio cabeçalho o tipo de cor, e o tipo **2** é `truecolor` — **sem canal
alfa**. Não existe pixel transparente em um PNG cujo cabeçalho diz que não há canal alfa:
é propriedade do formato, não leitura de amostra.

## 1. Prova estrutural (biblioteca padrão apenas)

```
arquivo            : src\assets\apple-touch-icon.png
bytes              : 16504
dimensoes (IHDR)   : 180x180
bits por canal     : 8
tipo de cor        : 2 = truecolor (SEM canal alfa)
compressao / filtro: 0 / 0   (0/0 = padrao)
entrelacamento     : 0   (0 = nenhum)
```

## 2. Segundo instrumento: cor dos cantos

```
modo / dimensoes   : RGB / (180, 180)
  canto sup-esq : (255, 255, 255)  ok
  canto sup-dir : (255, 255, 255)  ok
  canto inf-esq : (255, 255, 255)  ok
  canto inf-dir : (255, 255, 255)  ok
  centro (90,90)   : (228, 210, 160)
```

O centro **não** é branco — a arte continua visível. Uma composição mal feita que
cobrisse tudo de branco passaria nas quatro leituras de canto e falharia aqui.

## 3. A canônica, para contraste

```
canonica           : 512x512, tipo de cor 6 = truecolor+alfa
bytes canonica     : 32317
bytes / canonica   : 0.51x
```

**O contraste é o ponto inteiro da `D-02`.** A canônica é tipo **6** (com alfa) e a
derivada é tipo **2** (sem). Servir a canônica daria um ícone de atalho com fundo **preto**,
porque o sistema móvel compõe transparência sobre preto.

## 4. O cabeçalho descreve mesmo o fluxo?

```
IDAT descompactado : 97380 bytes
esperado (3 canais): 97380 bytes
```

O fluxo de imagem descompactado tem exatamente `altura × (1 + largura × 3)` bytes — que é
`180 × 541`. Isso prova que o arquivo **não está truncado** e que o cabeçalho descreve o
conteúdo, sem depender de nenhuma biblioteca de imagem.

## Veredito

| Afirmação | Instrumento | Resultado |
|---|---|---|
| 180×180 (`RF-02`) | IHDR, biblioteca padrão | ✅ |
| Sem canal alfa (`RF-03`) | tipo de cor 2 | ✅ |
| Fundo branco nos cantos (`RN-04`) | leitura de pixel | ✅ |
| Arte visível (não apagada) | leitura do centro | ✅ |
| Fluxo íntegro | descompactação do IDAT | ✅ |
| Tamanho da receita | contagem de bytes | ✅ 16.504 |

## Fontes

- `tests/icone_de_atalho.py` (a receita, com o valor esperado de 16.504 bytes)
- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (`RF-02`, `RF-03`, `RN-04`)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-02`)
