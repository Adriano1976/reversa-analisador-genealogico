# Adendo: veredicto do doador e diagrama recolhido no cartão

> Identificador: `015-veredicto-do-doador-no-cartao`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/` e `_reversa_sdd/screens/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não** saiu
> daquele pipeline — o conteúdo é fiel ao entregue, o formato pode divergir do que ele gera.

## Vigência

Vigente desde 2026-10-14.

Não emenda nenhuma `RN` vigente. É a primeira declaração sobre **como o cartão de resultado se
apresenta quando a data do registro impede que ele tenha doado o DNA**.

## Resumo da entrega

O operador formulou uma regra: *"todas as pessoas que tivessem um caminho genealógico no GEDCOM, mas
com janela de vida acusando, fossem classificadas como 'Parentesco documental não encontrado', como
as outras — ficaria melhor do que apresentar um gráfico inconsistente?"*

A pergunta foi medida antes de respondida, e três consequências apareceram:

| O que a regra faria | Medição |
|---|---|
| Alcança | **3 cartões** de 62 (`TG8027863`, `ZC1171551`, `ZL6373425`) |
| Perde | A **única** comparação de cM × parentesco que hoje acontece: `TG8027863` sai de `COMPATIVEL` para `INCONCLUSIVO` |
| Perde | 1 dos 5 cartões que apontam para o mesmo ancestral (`Manoel da Silva Vieira`, 1720) |
| Afirma | *"nenhum caminho genealógico foi encontrado no GEDCOM"* — **falso**: a árvore tem o caminho, em 11, 12 e 10 meioses |

A queixa por trás da regra é legítima: o diagrama de 12 ou 13 caixas terminando numa pessoa de 1673
**se apresentava como a resposta**. O que foi entregue ataca a moldura, e não o dado:

1. **O cartão abre com o veredicto.** Novo primeiro bloco do corpo, `div.veredicto-do-doador`:
   *"Nenhum parentesco atribuível ao doador."* — seguido de que o GEDCOM **tem** o caminho, que o
   registro escolhido pela busca por nome é que não pode ser o doador, e que o vínculo entre este DNA
   e esta árvore continua desconhecido.
2. **O parentesco passa a ser apresentado como o do registro.** O rótulo da seção 1 deixou de ser
   *"Parentesco encontrado:"* e passou a ser *"Parentesco do registro escolhido:"*. A troca vale para
   **todos** os cartões de DNA, e não só para os três: em 9 cartões a identidade já é `a_confirmar`,
   e neles o rótulo antigo também afirmava mais do que se sabe.
3. **O diagrama fica recolhido e intitulado.** `<details class="grafo-do-registro">`, fechado quando
   a janela de vida é `impossivel`, com o título *"Caminho do registro escolhido no GEDCOM — **não é
   o caminho do doador**"*. Fechado, e não apagado: o operador abre quando quiser.

O que **não** mudou: o caminho documental, o estado `documentary.status`, o confronto, os quatro
estados, a ordem de apresentação e o matching. Nenhuma linha do núcleo de decisão foi tocada — a
entrega é de template e folha de estilo, mais o JavaScript que faz o recolhimento funcionar.

## Por que o diagrama recolhido exige JavaScript

O Mermaid mede o container para dimensionar o SVG. Dentro de um `<details>` fechado o elemento tem
**tamanho zero**: o desenho sai quebrado e — pior — o nó fica marcado como `data-processed`, então
abrir depois não conserta. Por isso a rodada inicial passou a **pular** o que está dentro de um
`details` fechado (`closest("details:not([open])")`) e o evento `toggle` renderiza na primeira
abertura.

**Isto é a parte que não foi verificada em navegador.** O HTML servido, o filtro, o listener e a
guarda estão presos por teste; a renderização em si depende do Mermaid no cliente e só o operador
pode confirmar. Se o diagrama abrir em branco, a causa está aqui, e o recuo é uma linha (renderizar
tudo na carga, como antes).

## Regras alteradas

Nenhuma `RN` formal. As mudanças de apresentação que este adendo declara:

| Antes | Agora |
|---|---|
| O cartão abria pelo aviso da janela de vida | Abre pelo **veredicto do doador**, quando há caminho e a janela é impossível |
| *"Parentesco encontrado: `<rótulo>`"* | *"Parentesco **do registro escolhido**: `<rótulo>`"* |
| Diagrama solto sob *"Caminho genealógico no GEDCOM"* | `<details>` com título que diz de quem é o desenho; fechado no caso da janela impossível |

