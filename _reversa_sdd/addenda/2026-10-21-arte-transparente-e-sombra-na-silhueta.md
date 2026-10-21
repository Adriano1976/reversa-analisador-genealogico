# Adendo: a arte do topo chegou transparente, e a caixa em volta dela saiu

> Identificador: `2026-10-21-arte-transparente-e-sombra-na-silhueta`
> Data: `2026-10-21`
> Cenário: **legado** (âncora em `_reversa_sdd/recursos-da-tela/` e no adendo `037`)
> **Origem do registro:** escrito à mão, a pedido do operador, no mesmo dia da troca. Não saiu do
> pipeline `/reversa-sync`, e **não tem número de feature** porque não nasceu de uma pasta em
> `_reversa_forward/` — o número viria de uma pasta que não existe, e um `039` falso seria lido
> como feature pelo próximo ciclo.

## Vigência

Vigente desde 2026-10-21.

Emenda o adendo `023-arte-do-topo-sem-o-titulo` (que fixou a fonte canônica anterior) e a emenda
`E009` do adendo `037-redesenho-das-tres-fases` (que punha a arte dentro de uma caixa).

## Os dois pedidos, nas palavras do operador

1. *"Substitua a imagem `docs/assets/img/banner-analisador.png` por essa nova que está anexada."*
2. *"A imagem continua com um fundo. Pode retirar o fundo e deixar transparente?"*

O segundo pedido parecia ser sobre a imagem. **Não era**: a imagem já chegava transparente. O
fundo era a caixa de CSS que a `E009` tinha criado.

## Delta 1 — a arte: de opaca com quadriculado gravado para PNG transparente

| | Antes (2026-10-16) | Depois (2026-10-21) |
|---|---|---|
| Fonte `docs/assets/img/banner-analisador.png` | 1.101.780 bytes · 1024×547 · RGB com o quadriculado desenhado | **175.212 bytes · 1408×752 · PNG de paleta com alfa real (`tRNS`)** |
| Alfa da fonte | opaco em 100 % dos pixels | 70,8 % em `alfa 0`, 26,6 % em `alfa 254` |
| Derivada `src/assets/banner-da-tela.png` | 318.911 bytes · 1024×547 | **438.161 bytes · 1408×752 · RGBA** |
| Transparência da derivada | 71,8 % | **73,4 %** |

### O que a receita teve de aprender

`tests/banner_da_tela.py` fazia `Image.open(FONTE).convert("RGB")` antes de derivar, porque as duas
artes anteriores chegavam **opacas**, com o xadrez de transparência desenhado no bitmap. Com a fonte
nova, essa linha jogaria a transparência fora e o fundo voltaria como **bloco opaco** — o mesmo
defeito de sempre, por outro caminho.

Nasceu `fonte_ja_tem_fundo_transparente(imagem)`: fonte com mais de 1 % de pixels transparentes vai
direto para `RGBA`, sem remoção; fonte opaca segue pela receita antiga, que continua íntegra.

### Um número que quase passou como "arte vazia"

A primeira medição desta troca devolveu **"100 % transparente"**. Não era defeito: o exportador
grava a opacidade total como **`254`**, não `255` — medido, `histograma[255] == 0`. Comparar com 255
fazia a arte inteira parecer vazia, e teria transformado três testes de arte em fiscais cegos (um
deles passaria medindo "zero resíduo" sobre uma imagem sem nenhum pixel opaco).

Foi introduzido `ALFA_OPACO = 250`, usado tanto pelo resíduo quanto pelas asserções de tinta.

### Os testes de arte foram re-medidos, não afrouxados

| Teste | O que mudou |
|---|---|
| transparência entre 10 % e 90 % | passa a contar `alfa >= 250`; mede **73,4 %** — e é ele que **pega a conversão errada**, que devolveria 0 % |
| 12 pontos de tinta | coordenadas **re-medidas** para a composição nova (folhas, galhos, tronco, hélice, páginas, capa, lombada, base); todos em alfa 254 |
| faixa estreita de saturação | conta `alfa >= 250`; mede **1.119** pixels (eram 455), piso de 150 mantido |
| caixa de regressão `(778,232)-(918,338)` | mede **0 px**; continua como guarda para uma fonte opaca futura |
| rota serve a derivada e não a fonte | segue valendo (fonte 175.212 ≠ derivada 438.161) |

