# Relatório da feature 036 — refino visual do cartão de resultado

> Data: `2026-10-19`
> Feature: `036-refino-do-cartao-de-resultado`
> Estágio: coding (T001 a T019; o adendo é a T020, no `/reversa-sync`)

## 1. O que foi entregue

O cabeçalho do cartão de conexão passou de **duas** para **três faixas** — título, selos e sinais —
com o "Voltar" e o indicador de abrir ancorados à direita. O cartão ganhou superfície em degradê,
barra lateral, raio de 16 px e sombra no claro. Nenhum texto, cor de veredito ou regra de domínio
mudou; os blocos "Matches descartados" e "Observações do arquivo" continuam como estavam (`RN-07`).

## 2. Superfícies tocadas

| Arquivo | Delta | O que mudou |
|---------|-------|-------------|
| `src/templates/index.html` | +6 / −1 | `span.conteudo-do-cabecalho` em volta do `h5`; `span.titulo-da-conexao`; `span.selos-do-cabecalho`; **nenhum `div` novo** |
| `src/assets/app.css` | +93 | bloco escopado em `.cartao-do-resultado`: casco, barra, três faixas, pílula do "Voltar", caixa do indicador, hover e telefone |
| `tests/test_cartao_em_tres_faixas.py` | novo, 11 testes | prende o arranjo no HTML renderizado e as regras que o sustentam |

## 3. Ajuste de execução declarado

O roadmap (`D-02`) previa `h5` em `flex` com o "Voltar" como segundo item. Na execução o arranjo
saiu em **grid com áreas nomeadas dentro de `.conteudo-do-cabecalho`**:

```css
grid-template-areas:"titulo acao" "selos acao" "sinais acao";
```

A razão é objetiva: no `flex`, o link só viraria o segundo item se fosse **movido no DOM** (ele está
entre os selos e os sinais), e movê-lo é justamente o tipo de edição que quebra os extratores de
teste. Com áreas nomeadas, o link continua onde está e é posicionado por área. O resultado visual é
o mesmo, e o `grid-row:1/-1` frágil que o roadmap recusava não foi usado — as três linhas são
explícitas.

## 4. Medições

| Medição | Antes | Depois |
|---------|-------|--------|
| Suíte completa | 1.282 passam, 11 pulados (72,73 s) | **1.293 passam, 11 pulados** (95,45 s) |
| Guardas do cartão e do estilo | — | **291 passam** |
| Teste novo | 9 falhas + 2 passes (TDD) | **11 passes** |
| `GET /` (tela vazia) | 30.781 bytes, `c4a34f7b…` | **30.781 bytes, `c4a34f7b…`** — sem edição |
| `app.css` | — | +93 linhas |
| `index.html` | — | +6 / −1 |

Contraste dos elementos novos (superfície `--surface`): título 10,87/12,14:1; sinais 6,11/6,48:1;
"Voltar" 6,26/7,67:1; chevron 6,11/6,48:1; barra 6,11→10,87 / 6,48→12,14:1. A borda da caixa é
decoração (1,47/1,38:1) — a pista é o chevron.

## 5. O que foi preservado

- Os quatro selos de estado e o selo de cM em `bg-secondary` (4,69:1).
- O link `voltar-ao-indice` com o texto, o `href` e o `visually-hidden` ao caractere.
- A árvore `details → summary → card-header → h5` e a ausência de `div` no cabeçalho.
- O `focus-visible`, o `aria` nativo e o `prefers-reduced-motion`.
- As regras genéricas de `summary` dos blocos irmãos, e as duas rotações do losango.

## 6. Evidências

- `evidence/antes/`: suíte, `git status`/`git log`, hashes, cópias das duas superfícies e a falha
  esperada do teste novo.
- `evidence/depois/`: guardas (291), teste novo (11), hash de `GET /`, suíte (1.293), escopo e a
  medição do cartão (`cartao.md`).

## 7. Nota de método

A primeira medição de `GET /` (43.064 bytes, `06557360…`) usou a pasta real de uploads, com os
arquivos listados; o `SHA_DA_TELA` mede a tela **vazia**, com pasta temporária, como o fixture
`cliente_de_upload` faz. A segunda medição — a válida — devolveu 30.781 bytes e `c4a34f7b…`, e a
diferença está registrada em `evidence/depois/hash.txt`.
