# Crônica — analisador-genealogico

> Histórico cronológico dos agentes Reversa e dos artefatos gerados desde o início do projeto.
> Fontes: `.reversa/state.json`, `git log`, `_reversa_forward/**/progress.jsonl`, `_reversa_docs/.state.json`.
> Timestamps no formato ISO-8601 (horário nativo de cada fonte: `Z` para UTC, `-03:00` para local).

---

## 2026-08-03 — Inicialização e extração do sistema legado

- `2026-08-03T11:48:40Z` — **reversa-scout** — inventário da superfície. Gerou `_reversa_sdd/inventory.md`, `_reversa_sdd/dependencies.md`, `.reversa/context/surface.json`.
- `2026-08-03T12:22:00Z` — **reversa-archaeologist** — escavação do módulo `analisador-genealogico`. Gerou `_reversa_sdd/code-analysis.md`, `.reversa/context/modules.json`.
- `2026-08-03T12:31:00Z` — **reversa-detective** — conhecimento de negócio implícito. Gerou `_reversa_sdd/domain.md`.
- `2026-08-03T12:35:00Z` — **reversa-architect** — arquitetura. Gerou `_reversa_sdd/architecture.md`, `_reversa_sdd/c4-context.md`.
- `2026-08-03T12:50:00Z` — **reversa-writer** (fase geração) — specs das 3 unidades: `upload-gedcom`, `analise-dna`, `busca-caminho` (requirements.md + design.md + tasks.md cada).
- `2026-08-03T12:50:00Z` — **reversa-reviewer** — revisão e confiança. Gerou `_reversa_sdd/confidence-report.md`, `_reversa_sdd/questions.md` (4 perguntas respondidas; 1 reclassificação 🟢→🟡 no limiar HARD_MIN/GIVEN_MIN).
- `2026-08-03T12:52:00Z` — **reversa** (orquestrador) — extração completa, regression check silencioso, sem addendas pendentes.
- `2026-08-03T16:15:11-03:00` — bootstrap git `/reversa`: framework instalado, skills e templates criados (commit `e43ca22`).
- `2026-08-03T16:31:31-03:00` à `2026-08-03T18:13:45-03:00` — documentação do repo: README PT-BR, fix do parse Mermaid, autoria/créditos, contador de visitas e documentação interativa inicial (commits `d1d5707`, `d7cf49c`, `1e92fe8`, `8e80369`, `290399b`, `5fd0859`, `5f23f3d`, `d22fee9`, `10eba96`).

## 2026-08-06 — Atualização do framework

- `2026-08-06T14:35:38-03:00` — reconfiguração do projeto na nova versão do framework (commit `80e980d`).
- `2026-08-06T14:41:29-03:00` — aceite do framework **reversa 1.2.58** (commit `19564fc`).

## 2026-08-07 — Reconstrução bottom-up

- `2026-08-07T10:32:56-03:00` — **reversa-reconstructor** — plano de reconstrução: `_reversa_sdd/reconstruction-plan.md` (commit `864ac9b`).
- `2026-08-07T12:00:29-03:00` — módulos `domain.py`, `path_search.py` e `upload.py` com testes (commit `fa607b5`).
- `2026-08-07T12:43:35-03:00` — módulo `dna_analysis.py` com testes da análise de DNA (commit `5af2274`).
- `2026-08-07T12:52:39-03:00` — relatório final da reconstrução: `_reversa_sdd/reconstruction-report.md` (commit `2bf3ac3`).
- `2026-08-07T13:00:32-03:00` — testes do módulo `domain.py` (commit `73a404a`).
- `2026-08-07T13:06:05-03:00` — testes do módulo `upload.py` (commit `1d4e5d5`).
- `2026-08-07T13:10:07-03:00` — relatório final atualizado com novos testes (commit `a909066`).

## 2026-08-11 — Ciclo forward (features 001 e 002)

- `2026-08-11T13:36:03-03:00` — **reversa-forward → reversa-requirements → reversa-plan** — requirements e roadmap da feature 001 `001-reconstrua-o-conteudo-da-index` (commit `4937564`).
- `2026-08-11T13:45:55Z` — **reversa-coding** feature 001 — ações T001–T004 concluídas: reconstrução do conteúdo de `templates/index.html`.
- `2026-08-11T14:11:08-03:00` — entrega da index e requirements da integração app-módulos (feature 002) (commit `1818abb`).
- `2026-08-11T14:21:24-03:00` — **reversa-requirements → reversa-plan → reversa-to-do** — requirements, roadmap e actions da feature 002 `002-integrar-rota-app-modulos` (commit `9159c28`).
- `2026-08-11T14:30:22-03:00` — relatório `actions.md` do reversa-to-do (commit `7901d85`).
- `2026-08-11T14:32:10Z` — **reversa-coding** feature 002 — T001: módulos `reconstructed/` criados (`__init__.py`, `upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py`).
- `2026-08-11T14:33:34Z` — T002: testes `test_upload.py`, `test_path_search.py`, `test_dna_analysis.py`, `test_domain.py`.
- `2026-08-11T14:42:37Z` — T003–T006: integração das rotas no `app.py` (upload_gedcom, path_search, dna_analysis).
- `2026-08-11T14:43:52Z` — T007–T008: validação da suíte de testes e ajustes finais no `app.py`.
- `2026-08-11T16:13:47-03:00` — feat de integração dos módulos reconstruídos ao app Flask + reorganização da estrutura do projeto (commit `3ed0179`).

## 2026-08-12 — Mini-site do Reversa Docs

- `2026-08-12T13:41:00-03:00` — README com arquitetura modular e suíte de testes (commit `69ac99a`).
- `2026-08-12T14:00:00Z` — **reversa-docs** — início do pipeline (mapper, analyst, storyteller, publisher).
- `2026-08-12T14:16:28-03:00` — regeneração do mini-site `_reversa_docs/` para a arquitetura modular (commit `292b685`).
- `2026-08-12T16:16:48-03:00` — **reversa-docs-storyteller** — glossário interativo e slide deck do soul (commit `cc6ad4a`).
- `2026-08-12T18:41:35Z` — check-point final do docs: 17 páginas; timeline omitida por ausência do chronicle (que este arquivo agora resolve).

## 2026-08-13 — Licença, docstrings e merge

- `2026-08-13T01:30:56-03:00` — clarificação da licença no README (commit `bc570b4`).
- `2026-08-13T01:42:33-03:00` — adição da MIT License ao projeto (commit `3ad2cf5`).
- `2026-08-13T01:47:42-03:00` — revisão dos links da documentação no README (commit `ae58ef9`).
- `2026-08-13T10:30:26-03:00` — docstrings Google e correção de avisos do Pyrefly nos testes (commit `706f230`).
- `2026-08-13T10:47:31-03:00` — merge de `origin/master` e README com a LICENSE (commit `1b8e80e`).

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