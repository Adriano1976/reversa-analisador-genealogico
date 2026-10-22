# Actions: paginação dos Resultados das Análises de Conexão

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/046-paginacao-dos-resultados/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 14 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 10 (T001 → T002 → T004 → T006 → T007 → T009 → T010 → T011 → T012 → T014) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Registrar a baseline medida: suíte (`1585 passed, 9 skipped`) e os valores atuais de `SHA_DA_TELA` e `TAMANHO_ESPERADO` | - | - | `tests/test_icone_de_atalho.py` (leitura) | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Criar a série da **marcação e da folha**: o `nav.paginacao-das-conexoes` existe entre a contagem e o primeiro cartão; tem as três `option` com a 10 `selected`; "Página 1 de N"; `aria-current="page"` só no 1; "Anterior" desabilitado; as 7 classes existem na folha; a guarda `details.cartao-do-resultado[hidden]` existe; o controle **não** aparece com 8 cartões; os 68 `details` continuam no documento; a contagem do topo continua sendo o total | T001 | - | `tests/test_paginacao_na_tela.py` | 🟢 | `[X]` |
| T003 | Acrescentar a série da **ligação do script**: os quatro ouvintes existem; `abrirCartaoDoAlvo` mostra a página **antes** de `open = true`; "expandir/recolher" usam a fatia visível e não os 68; a troca de página não chama `fetch`/`submit` | T002 | - | `tests/test_paginacao_na_tela.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever o bloco de marcação no template: `{% set por_pagina = 10 %}`, `total_de_paginas` com divisão inteira para cima, guarda `{% if total_de_paginas > 1 %}`, `nav` com rótulo, seletor, posição, anterior/próxima e os números com `data-pagina` e `aria-current` | T002 | `[//]` | `src/templates/index.html` | 🟢 | `[X]` |
| T005 | Escrever as **7 classes** da paginação na folha e a guarda `details.cartao-do-resultado[hidden] { display: none !important; }`, mais o estado `:disabled` dos botões de passo | T002 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T006 | Escrever o motor da paginação no `<script>`: estado em closure (`pagina`, `porPagina`), `totalDePaginas`, `visiveis`, `desenhar` (marca/desmarca `hidden`, atualiza texto, `aria-current` e `disabled`), `irPara` com trava nos limites e rolagem para `#resultados` | T004, T005 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T007 | Fazer `abrirCartaoDoAlvo` revelar a página que contém o alvo **antes** de `alvo.open = true` | T006 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T008 | Fazer "Expandir todas" e "Recolher todas" operarem sobre a **fatia visível**, mantendo `todosOsCartoes()` para a paginação | T006 | - | `src/templates/index.html` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Rodar a suíte completa e tratar o que quebrou por estrutura (`test_cartoes_recolhiveis`, `test_estado_do_resultado`, `test_lista_na_tela`), **sem remover asserção** | T007, T008 | - | `tests/` | 🟢 | `[X]` |
| T010 | Atualizar `SHA_DA_TELA` e `TAMANHO_ESPERADO` com o valor **medido** na falha do teste, registrando a mudança declarada | T009 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |
| T011 | Verificar no arquivo real (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`): 68 cartões, 7 páginas a 10, contagem do topo intacta, e medir o tamanho do HTML antes/depois | T010 | - | — | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Comentar no template as três decisões que um leitor vai querer questionar: por que `hidden` e não remoção, por que mostrar a página antes de abrir, por que a guarda `> 1` | T011 | `[//]` | `src/templates/index.html` | 🟢 | `[X]` |
| T013 | Comentar na folha por que a guarda de `[hidden]` usa `!important` e por que as sete classes são separadas | T005 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T014 | Varredura final: nenhum arquivo de `src/app.py`, `src/application/`, `src/core/` ou `src/ports/` alterado, e nenhum arquivo de `src/uploads/` no `git status` | T012 | - | — | 🟢 | `[X]` |

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos surgidos durante a execução. -->

- **T004 (por que no HTML e não no script):** a suíte prende marcação renderizada, não execução de
  JavaScript. Um controle criado no `DOMContentLoaded` passaria a existir só no navegador e nenhum
  teste o veria — `D-03` do `roadmap.md`.
- **T005 (por que `!important`):** `hidden` é o atributo mais frágil da plataforma: qualquer regra
  `display` o vence. A guarda própria é o que impede um `display` de biblioteca de reabrir a lista.
- **T007 (a ordem importa):** abrir um cartão escondido dispara `toggle`, e o Mermaid mede um
  container de tamanho zero. É o problema que o adendo `018` documentou.
- **T010 (o número não se chuta):** o valor sai da falha do teste, e a mudança entra no
  `legacy-impact.md` e no adendo. Ajustar para "passar" esvazia o invariante.

### O que a execução acrescentou a estas notas

- **A `chamada` de `abrirCartaoDoAlvo()` teve de mudar de lugar.** Ela acontecia logo depois da
  definição da função, quando `mostrarPaginaDo` ainda era `null` — o cartão do `#` abriria, mas a
  página não trocaria. Passou para depois do bloco da paginação, e o comentário no template explica
  por quê. Um teste de estrutura não pegaria isso: o defeito é de **ordem de execução**.
- **O primeiro desenho não rola (`irPara(1, false)`).** A rolagem faz parte da navegação, não do
  carregamento; rolar na carga jogaria o operador para o meio do documento.
- **Um teste novo mediu a coisa errada na primeira versão.** `test_o_controle_nao_e_renderizado`
  procurava `paginacao-das-conexoes` em todo o documento, e o script cita a classe de propósito —
  o teste reprovava o código correto. Passou a medir o marcado (`<nav class=...`,
  `id="tamanho-da-pagina"`), que é o que a asserção queria dizer.
- **`TAMANHO_ESPERADO` não é o tamanho da tela.** A falha de `test_icone_de_atalho.py` mostrou que
  ele mede o **PNG do ícone** (16.504 bytes); a tela é medida pelo `SHA_DA_TELA`. Só o hash mudou:
  42.290 → **46.264 bytes** (+3.974, todos de script), porque o markup do controle vive dentro de
  `{% if dna_results %}` e não aparece na tela de entrada vazia.
- **Suíte:** **1615 passed, 9 skipped** (baseline 1585/9, +30 do arquivo novo).

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-22 | 14 de 14 ações executadas por `/reversa-coding`; suíte em 1615 passed / 9 skipped | reversa |