## Impacto por artefato da extração

| Artefato | Impacto |
|---|---|
| `_reversa_sdd/analise-dna/contracts.md` | **Sem impacto.** Os quatro estados e a ordem de conservadorismo continuam intactos; nada foi acrescentado ao domínio |
| `_reversa_sdd/analise-dna/requirements.md` (§ `RF-19`) | **Sem impacto no contrato.** O texto do rótulo da seção 1 não é regra: é apresentação |
| `_reversa_sdd/screens/golden/SCR-005*` | **Divergência declarada.** O cartão de resultado ganhou um bloco e um `<details>`. Em modo literal a paridade textual estrita não se aplica a estado de resultado com dados reais, mas fica registrado |
| `_reversa_sdd/design-system/tokens-derived.md` | Duas classes novas (`.veredicto-do-doador`, `details.grafo-do-registro`), com cores tiradas dos tokens existentes (`--danger`, `--aviso-bg`, `--primary`) |
| `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | **Atualizado:** `f2b2233e…` (28.858 bytes) → `9cf0e558…` (29.486 bytes) |
| `_reversa_bugs/_sondas-matching/bfs_verificar_na_tela.py` | Sonda atualizada: procurava o rótulo antigo |

### Sobre o `SHA_DA_TELA`, que mede a tela de entrada VAZIA

O hash mudou porque o **`<script>` global** mudou — o bloco do `mermaid.run`, que vive fora dos dois
ramos da tela. O conteúdo **visível** da tela de entrada vazia é o mesmo; o que mudou é o JavaScript
que ela carrega. Isso é dito aqui porque é exatamente o tipo de mudança que o teste existe para
obrigar a declarar, e não porque a tela de entrada tenha sido redesenhada.

## Dívidas declaradas, não fechadas

1. **A renderização do diagrama ao abrir não foi verificada em navegador.** Ver a seção acima.
2. **O `TG8027863` continua mostrando `COMPATIVEL` na seção 4** — e está certo ali, porque a seção 4
   pergunta se o cM cabe na faixa do parentesco documental. Quem carrega a contradição resolvida é o
   selo do cabeçalho (`compatível no cM, identidade impossível`). A seção 4 ganhou uma linha
   explicando que aquele veredito é do **registro**.
3. **A regra de medir a profundidade por lado, e não pela média, não está implementada.** Foi
   recomendada e aprovada em conversa, mas não é escopo deste adendo. Medição registrada: muda o
   estado de 2 cartões, e um deles é o da Margarida (`concorda` → `divergência` a 2,35× no lado do
   usuário). O obstáculo medido: **11 de 11** cartões com caminho têm mais de um ancestral comum
   (2 a 12), então a razão não separa "elo ausente" de "cM inflado por endogamia" — ela pode ser
   informada, nunca concluída.
4. **A leitura da profundidade continua dentro do `<details>`** nos cartões recolhidos, junto com o
   desenho. Nos cartões em que ela aparece e o diagrama está aberto, nada mudou.

## Regras sob vigilância

- **`RF-19` / `BR-D-27` / ADR-15** — os quatro estados do confronto. Esta entrega não os toca, e o
  teste `test_o_prefixo_estado_e_reservado_aos_quatro_estados` vigia o par selo↔folha.
- **ADR-21** (`endogamia: avisar, não corrigir`) — a mesma disciplina que este adendo aplica: avisar
  na moldura, sem apagar o dado.
- **A ordem de apresentação** (`_ordem`, documental primeiro) — não foi tocada.

## Fontes

- `_reversa_bugs/_sondas-matching/avaliar_regra_nao_encontrado.py` — a sonda que mediu o alcance da
  regra proposta e as três consequências.
- `_reversa_bugs/_sondas-matching/avaliar_proposta_margarida.py` — a sonda das quatro sugestões.
- `_docs_auxiliary/correcao-de-precisao-20261014-profundidade-do-caminho.md` — a verificação de profundidade,
  de que este bloco é vizinho.
- `src/templates/index.html`, `src/assets/app.css`,
  `tests/test_profundidade_do_caminho.py::TestOCartaoDoDoadorImpossivel`.
