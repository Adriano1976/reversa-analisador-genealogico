# Actions: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Roadmap: `_reversa_forward/037-redesenho-das-tres-fases/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 28 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 12 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Medir o baseline e guardar as evidências: suíte completa, `SHA_DA_TELA` (hash e bytes), `git status`, `git log -1`, cópias de `src/templates/index.html` e `src/assets/app.css` em `evidence/antes/` | - | `[//]` | `_reversa_forward/037-redesenho-das-tres-fases/evidence/antes/` | 🟢 | `[X]` |
| T002 | Levantar os testes que tocam a tela de entrada e anotar, para cada um, o que ele prende: nome, arquivo, linha e asserção. Gravar em `evidence/antes/guardioes.txt` | - | `[//]` | `tests/` (leitura) e `evidence/antes/guardioes.txt` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever os testes do esqueleto que **devem falhar antes** da mudança: três painéis, três botões na barra lateral, nenhuma fileira de abas, fase 1 ativa sem árvore e fase 2 ativa com árvore aberta | T001 | - | `tests/test_tres_fases_da_tela.py` | 🟢 | `[X]` |
| T004 | Escrever os testes dos estados vazios: com a pasta vazia, os painéis 2 e 3 não contêm `<input>`, `<select>` nem `<form>` de busca ou análise, e apontam para a fase 1 | T001 | - | `tests/test_tres_fases_da_tela.py` | 🟢 | `[X]` |
| T005 | Escrever os testes da fase 1: a lista e o envio aparecem nos **dois** estados; os contadores mostram total e disponíveis; "Abrir" só existe no item disponível | T001 | - | `tests/test_tres_fases_da_tela.py` | 🟢 | `[X]` |
| T006 | Escrever os testes do combobox: `<datalist>` ausente, bloco JSON presente e com `</script>` escapado, atributos ARIA (`role`, `aria-expanded`, `aria-controls`, `aria-activedescendant`), teclas tratadas no script e texto livre aceito | T001 | - | `tests/test_combobox_de_nomes.py` | 🟡 | `[X]` |
| T007 | Escrever o teste dos literais congelados: os oito rótulos e as mensagens de retorno continuam idênticos após a reorganização | T001 | - | `tests/test_tres_fases_da_tela.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Reescrever o esqueleto da tela de entrada num bloco único: uma barra lateral `role="tablist"` com os três botões `data-bs-toggle="tab"` e três painéis `tab-pane`, removendo as duas fileiras de abas dos ramos atuais | T003 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T009 | Preencher a fase 1: cabeçalho `Fase 1 — Árvores GEDCOM`, caixa de status com a árvore aberta e o link "Escolher outra árvore", os dois contadores, a tabela pelo macro existente e o bloco de envio; remover a linha "Árvore aberta: …" de cima das fases | T008 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T010 | Preencher a fase 2: cabeçalho, caixa "Consulta baseada em", a nota de que a busca é documental, e os dois campos com a ação na mesma linha | T008 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T011 | Preencher a fase 3: cabeçalho, caixa "Modo de análise", a nota de que o DNA não altera o parentesco, o bloco do CSV e o bloco do nome com a ação | T008 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T012 | Escrever os estados vazios das fases 2 e 3, com o botão que leva à fase 1 e sem nenhum campo de formulário | T009 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T013 | Escrever o script do retorno do arquivo escolhido: ao escolher um arquivo, o bloco de envio troca o texto padrão pelo nome; ao limpar, volta ao texto padrão | T009 | - | `src/templates/index.html` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Trocar a `<datalist id="gedcom_names">` por um bloco `<script type="application/json">` com `all_names` filtrado por `tojson`, e remover a marcação por `<option>` | T011 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T015 | Escrever o script do combobox: leitura do JSON, filtro sem acento e sem caixa, teto de 50 opções com rodapé de total, `aria-expanded`/`aria-activedescendant`, ↑/↓/`Enter`/`Esc`, e saída limpa quando não há JavaScript | T014 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T016 | Escrever o CSS da navegação e dos painéis: barra lateral, item ativo com peso e fundo além da cor, cabeçalho de fase, caixa de status e blocos | T008 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T017 | Escrever o CSS dos contadores, da tabela (listramento, respiro, ações empilhadas), do bloco de envio e da linha com a ação junto do campo | T009 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T018 | Escrever o CSS do combobox: posição da lista, opção destacada, rodapé de total e o par de cores da seleção nos dois temas | T015 | - | `src/assets/app.css` | 🟡 | `[X]` |
| T019 | Escrever o comportamento móvel da barra: abaixo de 992 px vira faixa horizontal de três botões, com a fase ativa marcada do mesmo jeito, e conferir em 320 px que nenhuma fase produz rolagem horizontal | T016 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T020 | Verificar em execução se o plugin de abas trata ↑/↓ na barra vertical; se não tratar, acrescentar o handler mínimo que mapeia as setas para a ativação da fase | T008 | - | `src/templates/index.html` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Reduzir a escala do botão de tema preservando posição fixa, rótulo de destino, `aria-pressed` e o piso de legibilidade | T016 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T022 | Medir os contrastes novos nos dois temas (rótulos de fase, contadores, item ativo, opção destacada, texto do rodapé) e anotar os pares na folha | T015 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T023 | Medir o `GET /` com pasta vazia, comparar com `evidence/antes/`, e atualizar `SHA_DA_TELA` com hash antigo e novo registrados | T022 | - | `tests/test_icone_de_atalho.py` e `evidence/depois/hash.txt` | 🟢 | `[X]` |
| T024 | Rodar a suíte completa e as guardas da tela, e gravar os resultados em `evidence/depois/` | T023 | - | `_reversa_forward/037-redesenho-das-tres-fases/evidence/depois/` | 🟢 | `[X]` |
| T025 | Conferir o escopo por diff: só template, folha e testes; nenhum arquivo de `application/`, `ports/` ou `core/`; área de resultados intacta; literais preservados | T024 | - | `evidence/depois/escopo.txt` | 🟢 | `[X]` |
| T026 | Escrever `legacy-impact.md` com os componentes tocados e o tipo de impacto de cada um | T025 | `[//]` | `_reversa_forward/037-redesenho-das-tres-fases/legacy-impact.md` | 🟢 | `[X]` |
| T027 | Escrever `regression-watch.md` com os itens sob vigilância e as observações | T025 | `[//]` | `_reversa_forward/037-redesenho-das-tres-fases/regression-watch.md` | 🟢 | `[X]` |
| T028 | Escrever o relatório consolidado em `evidence/RELATORIO.md`, incluindo o que o teste não cobre (o comportamento executado do combobox) e o resultado do checklist manual | T025 | - | `evidence/RELATORIO.md` | 🟢 | `[X]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-to-do` | reversa |

## Emendas

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| E001 | Masthead em duas colunas — subtítulo, título e texto à esquerda; arte à direita —, emendando a `RN-24` | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| E002 | Separar a masthead da área das fases: mais ar e uma linha fina entre as duas | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E003 | Cabeçalho da fase ocupando a largura inteira, com a caixa de status alinhada à borda da nota | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E004 | Rótulos e campos da fase 3 alinhados pelo topo, na mesma linha | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E005 | Três blocos informativos da jornada entre a linha divisória e as fases | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| E006 | Fileira de três abas acima do painel, como segundo controle das mesmas fases | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| E007 | Abas na coluna do conteúdo, ao lado da barra lateral, e não atravessando acima dela | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E008 | Sem barra de rolagem na fileira de abas: ela quebra em vez de rolar | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E009 | Arte da masthead dentro de uma caixa com cantos arredondados e sombra | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E010 | Tipografia da sugestão visual: Cormorant Garamond + Manrope, com as nativas como plano B | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| E011 | "Observações do arquivo" nasce fechada, mantendo o recolhível | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| E012 | Resumo dos resultados num parágrafo só: contagem, sugestão e legenda juntas | - | - | `src/templates/index.html` | 🟢 | `[X]` |
