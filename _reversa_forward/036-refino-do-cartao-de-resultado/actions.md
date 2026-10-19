# Actions: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Roadmap: `_reversa_forward/036-refino-do-cartao-de-resultado/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 20 |
| Paralelizáveis (`[//]`) | 5 |
| Maior cadeia de dependência | 14 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Congelar a linha de base: `git status --porcelain`, `git log -1 --oneline` e a suíte completa; esperado **1.282 passam, 11 pulados, 0 falham** (`D-01`) | - | `[//]` | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/antes/suite.txt` | 🟢 | [X] |
| T002 | Copiar as duas superfícies para o baseline de diff — `src/assets/app.css` e `src/templates/index.html` — e registrar o `SHA_DA_TELA` (`c4a34f7b…`, 30.781 bytes) (`D-01`) | - | `[//]` | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/antes/` | 🟢 | [X] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever `tests/test_cartao_em_tres_faixas.py`: as três faixas no `h5` (título, selos e sinais), o título em 1,4 rem, as regras escopadas em `.cartao-do-resultado`, o hover sem sublinhado e a ausência de `div` dentro do `card-header` (`D-01`, `D-09`, `RF-01` a `RF-03`) | T002 | `[//]` | `tests/test_cartao_em_tres_faixas.py` | 🟢 | [X] |
| T004 | Rodar o arquivo novo **antes da edição** e registrar a falha esperada, provando que ele mede o arranjo novo e não passa por acidente (`D-01`) | T003 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/antes/novo-teste.txt` | 🟢 | [X] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Reestruturar o `h5` do cartão: `span.conteudo-do-cabecalho` com `span.titulo-da-conexao`, `span.selos-do-cabecalho` e o `span.cabecalho-sinais` existente; o link `voltar-ao-indice` sai do meio e passa a ser o segundo item do `h5`. **Só `span`; nenhum `div`** (`D-01`, `D-02`, `RN-05`) | T002 | `[//]` | `src/templates/index.html` | 🟢 | [X] |
| T006 | Criar o casco do cartão em `.cartao-do-resultado`: `position:relative`, raio de 16 px, degradê `--surface → --surface-2`, sombra no claro, `::before` de 5 px com `--muted → --head`, header sem o tom `--surface-2`, padding à esquerda da barra e o comentário com os contrastes medidos (`D-05`, `D-06`, `RF-06`, `RF-12`) | T002 | `[//]` | `src/assets/app.css` | 🟢 | [X] |
| T007 | Criar as três faixas: `h5` em `flex` com `align-items:center`, `.conteudo-do-cabecalho` com `min-width:0`, `.titulo-da-conexao` em bloco a 1,4 rem, `.selos-do-cabecalho` em `flex` com quebra e a terceira faixa com `clear:none` (`D-02`, `D-09`, `RF-01` a `RF-03`) | T006 | - | `src/assets/app.css` | 🟢 | [X] |
| T008 | Refinar o "Voltar": `float:none`, `inline-flex`, `gap`, `padding` da pílula, fundo `--surface` e o chevron à esquerda em `::before` com bordas giradas; nada de markup novo (`D-03`, `RF-04`) | T007 | - | `src/assets/app.css` | 🟢 | [X] |
| T009 | Refinar o indicador: `padding-right` no `summary`, caixa arredondada em `::before` e o chevron (`::after`) absoluto por cima, mantendo as regras genéricas de `details.card > summary…` intactas (`D-04`, `RF-05`) | T008 | - | `src/assets/app.css` | 🟢 | [X] |
| T010 | Neutralizar o sublinhado no hover e empilhar o cabeçalho abaixo de 575,98 px (`flex-wrap` + `flex-basis:100%`), com o "Voltar" na própria linha (`D-08`, `D-10`, `RF-07`, `RF-08`) | T009 | - | `src/assets/app.css` | 🟢 | [X] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Rodar as guardas da tela e do cartão — `test_cartoes_recolhiveis`, `test_estado_do_resultado`, `test_estilo_da_tela`, `test_validacao_no_cartao`, `test_contador_em_tres_faixas`, `test_identidade_do_match`, `test_janela_de_vida`, `test_arvore_sugerida_na_tela` — e corrigir o que quebrar (`RN-05`, `RN-06`, `RF-09`) | T005, T010 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/guardas.txt` | 🟢 | [X] |
| T012 | Rodar o teste novo da T003 e confirmar que ele passa com o arranjo entregue (`RF-01` a `RF-03`) | T003, T011 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/novo-teste.txt` | 🟢 | [X] |
| T013 | Medir o `sha256` e o tamanho de `GET /` e atualizar `SHA_DA_TELA` **só se** tiver movido, com bloco datado; esperado inalterado (`D-01`, `RF-10`) | T011 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/hash.txt` | 🟢 | [X] |
| T014 | Rodar a suíte completa **depois** e comparar com a T001: ≥ 1.282 passam, 11 pulados, 0 falhas, sem teste removido (`RF-11`) | T012, T013 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/suite.txt` | 🟢 | [X] |
| T015 | Provar o escopo: `git diff --stat -- src/` listando só os dois arquivos, e nenhuma regra nova alcançando `bloco-descartados`/`observacoes-do-arquivo` (`RN-07`, `RF-09`) | T014 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/escopo.txt` | 🟢 | [X] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Conferir por medição no HTML servido: as três faixas na ordem, o link `voltar-ao-indice` intacto, o chevron e os contrastes resolvidos nos dois temas; registrar o observado (`D-03`, `D-04`, `RF-12`) | T015 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/cartao.md` | 🟡 | [X] |
| T017 | Consolidar o relatório da feature: superfícies tocadas, contrastes, escopo do diff, hash e suíte (`D-06`) | T016 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/RELATORIO.md` | 🟢 | [X] |
| T018 | Escrever o `legacy-impact.md`: arquivos tocados, tipo de impacto e os blocos irmãos intocados | T017 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/legacy-impact.md` | 🟢 | [X] |
| T019 | Escrever o `regression-watch.md`: as três faixas, o link, o indicador, o hover, o escopo e o hash, cada um com o sintoma | T018 | - | `_reversa_forward/036-refino-do-cartao-de-resultado/regression-watch.md` | 🟢 | [X] |
| T020 | Escrever o adendo `036-refino-do-cartao-de-resultado.md` em `_reversa_sdd/addenda/`. **Estágio `/reversa-sync`** (`RF-10`) | T019 | - | `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` | 🟢 | [X] |

## Notas de execução

- A suíte cria `tests/.tmp`; se o ambiente negar escrita nessa pasta, o erro é de permissão do Windows, não da feature.
- **T005:** o `h5` não pode ganhar nenhum `div` — os extratores dos testes cortam o cabeçalho no primeiro `</div>` (`RN-05`). O link e os sinais continuam dentro dele.
- **T006–T010:** todas as regras novas são escopadas em `.cartao-do-resultado`; as regras genéricas `details.card > summary.sumario-do-cartao…` ficam intactas porque os blocos irmãos as usam (`RN-07`).
- **T009:** os literais `details.card > summary.sumario-do-cartao::after{`, `transform:rotate(45deg)` e `transform:rotate(-135deg)` continuam na folha; o escopo só acrescenta posição e `margin`.
- **T013:** a mudança vive sob `{% if dna_results %}`; a tela vazia que o hash mede não deve mover.
- **Execução:** o arranjo final saiu em grid com áreas nomeadas dentro de `.conteudo-do-cabecalho`, e não em `flex` no `h5` como o `D-02` previa. O motivo e o resultado estão em `evidence/RELATORIO.md` §3; o visual é o mesmo e o link não precisou mudar de lugar no DOM.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-to-do` | reversa |
