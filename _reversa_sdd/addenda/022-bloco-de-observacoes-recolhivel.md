# Adendo: o bloco "Observações do arquivo" é recolhível

> Identificador: `022-bloco-de-observacoes-recolhivel`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

Aplica ao bloco **"Observações do arquivo"** (adendo `017`) a mesma forma declarada no adendo `020`
para o grupo "Matches descartados". **Não altera `SHA_DA_TELA`** — verificado, e não suposto.

## O pedido

> *"Transforme o campo 'Observações do arquivo'. E agora, faça a mesma coisa usando o nome do grupo
> 'Observações do arquivo' como sendo `<summary>Observações do arquivo</summary>`."*

## O que mudou

| | Antes | Depois |
|---|---|---|
| Container | `<div class="observacoes-do-arquivo">` | `<details class="card observacoes-do-arquivo" open>` |
| Título | `<h3 class="h6">` | `<summary class="sumario-do-cartao">` com `<div class="card-header"><h5>` |
| Corpo | direto no `div` | `<div class="card-body">` |
| Estado inicial | sempre visível | **aberto** (`open`), e recolhível |

A classe `observacoes-do-arquivo` **fica no container**, e não é detalhe: é ela que o teste do
adendo `017` usa para achar o bloco e para prender que ele renderiza **fora** da guarda de
`dna_results`.

## A decisão que difere do bloco dos descartados: ele nasce ABERTO

O bloco dos descartados começa fechado porque é o **rodapé** da análise — centenas de linhas que o
operador raramente lê. Este carrega **aviso**: nome em mais de um kit, CSV sem coluna de kit,
linhas ignoradas, cabeçalho fora do lugar, raiz ambígua. Coisas que mudam a leitura do resultado.

O adendo `017` tirou esses avisos de dentro dos cartões **para que fossem lidos**. Escondê-los
atrás de um clique desfaria exatamente isso. O recolhimento continua disponível — o operador
fecha se quiser —, mas o padrão mostra.

Há precedente no próprio código: o `grafo-do-registro` usa
`{% if result.janela_de_vida != 'impossivel' %} open{% endif %}` — abre, e só recolhe quando há um
motivo. Aqui não há motivo para recolher por padrão.

Por consequência, na folha o bloco tem **aparência de aviso** e não de apêndice: o creme de
`--aviso-bg` percorre o bloco inteiro (`.observacoes-do-arquivo{--bs-card-bg:var(--aviso-bg);…}`),
enquanto o bloco dos descartados tem o título em `--muted`.

## `SHA_DA_TELA` NÃO mudou — e isso foi medido

O bloco vive sob `{% if observacoes_do_arquivo %}`, que é indefinido e falso na tela de entrada; o
corpo é pulado inteiro. Como as linhas do `{% if %}` e do `{% endif %}` não foram tocadas, o
whitespace que elas emitem continua idêntico — e o hash continua
`39c6257f43419adb15fb521a63a03fdb2193feab6adadd8b10ca11db02fd0560`. Os dois testes do hash passam
sem alteração, o que **é** a verificação.

## Três testes caíram, e as duas causas valem registro

### 1. "O primeiro `card-header` do documento" deixou de ser um cartão

`test_identidade_do_match.py::test_o_sinal_de_identidade_esta_no_cabecalho_do_cartao` e
`test_janela_de_vida.py::test_o_sinal_de_janela_esta_no_cabecalho_do_cartao` procuravam
`<div class="card-header">(.*?)</div>` e ficavam com o **primeiro** do arquivo. O bloco de avisos
agora também tem um `card-header`, e ele vem **antes** dos cartões — os dois passaram a medir o
bloco de avisos.

É a **terceira vez** nesta sessão que essa mesma forma de falha aparece: um elemento novo entra
antes, e um teste ancorado em "o primeiro que casar" passa a medir outra coisa (as outras duas
foram a prosa de um comentário Jinja e a remoção da tabela do índice). A correção é a mesma nos
três: **ancorar no marcador do elemento** — aqui, `cartao-do-resultado`.

### 2. `details.card` deixou de significar "cartão de resultado"

`tests/test_cartoes_recolhiveis.py` usa um parser que chama de "cartão" todo `details.card`. O
bloco de avisos é um deles, e cinco asserções quebravam — inclusive
`test_o_alvo_da_ancora_e_o_proprio_details`, que exigia `id` em **todo** `details.card`.

O bloco dos descartados já tinha esse problema em potencial, e eu o havia resolvido com um
marcador (`bloco-descartados`) sem propagar a distinção para as asserções. Agora as cinco filtram
por `do_resultado`, que é o que elas sempre quiseram dizer, e o parser ganhou o helper
`_cabecalhos_dos_cartoes`.

## Limpeza

`TestABlocoNaTela._blocos_do_arquivo` era um helper **nunca chamado**, e ficou obsoleto (procurava
`<div class="observacoes-do-arquivo`). Foi removido e substituído por `_bloco`, que delimita o
`<details>` de verdade — um helper que devolve `[]` em silêncio é como um teste passa por
vacuidade.

## Verificação

| | |
|---|---|
| Suíte | **1019 passou, 9 pulados**, exit 0 |
| `SHA_DA_TELA` | **inalterado** (`39c6257f…`, 30.759 bytes) |
| Testes novos | 4 em `tests/test_observacoes_do_arquivo.py::TestOBlocoRecolhivel` |
| Testes ajustados | 2 de headers + 5 de contagem em `test_cartoes_recolhiveis.py` |

## Resíduo declarado

1. **O comportamento do navegador segue não verificado em navegador real**, como nos adendos
   `016`, `018` e `020`.
2. **O `open` é escolha declarada, e é reversível numa palavra.** Se o operador preferir o bloco
   fechado por padrão (como os descartados), basta tirar o `open` — e o teste
   `test_o_bloco_nasce_aberto` é o que registra a decisão atual.
3. **O resumo não traz contagem.** O bloco dos descartados mostra "(N)"; este mostra só
   "Observações do arquivo", que foi o texto literal pedido. Contar exigiria
   `{{ observacoes_do_arquivo | length }}` no `summary` — uma linha, se for desejado.
