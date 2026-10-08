# Actions: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Roadmap: `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **15** |
| Paralelizáveis (`[//]`) | **6** (`T004`, `T005`, `T008`, `T010`, `T011`, `T012`) |
| Maior cadeia de dependência | **7 ações** (6 elos): `T001` → `T002` → `T007` → `T008` → `T009` → `T013` → `T014` |
| Linha de base herdada | `282 passed`, `8 skipped`, paridade `100 %` — medidos em 2026-10-08, **antes** do plano |

> **Aviso de proporção, para quem ler a tabela.** Esta é uma feature **pequena**: uma rota, um
> arquivo de arte e dois arquivos de teste. A `Fase 3` tem **uma** ação e ela é a rota inteira,
> porque a feature **não tem lógica de domínio** — servir um arquivo fixo é adaptação de entrada
> (`D-01`). Uma decomposição maior aqui seria cerimônia, e o `roadmap.md` §3 registra a
> alternativa descartada de criar um caso de uso para uma rota que não decide nada.

## Fase 1, Preparação

<!-- Setup, scaffolding, migrações iniciais, configuração de infraestrutura local. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Escrever a receita de derivação de `D-02` como função pura — compor a arte canônica sobre branco `#ffffff`, reamostrar para 180×180 e salvar em PNG otimizado — num módulo auxiliar de `tests/`, com o comando de regeneração no docstring | - | - | `tests/icone_de_atalho.py` | 🟢 | `[X]` |
| T002 | Executar a receita de `T001` e gravar a arte de runtime em `src/assets/apple-touch-icon.png`, criando a pasta. Conferir no ato: **180×180**, alfa `(255, 255)` e **16.504 bytes** | T001 | - | `src/assets/apple-touch-icon.png` | 🟢 | `[X]` |
| T003 | Conferir a arte gravada com sonda **independente** da que a produziu — dimensão, canais, quatro cantos `(255, 255, 255)` e tamanho — e gravar a medição em evidência | T002 | - | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T003-arte-derivada.md` | 🟢 | `[X]` |

## Fase 2, Testes

<!-- Testes que precisam existir antes ou logo após o núcleo. Omitir se a equipe não pratica TDD. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever o teste da rota que **falha antes** da mudança: `GET /apple-touch-icon.png` → `200`, tipo de imagem, **180×180**, **nenhum** pixel transparente (`RF-01`, `RF-02`, `RF-03`, `RF-08`). Registrar a execução contra o estado anterior como prova do "falha antes". ⚠️ **Concluir esta ação significa "escrito e falhando"**, não "verde": a rota só existe em `T007`, e é `T010` que mede o verde | T001 | `[//]` | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |
| T005 | Escrever o teste de deriva da arte (`RF-10`): **regenerar** a partir de `docs/assets/img/logo.png` com a receita de `T001` e comparar **pixel a pixel**; incluir o caso que **não** pode falhar — reencodar a canônica com outra compressão. Confirmar que alterar **um** pixel da arte de runtime faz o teste falhar | T001 | `[//]` | `tests/test_deriva_da_arte.py` | 🟢 | `[X]` |
| T006 | Acrescentar ao mesmo arquivo de `T004`: recusa de método (`RF-06`), revalidação com resposta de conteúdo não modificado e **sem** validade longa (`RF-07`), imutabilidade byte a byte da tela (`RF-05`, `RF-09`) e os caminhos não servidos continuando sem resposta (`RF-11`, `RN-08`) | T004 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

<!-- Lógica central da feature. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Registrar `GET /apple-touch-icon.png` em `src/app.py`, ao lado da rota do formulário: servir a arte de `src/assets/` pela facilidade de arquivo do framework (`D-04`), **sem** validade longa declarada (`D-05`), com o caminho derivado de `__file__` e **nenhuma** entrada do cliente (`D-06`). Registrar a rota **só** com `GET`, para a recusa de método sair do roteador (`D-07`) | T002 | - | `src/app.py` | 🟢 | `[X]` |

> A `Fase 3` tem **uma** ação porque a feature não tem núcleo de domínio. Nenhuma linha de
> `src/core/`, `src/parsers/`, `src/reporting/` ou `src/utils/` é tocada — e o critério de pronto
> do roadmap exige provar isso por `diff` (`T012`), não por afirmação.

## Fase 4, Integração

<!-- Cola com outras partes do sistema, contratos externos, ganchos. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Provar que a arte entra na **imagem**, e não só no host: reconstruir o contêiner e listar o arquivo dentro dele (`RF-04`). Registrar a saída do `ls` como evidência | T007 | `[//]` | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T008-arte-na-imagem.md` | 🟢 | `[X]` |
| T009 | Provar por HTTP **de dentro do contêiner**, na porta do contêiner e não na publicada, que a rota responde `200` com o tipo e o tamanho esperados (`RF-04`). Diferenciar explicitamente este caso do de `T008`: um arquivo presente com rota quebrada passaria em `T008` e falharia aqui | T008 | - | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T009-rota-no-conteiner.md` | 🟢 | `[X]` |
| T010 | Medir a **suíte** e a **paridade** depois da mudança e registrar os dois números contra a linha de base do resumo. A paridade é a mesma por construção, porque o núcleo não é tocado — e é justamente por isso que ela tem de ser **medida**, não presumida | T007 | `[//]` | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T010-linha-de-base.md` | 🟢 | `[X]` |

## Fase 5, Polimento

<!-- Logs, telemetria, mensagens de erro, documentação curta. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Varredura de forma: conferir que o contexto de build **não** exclui a arte, que `src/static/` continua **ausente** e que nenhuma superfície sem consumidor foi criada — o alias legado e o caminho do ícone de aba continuam sem resposta (`RN-07`, `RN-09`, `W004`) | T007 | `[//]` | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T011-varredura-de-forma.md` | 🟢 | `[X]` |
| T012 | Provar por `diff` que o template e o núcleo estão **intocados**, e que `src/app.py` mudou **apenas** no que a rota exige (`RF-05`, `RN-02`, `W005`, `W016`) | T007 | `[//]` | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T012-conferencia-de-escopo.md` | 🟢 | `[X]` |
| T013 | Produzir `evidence/README-evidencias.md`: os instrumentos usados, os comandos, o resíduo deixado em disco e as lacunas que restaram | T009, T010, T011, T012 | - | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/README-evidencias.md` | 🟢 | `[X]` |
| T014 | Gerar `regression-watch.md` com os itens de vigilância desta entrega e as observações do que foi medido, sem reciclar IDs de features anteriores | T013 | - | `_reversa_forward/009-rota-do-apple-touch-icon/regression-watch.md` | 🟢 | `[X]` |
| T015 | Verificação manual pelo `onboarding.md`, na parte que o host e o contêiner provam. A prova em **aparelho real** é declarada como **pendente do operador** — nenhum comando daqui a substitui (`investigation.md` §6.1) | T013 | - | `_reversa_forward/009-rota-do-apple-touch-icon/evidence/T015-verificacao-manual.md` | 🟢 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-to-do` | reversa |
