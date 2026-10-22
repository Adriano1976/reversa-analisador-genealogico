# Investigação: paginação da lista de resultados

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/046-paginacao-dos-resultados/requirements.md`

## 1. A pergunta de fundo

"Paginar" descreve um efeito de tela, não um mecanismo. Antes de decidir **como**, a pergunta que
manda é: **onde vive o conjunto paginado?** Há três respostas possíveis num sistema como este —
no servidor, no estado entre requisições, ou no documento que já chegou ao navegador — e só a
terceira é compatível com o que a extração registra.

## 2. O que a extração já decidiu por nós

| Fato medido | Fonte | Consequência para a paginação |
|---|---|---|
| **Não há cache entre requisições**: a cada `POST`, o GEDCOM é reparseado integralmente | `_reversa_sdd/architecture.md#1` | Paginar no servidor significa **reanalisar** a cada página |
| Uma análise leva de **12 a 31 s** no arquivo real (medido em 2026-10-22, varia por máquina) | execução local da análise real | O custo de uma paginação server-side é a análise inteira **por clique** |
| A árvore entra **por parâmetro** e não há estado global (`ADR-24`) | `_reversa_sdd/adrs/24-nucleo-puro-arvore-por-parametro.md` | Não existe onde pendurar o resultado entre duas requisições |
| O recolhimento dos cartões é **visual**, e remover conteúdo do HTML é recusado | `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#Nada sai do documento` | Esconder é legítimo; remover, não |
| A suíte exige **um cartão por conexão** e **numeração sem buraco** | `tests/test_estado_do_resultado.py` | O HTML tem de continuar com os 68 |
| A tela de 68 cartões tem **≈ 3,9 MB** | execução local | Os bytes não caem com paginação; o ganho é de leitura |

## 3. Alternativas avaliadas

| Alternativa | Como seria | Por que foi descartada |
|---|---|---|
| **Paginação no servidor** (`POST` com a página) | Um campo oculto com a página; o servidor re-renderiza com outra fatia | Reparseia GEDCOM e refaz a análise a cada clique — 12 a 31 s por página no arquivo real |
| **Sessão/cache do resultado** | Guardar o resultado na sessão e servir fatias | Contraria `ADR-24` e a decisão explícita de não haver estado entre requisições; abriria isolamento entre operadores, que o sistema não tem |
| **Rolagem infinita / carga sob demanda** | Renderizar 10 e buscar mais ao rolar | Não tem "página 3 de 7", não dá para voltar a um ponto e não permite escolher 20 ou 30; e o conteúdo já está todo no cliente, então não economiza nada |
| **Divulgação por página** (um `<details>` por página, fechado) | Agrupar os cartões em sete grupos recolhíveis | Mistura dois mecanismos com semânticas diferentes: `<details>` diz "há mais aqui dentro", paginação diz "há mais **adiante**". E não responde "quantas páginas" |
| **`content-visibility: auto`** | Deixar o navegador pular a renderização fora da tela | Resolve custo de renderização, não resolve leitura: não há controle, não há contagem, não há escolha de tamanho |
| **Componente de paginação da biblioteca de estilo** | Usar o componente pronto que a tela já carrega | A tela tem folha própria e classes próprias para todos os controles (`botao-do-cartao`, `botao-do-tema`); um componente novo traria marcação e estilo que a suíte não prende |
| **Paginação no cliente sobre o DOM** ✅ | Marcar `hidden` nos cartões fora da página | Escolhida. Sem rede, sem reanálise, sem estado persistido, e os 68 cartões ficam no documento |

## 4. O precedente do próprio repositório, e por que ele não se transfere

O `_reversa_sdd/migration/screen_deviation_log.md` registra a **DEV-003**: a `datalist` que embute
todos os nomes do GEDCOM no HTML deveria virar **busca/autocomplete paginado por endpoint**. É o
precedente mais próximo deste problema, e ele aponta para o lado oposto.

A diferença está no que a lista **é**:

