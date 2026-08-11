# Adendo — reconstrua o conteudo da index.html

> Identificador da feature: `001-reconstrua-o-conteudo-da-index`
> Data: 2026-08-11T13:45:55Z
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Vigência

Vigente desde 2026-08-11.

## Resumo da entrega

Reconstrução fiel da interface principal (`templates/index.html`) do analisador genealógico e de DNA: estrutura base com Bootstrap 5 via CDN, formulário de upload de GEDCOM, abas "Buscar Conexão no GEDCOM" / "Analisador de DNA" com blocos condicionais Jinja2 de resultados (path_search, dna_results, skipped_matches) e spinner de loading durante submissão. Única mudança funcional: inicialização do Mermaid com `securityLevel: 'strict'` (antes `'loose'`), conforme decisão D-02 do roadmap — fecha vetor de XSS vindo dos arquivos do usuário (GEDCOM/CSV).

**Ações concluídas: 4/4** (T001, T002, T003, T004).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | #2 Diagrama C4 — Contexto (Frontend UI) | regra-alterada | A front-end segue monolítica com Bootstrap 5 + Mermaid via CDN, mas o Mermaid agora é inicializado com `securityLevel: 'strict'` — leia a index como configurada com o modo estrito de segurança. |
| `_reversa_sdd/domain.md` | #3 Regras de decisão e fluxo | regra-alterada (mantida) | Fluxos de DNA Analysis / Path Search e o estado de upload de GEDCOM continuam idênticos no front-end; nenhuma regra de negócio foi alterada ou removida. |

Nenhuma regra 🟢 do `domain.md` foi modificada ou removida (seção "Modificadas" vazia no `legacy-impact.md`).

## Regras sob vigilância

Nenhum watch item (`W001`...) foi criado nesta rodada — ver `_reversa_forward/001-reconstrua-o-conteudo-da-index/regression-watch.md` para as observações sem peso de regressão (OBS-01: código morto HARD_MIN/GIVEN_MIN; OBS-02: novo `securityLevel: 'strict'`).

## Fontes

- `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md`
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/roadmap.md`
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/actions.md`
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/progress.jsonl`
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md`
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/regression-watch.md`
