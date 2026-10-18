# Actions: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Roadmap: `_reversa_forward/027-harmonizar-topo-da-tela/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 18 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 10 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Congelar a linha de base: `git status --porcelain`, `git log -1 --oneline`, a suíte completa e o `SHA_DA_TELA` atual; esperado **1.048 passam, 9 pulados, 0 falham** (`D-09`) | - | `[//]` | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/antes/suite.txt` | 🟢 | [X] |
| T002 | Registrar o recorte atual do topo: as classes do alerta, as três ocorrências de `d-grid`, o `clamp` do `h1`, a largura da arte e o texto do comentário da introdução (`D-01` a `D-07`) | - | `[//]` | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/antes/topo.txt` | 🟢 | [X] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Rodar **antes da edição** os três arquivos de guarda — `tests/test_banner_do_topo.py`, `tests/test_estilo_da_tela.py`, `tests/test_icone_de_atalho.py` — e registrar a saída, com atenção ao teste da `RN-24` | T001 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/antes/testes-da-tela.txt` | 🟢 | [X] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Acrescentar ao `:root` e ao tema escuro os quatro tokens de alerta: `--sucesso-bg`, `--sucesso-line`, `--perigo-bg`, `--perigo-line`, com os valores medidos no `data-delta.md` (`D-04`) | T001 | - | `src/assets/app.css` | 🟢 | [X] |
| T005 | Criar as regras de `.alert-success`, `.alert-danger` e `.alert .btn-close` com os tokens novos, forma compacta e o comentário trazendo os oito contrastes medidos; **não** usar seletor `.alert` genérico (`D-03`, `D-05`, `RF-02`, `RF-10`) | T004 | - | `src/assets/app.css` | 🟢 | [X] |
| T006 | Aliviar a ação principal: `.d-grid > .btn` com largura natural e `justify-self:start` dentro de `@media (min-width:576px)`, mantendo a largura total abaixo (`D-06`, `RF-03`) | T001 | - | `src/assets/app.css` | 🟢 | [X] |
| T007 | Compactar a escala do topo: `h1` para `clamp(1.8rem, 3.2vw, 2.2rem)` e arte para `min(50%, 280px)` (`D-07`, `RF-04`) | T001 | - | `src/assets/app.css` | 🟢 | [X] |
| T008 | Corrigir o comentário da masthead para descrever a `RN-24` (texto centralizado e em coluna estreita), **sem tocar no markup da introdução** (`D-02`, `RF-01`) | T001 | `[//]` | `src/templates/index.html` | 🟢 | [X] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Medir os degraus de espaçamento do topo (1rem dos campos, 1,5rem das abas/masthead/observações) e ajustar **somente** o que estiver fora; registrar a medição (`D-08`, `RF-05`) | T005, T006, T007, T008 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/ritmo.txt` | 🟡 | [X] |
| T010 | Medir o novo `sha256` de `GET /` e atualizar `SHA_DA_TELA` em `tests/test_icone_de_atalho.py`, com um bloco datado explicando a contribuição de cada mudança (`D-09`, `RF-08`) | T008 | - | `tests/test_icone_de_atalho.py` | 🟢 | [X] |
| T011 | Rodar **depois** os mesmos três arquivos de guarda e comparar com a T003: contraste dos selos, hash da tela e a `RN-24` verde (`RF-07`, `RF-09`) | T009, T010 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/testes-da-tela.txt` | 🟢 | [X] |
| T012 | Rodar a suíte completa **depois** e comparar com a T001: **1.048 passam, 9 pulados, 0 falham**, sem teste removido (`RF-09`) | T011 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/suite.txt` | 🟢 | [X] |
| T013 | Provar o escopo: `git diff --stat` só com `src/assets/app.css` e `src/templates/index.html`; `text-start` ausente; nenhuma regra dos cartões de resultado alterada (`RN-08`, `RF-06`) | T010 | `[//]` | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/escopo.txt` | 🟢 | [X] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Conferir por medição os alertas nos dois temas (incluindo o X), a largura da ação nas duas faixas e a escala do `h1`/arte; registrar o observado (`D-03`, `D-06`, `D-07`) | T012 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/depois/tela.md` | 🟡 | [X] |
| T015 | Consolidar o relatório da feature: tokens novos, contrastes, escala, escopo do diff, hash e suíte (`D-09`) | T013, T014 | - | `_reversa_forward/027-harmonizar-topo-da-tela/evidence/RELATORIO.md` | 🟢 | [X] |
| T016 | Escrever o `legacy-impact.md`: arquivos tocados, tipo de impacto e a `RN-24` preservada | T015 | - | `_reversa_forward/027-harmonizar-topo-da-tela/legacy-impact.md` | 🟢 | [X] |
| T017 | Escrever o `regression-watch.md`: alertas na paleta, CTA natural, escala, `SHA_DA_TELA`, `RN-24` e rodapé intocado, cada um com o sintoma | T015 | - | `_reversa_forward/027-harmonizar-topo-da-tela/regression-watch.md` | 🟢 | [X] |
| T018 | Escrever o adendo `027-harmonizar-topo-da-tela.md` em `_reversa_sdd/addenda/`. **Estágio `/reversa-sync`** (`RF-08`) | T017 | - | `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md` | 🟢 | [X] |

## Notas de execução

- A suíte cria `tests/.tmp`; se o ambiente negar escrita nessa pasta, o erro é de permissão do Windows, não da feature.
- O comentário da T008 fica ao lado do markup da introdução: **nenhuma tag, classe ou atributo** daquele bloco pode mudar. O teste da `RN-24` é a guarda.
- A regra da T005 não pode usar `.alert` sozinho: há um `alert-warning` dentro de um cartão de resultado (`index.html:1015`) que precisa ficar como está.
- **T009:** os degraus do topo estão consistentes (1 rem nos campos, 1,5 rem nos blocos). Nenhum espaçamento foi alterado; a medição está em `evidence/depois/ritmo.txt`.
- **T010:** o comentário da masthead é **Jinja** e não chega ao HTML. O `SHA_DA_TELA` **não mudou** (`c4a34f7b…`), o teste do hash passou sem edição, e a razão está em `evidence/depois/hash.txt`.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-to-do` | reversa |
