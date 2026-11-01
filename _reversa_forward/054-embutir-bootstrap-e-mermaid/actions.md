# Actions: os recursos visuais da tela vêm da própria aplicação

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Roadmap: `_reversa_forward/054-embutir-bootstrap-e-mermaid/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 27 |
| Paralelizáveis (`[//]`) | 13 |
| Maior cadeia de dependência | 7 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Baixar `bootstrap.min.css` 5.3.3 do jsDelivr para `src/assets/` e conferir os 232.803 bytes e o `sha256` `3c8f27e6…` | - | `[//]` | `src/assets/bootstrap.min.css` | 🟢 | `[X]` |
| T002 | Baixar `bootstrap.bundle.min.js` 5.3.3 do jsDelivr para `src/assets/` e conferir os 80.721 bytes e o `sha256` `0833b2e9…` | - | `[//]` | `src/assets/bootstrap.bundle.min.js` | 🟢 | `[X]` |
| T003 | Baixar `mermaid.min.js` **10.9.8** do jsDelivr para `src/assets/` e conferir os 3.337.857 bytes e o `sha256` `8d607d7e…` | - | `[//]` | `src/assets/mermaid.min.js` | 🟢 | `[X]` |
| T004 | Escrever a receita `tests/fontes_da_tela.py`: consultar o CSS2 do Google como navegador, reescrever as 11 URLs de `woff2` para `/fontes/<arquivo>.woff2`, gravar `src/assets/fontes.css` e os `woff2`; import sem rede e `main()` manual | - | - | `tests/fontes_da_tela.py` | 🟢 | `[X]` |
| T005 | Executar a receita e conferir o derivado: 45 blocos `@font-face`, 11 URLs locais, 201.468 bytes de `woff2` e nenhuma URL de `fonts.gstatic.com` no CSS | T004 | - | `src/assets/fontes.css` | 🟢 | `[X]` |
| T006 | Registrar a procedência num rascunho de evidência: versão, origem, bytes, `sha256` e licença de cada arquivo embutido | T001, T002, T003, T005 | - | `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/procedencia.md` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Escrever `tests/test_recursos_embutidos.py`: cada uma das cinco rotas responde 200, com o tipo de mídia declarado e corpo byte a byte igual ao arquivo em disco, contra o `sha256` fixado | T001, T002, T003, T005 | `[//]` | `tests/test_recursos_embutidos.py` | 🟢 | `[X]` |
| T008 | Escrever `tests/test_recursos_degradacao.py`: arquivo ausente por `monkeypatch` devolve 404 com a tela ainda em 200; nome de `woff2` fora do conjunto fecha em 404; tentativa com separador de caminho e `..` também | T001, T002, T003 | `[//]` | `tests/test_recursos_degradacao.py` | 🟢 | `[X]` |
| T009 | Escrever `tests/test_tela_sem_origem_externa.py`: o HTML de `GET /` e das seis telas de identidade não tem URL absoluta em `link`, `preconnect` nem `script`; Bootstrap antes de `app.css`; `bootstrap.js` no fim do corpo e `mermaid.js` no `<head>` | - | `[//]` | `tests/test_tela_sem_origem_externa.py` | 🟢 | `[X]` |
| T010 | Escrever `tests/test_fontes_da_tela.py`: o derivado confere **sem rede** — 11 arquivos existem com o `sha256` declarado, o CSS tem 45 blocos e aponta só para caminhos locais | T005 | `[//]` | `tests/test_fontes_da_tela.py` | 🟢 | `[X]` |
| T011 | Atualizar as listas fechadas de rotas: acrescentar as cinco rotas em `test_fabrica_do_app.py` e em `test_cabecalho_de_enquadramento.py`, as cinco chaves em `CHAVES`, e os caminhos novos em `test_host_permitido.py` | - | `[//]` | `tests/test_fabrica_do_app.py` | 🟢 | `[X]` |
| T012 | Atualizar `test_sessao_e_guarda.py` (as rotas novas continuam públicas) e `verificacao_no_conteiner.py` (entram em `ROTAS_DE_ARTE`), sem afrouxar o que os dois já prendem | - | `[//]` | `tests/test_sessao_e_guarda.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Acrescentar a `src/app.py` as cinco constantes de caminho (`BIBLIOTECA_CSS`, `BIBLIOTECA_JS`, `MERMAID`, `FOLHA_DE_FONTES`, `PASTA_DE_FONTES`) e publicá-las em `create_app`, no molde de `ESTILO_DA_TELA` | T001, T002, T003, T005 | - | `src/app.py` | 🟢 | `[X]` |
| T014 | Implementar em `src/web/rotas_assets.py` as três rotas de biblioteca (`/bootstrap.css`, `/bootstrap.js`, `/mermaid.js`), com `mimetype` explícito e 404 para arquivo ausente | T013 | - | `src/web/rotas_assets.py` | 🟢 | `[X]` |
| T015 | Implementar em `src/web/rotas_assets.py` a folha de fontes e a rota dos `woff2`, validando o nome contra o conjunto fechado dos 11 arquivos e recusando o resto com 404 | T013, T005 | - | `src/web/rotas_assets.py` | 🟢 | `[X]` |
| T016 | Acrescentar os cinco endpoints novos a `PUBLICOS` em `src/web/sessao.py`, nomeando cada um | T014, T015 | - | `src/web/sessao.py` | 🟢 | `[X]` |
| T017 | Trocar as quatro tags externas de `index.html` pelas locais, com `?v=`: Bootstrap CSS, folha de fontes, Mermaid e Bootstrap JS; preservar a ordem do `<head>` e a posição dos scripts | T014, T015 | `[//]` | `src/templates/index.html` | 🟢 | `[X]` |
| T018 | Trocar a tag do Bootstrap em `_entrada_base.html` por `/bootstrap.css?v=5.3.3`, sem tocar no resto do `<head>` | T014 | `[//]` | `src/templates/_entrada_base.html` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T019 | Rodar a suíte completa e corrigir o que a mudança quebrou; nenhum teste existente é ajustado para passar — só o que a feature mudou de contrato e está declarado | T007, T008, T009, T010, T011, T012, T016, T017, T018 | - | `tests/` | 🟢 | `[X]` |
| T020 | Rodar `tests/rodar_paridade.py` e comparar o número de divergências com a linha de base de 2026-10-30 (30), registrando o resultado | T019 | - | `tests/rodar_paridade.py` | 🟢 | `[X]` |
| T021 | Recalcular `SHA_DA_TELA`, atualizar o valor em `tests/test_icone_de_atalho.py` e escrever o comentário com a data, o delta em bytes e o ponteiro para a declaração | T017 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |
| T022 | Registrar em `evidence/SHA_DA_TELA.md` o valor anterior (`577a17fd…`, 51.612 bytes), o novo, a diferença em bytes e a razão — as tags do `<head>` —, para o adendo do `/reversa-sync` | T021 | - | `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/SHA_DA_TELA.md` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Medir o tempo de resposta de cada rota nova e o peso total por página; registrar em `evidence/medicoes.md` | T019 | `[//]` | `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/medicoes.md` | 🟡 | `[X]` |
| T024 | Rodar a verificação dentro do contêiner (`docker compose build` e `run --rm app python tests/verificacao_no_conteiner.py`) e registrar a saída | T019 | - | `tests/verificacao_no_conteiner.py` | 🟢 | `[X]` |
| T025 | Atualizar o `README.md`: a pilha de front-end passa a ser servida pela aplicação e a afirmação de "assets por CDN" deixa de valer | T019 | `[//]` | `README.md` | 🟢 | `[X]` |
| T026 | Gerar `regression-watch.md` da feature, com os itens de vigilância e o marco da suíte | T019 | - | `_reversa_forward/054-embutir-bootstrap-e-mermaid/regression-watch.md` | 🟢 | `[X]` |
| T027 | Executar a conferência offline automatizável e registrar em `evidence/conferencia.md` o que ficou para o operador (olho no desenho, nas abas e no diagrama), com o roteiro do `onboarding.md` | T024 | - | `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/conferencia.md` | 🟢 | `[X]` |

## Notas de execução

- A aquisição de T001–T003 e da receita T004 exige rede. Medido em 2026-10-31: o Python do `.venv` alcança o
  jsDelivr e o Google Fonts; o `pwsh` da sessão não. Se a rede falhar, o operador baixa os arquivos e o `sha256`
  de T007/T010 confirma que são os certos.
- T005 e T010 não podem depender de rede: a receita é manual, o teste confere só o derivado commitado.
- T021 **não** é licença para atualizar o hash por rotina: o delta e a razão vão para T022, e o adendo definitivo
  nasce no `/reversa-sync`.
- `src/static/` continua proibida; se alguma ação parecer pedir uma pasta estática, a resposta é errada.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-31 | Versão inicial gerada por `/reversa-to-do` | reversa |
