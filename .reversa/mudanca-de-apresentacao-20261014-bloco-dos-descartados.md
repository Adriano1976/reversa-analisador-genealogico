# Mudança — o bloco "Matches descartados" virou recolhível

**Data:** 2026-10-14
**Tipo:** **apresentação**. Não altera quais matches são descartados, nem o motivo, nem a contagem.
**Adendo:** `_reversa_sdd/addenda/020-bloco-dos-descartados-recolhivel.md` (declara `SHA_DA_TELA`)
**Arquivos alterados:** `src/templates/index.html`, `src/assets/app.css`
**Testes novos:** `tests/test_cartoes_recolhiveis.py::TestOBlocoDosDescartados` (6)
**Servidor:** reiniciado (PID 6784) e verificado com a análise real

## O pedido

> *"E agora, faça a mesma coisa usando o nome do grupo 'Matches descartados' como sendo
> `<summary>Matches descartados (266)</summary>`."*

O `<h2>` que titulava o grupo **virou o próprio `<summary>`** — não há cabeçalho acima de um
`details`, como não há nos cartões. A contagem sai de `{{ skipped_matches | length }}`: 266 é o
número da análise do operador, e o template não sabe qual é. Na análise usada na verificação,
o título renderizado foi `Matches descartados (642)`.

## O que mudou

| Onde | O quê |
|---|---|
| `index.html` | `<h2>` + `<div class="card">` → um único `<details class="card bloco-descartados">`, fechado |
| `index.html` | `<summary class="sumario-do-cartao">` embrulha o `card-header` com o `<h5>` |
| `index.html` | Os cartões de resultado ganharam `cartao-do-resultado`; o JS dos botões passou a usá-lo |
| `app.css` | `.bloco-descartados > summary .card-header h5` — título em `--muted`, um degrau menor |

### Duas decisões que o pedido não fixava

1. **Nasce fechado**, como os cartões: são centenas de linhas que o operador raramente lê, e o
   número no resumo já diz de relance o que ele precisa saber.
2. **Fica fora dos botões "Expandir/Recolher todas"**. Os botões dizem *"Expandir todas as
   análises"*, e arrastar 642 descartes junto seria surpresa. Isso exigiu marcador explícito: o
   seletor antigo (`details.card`) passaria a alcançar os dois blocos. A alternativa —
   `details.card:not(.bloco-descartados)` — foi descartada porque quebra em silêncio no dia em que
   um terceiro `details.card` aparecer.

O bloco continua sendo o **rodapé** da análise: mesma forma, não a mesma importância. A única
diferença visual é o título em `--muted`.

## `SHA_DA_TELA`, e a medição que quase me enganou

```
6cc496b4…   (30.768 bytes)
5e6842be…   (30.783 bytes)
```

**A causa é o seletor do JS, e não o bloco dos descartados**: o bloco vive sob
`{% if skipped_matches %}`, e na tela de entrada vazia esse nome é indefinido — o corpo do `if` é
pulado inteiro, comentário incluído. Os `+15` bytes são `details.card` → `details.cartao-do-resultado`.

A primeira medição deu **+69 bytes**, e o número não fechava com os 15 do seletor. Antes de declarar
o resíduo como "não sei", reconstruí o template anterior e comparei os **dois renders com o mesmo
contexto**: `+15`, uma única linha de diferença. O erro era comparar o HTML do Flask com um render
de Jinja de contexto vazio — laranjas com bananas.

## Verificação

| | |
|---|---|
| Suíte | **1007 passou, 9 pulados**, exit 0 |
| No servidor, análise real | **1** `<details class="card bloco-descartados">`, **0** aberto, `<h2>` antigo **0** |
| Título renderizado | `Matches descartados (642)` — dinâmico |
| Botões | 142 `cartao-do-resultado`; seletor do JS `details.cartao-do-resultado`, **0** do antigo |
| Recollhido ≠ removido | a tabela dos descartados continua no HTML, e há teste |

## Resíduo

1. Comportamento do navegador segue **não verificado em navegador real** (dívida que vem dos
   adendos `016` e `018`).
2. O bloco **não** entra no "Expandir todas", por decisão declarada — o teste
   `test_o_bloco_nao_e_alcancado_pelos_botoes_das_analises` é o que a registra.
