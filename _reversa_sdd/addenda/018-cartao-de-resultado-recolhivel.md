# Adendo: o cartão de resultado é recolhível

> Identificador: `018-cartao-de-resultado-recolhivel`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

**Emenda o comentário do índice em `src/templates/index.html`**, que declarava o colapso dos
cartões como descartado. Ele continua correto sobre o **motivo** — o Mermaid mede o container, e
fechado o container tem tamanho zero —, e deixa de valer como impedimento, porque o código já
continha a solução: o `toggle` que renderiza o diagrama na primeira abertura, criado para o
`grafo-do-registro` no adendo `015`.

Este adendo **declara uma mudança de `SHA_DA_TELA`**, e é o primeiro desde o `015` a mexer no
`<script>` global.

## O pedido

> *"Implemente o elemento `<details>` no HTML para cada Resultado da Análise. Com isso, o usuário
> terá melhor controle do que ver. Isso seria uma lista suspensa?"*

**Não é uma lista suspensa.** Lista suspensa é `<select>` — o operador escolhe um valor, e a
escolha **substitui** o que estava visível. `<details>` é um **widget de divulgação**: o conteúdo
está no documento e continua lá, apenas escondido, e o operador pode abrir vários ao mesmo tempo.
A diferença não é de vocabulário: é ela que garante que nada some da análise (ver a seção
"Nada sai do documento").

## O que mudou

| Onde | O quê |
|---|---|
| `index.html` | `<div class="card" id="resultado-N">` → `<details class="card" id="resultado-N">`, fechado por padrão |
| `index.html` | O `card-header` passou a ser **embrulhado** por `<summary class="sumario-do-cartao">`, e não substituído |
| `index.html` | Dois botões — **Expandir todas as análises** e **Recolher todas** —, guardados por `dna_results \| length > 1` |
| `index.html` | O `<script>` global: o `toggle` do Mermaid deixou de nomear `details.grafo-do-registro` e passou a alcançar qualquer `details` com diagrama |
| `app.css` | `details.card`, `summary.sumario-do-cartao`, o losango de aberto/fechado e os dois botões |

### Por que o `card-header` foi embrulhado, e não substituído

Fechado, o cartão tem de continuar dizendo **de quem é, quanto é e qual o veredito** — quem decide
se vale abrir decide pelo cabeçalho. Manter `<div class="card-header">` dentro do `<summary>`
preserva isso e, de quebra, preserva o extrator do teste do índice
(`test_estado_do_resultado.py::_cabecalhos`, que procura literalmente `<div class="card-header">`).
Substituir o `div` pelo `summary` teria quebrado o teste **sem** quebrar a tela — o pior tipo de
quebra.

## Os dois acoplamentos que o recolhimento cria

Nenhum dos dois existia antes, e os dois produzem defeito silencioso:

1. **O índice manda para `#resultado-N`, e o cartão está fechado.** O clique levaria a um cartão
   recolhido, e o operador concluiria que o link não funciona. `abrirCartaoDoAlvo` abre o
   `<details>` do alvo, no carregamento e no `hashchange` — o `id` estar **no próprio `details`**
   é o que torna isso possível, e é por isso que há teste para essa posição.
2. **O "Voltar" mora no cabeçalho, que agora é o gatilho.** Sem guarda, clicar em "Voltar"
   fecharia o cartão enquanto a página rola de volta ao índice. O `stopPropagation` no link corta
   o caminho do evento antes do `summary`.

## Nada sai do documento

O recolhimento é **visual**. O texto das cinco seções continua no HTML, e isso é asserção de
teste, não promessa: `test_o_conteudo_dos_cartoes_continua_no_html` confere que as seções seguem
presentes com os cartões fechados. Uma implementação que removesse o conteúdo passaria em todos
os outros testes — e teria destruído a leitura da análise como texto.

## Verificação

| | |
|---|---|
| Suíte | **1001 passou, 2 falharam, 9 pulados** → depois do hash declarado, **1003 passou / 9 pulados** |
| Teste novo | `tests/test_cartoes_recolhiveis.py` — **28 testes** |
| Estrutura | lida por **parser de HTML**, não por regex: `<details>` que não fecha não é erro de HTML, o navegador fecha no lugar errado e engole os cartões seguintes |
| Sensibilidade do parser | 5 testes provam que ele **detecta** árvore quebrada (`TestOSensibilidadeDoParser`) |
| Contagem de cartões | a suíte foi de 984 para 1012 testes coletados: **+28**, exatamente o arquivo novo |

## `SHA_DA_TELA`, declarado

```
9cf0e558f30ca4fbffc52601b53dda32f758600ed89f43545a361c33a192c9b0   (29.486 bytes)
6cc496b4f81cec6867a2faaf1c1c1bc9401491159040a4f7916e5c9a641418dc   (30.768 bytes)
```

A tela de entrada vazia **não foi redesenhada**: os dois botões estão sob `{% if dna_results %}`
e não aparecem nela. O que entrou no que o hash mede foi o `<script>` global — o ouvinte de
`hashchange`, a guarda dos links em `summary` e os dois controles —, que vive fora dos dois ramos
da tela. `+1.282` bytes, todos de script.

## Resíduo declarado

1. **O comportamento do navegador não foi verificado em navegador real.** Vale para a guarda do
   `stopPropagation` no `summary`, e é dívida que já vinha do `016` (onde o `details` do
   `grafo-do-registro` nunca foi visto renderizando). O que os testes provam é **estrutura e
   ligação**: a árvore, as classes, os ouvintes e os seletores. Não provam o resultado visual do
   clique.
2. **O `<details>` fechado continua no documento.** Uma análise de 142 cartões segue com a mesma
   página de ~7 MB; o recolhimento economiza rolagem, não bytes. Reduzir o HTML exigiria remover
   conteúdo, que é exatamente o que a seção "Nada sai do documento" recusa.
3. **Os cartões nascem fechados.** É escolha de leitura, e não de estilo: o índice acima já traz
   as sete colunas de todas as conexões, então nada some quando o cartão fecha. Trocar o padrão é
   acrescentar ` open` ao `<details>` — uma palavra —, e a decisão é do operador.
