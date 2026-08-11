# Adendo — integrar a rota index() do app.py com os modulos reconstruidos

> Identificador da feature: `002-integrar-rota-app-modulos`
> Data: 2026-08-11T14:32:10Z
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Vigência

Vigente desde 2026-08-11.

## Resumo da entrega

Fechou a camada de apresentação que faltou na reconstrução: os módulos `reconstructed/` foram promovidos para `analisador-genealogico/reconstructed/` e o `app.py` deixou de conter a lógica duplicada inline (matching, Mermaid, tabela cM, helpers de nome) — as rotas `upload_gedcom`, `path_search` e `dna_analysis` agora delegam aos módulos movidos, mantendo o contrato Jinja2 com `templates/index.html` intacto. Suíte de 47 testes passou sem regressão; fluxos validados por smoke de ponta a ponta.

**Ações concluídas: 8/8** (T001–T008).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | #2 Diagrama C4 — Contexto (aplicação Flask monolítica) | regra-alterada | O `app.py` (~887 linhas) virou camada de rota fina (~70 linhas): a lógica de negócio vive agora em `analisador-genealogico/reconstructed/` (`upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py`). |
| `_reversa_sdd/architecture.md` | #5 Dívidas Técnicas | regra-removida | A dívida nº 5 ("Código monolítico com rotas + lógica acopladas") foi endereçada: rotas e lógica estão separadas. |
| `_reversa_sdd/domain.md` | #3 Regras de decisão e fluxo | regra-alterada (mantida) | Nenhuma regra de negócio mudou de comportamento; os fluxos DNA Analysis / Path Search / upload passam a ser executados pelos módulos movidos. |
| `_reversa_sdd/reconstruction-report.md` | Tarefas executadas | componente-novo | Os 4 módulos reconstruídos agora residem em `analisador-genealogico/reconstructed/` (fora da raiz do projeto). |

## Regras sob vigilância

Nenhum watch item (`W001`...) foi criado nesta rodada — ver `_reversa_forward/002-integrar-rota-app-modulos/regression-watch.md` para as observações sem peso de regressão (OBS-01: app como rota fina; OBS-02: módulos no novo local; OBS-03: HARD_MIN/GIVEN_MIN preservados).

## Fontes

- `_reversa_forward/002-integrar-rota-app-modulos/requirements.md`
- `_reversa_forward/002-integrar-rota-app-modulos/roadmap.md`
- `_reversa_forward/002-integrar-rota-app-modulos/actions.md`
- `_reversa_forward/002-integrar-rota-app-modulos/progress.jsonl`
- `_reversa_forward/002-integrar-rota-app-modulos/legacy-impact.md`
- `_reversa_forward/002-integrar-rota-app-modulos/regression-watch.md`
