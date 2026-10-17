# Actions: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Roadmap: `_reversa_forward/026-polimento-visual-da-tela/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 15 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 11 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Congelar a linha de base: `git status --porcelain`, `git log -1 --oneline` e a suíte completa, com `DATABASE_URL` ausente; esperado **1.048 passam, 9 pulados, 0 falham** (`D-08`) | - | `[//]` | `_reversa_forward/026-polimento-visual-da-tela/evidence/antes/suite.txt` | 🟢 | [ ] |
| T002 | Registrar o recorte atual da folha: as quatro definições mortas (`--ok`, `--poss`, `--conf`, `--inc`), a declaração de `--st-inconclusivo` e os dois comentários do bloco do banner, com os números de linha (`D-02`, `D-05`) | - | `[//]` | `_reversa_forward/026-polimento-visual-da-tela/evidence/antes/folha.txt` | 🟢 | [ ] |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Rodar **antes da edição** os três arquivos de guarda — `tests/test_estilo_da_tela.py`, `tests/test_icone_de_atalho.py`, `tests/test_banner_do_topo.py` — e registrar a saída, para comparar com a de depois (`D-07`, `D-08`) | T001 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/antes/testes-da-tela.txt` | 🟢 | [ ] |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Remover do `:root` as definições `--ok`, `--poss`, `--conf` e `--inc`; a família `--st-*` passa a ser a única declaração das quatro cores (`D-02`, `RF-11`) | T001 | - | `src/assets/app.css` | 🟢 | [ ] |
| T005 | Comentar a declaração de `--st-inconclusivo`: manter `#6A6150`, proibir o alias com `--muted` e registrar que branco sobre o selo dá **6,11:1**, enquanto o `--muted` escuro (`#A99F88`) daria **2,62:1** (`D-03`, `RF-04`) | T004 | - | `src/assets/app.css` | 🟢 | [ ] |
| T006 | Acrescentar ao comentário da seção de estados os quatro contrastes medidos — **6,39 / 7,13 / 6,69 / 6,11:1** — e a razão do texto branco, **preservando** o caso histórico do laranja (`#fd7e14` = 2,57:1) (`D-04`, `RF-05`) | T005 | - | `src/assets/app.css` | 🟢 | [ ] |
| T007 | Reescrever os **dois** comentários do bloco do banner: o da placa branca do tema escuro (que hoje diz que o texto da arte é marrom) e o do `<h1>` (que hoje diz que o banner mostra o nome), descrevendo a arte atual — sem texto, com a placa justificada pelo fundo claro da ilustração (`D-05`, `RF-06`) | T006 | - | `src/assets/app.css` | 🟢 | [ ] |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Rodar **depois** os mesmos três arquivos de guarda e comparar com a saída da T003: contraste dos selos nos dois temas, `sha256` da tela `c4a34f7b…` e `h1` sem `visually-hidden` (`D-07`, `RF-10`) | T007 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/depois/testes-da-tela.txt` | 🟢 | [ ] |
| T009 | Rodar a suíte completa **depois** e comparar com a T001: **1.048 passam, 9 pulados, 0 falham**, sem teste removido ou desabilitado (`RF-09`) | T008 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/depois/suite.txt` | 🟢 | [ ] |
| T010 | Provar o escopo com `git diff --stat`: **apenas** `src/assets/app.css`; nenhuma alteração em `src/templates/`, `src/app.py` ou `tests/`; registrar também que o `SHA_DA_TELA` não foi tocado (`D-01`, `RF-17`, `RF-10`) | T007 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/depois/escopo.txt` | 🟢 | [ ] |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Conferir na tela pelos passos 2 a 5 do `onboarding.md` — ícone da aba, rota do atalho, selo `Inconclusivo` nos dois temas e ausência dos tokens — e registrar o observado (`D-08`) | T009 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/depois/tela.md` | 🟡 | [ ] |
| T012 | Consolidar o relatório da feature: tabela antes/depois dos tokens, os quatro contrastes, o recorte do diff, o resultado do hash e a contagem da suíte (`D-08`) | T010, T011 | - | `_reversa_forward/026-polimento-visual-da-tela/evidence/RELATORIO.md` | 🟢 | [ ] |
| T013 | Escrever o `legacy-impact.md`: o único arquivo tocado, o tipo de impacto (`regra-alterada` de apresentação) e a evidência que o sustenta (`D-01`) | T012 | - | `_reversa_forward/026-polimento-visual-da-tela/legacy-impact.md` | 🟢 | [ ] |
| T014 | Escrever o `regression-watch.md`: tokens mortos ausentes, os quatro contrastes, `SHA_DA_TELA` inalterado, suíte em 1.048/9 e template intocado, cada um com o sintoma que o dispara (`D-03`, `D-08`) | T012 | - | `_reversa_forward/026-polimento-visual-da-tela/regression-watch.md` | 🟢 | [ ] |
| T015 | Escrever o adendo `026-polimento-visual-da-tela.md` em `_reversa_sdd/addenda/`: vigência, as três decisões, a remoção dos tokens e a evidência. **Estágio `/reversa-sync`** (`D-09`, `RF-03`) | T014 | - | `_reversa_sdd/addenda/026-polimento-visual-da-tela.md` | 🟢 | [ ] |

## Notas de execução

- A suíte cria `tests/.tmp`; se o ambiente negar escrita nessa pasta, o erro é de permissão do Windows, não da feature. Rodar com o workspace gravável (ver `onboarding.md` §5).
- Nenhuma ação desta feature toca `src/templates/index.html`, `src/app.py`, `tests/` ou qualquer módulo de `application/`, `ports/`, `core/`, `parsers/` ou `reporting/`.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-to-do` | reversa |
