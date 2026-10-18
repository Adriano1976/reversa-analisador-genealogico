# Investigation: veredito de validação no cartão

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Escopo: por que o veredito entra no dicionário da tela, por que o selo é de contorno, de onde vem o
> intervalo de geração e o que foi medido antes de planejar.

## 1. O problema real não é o selo

O selo é fácil: uma `span`, uma condição, uma classe. A parte que pode dar errado é **de onde sai o
número de gerações**.

`validar_comparacao` precisa de `intervalo_de_geracao` para converter gerações em anos. Na fachada da
`028`, esse valor vem de `application.validacao.intervalo_de_geracao_mediano(arvore)` — a mediana dos
intervalos pai-filho datados, com fallback de 25. No fluxo de DNA, esse valor **não existe hoje**.

Se o cartão chamasse o validador sem o intervalo, ele usaria o prior de 25 e produziria um veredito
possivelmente **diferente** do que `validar_arquivos` produz para o mesmo kit. Duas telas, dois
vereditos, mesma árvore — o tipo de divergência que ninguém percebe até alguém comparar.

Saídas consideradas:

| # | Saída | Problema |
|---|-------|----------|
| A | Duplicar a função no núcleo | Duas implementações de G, que podem divergir em silêncio |
| B | Passar o intervalo por parâmetro até a rota | `app.py` passaria a calcular um número de domínio antes de chamar o caso de uso |
| C | Usar o prior de 25 no cartão | Veredito diferente do da fachada — inaceitável |
| D | Mover a função para `core/documentary_relationship` e a fachada delegar | **Escolhida.** Uma implementação, um G, e a fachada mantém o nome público |

`core/documentary_relationship.py` é o lugar natural: já tem `parse_year` e `birth_date`, e a função
só percorre famílias e datas.

## 2. Por que o veredito entra no dicionário, e não na dataclass

Medido no código: `app.py:686` passa `dna_results=resultado.resultados`, e `ResultadoDeAnalise`
(`application/dna_analysis.py:42`) tem apenas `resultados`, `descartados`, `mensagem` e dois campos de
aviso. Ou seja, **`resultados` é a lista de dicionários do núcleo**, e o template lê
`result.cm`, `result.comparison`, `result.documentary` — chaves de dicionário via acesso de atributo do
Jinja.

Consequência: para o selo aparecer, as chaves precisam estar **no dicionário**. Mexer em
`ResultadoDeAnalise` não mudaria nada na tela.

E há precedente dentro do próprio núcleo: o dicionário já carrega rótulos humanos —
`confrontacao_rotulo` (`core/dna_analysis.py:432`), `janela_aviso`, `profundidade_aviso`. Produzir
`validacao_rotulo` e `validacao_classe` ali segue o padrão que existe, em vez de abrir uma segunda
camada de tradução.

## 3. A armadilha do CSS, medida duas vezes

`src/assets/app.css:207` diz `.badge[class*="estado-"]{color:#fff}` — a regra reivindica **qualquer**
classe que **contenha** `estado-`, não só as quatro. As cores `--st-*` são escuras justamente para o
texto branco.

Em 2026-10-14 um selo de aviso nasceu com classe `estado-identidade_impossivel`: o branco venceu e o
texto ficou branco sobre creme, **1,11:1** — o rótulo sumiu. A correção foi renomear a classe para
fora do prefixo (`app.css:311-324`).

Por isso o selo novo usa `validacao-*`, e **contorno em vez de preenchimento**: assim ele não
reivindica a família de cor dos estados e não compete visualmente com o selo de confronto, que é
preenchido.

## 4. Contraste, calculado

O contorno põe a cor do status na **borda** e o texto em `--ink`. Mas `--st-*` **não** são redefinidas
no tema escuro (`:root[data-bs-theme="dark"]`, `app.css:47-69`): elas continuam escuras, porque o
texto dos selos preenchidos é branco. Um contorno com `#A8321F` sobre `#16140F` ficaria em ~2,3:1.

Solução: duas variáveis por tema, com os valores que `--primary` e `--danger` já usam em cada bloco.
Contraste **medido em 2026-10-18** com a fórmula WCAG (luminância relativa):

| Tema | Status | Cor | Fundo | Contraste |
|------|--------|-----|-------|-----------|
| claro | validado | `#2F6B3A` | `#F5F1E6` | **5,66:1** |
| claro | conflito | `#A8321F` | `#F5F1E6` | **5,92:1** |
| escuro | validado | `#8DBB6E` | `#16140F` | **8,30:1** |
| escuro | conflito | `#EE9A88` | `#16140F` | **8,42:1** |

Todos acima do mínimo AA de 4,5:1 para texto pequeno, e acima de 3:1 para a borda (elemento não
textual).

## 5. Alternativas de apresentação avaliadas

| # | Abordagem | Por que foi descartada (ou escolhida) |
|---|-----------|----------------------------------------|
| A | Selo preenchido com `--st-*` | Verde de "Compatível" e verde de "Validado" ficariam iguais à primeira vista, no mesmo cabeçalho |
| B | Selo preenchido com cor nova | Cria cor fora da paleta, que é decisão de design system |
| C | Ícone sem texto | Não cabe a frase "linha em conflito" num ícone, e a tela não tem ícones de status |
| D | Selo de contorno com as cores dos estados | **Escolhida.** Distingue por forma, sem cor nova |
| E | Texto solto no parágrafo da seção 4 | Exige abrir o cartão para ver — o oposto do objetivo |
| F | Selo para os três status | Marca quase todos os 142 cartões e deixa de marcar qualquer um |

## 6. Fatos medidos no código

| Fato | Onde |
|------|------|
| O template consome os dicionários do núcleo | `src/app.py:686`; `src/application/dna_analysis.py:42` |
| O dicionário já carrega rótulos humanos | `src/core/dna_analysis.py:432` |
| O laço já tem `documentary`, `comparison` e `ano_base` | `src/core/dna_analysis.py:431-448` |
| `.badge[class*="estado-"]` reivindica qualquer classe com o prefixo | `src/assets/app.css:207` |
| `--st-*` não são redefinidas no tema escuro | `src/assets/app.css:47-69` |
| O hash da tela é preso em dois pontos | `tests/test_icone_de_atalho.py:214, 307` |
| A fachada expõe `intervalo_de_geracao_mediano` | `src/application/validacao.py`; teste em `tests/test_validacao_de_arquivos.py` |

## 7. Fontes externas

- WCAG 2.1, contraste mínimo de texto (1.4.3): <https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html>
- WCAG 2.1, contraste de elemento não textual (1.4.11): <https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html>
- Fórmula de luminância relativa usada na medição: <https://www.w3.org/WAI/GL/wiki/Relative_luminance>
- Bootstrap 5.3, componente `badge` (a classe base usada pela tela): <https://getbootstrap.com/docs/5.3/components/badge/>

## 8. Lacunas de investigação

- **Não foi medido** o tempo das 142 chamadas de `validar_comparacao` numa análise real. A função é
  pura e O(saltos), mas o número não foi cronometrado; o teste de integração pode registrar.
- **Não foi verificado** se algum consumidor de `validacao.intervalo_de_geracao_mediano` depende do
  módulo de origem (além dos testes da `028`). A varredura de imports é feita no coding.
