# Investigação: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Requirements: `_reversa_forward/037-redesenho-das-tres-fases/requirements.md`

## 1. O que existe hoje, medido

| Item | Medida | Onde |
|---|---|---|
| Template da tela | 1.544 linhas | `src/templates/index.html` |
| Região da tela de entrada | linhas 239–418 (dois ramos, um por estado) | `src/templates/index.html` |
| Macro da tabela | 87 linhas, usada pelas duas abas | `src/templates/index.html:1-87` |
| Abas atuais | **duas**: `Buscar Conexão no GEDCOM` e `Analisador de DNA` | `index.html:246-253` e `:335-342` |
| Nomes entregues por `<datalist>` | um `<option>` por nome | `index.html:413-417` |
| Plugin de abas | `bootstrap.bundle.min.js` (5.3.3), no fim do corpo | `index.html:1444` |
| Folha de estilo | 551 linhas, servida por `GET /app.css` | `src/assets/app.css` |
| Tema | botão fixo, `localStorage`, `aria-pressed` | `index.html:140-170`, `app.css:449-461` |

Consequências diretas:

1. A navegação atual **não é um componente morto**: o plugin de abas está carregado, então `data-bs-toggle="tab"` funciona. A barra lateral pode ser só um desenho diferente do mesmo mecanismo.
2. O bloco de abas está **duplicado** nos dois ramos do `{% if %}`. Somar uma terceira fase duplicada três vezes seria a pior opção disponível.
3. A `<datalist>` já carrega o acervo inteiro de nomes no documento, um nó por nome.

## 2. Alternativas para a navegação

| Alternativa | Ganho | Custo | Veredito |
|---|---|---|---|
| **A — Barra lateral reusando o plugin de abas** | Um mecanismo só, já carregado; `.active`, `aria-selected` e clique vêm de graça; nenhum JS novo de painel | Desenho em coluna é CSS; setas verticais a confirmar | **Escolhida** (`D-01`) |
| B — Barra lateral com JS próprio | Controle total do teclado | Um segundo mecanismo de painel convivendo com o primeiro; duas formas de esquecer `aria-selected` | Descartada |
| C — Links com âncora e `:target` | Nenhum JS | Recarrega a página a cada troca, perde o "sem JavaScript" limpo e enche o histórico | Descartada |
| D — Manter abas horizontais | Menor mudança | Não entrega a leitura de "fases" que o operador pediu; contraria a `Q-01` | Descartada |
| E — Barra lateral **e** abas, como o mockup | Fidelidade ao mockup | Dois controles anunciando os mesmos três destinos; dobro de tabstops; no telefone, dois controles para a mesma coisa | Descartada na `Q-01` |

**Sobre as setas.** O plugin de abas do Bootstrap trata as setas horizontais dentro do `tablist`. Uma barra **vertical** pede ↑/↓. Antes de escrever qualquer handler, a execução deve conferir o comportamento real; o `D-05` registra as duas saídas e a ordem em que elas serão tentadas.

## 3. Alternativas para o autocomplete

| Alternativa | Ganho | Custo | Veredito |
|---|---|---|---|
| **A — Combobox próprio sobre um bloco JSON** | Filtro e destaque sob controle, ARIA explícito, um nó de lista em vez de milhares de `<option>` | ~100 linhas de JS e uma superfície de acessibilidade a manter | **Escolhida** (`D-07`, `D-10`) |
| B — Manter a `<datalist>` | Zero código | Sem filtro controlado, sem destaque, aparência ditada pelo navegador; e o custo de DOM continua | Descartada na `Q-02` |
| C — `<select>` com filtro | Nativo | Não aceita texto livre, e a busca **precisa** aceitar o que o operador digitar | Descartada |
| D — Biblioteca de terceiros (typeahead) | Pronta | Dependência nova, CDN novo, e o projeto tem três hosts externos por decisão declarada | Descartada |

**Por que o texto livre precisa sobreviver.** A busca documental faz correspondência aproximada: o operador pode digitar um nome que não está na lista e a busca tenta resolvê-lo. Um combobox que só aceitasse itens da lista **mudaria o comportamento da busca**, o que a `RN-10` proíbe.

**Por que JSON e não `<option>`.** A lista atual é markup: cada nome custa um elemento com atributo e fechamento. Em JSON, o mesmo nome custa uma string entre aspas. Para dezenas de milhares de nomes a diferença é de ordem de grandeza, e o documento fica menor do que é hoje com a mesma árvore aberta.

**Risco de injeção.** O bloco vai num `<script type="application/json">`, e todo o conteúdo vem de nome de pessoa em GEDCOM. O filtro `tojson` do Flask escapa `<`, `>` e `&` como sequências unicode, o que impede o fechamento prematuro da tag. Ainda assim, o teste deve tentar um nome com `</script>` e conferir que ele aparece escapado.

## 4. Acessibilidade: o padrão de combobox

O padrão da especificação ARIA para combobox com lista popup exige:

- um campo com `role="combobox"` (ou um `input` que o receba), `aria-expanded` refletindo o estado da lista e `aria-controls` apontando para ela;
- a lista com `role="listbox"`, e cada item com `role="option"` e `aria-selected`;
- `aria-activedescendant` no campo apontando para o **id** da opção destacada, enquanto o foco permanece no campo;
- `Enter` escolhe a opção destacada, `Esc` fecha sem apagar o texto, ↑/↓ percorrem, e o foco nunca sai do campo durante a navegação;
- o anúncio da quantidade de resultados por região viva, para quem não vê a lista.

O projeto já usa `aria-selected`/`aria-controls` nas abas e `visually-hidden` para o que a cor não diz — o combobox segue a mesma casa.

## 5. Como testar sem navegador

O projeto **não tem** navegador headless nem executor de JavaScript: a limitação está declarada desde a `013` (`D-07`). Os testes de tela leem o HTML servido e procuram estrutura por string e expressão regular.

Isso significa:

- é possível prender que a `<datalist>` sumiu, que o bloco JSON existe, que os atributos ARIA estão no markup e que o script contém as teclas tratadas;
- **não** é possível prender que a lista abre ao digitar, que o foco fica no campo ou que `Esc` fecha.

O `D-14` registra essa fronteira, e o `onboarding.md` carrega o checklist manual que cobre o que o teste não cobre.

## 6. Fontes externas

- W3C — WAI-ARIA Authoring Practices, *Combobox Pattern*: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/
- W3C — *Understanding Success Criterion 1.4.3 (Contrast Minimum)*: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Bootstrap 5.3 — *Navs and tabs*: https://getbootstrap.com/docs/5.3/components/navs-tabs/
- MDN — *`<datalist>`*, com a nota de que a aparência e o filtro são do navegador: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/datalist
- MDN — *`String.prototype.normalize`*, base do filtro sem acento: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/normalize

## 7. Notas de execução

- Nenhuma biblioteca nova entra em `requirements.txt`: o combobox é JavaScript de navegador, não dependência Python.
- Nenhuma fonte nova por CDN: `Newsreader` e `IBM Plex Sans` continuam sendo as duas famílias da tela.
- O mockup de referência usa outras fontes, animações de entrada e azul de link; nada disso é adotado (§2.4 do `requirements.md`).
