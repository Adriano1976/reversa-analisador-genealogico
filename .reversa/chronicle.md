# Crônica — analisador-genealogico

> Histórico cronológico dos agentes Reversa e dos artefatos gerados desde o início do projeto.
> Fontes: `.reversa/state.json`, `git log`, `_reversa_forward/**/progress.jsonl`, `_reversa_docs/.state.json`.
> Timestamps no formato ISO-8601 (horário nativo de cada fonte: `Z` para UTC, `-03:00` para local).

> [!WARNING]
> **Correção de proveniência aplicada em 2026-09-30.** As entradas originais (2026-08-03 a 2026-08-13) citavam **23 hashes de commit que não existem no histórico atual do repositório** — os assuntos apareciam reescritos e os hashes não correspondiam a objeto algum (`git cat-file -t` falhava em todos). Todos os 23 foram reconferidos contra o `git log` e **22 foram corrigidos** para o commit real do mesmo dia, identificado por assunto; o vigésimo terceiro (o bootstrap de 2026-08-03, atribuído a `e43ca22`) não tem correspondência verificável e foi substituído por nota explícita.
>
> O arquivo tinha 23 hashes inválidos; agora tem **60 hashes, todos válidos**. Nenhuma descrição de evento foi alterada — apenas as referências de commit.

---

## 2026-08-03 — Inicialização e extração do sistema legado

- `2026-08-03T11:48:40Z` — **reversa-scout** — inventário da superfície. Gerou `_reversa_sdd/inventory.md`, `_reversa_sdd/dependencies.md`, `.reversa/context/surface.json`.
- `2026-08-03T12:22:00Z` — **reversa-archaeologist** — escavação do módulo `analisador-genealogico`. Gerou `_reversa_sdd/code-analysis.md`, `.reversa/context/modules.json`.
- `2026-08-03T12:31:00Z` — **reversa-detective** — conhecimento de negócio implícito. Gerou `_reversa_sdd/domain.md`.
- `2026-08-03T12:35:00Z` — **reversa-architect** — arquitetura. Gerou `_reversa_sdd/architecture.md`, `_reversa_sdd/c4-context.md`.
- `2026-08-03T12:50:00Z` — **reversa-writer** (fase geração) — specs das 3 unidades: `upload-gedcom`, `analise-dna`, `busca-caminho` (requirements.md + design.md + tasks.md cada).
- `2026-08-03T12:50:00Z` — **reversa-reviewer** — revisão e confiança. Gerou `_reversa_sdd/confidence-report.md`, `_reversa_sdd/questions.md` (4 perguntas respondidas; 1 reclassificação 🟢→🟡 no limiar HARD_MIN/GIVEN_MIN).
- `2026-08-03T12:52:00Z` — **reversa** (orquestrador) — extração completa, regression check silencioso, sem addendas pendentes.
- `2026-08-03T16:15:11-03:00` — bootstrap git `/reversa`: framework instalado, skills e templates criados (commit de origem nao resolve mais no historico atual).
- `2026-08-03T16:31:31-03:00` à `2026-08-03T18:13:45-03:00` — documentação do repo: README PT-BR, fix do parse Mermaid, autoria/créditos, contador de visitas e documentação interativa inicial (commits `d1d5707`, `d7cf49c`, `1e92fe8`, `8e80369`, `290399b`, `5fd0859`, `5f23f3d`, `d22fee9`, `10eba96`).

## 2026-08-06 — Atualização do framework

- `2026-08-06T14:35:38-03:00` — reconfiguração do projeto na nova versão do framework (commit `3a537a7`).
- `2026-08-06T14:41:29-03:00` — aceite do framework **reversa 1.2.58** (commit `56f9423`).

## 2026-08-07 — Reconstrução bottom-up

- `2026-08-07T10:32:56-03:00` — **reversa-reconstructor** — plano de reconstrução: `_reversa_sdd/reconstruction-plan.md` (commit `cd1fe0d`).
- `2026-08-07T12:00:29-03:00` — módulos `domain.py`, `path_search.py` e `upload.py` com testes (commit `d2ea17a`).
- `2026-08-07T12:43:35-03:00` — módulo `dna_analysis.py` com testes da análise de DNA (commit `5ee57c9`).
- `2026-08-07T12:52:39-03:00` — relatório final da reconstrução: `_reversa_sdd/reconstruction-report.md` (commit `1f90442`).
- `2026-08-07T13:00:32-03:00` — testes do módulo `domain.py` (commit `99b20b7`).
- `2026-08-07T13:06:05-03:00` — testes do módulo `upload.py` (commit `c6f178a`).
- `2026-08-07T13:10:07-03:00` — relatório final atualizado com novos testes (commit `d8ecd1b`).

