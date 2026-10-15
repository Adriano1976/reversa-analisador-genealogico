# Mudança — o cartão de resultado virou recolhível

**Data:** 2026-10-14
**Tipo:** **apresentação** e **interação**. Não altera decisão de matching, caminho, cM, veredito,
contagem de cartões, ordem de apresentação nem uma linha de texto de contrato.
**Adendo:** `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` (declara mudança de `SHA_DA_TELA`)
**Arquivos alterados:** `src/templates/index.html`, `src/assets/app.css`
**Teste novo:** `tests/test_cartoes_recolhiveis.py` (28 testes)
**Teste alterado:** `tests/test_estilo_da_tela.py` (`CLASSES_DO_TEMPLATE` +3),
`tests/test_icone_de_atalho.py` (`SHA_DA_TELA` declarado)

## O pedido

> *"Implemente o elemento `<details>` no HTML para cada Resultado da Análise. Com isso, o usuário
> terá melhor controle do que ver. Isso seria uma lista suspensa?"*

**Não é lista suspensa.** Lista suspensa é `<select>`: o operador escolhe um valor e a escolha
**substitui** o que estava visível. `<details>` é widget de divulgação — o conteúdo permanece no
documento, apenas escondido, e vários podem ficar abertos ao mesmo tempo. A diferença decide o
desenho: é ela que permite recolher sem tirar nada da análise.

## O que já estava escrito contra isso, e por que deixou de valer

O próprio template registrava o colapso dos cartões como **descartado por motivo medido**:

> *"Colapsar os cartões seria a outra saída, e ela está descartada por um motivo medido: o Mermaid
> mede o tamanho do grafo no momento em que desenha, e um grafo dentro de um bloco fechado sai com
> dimensão errada quando o bloco abre."*

O motivo continua verdadeiro. O que mudou é que **a solução já existia no código**: o ouvinte de
`toggle` que renderiza o diagrama na primeira abertura, criado no adendo `015` para o
`grafo-do-registro`. O cartão em volta do grafo tem exatamente o mesmo problema do bloco do grafo —
bastou o seletor deixar de nomear aquela classe e passar a alcançar qualquer `details` com
diagrama. Não foi preciso inventar nada.

## O que mudou

| Onde | O quê |
|---|---|
| `index.html` | `<div class="card" id="resultado-N">` → `<details class="card" id="resultado-N">`, **fechado por padrão** |
| `index.html` | `card-header` **embrulhado** por `<summary class="sumario-do-cartao">`, não substituído |
| `index.html` | Botões **Expandir todas as análises** / **Recolher todas**, sob `dna_results \| length > 1` |
| `index.html` | `<script>`: `toggle` do Mermaid generalizado; `abrirCartaoDoAlvo`; guarda dos links em `summary`; os dois controles |
| `app.css` | `details.card`, `summary.sumario-do-cartao`, losango de aberto/fechado, `.botao-do-cartao` |

### O `card-header` foi embrulhado, e não substituído

Fechado, o cartão continua dizendo **de quem é, quanto é e o veredito** — quem decide se vale abrir
decide pelo cabeçalho. Além disso, o teste do índice extrai literalmente `<div class="card-header">`
(`test_estado_do_resultado.py::_cabecalhos`); trocar o `div` pelo `summary` teria quebrado o teste
**sem** quebrar a tela.

## Os dois acoplamentos novos, os dois com defeito silencioso

1. **Âncora e cartão fechado.** O índice manda para `#resultado-N`; com o cartão fechado, o clique
   levaria a um cartão recolhido e o link pareceria quebrado. `abrirCartaoDoAlvo` abre o alvo no
   carregamento e no `hashchange`. Isso só funciona porque o `id` está **no próprio `<details>`** —
   e há teste para essa posição.
2. **O "Voltar" dentro do gatilho.** O link mora no cabeçalho, que agora alterna o cartão: sem
   guarda, clicar em "Voltar" fecharia o cartão enquanto a página rola. `stopPropagation` no link.

## Nada sai do documento

O recolhimento é visual. As cinco seções continuam no HTML, e isso é asserção de teste
(`test_o_conteudo_dos_cartoes_continua_no_html`), não promessa: uma implementação que removesse o
conteúdo passaria em todos os outros testes e teria destruído a leitura da análise como texto.

## Verificação

| | |
|---|---|
| Suíte | **1003 passou, 9 pulados**, exit 0 (antes: 975 / 9) |
| Testes coletados | 984 → **1012** (+28, exatamente o arquivo novo) |
| Estrutura | lida por **parser de HTML**, e não por regex |
| Sensibilidade | 5 testes provam que o parser **detecta** árvore quebrada |
| No servidor, análise real de 142 cartões | **142** `<details class="card"`, **0** com `open`, **142** `summary` nomeados, 488 `</details>` balanceados, os dois botões, e as seções ainda no documento |

`SHA_DA_TELA`: `9cf0e558…` (29.486 bytes) → `6cc496b4…` (30.768). A tela de entrada vazia não foi
redesenhada — os botões estão sob `{% if dna_results %}` —, e o que entrou no hash foi o
`<script>` global, que vive fora dos dois ramos da tela.

## Resíduo declarado

1. **Nada foi verificado em navegador real.** Os testes provam estrutura, classes, seletores e
   ligação dos ouvintes; não provam o resultado visual do clique. A dívida já vinha do `016`.
2. **A página não encolheu.** 142 cartões fechados ainda são ~7 MB de HTML: o recolhimento
   economiza rolagem, não bytes.
3. **Fechado por padrão é escolha de leitura**, e a decisão é do operador: trocar exige acrescentar
   ` open` ao `<details>` — uma palavra.
