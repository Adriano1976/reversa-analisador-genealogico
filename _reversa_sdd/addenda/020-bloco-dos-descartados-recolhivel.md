# Adendo: o bloco dos descartados é recolhível

> Identificador: `020-bloco-dos-descartados-recolhivel`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

Aplica ao grupo **"Matches descartados"** a mesma forma declarada no adendo `018` para os cartões
de resultado. **Declara mudança de `SHA_DA_TELA`**, e explica por que a causa dela não é o bloco.

## O pedido

> *"E agora, faça a mesma coisa usando o nome do grupo 'Matches descartados' como sendo
> `<summary>Matches descartados (266)</summary>`."*

O `<h2>` que titulava o grupo **virou o próprio `<summary>`** — não há cabeçalho acima de um
`details`, como não há nos cartões. A contagem sai de `{{ skipped_matches | length }}`, e não de um
número escrito: 266 é o valor da análise do operador, e o template não sabe qual é.

## O que mudou

| Onde | O quê |
|---|---|
| `index.html` | `<h2>Matches descartados (N)</h2>` + `<div class="card">` → um único `<details class="card bloco-descartados">` |
| `index.html` | `<summary class="sumario-do-cartao">` embrulha o `card-header` com o `<h5>`, igual aos cartões |
| `index.html` | Os cartões de resultado ganharam `cartao-do-resultado`, e o JS dos botões passou a usá-lo |
| `app.css` | `.bloco-descartados > summary .card-header h5` — título em `--muted` e um degrau menor |

### Duas decisões que o pedido não fixava

1. **Nasce fechado**, como os cartões: são centenas de linhas que o operador raramente lê, e o
   número no resumo já diz de relance o que ele precisa saber.
2. **Fica FORA dos botões "Expandir/Recolher todas"**. Os botões dizem *"Expandir todas as
   análises"*, e arrastar 266 descartes junto seria surpresa. Isso exigiu um marcador explícito
   (`cartao-do-resultado`) porque o seletor antigo — `details.card` — passaria a alcançar os dois
   blocos. A alternativa (excluir por negação, `details.card:not(.bloco-descartados)`) foi
   descartada: ela quebra em silêncio no dia em que um terceiro `details.card` aparecer.

O bloco continua sendo o **rodapé** da análise, e a única diferença visual é o título em `--muted`:
mesma forma, não a mesma importância.

## `SHA_DA_TELA`, declarado

```
6cc496b4f81cec6867a2faaf1c1c1bc9401491159040a4f7916e5c9a641418dc   (30.768 bytes)
5e6842bec9258e912ca2f04b6a5ae92efa5fc937a4b124a7e77fda4459feedf7   (30.783 bytes)
```

**A causa é o seletor do JS, e não o bloco dos descartados.** O bloco vive sob
`{% if skipped_matches %}`, e na tela de entrada vazia `skipped_matches` é indefinido — o corpo do
`{% if %}` inteiro é pulado, comentário incluído. Os `+15` bytes são exatamente
`details.card` → `details.cartao-do-resultado` dentro do `<script>` global, que fica fora dos dois
ramos da tela.

Isso foi **medido, e não deduzido**. A primeira medição deu `+69` bytes, e o número não fechava com
os 15 do seletor; a causa era eu estar comparando o HTML do Flask com um render de Jinja de contexto
vazio — laranjas com bananas. A medição correta reconstrói o template anterior e compara os **dois
renders com o mesmo contexto**, que dá `+15` e uma única linha de diferença.

## Verificação

| | |
|---|---|
| Suíte | **1012 passou, 9 pulados**, exit 0 |
| Testes novos | `tests/test_cartoes_recolhiveis.py::TestOBlocoDosDescartados` (6) |
| Estrutura | o parser de HTML passou a distinguir os dois tipos de `details.card` (`do_resultado` / `descartados`) |
| Guarda contra o botão | teste que recusa o bloco carregar o marcador dos cartões de análise |
| Sem descarte | teste de que o bloco **não existe** quando `skipped_matches` é vazio |

## Resíduo declarado

1. **O comportamento do navegador segue não verificado em navegador real**, como nos adendos `016`
   e `018`. Os testes provam estrutura, classes, seletores e ligação.
2. **A tabela dos descartados continua no documento** com o bloco fechado — é o que preserva a
   leitura do descarte como texto, e há teste para isso.
3. **O bloco não entra no "Expandir todas"**, por decisão declarada acima. Se o operador quiser
   incluí-lo, é trocar o seletor do JS e o marcador no template, e o teste
   `test_o_bloco_nao_e_alcancado_pelos_botoes_das_analises` é o que registra a decisão atual.
