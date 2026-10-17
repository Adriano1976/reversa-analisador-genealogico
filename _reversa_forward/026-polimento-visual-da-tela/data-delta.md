# Data Delta: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/026-polimento-visual-da-tela/requirements.md`

## 1. Veredito

**Nenhum dado de domínio, nenhum payload, nenhuma tabela e nenhuma migração.** O delta desta feature
é de **apresentação**: quatro definições de token saem, uma declaração de token ganha comentário e
dois comentários de bloco são corrigidos. As cores efetivas dos quatro estados e do texto neutro
continuam exatamente as mesmas.

## 2. O que não muda

| Camada | Situação |
|--------|----------|
| Modelo de domínio (`_reversa_sdd/data-dictionary.md`) | nenhuma estrutura criada, alterada ou removida |
| Esquema PostgreSQL (`init.sql`, 6 tabelas) | intocado |
| Payloads das portas (`src/ports/__init__.py`) | intocados |
| Formulários, rotas e respostas HTTP | intocados |
| Documento servido em `GET /` | intocado — nenhum byte muda |
| Arquivos do operador (`src/uploads/`) | intocados |

## 3. Delta de tokens

Saem da folha, por não terem nenhuma referência no sistema em execução:

| Token | Valor | Uso medido |
|-------|-------|------------|
| `--ok` | `#2F6B3A` | 0 |
| `--poss` | `#7A4F00` | 0 |
| `--conf` | `#A8321F` | 0 |
| `--inc` | `#6A6150` | 0 |

Permanecem, como a única declaração de cada cor de estado:

| Token | Valor | Uso |
|-------|-------|-----|
| `--st-compativel` | `#2F6B3A` | `.estado-COMPATIVEL` |
| `--st-possivel` | `#7A4F00` | `.estado-POSSIVEL` |
| `--st-conflitante` | `#A8321F` | `.estado-CONFLITANTE` |
| `--st-inconclusivo` | `#6A6150` | `.estado-INCONCLUSIVO` |

As 27 ocorrências de `var(--ok)` no repositório estão em documentos HTML autocontidos de
`_reversa_refactor/` e `_reversa_bugs/`, que declaram os próprios tokens e não carregam `/app.css`.
Nenhuma delas é consumidora da folha da tela.

## 4. Cores efetivas (invariantes)

O texto dos selos de estado é branco por `.badge[class*="estado-"]{color:#fff}`. O par texto/fundo
medido, com o selo de cor cheia, é:

| Estado | Fundo | Texto | Contraste |
|--------|-------|-------|-----------|
| `COMPATIVEL` | `#2F6B3A` | `#fff` | 6,39:1 |
| `POSSIVEL` | `#7A4F00` | `#fff` | 7,13:1 |
| `CONFLITANTE` | `#A8321F` | `#fff` | 6,69:1 |
| `INCONCLUSIVO` | `#6A6150` | `#fff` | 6,11:1 |

Texto neutro: `--muted` é `#6A6150` no claro e `#A99F88` no escuro. O valor claro coincide com o do
selo `INCONCLUSIVO`; o escuro **não** coincide.

## 5. A armadilha do alias

Se `--st-inconclusivo` passar a ser `var(--muted)`:

- no tema claro, nada muda (é o mesmo `#6A6150`);
- no tema escuro, o fundo do selo vira `#A99F88` e o texto branco cai para **2,62:1**, abaixo de
  4,5:1 exigidos por WCAG AA.

É por isso que o valor do selo é declarado **separadamente** do texto neutro, e por isso o comentário
ao lado do token registra o número. O teste `TestOContrasteDosSelos` resolve o `var()` pela cascata
nos dois temas e reprova a troca.

## 6. Tema escuro

Os quatro tokens `--st-*` **não** têm override no bloco `:root[data-bs-theme="dark"]`, e isso é
deliberado: o selo é cor cheia com texto branco nos dois temas, então o par texto/fundo não depende do
tema. O que muda no escuro é o texto neutro (`--muted`), e é justamente essa diferença que o selo não
pode herdar.

## 7. Migração e reversão

- **Migração de dados:** n/a.
- **Migração de configuração:** n/a.
- **Reversão:** `git revert` do commit da feature. Como o template não é tocado, não há hash, golden
  ou cache de cliente a realinhar; o `ETag` de `/app.css` muda sozinho e o navegador revalida.

## 8. Rastreabilidade

| Requisito | Onde o delta aparece |
|-----------|----------------------|
| `RF-04` | declaração de `--st-inconclusivo` com comentário |
| `RF-05` | comentário do bloco de estados com os quatro números |
| `RF-11` | remoção dos quatro tokens sem uso |
| `RF-06` | comentários do banner corrigidos |
| `RF-10` | `SHA_DA_TELA` inalterado (nenhum byte do documento muda) |