## Delta 2 — a caixa da arte saiu (reversão declarada da `E009`)

| `.masthead-arte` | Antes (E009, 2026-10-20) | Depois |
|---|---|---|
| fundo | `background: var(--surface-2)` | `transparent` |
| borda | `1px solid var(--line)` | nenhuma |
| cantos | `border-radius: 16px` | sem efeito (sem superfície) |
| sombra | `box-shadow: 0 12px 28px` na caixa | **`filter: drop-shadow(...)` na imagem** |

**Por que não foi só apagar o painel:** sombra de caixa sobre fundo transparente não desaparece —
vira uma **névoa quadrada** atrás da arte. O `drop-shadow` segue o alfa do desenho (folhas, tronco,
livro) e desenha a **silhueta**. A sombra que o operador pediu em 2026-10-20 continua existindo;
mudou de forma, porque o objeto que a projeta mudou.

Isto é **reversão declarada**, não correção de erro: a `E009` respondeu a um pedido real ("uma caixa
com os cantos arredondados") sobre uma arte que era opaca. Com a arte transparente, a caixa virou a
única coisa entre o desenho e o cartão.

## O que NÃO mudou

- Rota `GET /banner.png`, `ETag`, `304` e o `404` quando a arte falta.
- A arte dentro de `.masthead-arte` mantém `w-50` e o teto de **280 px** — não foi pedido aumento.
- A ordem do documento (arte primeiro) e a grade de duas colunas da masthead.
- `SHA_DA_TELA`: a imagem não entra no HTML.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/recursos-da-tela/requirements.md` | §Evidência de execução | delta-de-dados | A fonte canônica tem 175.212 bytes em 1408×752; a derivada, 438.161 |
| `_reversa_sdd/recursos-da-tela/design.md` | §A receita do banner | regra-alterada | A receita decide pelo alfa da fonte antes de remover fundo |
| `_reversa_sdd/recursos-da-tela/contracts.md` | §Contrato da arte | delta-de-contrato-externo | A fonte é PNG de paleta com `tRNS`, e não RGB sem alfa |
| `_reversa_sdd/code-analysis.md` | §A arte servida não é a arte canônica | regra-alterada | Existem duas receitas: uma para fonte opaca com xadrez, outra para fonte transparente |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` | tabela de impacto | delta-de-dados | A fonte foi substituída de novo: 1.101.780 → **175.212** bytes |
| `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` | emenda `E009` | regra-removida | A caixa com fundo, borda e sombra deixou de existir; a sombra virou `drop-shadow` na imagem |
| `docs/features/recursos-da-tela.html` e `_reversa_docs/features/recursos-da-tela.html` | inventário e receita | delta-de-dados | Números, formato e passo 1 da receita atualizados |

## Regras sob vigilância

| ID | Regra | Onde é verificada |
|---|---|---|
| `A001` | A rota serve a **derivada**, nunca a fonte | `test_a_arte_servida_e_a_derivada_e_nao_a_fonte` |
| `A002` | Fonte com alfa **não** pode ser convertida para `RGB`: a derivada perderia a transparência | `test_a_arte_transparente_e_uma_fatia_util_da_imagem` (mediria 0 %) |
| `A003` | "Opaco" é `alfa >= 250`, porque o exportador grava 254 | `ALFA_OPACO`, usado por resíduo e pontos |
| `A004` | A arte não perde as partes do desenho | `test_a_arte_nao_perdeu_as_partes_claras_que_sao_arte` (12 pontos) |
| `A005` | `.masthead-arte` não tem fundo nem borda, e a sombra é `drop-shadow` na imagem | **sem teste automatizado** — só inspeção visual. É a lacuna deste adendo |

## Fontes

- `tests/banner_da_tela.py` — a receita, com `fonte_ja_tem_fundo_transparente` e `ALFA_OPACO`
- `tests/test_banner_do_topo.py` — os 20 testes da rota e da arte
- `src/assets/app.css` — bloco `.masthead-arte` (linha 156)
- `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` — a troca anterior
- `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` — a `E009`, agora revertida
- `docs/features/recursos-da-tela.html` — o inventário das artes