## 2026-08-11 — Ciclo forward (features 001 e 002)

- `2026-08-11T13:36:03-03:00` — **reversa-forward → reversa-requirements → reversa-plan** — requirements e roadmap da feature 001 `001-reconstrua-o-conteudo-da-index` (commit `f24c561`).
- `2026-08-11T13:45:55Z` — **reversa-coding** feature 001 — ações T001–T004 concluídas: reconstrução do conteúdo de `templates/index.html`.
- `2026-08-11T14:11:08-03:00` — entrega da index e requirements da integração app-módulos (feature 002) (commit `b5884e9`).
- `2026-08-11T14:21:24-03:00` — **reversa-requirements → reversa-plan → reversa-to-do** — requirements, roadmap e actions da feature 002 `002-integrar-rota-app-modulos` (commit `ed3e6c0`).
- `2026-08-11T14:30:22-03:00` — relatório `actions.md` do reversa-to-do (commit `3e97f27`).
- `2026-08-11T14:32:10Z` — **reversa-coding** feature 002 — T001: módulos `reconstructed/` criados (`__init__.py`, `upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py`).
- `2026-08-11T14:33:34Z` — T002: testes `test_upload.py`, `test_path_search.py`, `test_dna_analysis.py`, `test_domain.py`.
- `2026-08-11T14:42:37Z` — T003–T006: integração das rotas no `app.py` (upload_gedcom, path_search, dna_analysis).
- `2026-08-11T14:43:52Z` — T007–T008: validação da suíte de testes e ajustes finais no `app.py`.
- `2026-08-11T16:13:47-03:00` — feat de integração dos módulos reconstruídos ao app Flask + reorganização da estrutura do projeto (commit `f51bac1`).

## 2026-08-12 — Mini-site do Reversa Docs

- `2026-08-12T13:41:00-03:00` — README com arquitetura modular e suíte de testes (commit `32ebb25`).
- `2026-08-12T14:00:00Z` — **reversa-docs** — início do pipeline (mapper, analyst, storyteller, publisher).
- `2026-08-12T14:16:28-03:00` — regeneração do mini-site `_reversa_docs/` para a arquitetura modular (commit `12a5708`).
- `2026-08-12T16:16:48-03:00` — **reversa-docs-storyteller** — glossário interativo e slide deck do soul (commit `02ff1ee`).
- `2026-08-12T18:41:35Z` — check-point final do docs: 17 páginas; timeline omitida por ausência do chronicle (que este arquivo agora resolve).

## 2026-08-13 — Licença, docstrings e merge

- `2026-08-13T01:30:56-03:00` — clarificação da licença no README (commit `cfe96b0`).
- `2026-08-13T01:42:33-03:00` — adição da MIT License ao projeto (commit `f1ca958`).
- `2026-08-13T01:47:42-03:00` — revisão dos links da documentação no README (commit `c6632d5`).
- `2026-08-13T10:30:26-03:00` — docstrings Google e correção de avisos do Pyrefly nos testes (commit `fe4d19c`).
- `2026-08-13T10:47:31-03:00` — merge de `origin/master` e README com a LICENSE (commit `17ac0c3`).

## 2026-08-16 — Crônica e timeline do mini-site

- `2026-08-16T16:48:38-03:00` — criação deste arquivo e da timeline do mini-site (commit `89c255e`). A partir daqui a crônica passa a existir como fonte; a timeline de `_reversa_docs/` passa a consumi-la.

> **Vazio de atividade entre 2026-08-17 e 2026-09-27.** O intervalo de ~6 semanas não tem nenhum commit no repositório. O ciclo forward parou depois da feature 002.

## 2026-09-28 — Ciclo de migração

- `2026-09-28T02:14:23-03:00` — artefatos de migração e documentação atualizados (commit `b7f786f`).
- `2026-09-28T13:02:20-03:00` — resíduos de execução do harness de paridade passam a ser ignorados (commit `2478ac7`).
- `2026-09-28T13:02:39-03:00` — **harness diferencial** oráculo × reconstrução (commit `7d5bce7`). Dois subprocessos obrigatórios, porque o oráculo mantém estado global mutável e importar ambos no mesmo processo contaminaria o candidato.
- `2026-09-28T13:02:48-03:00` — documentação do harness de paridade e da verificação pós-handoff (commit `cd34623`).
- `2026-09-28T15:17:17-03:00` — snapshot do repositório antes do Reversa (commit `797b57b`).
- **Artefatos do ciclo:** `_reversa_sdd/migration/` (19 artefatos, 6 agentes, strategy C), `_reversa_sdd/oracle/`, `_reversa_sdd/parity/`. Resultado medido: **paridade de 100%** em 6/6 fixtures sintéticas e 5/5 árvores reais, inclusive uma de 35.460 pessoas. A divergência `DIV-001` (`get_name`) foi encontrada e corrigida.

