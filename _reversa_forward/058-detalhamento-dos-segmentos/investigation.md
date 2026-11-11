<!--
Investigação de fundo da feature 058 — Detalhamento dos segmentos compartilhados.
Pesquisa de alternativas e fontes; não decide requisito (isso está no requirements.md).
-->

# Investigação: detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Insumo: pedido do operador de 2026-11-11 (captura de um painel de outro produto) e a sessão de
> esclarecimentos do mesmo dia

## 1. O problema real

O bloco "Regiões compartilhadas" já mostra a região de dois jeitos: o **ideograma** (onde ela cai) e
a **lista** (o resumo da região: faixa, kits, cM, desfecho). O que não existe é a linha por
**segmento**: qual match, com qual kit, em que faixa exata, com quantos cM. Essa é a pergunta que a
tabela responde — e ela é a única das três que permite conferir um match específico sem abrir o CSV
de origem.

## 2. Onde filtrar: servidor ou documento

O projeto já resolveu essa questão uma vez, na feature 046, e a resposta vale igual aqui: **não
paginar nem filtrar no servidor**. Cada `POST` de análise reparseia o GEDCOM inteiro — de 12 a 31 s
no arquivo real (`_reversa_sdd/addenda/046-paginacao-dos-resultados.md`), porque a análise não é
cacheada entre requisições. Um filtro por query string significaria refazer a análise a cada tecla.

O caminho adotado é o mesmo da 046: o HTML sai **completo** e o script marca `hidden` nas linhas que
não pertencem à vista. Nada é recalculado, nada é reenviado, e o navegador fica com o filtro na
memória da página.

## 3. Como destacar a faixa sem JavaScript

A tela já usa `:target` para destacar um cartão por âncora (`.card:target` em `app.css`). A mesma
ideia resolve o clique da tabela: a faixa do ideograma ganha `id`, a linha aponta para esse `id`, e o
CSS estiliza `:target`.

O `:target` é **Baseline Widely available** — funciona em qualquer navegador desde 2015
([MDN, `:target`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:target)). O
próprio exemplo da documentação é uma tabela de conteúdo que destaca a seção linkada, que é
exatamente a nossa forma.

Dois cuidados que a documentação do recurso não cobre e que entram no plano:

- o `:target` muda na navegação por fragmento e no histórico, mas **não** com `history.pushState` —
  não usamos `pushState`, então o comportamento é o esperado;
- o navegador rola até o alvo; sem `scroll-margin`, a faixa pode parar **sob a barra fixa do topo**.
  Por isso a faixa ganha `scroll-margin-block-start`.

## 4. Copiar a linha

A ação de copiar usa `navigator.clipboard.writeText`, que exige contexto seguro (a aplicação roda em
`localhost`, que conta como seguro) e pode falhar por permissão. O desenho trata a falha como
silêncio: o rótulo do botão vira "copiado" quando dá certo e não muda quando não dá — a tabela
continua utilizável nos dois casos.

## 5. Alternativas de interação descartadas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Filtrar no servidor | Repetiria o parse de 12 a 31 s por filtro (acima) |
| Destacar a faixa por classe via JavaScript | Funciona, mas amarra o destaque ao script; `:target` funciona até com o script quebrado |
| Abrir o cartão da região no clique | Exigiria `open` via JS e um vínculo a mais entre tabela e lista; o operador preferiu o destaque simples (pergunta 3, resposta a) |
| Tabela em cartões, sem `<table>` | Perde `<th scope>`, o `caption` e a leitura de linha por coluna no leitor de tela |
| Rolagem interna no lugar de paginação | Rolagem dentro de rolagem é pior de operar; a decisão foi o seletor 10/20/30 (resposta 4b) |

## 6. Volume esperado

- Teto de regiões: `LIMITE_DE_REGIOES = 200` (`src/core/regioes.py`).
- Análise real medida na 056: **32 regiões** e 108 kits cobertos, sobre 783 segmentos.
- Linhas da tabela = soma de kits por região (um segmento por kit). Com 32 regiões e cerca de 5 kits
  por região, a ordem de grandeza é **dezenas a poucas centenas de linhas** — não milhares.
- A fixture sintética da 057 produz **11 linhas** (4 + 4 + 3), que é o caso do onboarding.

## 7. Fontes consultadas

- MDN — `:target` (Baseline Widely available, exemplo de tabela de conteúdo): https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:target (consultado em 2026-11-11)
- MDN — `Clipboard.writeText`: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText (consultado em 2026-11-11)
- `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` — por que paginar no documento e não no servidor
- `_reversa_sdd/addenda/056-regioes-compartilhadas.md` — o que é uma região e o piso de 10 cM
- `src/core/regioes.py`, `src/application/regioes.py`, `src/reporting/ideograma.py` — a projeção e o desenho que a tabela reaproveita