- na `datalist`, a lista é **entrada de formulário**: o navegador precisa dela antes de o operador
  digitar, e embutir 35 mil nomes custa HTML em toda requisição, inclusive nas telas que não usam a
  lista;
- na lista de resultados, o conteúdo **já é o produto da requisição**: os cartões existem porque a
  análise acabou de rodar, e a fatia visível é decisão de leitura, não de transporte.

Ou seja: DEV-003 troca HTML por requisição; aqui, a alternativa com requisição custaria a análise
inteira. O precedente que se transfere é o **princípio** — não embutir o que não é preciso —, e ele
já está respeitado: os cartões são precisos, a página é que escolhe quais mostrar.

## 5. Acessibilidade: como esconder importa mais do que o quanto

| Mecanismo | Some do foco? | Some da árvore de acessibilidade? | Serve? |
|---|---|---|---|
| `hidden` (atributo) | sim | sim | **escolhido** |
| `display: none` por classe | sim | sim | equivalente, mas exige classe por cartão e não é semântico |
| `visibility: hidden` | sim | sim | mantém a caixa, o que aqui não ajuda em nada |
| `opacity: 0` | **não** | **não** | deixaria 58 cartões focáveis e invisíveis |
| `.visually-hidden` (recorte) | não | não | é para texto de leitor de tela, não para esconder bloco |

O controle precisa dizer **onde o operador está**: `aria-current="page"` no botão da página
corrente, e um `<nav aria-label="Paginação das conexões">` como região. O texto "Página 3 de 7"
existe para quem não vê os botões.

## 6. A tensão com o adendo 018, declarada

O adendo `018` recusa remover conteúdo do HTML porque "uma implementação que removesse o conteúdo
passaria em todos os outros testes — e teria destruído a leitura da análise como texto". A
paginação **esconde** parte desse texto, e isso tem um preço real: a busca do navegador (Ctrl+F)
não alcança cartões com `hidden`. O operador que procura um sobrenome na página 1 de 7 pode
concluir que ele não está na análise.

Não há mecanismo barato que resolva isso: manter o texto buscável e invisível exigiria
posicionamento fora da tela, o que reintroduz o problema de foco. A posição registrada é:

1. **esconder ≠ remover** — os 68 cartões estão no documento, e a impressão/leitura por página
   continua funcionando nas páginas visitadas;
2. a frase do topo diz **68 conexões analisadas**, então a informação "há mais" está na tela;
3. a resposta definitiva para "achar um nome" é **busca/filtro**, não paginação — e essa é uma
   feature diferente, que não foi pedida.

## 7. Padrão aplicado

Controle de paginação com: seletor de tamanho, anterior/próxima, números das páginas e indicador de
posição — o arranjo que o padrão de paginação da WAI-ARIA descreve para listas longas, sem os
refinamentos de "primeira/última" que não têm uso aqui (a lista tem 3 a 15 páginas).

## 8. Fontes externas consultadas

- **WHATWG HTML Living Standard** — o atributo global `hidden` e o elemento `details`:
  <https://html.spec.whatwg.org/multipage/interaction.html> (consultado em 2026-10-22).
- **WAI-ARIA 1.2** — `aria-current` e o vocabulário de estado corrente:
  <https://www.w3.org/TR/wai-aria-1.2/> (consultado em 2026-10-22).
- **MDN Web Docs** — `aria-current`:
  <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes/aria-current>
  (consultado em 2026-10-22).

## 9. O que não foi investigado

- **Comportamento em navegador real.** Nenhum dos mecanismos desta feature foi observado rodando em
  navegador — só a estrutura, a ligação e a folha. É o mesmo limite que o adendo `018` declarou.
- **Custo de renderização dos 68 cartões escondidos.** A paginação não muda o número de nós; se o
  tempo de layout for problema, o caminho é `content-visibility`, que ficou fora do escopo.
- **Leitor de tela de verdade.** O `aria-current` e o `hidden` seguem a especificação, mas não foram
  anunciados por um leitor real.