## 2026-09-29 — Refactor de qualidade, bugs e princípios

- `2026-09-29T03:20:41-03:00` — framework atualizado para **reversa 1.3.4** (commit `481c8c2`).
- `2026-09-29T03:20:49-03:00` — política de edição do legado documentada em `.reversa/reversa-config.json` (commit `80afe02`). Escrita fora das pastas do Reversa passa a exigir glob explícito.
- `2026-09-29T03:20:55-03:00` — **reversa-refactor** aplica as primeiras otimizações medidas (commit `4c7ca7d`).
- `2026-09-29T03:21:00-03:00` — **reversa-principles** e **reversa-debugger** registram princípios, bugs e oportunidades de refactor; cria `.reversa/principles.md` (commit `d25e2c3`).
- `2026-09-29T14:22:16-03:00` — redes de segurança do refactor promovidas a **testes permanentes** (commit `d51af14`). Surgem `tests/test_characterization_matching.py` e `tests/test_characterization_mermaid.py`.
- `2026-09-29T14:22:21-03:00` — adendo do refactor de qualidade de código: `_reversa_sdd/addenda/003-refactor-code-quality.md` (commit `e172e91`).
- `2026-09-29T14:33:51-03:00` — fim de linha normalizado em LF (commit `f9f65ae`).
- `2026-09-29T14:41:43-03:00` — **`OPP-B5F2` opção B** — limpeza de nome unificada em `domain.py` (commit `9318864`). Havia duas implementações que divergiam em **5 de 9 casos**.
- `2026-09-29T14:41:48-03:00` — registro da transformação `OPP-B5F2` (commit `45fc7c6`).
- `2026-09-29T14:41:54-03:00` — `extraPaths` do Pylance configurado para a raiz da fonte (commit `755f679`).
- `2026-09-29T14:55:52-03:00` — **`OPP-4MGR`** — o índice deixa de renormalizar na construção (commit `8e09fe5`). Medido: 27,77 ms → 2,29 ms por match (12,13x).
- `2026-09-29T14:55:58-03:00` — registro de `OPP-4MGR` e de 5 oportunidades novas (commit `65a532b`).
- `2026-09-29T15:07:46-03:00` — **`OPP-IM3Q`** — `python-Levenshtein` não importado é removido (commit `e82451b`).
- `2026-09-29T15:07:56-03:00` — **`OPP-DW3U`** — propriedade morta `g` removida de `GenealogyGraph` (commit `c272bde`).
- `2026-09-29T15:08:03-03:00` — registro das transformações `OPP-IM3Q` e `OPP-DW3U` (commit `1cd73ee`).
- `2026-09-29T15:13:47-03:00` — **README do legado corrigido: Pyvis → Mermaid** (commit `70703f7`). Fecha divergência documental que existia desde a remoção do Pyvis.
- `2026-09-29T15:13:59-03:00` — divergência do README do legado fechada; divergências do README da raiz abertas (commit `27aaed5`).
- `2026-09-29T16:08:47-03:00` — **`OPP-U2NK`** — import `re` órfão removido (commit `c704bf9`).
- `2026-09-29T16:08:56-03:00` — **`OPP-Z6IO`** — configuração do pyrefly corrigida e supressões de tipo removidas (commit `c235701`).
- `2026-09-29T16:09:03-03:00` — evidências convertidas de UTF-16LE para UTF-8 (commit `9158405`).
- `2026-09-29T16:09:09-03:00` — README da raiz corrigido e divergências do adendo 003 fechadas (commit `689f3d9`).
- `2026-09-29T16:09:15-03:00` — **reversa-debugger** reavalia os bugs e regenera as views (commit `4a27198`).
- **Artefatos do ciclo:** `_reversa_refactor/` (7 transformações `OPP-*`), `_reversa_bugs/`, `.reversa/principles.md`.

## 2026-09-30 — Correção do escape Mermaid e re-extração

- `2026-09-30T11:16:52-03:00` — **fix:** fecha o escape do rótulo Mermaid (`BUG-20260929-J6PQ`) (commit `c709ea0`). O gatilho confirmado em navegador é **aspa dupla seguida de crase** num nome vindo do GEDCOM: o lexer desvia para *markdown-string* e o fecha-colchete nunca vira o token que a gramática exige, derrubando o diagrama inteiro. A correção inverte duas coisas: **lista branca em vez de negra**, e o escape de `&`/`<`/`>` passa a rodar **depois** do filtro. 19 testes novos; fuzz independente sem vazamento em 288 payloads combinados.
- `2026-09-30T11:17:02-03:00` — bug fechado com os dois gates (commit `122e334`).
- `2026-09-30T11:17:07-03:00` — BOM UTF-8 removido dos change sets; views regeneradas (commit `48b179d`).
- `2026-09-30T13:20:04-03:00` — **o oráculo congelado é recuperado** (commit `4e172cd`). Ele havia sumido do alcançável.
- `2026-09-30T13:20:11-03:00` — views globais do refactor regeneradas (commit `e995f9b`).
- `2026-09-30T15:11:57-03:00` — selo de proveniência padronizado no rodapé (commit `6d9bee8`).
- `2026-09-30T15:47:24-03:00` — **re-extração das specs contra a árvore atual** (commit `4c93f80`). Primeira re-extração desde 03/08: rodou Scout, Arqueólogo, Detetive, Arquiteto, Redator e Revisor no nível **essencial**, com snapshot da extração anterior em `.reversa/snapshots/2026-09-30-pre-reextracao/`.
- `2026-09-30T15:47:29-03:00` — snapshots do Reversa passam a ser ignorados pelo git (commit `3333a49`).
- `2026-09-30T16:36:42-03:00` — **entidades mortas removidas de `domain.py`** (commit `6a52d69`). `Family`, `GenealogyGraph` e `DNAGroup` eram arquitetura abandonada: nenhuma era instanciada em caminho de produção. O módulo caiu de 115 para 84 linhas.
- `2026-09-30T16:36:48-03:00` — **re-extração das specs após a remoção das entidades** (commit `5656a39`).
- **Resultado da re-extração:** 819 afirmações catalogadas, **90,5%** de confiança geral. Correções contra a extração anterior: `HARD_MIN`/`GIVEN_MIN` não existem na reconstrução; `cM ≤ 0` devolve lista vazia; a `action` de DNA é `dna_analysis` e não `process_dna`; 8 ADRs reconstruídos de 66 commits. Cinco perguntas de validação humana respondidas e aplicadas; resta uma pendente (medição de calibração do limiar 0,33).

---

## Resumo por fase

| Fase | Período | Agentes principais | Artefatos |
|------|---------|--------------------|-----------|
| Extração | 2026-08-03 | scout, archaeologist, detective, architect, writer, reviewer | `_reversa_sdd/` completo |
| Framework | 2026-08-06 | reversa (orquestrador) | reversa 1.2.58 |
| Reconstrução | 2026-08-07 | reconstructor | módulos `reconstructed/` + testes |
| Forward | 2026-08-11 | forward, requirements, plan, to-do, coding | index.html, integração app-módulos |
| Docs | 2026-08-12 | docs (mapper, analyst, storyteller, publisher) | `_reversa_docs/` mini-site |
| Licença/polimento | 2026-08-13 | — (edição manual / commits) | LICENSE, docstrings, README |
| Crônica | 2026-08-16 | docs (publisher) | `.reversa/chronicle.md`, timeline do mini-site |
| Migração | 2026-09-28 | migrate (6 agentes) + oráculo e harness de paridade | `_reversa_sdd/migration/`, `oracle/`, `parity/` |
| Refactor e bugs | 2026-09-29 | refactor, principles, debugger, sync | `_reversa_refactor/`, `_reversa_bugs/`, `principles.md` |
| Correção e re-extração | 2026-09-30 | debugger-fix, reconstructor (oráculo), core do reversa (6 agentes) | specs regeneradas, `domain.py` enxugado |

---

*Atualizado manualmente em 2026-09-30. A crônica não tem agente produtor instalado neste projeto (`reversa-chronicler` não existe no catálogo; ver `_reversa_docs/.state.json` e `references/expected_sources.yaml` do skill de docs, que o citam como produtor). A extensão de 2026-08-16 a 2026-09-30 foi derivada de `git log` (43 commits) e do `.reversa/state.json`.*